"""
Cloud Scanner Module
Handles scanning of GCP BigQuery and Google Cloud Storage
"""

import logging
import tempfile
import json
import os
from typing import Dict, List, Any, Optional
from .base_scanner import BaseScanner

# Import config_manager for credential handling
try:
    from config_manager import AgentConfigManager
    CONFIG_MANAGER_AVAILABLE = True
except ImportError:
    CONFIG_MANAGER_AVAILABLE = False

logger = logging.getLogger(__name__)

# Now we can use logger
if not CONFIG_MANAGER_AVAILABLE:
    logger.warning("Config manager not available. Will use local credential files.")

try:
    from google.cloud import bigquery
    from google.cloud import storage
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    logger.warning("Google Cloud libraries not available. Install google-cloud-bigquery and google-cloud-storage for full functionality.")


class CloudScanner(BaseScanner):
    """Base scanner for cloud data sources"""
    
    def scan(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scan cloud source based on type
        
        Args:
            source: Cloud source configuration
            
        Returns:
            List of SDE findings
        """
        source_type = source.get('type', '').lower()
        
        if 'bigquery' in source_type:
            return BigQueryScanner(self.privacy_patterns, self.field_mappings, self.sde_categories).scan(source)
        elif 'gcs' in source_type or 'cloud_storage' in source_type:
            return GCSScanner(self.privacy_patterns, self.field_mappings, self.sde_categories).scan(source)
        else:
            logger.warning(f"Unsupported cloud source type: {source_type}")
            return []


class BigQueryScanner(BaseScanner):
    """Scanner for Google BigQuery datasets and tables"""
    
    def scan(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scan BigQuery dataset/table for SDEs
        
        Args:
            source: BigQuery configuration containing project, dataset, table info
            
        Returns:
            List of SDE findings
        """
        findings = []
        
        if not GOOGLE_CLOUD_AVAILABLE:
            logger.error("Google Cloud libraries not available. Cannot scan BigQuery.")
            return findings
        
        try:
            # Initialize BigQuery client
            project_id = source.get('project_id')
            client_id = source.get('client_id')
            
            # First, check if credentials are already provided in the source config
            if 'credentials' in source and source['credentials'] is not None:
                # Use the credentials object that was already created
                cred_dict = source['credentials']
                logger.info("Using provided credentials object for BigQuery client")
                
                # Create temporary credentials file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                    json.dump(cred_dict, temp_file)
                    temp_cred_path = temp_file.name
                
                try:
                    client = bigquery.Client.from_service_account_json(temp_cred_path, project=project_id)
                    logger.info(f"BigQuery client created with project: {project_id}")
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_cred_path):
                        os.unlink(temp_cred_path)
            # Use config_manager to get credentials if available
            elif CONFIG_MANAGER_AVAILABLE and client_id:
                try:
                    config_manager = AgentConfigManager()
                    cred_dict = config_manager.get_credential_dict_for_client(client_id, 'bigquery')
                    
                    if cred_dict:
                        # Create temporary credentials file
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                            json.dump(cred_dict, temp_file)
                            temp_cred_path = temp_file.name
                        
                        try:
                            client = bigquery.Client.from_service_account_json(temp_cred_path, project=project_id)
                        finally:
                            # Clean up temporary file
                            if os.path.exists(temp_cred_path):
                                os.unlink(temp_cred_path)
                    else:
                        logger.warning(f"No credentials found for client {client_id}, using default credentials")
                        client = bigquery.Client(project=project_id)
                        
                except Exception as e:
                    logger.warning(f"Failed to get credentials via config_manager: {e}, using default credentials")
                    client = bigquery.Client(project=project_id)
            else:
                # Fallback to local credentials path
                credentials_path = source.get('credentials_path')
                if credentials_path:
                    client = bigquery.Client.from_service_account_json(credentials_path, project=project_id)
                else:
                    client = bigquery.Client(project=project_id)
            
            dataset_id = source.get('dataset_id')
            table_id = source.get('table_id')
            
            if table_id:
                # Scan specific table
                findings.extend(self._scan_bigquery_table(client, dataset_id, table_id, source))
            else:
                # Scan entire dataset
                findings.extend(self._scan_bigquery_dataset(client, dataset_id, source))
                
        except Exception as e:
            logger.error(f"Error scanning BigQuery source: {str(e)}")
        
        return findings
    
    def _scan_bigquery_dataset(self, client, dataset_id: str, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan all tables in a BigQuery dataset"""
        findings = []
        
        try:
            dataset_ref = client.dataset(dataset_id)
            tables = client.list_tables(dataset_ref)
            
            for table in tables:
                table_findings = self._scan_bigquery_table(
                    client, dataset_id, table.table_id, source
                )
                findings.extend(table_findings)
                
        except Exception as e:
            logger.error(f"Error scanning BigQuery dataset {dataset_id}: {str(e)}")
        
        return findings
    
    def _scan_bigquery_table(self, client, dataset_id: str, table_id: str, 
                            source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan a specific BigQuery table"""
        findings = []
        
        try:
            table_ref = client.dataset(dataset_id).table(table_id)
            table = client.get_table(table_ref)
            
            # Analyze table schema
            for field in table.schema:
                field_findings = self.analyze_field_name(
                    field.name, field.field_type, f"{dataset_id}.{table_id}", source
                )
                findings.extend(field_findings)
            
            # Sample data for content analysis if enabled
            if source.get('perform_content_scan', True):
                content_findings = self._scan_bigquery_table_content(
                    client, dataset_id, table_id, table.schema, source
                )
                findings.extend(content_findings)
                
        except Exception as e:
            logger.error(f"Error scanning BigQuery table {dataset_id}.{table_id}: {str(e)}")
        
        return findings
    
    def _scan_bigquery_table_content(self, client, dataset_id: str, table_id: str,
                                    schema, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan BigQuery table content for SDE patterns"""
        findings = []
        
        try:
            sample_size = source.get('content_sample_size', 100)
            
            # Create sampling query for each string field
            for field in schema:
                if field.field_type in ['STRING', 'TEXT']:
                    query = f"""
                    SELECT {field.name}
                    FROM `{client.project}.{dataset_id}.{table_id}`
                    WHERE {field.name} IS NOT NULL
                    LIMIT {sample_size}
                    """
                    
                    query_job = client.query(query)
                    results = query_job.result()
                    
                    for row in results:
                        content = str(row[0]) if row[0] is not None else ""
                        if content and len(content.strip()) > 0:
                            content_findings = self.analyze_field_content(
                                content, field.name, source
                            )
                            findings.extend(content_findings)
                            
        except Exception as e:
            logger.warning(f"Error scanning BigQuery table content: {str(e)}")
        
        return findings


class GCSScanner(BaseScanner):
    """Scanner for Google Cloud Storage buckets"""
    
    def scan(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scan GCS bucket for files containing SDEs
        
        Args:
            source: GCS configuration containing bucket and path info
            
        Returns:
            List of SDE findings
        """
        findings = []
        
        logger.info(f"🔍 GCSScanner.scan() called with source keys: {list(source.keys())}")
        logger.info(f"🔧 Source config: bucket_name={source.get('bucket_name')}, project_id={source.get('project_id')}")
        
        if not GOOGLE_CLOUD_AVAILABLE:
            logger.error("❌ Google Cloud libraries not available. Cannot scan GCS.")
            return findings
        
        try:
            # Initialize GCS client
            project_id = source.get('project_id')
            client_id = source.get('client_id')
            
            logger.info(f"🔧 Initializing GCS client for project_id={project_id}, client_id={client_id}")
            
            # First, check if credentials are already provided in the source config
            if 'credentials' in source and source['credentials'] is not None:
                # Use the credentials object that was already created
                logger.info("✅ Using provided credentials object for GCS client")
                client = storage.Client(project=project_id, credentials=source['credentials'])
                logger.info(f"✅ GCS client created with provided credentials for project: {project_id}")
            # Use config_manager to get credentials if available
            elif CONFIG_MANAGER_AVAILABLE and client_id:
                logger.info(f"🔑 Attempting to get credentials via config_manager for client_id={client_id}")
                try:
                    config_manager = AgentConfigManager()
                    cred_dict = config_manager.get_credential_dict_for_client(client_id, 'gcp-bucket')
                    
                    if cred_dict:
                        logger.info(f"✅ Found credentials via config_manager: type={cred_dict.get('type', 'unknown')}")
                        # Create temporary credentials file
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                            json.dump(cred_dict, temp_file)
                            temp_cred_path = temp_file.name
                        
                        try:
                            logger.info(f"🔧 Creating GCS client from temporary credentials file: {temp_cred_path}")
                            client = storage.Client.from_service_account_json(temp_cred_path, project=project_id)
                            logger.info(f"✅ GCS client created from temporary credentials for project: {project_id}")
                        finally:
                            # Clean up temporary file
                            if os.path.exists(temp_cred_path):
                                os.unlink(temp_cred_path)
                                logger.info(f"🧹 Cleaned up temporary credentials file: {temp_cred_path}")
                    else:
                        logger.warning(f"⚠️ No credentials found for client {client_id}, using default credentials")
                        client = storage.Client(project=project_id)
                        logger.info(f"✅ GCS client created with default credentials for project: {project_id}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed to get credentials via config_manager: {e}, using default credentials")
                    client = storage.Client(project=project_id)
                    logger.info(f"✅ GCS client created with default credentials after config_manager failure")
            else:
                logger.info("🔧 Using fallback credential methods")
                # Fallback to local credentials path
                credentials_path = source.get('credentials_path')
                if credentials_path:
                    logger.info(f"🔧 Using credentials path: {credentials_path}")
                    client = storage.Client.from_service_account_json(credentials_path, project=project_id)
                    logger.info(f"✅ GCS client created from credentials path for project: {project_id}")
                else:
                    logger.info("🔧 No credentials path found, using default credentials")
                    client = storage.Client(project=project_id)
                    logger.info(f"✅ GCS client created with default credentials for project: {project_id}")
            
            bucket_name = source.get('bucket_name')
            prefix = source.get('prefix', '')
            
            logger.info(f"🔍 Accessing bucket: {bucket_name} with prefix: {prefix}")
            
            bucket = client.bucket(bucket_name)
            logger.info(f"✅ Bucket object created for: {bucket_name}")
            
            # Test bucket access
            try:
                bucket.reload()
                logger.info(f"✅ Successfully accessed bucket: {bucket_name}")
            except Exception as e:
                logger.error(f"❌ Failed to access bucket {bucket_name}: {e}")
                raise
            
            blobs = bucket.list_blobs(prefix=prefix)
            blob_list = list(blobs)  # Convert to list to get count
            logger.info(f"📁 Found {len(blob_list)} blobs in bucket {bucket_name}")
            
            # Log some sample blobs for debugging
            for i, blob in enumerate(blob_list[:5]):  # Show first 5 blobs
                logger.info(f"  Blob {i+1}: {blob.name} ({blob.size} bytes)")
            
            for blob in blob_list:
                logger.info(f"🔍 Scanning blob: {blob.name}")
                blob_findings = self._scan_gcs_blob(blob, source)
                logger.info(f"  Found {len(blob_findings)} findings in {blob.name}")
                findings.extend(blob_findings)
                
            logger.info(f"✅ GCSScanner.scan() completed. Total findings: {len(findings)}")
                
        except Exception as e:
            logger.error(f"❌ Error scanning GCS bucket: {str(e)}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        
        return findings
    
    def _scan_gcs_blob(self, blob, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan individual GCS blob/file"""
        findings = []
        
        try:
            # Determine file type from name
            file_name = blob.name
            file_extension = file_name.split('.')[-1].lower() if '.' in file_name else ''
            
            logger.info(f"🔍 Scanning blob: {file_name} (extension: {file_extension}, size: {blob.size} bytes)")
            
            # Skip non-data files
            if file_extension not in ['csv', 'json', 'yaml', 'yml', 'txt']:
                logger.info(f"⏭️ Skipping non-data file: {file_name} (extension: {file_extension})")
                return findings
            
            # Skip large files to avoid memory issues
            max_file_size = source.get('max_file_size_mb', 50) * 1024 * 1024
            if blob.size > max_file_size:
                logger.warning(f"⏭️ Skipping large file {file_name} ({blob.size} bytes > {max_file_size} bytes)")
                return findings
            
            # Download and scan file content
            logger.info(f"📥 Downloading content from {file_name}")
            content = blob.download_as_text()
            logger.info(f"✅ Downloaded {len(content)} characters from {file_name}")
            
            if file_extension == 'csv':
                logger.info(f"🔍 Scanning CSV content from {file_name}")
                findings = self._scan_csv_content(content, file_name, source)
            elif file_extension == 'json':
                logger.info(f"🔍 Scanning JSON content from {file_name}")
                findings = self._scan_json_content(content, file_name, source)
            elif file_extension in ['yaml', 'yml']:
                logger.info(f"🔍 Scanning YAML content from {file_name}")
                findings = self._scan_yaml_content(content, file_name, source)
            else:
                # Generic text scanning
                logger.info(f"🔍 Scanning text content from {file_name}")
                findings = self._scan_text_content(content, file_name, source)
            
            logger.info(f"✅ Completed scanning {file_name}. Found {len(findings)} findings")
                
        except Exception as e:
            logger.warning(f"⚠️ Error scanning GCS blob {blob.name}: {str(e)}")
            logger.warning(f"⚠️ Exception type: {type(e).__name__}")
        
        return findings
    
    def _scan_csv_content(self, content: str, file_name: str, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan CSV content from GCS"""
        findings = []
        
        try:
            import io
            import csv
            
            csv_reader = csv.reader(io.StringIO(content))
            headers = next(csv_reader)
            
            # Analyze headers
            for header in headers:
                field_findings = self.analyze_field_name(
                    header, 'string', file_name, source
                )
                findings.extend(field_findings)
            
            # Sample content analysis
            if source.get('perform_content_scan', True):
                sample_rows = 0
                max_samples = source.get('content_sample_size', 100)
                
                for row in csv_reader:
                    if sample_rows >= max_samples:
                        break
                    
                    for i, value in enumerate(row):
                        if i < len(headers) and value:
                            content_findings = self.analyze_field_content(
                                value, headers[i], source
                            )
                            findings.extend(content_findings)
                    
                    sample_rows += 1
                    
        except Exception as e:
            logger.warning(f"Error scanning CSV content: {str(e)}")
        
        return findings
    
    def _scan_json_content(self, content: str, file_name: str, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan JSON content from GCS"""
        findings = []
        
        try:
            import json
            data = json.loads(content)
            
            # Use JSON scanner logic
            from .file_scanner import JSONScanner
            json_scanner = JSONScanner(self.privacy_patterns, self.field_mappings, self.sde_categories)
            findings = json_scanner._scan_json_object(data, source, file_name)
            
        except Exception as e:
            logger.warning(f"Error scanning JSON content: {str(e)}")
        
        return findings
    
    def _scan_yaml_content(self, content: str, file_name: str, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan YAML content from GCS"""
        findings = []
        
        try:
            import yaml
            data = yaml.safe_load(content)
            
            # Use YAML scanner logic
            from .file_scanner import YAMLScanner
            yaml_scanner = YAMLScanner(self.privacy_patterns, self.field_mappings, self.sde_categories)
            findings = yaml_scanner._scan_yaml_object(data, source, file_name)
            
        except Exception as e:
            logger.warning(f"Error scanning YAML content: {str(e)}")
        
        return findings
    
    def _scan_text_content(self, content: str, file_name: str, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan generic text content for patterns"""
        findings = []
        
        # Analyze content for SDE patterns
        content_findings = self.analyze_field_content(
            content, file_name, source
        )
        findings.extend(content_findings)
        
        return findings
