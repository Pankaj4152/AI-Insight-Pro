"""
Central Configuration Manager for AI Agents
Handles database connections, credentials, and data source configurations
"""

import os
import yaml
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import psycopg2

# from backend.src.pii_detection.findings import get_all_data_stores
DB_URL = os.getenv("DB_URL")

@dataclass
class DataSourceConfig:
    """Configuration for a data source"""
    name: str
    type: str  # 'gcs', 'postgresql', 'bigquery', 'csv', 'json'
    location: str  # bucket name, file path, database host
    project_id: Optional[str] = None
    credentials_path: Optional[str] = None
    database_name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    access_control: Optional[str] = None

class AgentConfigManager:
    """
    Centralized configuration manager for all AI agents
    """
    
    def __init__(self, config_file: str = None, env_file: str = None):
        """
        Initialize configuration manager
        
        Args:
            config_file: Path to YAML config file
            env_file: Path to .env file
        """
        self.base_path = Path(__file__).parent.parent.parent
        self.config_file = config_file or str(self.base_path / "config" / "agent_config.yaml")
        self.env_file = env_file or str(self.base_path / ".env")
        self.cloudscan_db = str(self.base_path / "backend" / "cloud_scan_api" / "cloudscan.db")
        
        # Load configurations
        self.env_vars = self._load_env_vars()
        self.config = self._load_config()
        
    def _load_env_vars(self) -> Dict[str, str]:
        """Load environment variables from .env file"""
        env_vars = {}
        if os.path.exists(self.env_file):
            with open(self.env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        env_vars[key] = value
                        os.environ[key] = value
        return env_vars
    
    def _load_config(self) -> Dict[str, Any]:
        """Load YAML configuration file"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Create default config if not exists
            default_config = self._create_default_config()
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            return default_config
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        # Get database URL from environment
        db_url = os.getenv("DB_URL")
        
        # Default database configuration
        db_config = {
            'host': '34.131.224.110',
            'port': 5432,
            'database': 'master_data_privacy',
            'user': 'data_privacy_user',
            'password': 'data_privacy_db123_pass',
            'sslmode': 'prefer'
        }
        
        return {
            'database': db_config,
            'api': {
                'gcs_credentials_path': 'credentials/api-gateway-463207-e178c85cf579.json',
                'openai_api_key_env': 'OPENAI_API_KEY'
            },
            'data_sources': {
                'gcs_bucket': {
                    'name': 'ai-data-privacy',
                    'type': 'gcs',
                    'project_id': 'test-team-465710',
                    'location': 'ai-data-privacy'
                }
            },
            'scanning': {
                'max_file_size_mb': 50,
                'content_sample_size': 100,
                'perform_content_scan': True
            }
        }
    
    def get_data_source_config(self, source_name: str) -> Optional[DataSourceConfig]:
        """
        Get configuration for a specific data source
        
        Args:
            source_name: Name of the data source
            
        Returns:
            DataSourceConfig object or None if not found
        """
        sources = self.config.get('data_sources', {})
        if source_name not in sources:
            return None
        
        source_data = sources[source_name]
        
        # Resolve credentials path
        creds_path = self.config.get('credentials', {}).get('gcs_credentials_path')
        if creds_path and not os.path.isabs(creds_path):
            creds_path = str(self.base_path / creds_path)
        
        return DataSourceConfig(
            name=source_data.get('name'),
            type=source_data.get('type'),
            location=source_data.get('location'),
            project_id=source_data.get('project_id'),
            credentials_path=creds_path,
            database_name=source_data.get('database_name'),
            host=source_data.get('host'),
            port=source_data.get('port'),
            username=source_data.get('username'),
            password=source_data.get('password'),
            access_control=source_data.get('access_control', 'private')
        )
    
    
    def get_cloudscan_db_path(self) -> str:
        """Get path to cloudscan.db"""
        return self.cloudscan_db
    
    def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key from environment"""
        key_env = self.config.get('credentials', {}).get('openai_api_key_env', 'OPENAI_API_KEY')
        return os.getenv(key_env)
    
    def get_scanning_config(self) -> Dict[str, Any]:
        """Get scanning configuration"""
        return self.config.get('scanning', {})
    
    def add_data_source(self, source_config: DataSourceConfig) -> bool:
        """
        Add a new data source to configuration
        
        Args:
            source_config: DataSourceConfig object
            
        Returns:
            True if successful
        """
        try:
            if 'data_sources' not in self.config:
                self.config['data_sources'] = {}
            
            self.config['data_sources'][source_config.name] = {
                'name': source_config.name,
                'type': source_config.type,
                'location': source_config.location,
                'project_id': source_config.project_id,
                'database_name': source_config.database_name,
                'host': source_config.host,
                'port': source_config.port,
                'username': source_config.username,
                'password': source_config.password,
                'access_control': source_config.access_control
            }
            
            # Save updated config
            with open(self.config_file, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            
            return True
        except Exception as e:
            print(f"❌ Error adding data source: {e}")
            return False
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.config.get('database', {})
    
    def get_credential_path_for_client(self, client_id: str, connections_type: str) -> Optional[str]:
        """
        Get the credential file path from the client_connections table in PostgreSQL.
        This method only retrieves the path, it does not download the actual credentials.
        
        Args:
            client_id: Client ID
            connections_type: Type of connection (e.g., 'gcp', 'postgresql', etc.)
            
        Returns:
            String path to the credential file or None if not found
        """
        import json
        
        conn = psycopg2.connect(os.getenv("DB_URL", "postgresql://data_privacy_user:data_privacy_db123_pass@34.131.224.110:5432/master_data_privacy"))
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT connection_cred
                FROM client_connections
                WHERE client_id = %s AND connections_type = %s
                ORDER BY cli_conn_id DESC
                LIMIT 1
                """,
                (client_id, connections_type)
            )
            row = cursor.fetchone()
            if row:
                cred_json = row[0]
                if isinstance(cred_json, str):
                    cred_json = json.loads(cred_json)
                
                # Get the path from the stored credentials
                credential_path = cred_json.get("path")
                if credential_path:
                    print(f"✅ Found credential path for client {client_id}: {credential_path}")
                    return credential_path
                else:
                    print(f"❌ No credential path found for client {client_id}")
                    return None
            else:
                print(f"❌ No credential record found for client {client_id} with connection type {connections_type}")
                return None
        except Exception as e:
            print(f"❌ Error retrieving credential path: {e}")
            return None
        finally:
            cursor.close()
    
    def get_credential_dict_for_client(self, client_id: str, connections_type: str) -> Optional[dict]:
        """
        Download credentials JSON from GCS for a client using Cloud Run service and return it as a dict.
        The blob_name is stored in the client_connections table.
        This is the preferred method for GCS-based credentials.
        """
        import json
        import requests
        import tempfile
        
        # Get Cloud Run service URL from environment
        cloud_run_url = os.getenv("CLOUD_RUN_SERVICE_URL", "https://risk-analyzer-1071432896229.asia-south2.run.app")
        
        conn = psycopg2.connect(os.getenv("DB_URL", "postgresql://data_privacy_user:data_privacy_db123_pass@34.131.224.110:5432/master_data_privacy"))
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT connection_cred
                FROM client_connections
                WHERE client_id = %s AND connections_type = %s
                ORDER BY cli_conn_id DESC
                LIMIT 1
                """,
                (client_id, connections_type)
            )
            row = cursor.fetchone()
            if row:
                cred_json = row[0]
                if isinstance(cred_json, str):
                    cred_json = json.loads(cred_json)
                
                # Get blob_name from the stored credentials
                blob_name = cred_json.get("location")
                if not blob_name:
                    print(f"❌ No blob_name found in credentials for client {client_id}")
                    return None
                
                print(f"🔍 Found blob_name in database: {blob_name}")
                print(f"🔧 Will download from Cloud Run service: {cloud_run_url}")
                
                # Call Cloud Run service to download the file
                try:
                    url = f"{cloud_run_url}/bucket/download-json"
                    params = {
                        'client_id': client_id,
                        'blob_name': blob_name
                    }
                    
                    # Add master bucket name from environment if available
                    master_bucket_name = os.getenv("MASTER_BUCKET_NAME")
                    if master_bucket_name:
                        params['master_bucket_name'] = master_bucket_name
                        print(f"🔧 Using MASTER_BUCKET_NAME from environment: {master_bucket_name}")
                    else:
                        print("⚠️  MASTER_BUCKET_NAME not set in environment")
                    
                    print(f"🌐 Calling Cloud Run service with params: {params}")
                    response = requests.get(url, params=params)
                    response.raise_for_status()
                    result = response.json()
                    
                    if result.get('status') == 'success':
                        # The Cloud Run service returns the JSON content directly
                        credentials_dict = result.get('content')
                        if credentials_dict:
                            print(f"✅ Successfully downloaded credentials via Cloud Run for client {client_id}")
                            print(f"📄 Credential type: {credentials_dict.get('type', 'unknown')}")
                            print(f"🏢 Project ID: {credentials_dict.get('project_id', 'unknown')}")
                            return credentials_dict
                        else:
                            print(f"❌ No content found in Cloud Run response for client {client_id}")
                            return None
                    else:
                        print(f"❌ Cloud Run service returned error: {result.get('message', 'Unknown error')}")
                        return None
                        
                except requests.exceptions.RequestException as e:
                    print(f"❌ Failed to call Cloud Run service: {e}")
                    print("❌ No fallback method available - Cloud Run service is required")
                    return None
                    
            else:
                print(f"❌ No credential record found for client {client_id} with connection type {connections_type}")
                return None
        except Exception as e:
            print(f"❌ Database error: {e}")
            return None
        finally:
            cursor.close()
    


    def get_credential_dict_for_client_custom_bucket(self, client_id: str, connections_type: str, custom_bucket_name: str = None) -> Optional[dict]:
        """
        Download credentials JSON from GCS for a client using a custom bucket.
        The blob_name is stored in the client_connections table.
        
        Args:
            client_id: Client ID
            connections_type: Type of connection
            custom_bucket_name: Custom bucket name to use (optional)
        """
        import json
        import requests
        import tempfile
        
        # Get Cloud Run service URL from environment
        cloud_run_url = os.getenv("CLOUD_RUN_SERVICE_URL", "https://risk-analyzer-1071432896229.asia-south2.run.app")
        
        conn = psycopg2.connect(os.getenv("DB_URL", "postgresql://data_privacy_user:data_privacy_db123_pass@34.131.224.110:5432/master_data_privacy"))
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT connection_cred
                FROM client_connections
                WHERE client_id = %s AND connections_type = %s
                ORDER BY cli_conn_id DESC
                LIMIT 1
                """,
                (client_id, connections_type)
            )
            row = cursor.fetchone()
            if row:
                cred_json = row[0]
                if isinstance(cred_json, str):
                    cred_json = json.loads(cred_json)
                
                # Get blob_name from the stored credentials
                blob_name = cred_json.get("location")
                if not blob_name:
                    print(f"❌ No blob_name found in credentials for client {client_id}")
                    return None
                
                # Call Cloud Run service to download the file with custom bucket
                try:
                    url = f"{cloud_run_url}/bucket/download-json"
                    params = {
                        'client_id': client_id,
                        'blob_name': blob_name
                    }
                    
                    # Add custom bucket parameter if provided, otherwise use environment variable
                    if custom_bucket_name:
                        params['master_bucket_name'] = custom_bucket_name
                        print(f"🔧 Using custom bucket: {custom_bucket_name}")
                    else:
                        # Use environment variable if no custom bucket specified
                        master_bucket_name = os.getenv("MASTER_BUCKET_NAME")
                        if master_bucket_name:
                            params['master_bucket_name'] = master_bucket_name
                            print(f"🔧 Using MASTER_BUCKET_NAME from environment: {master_bucket_name}")
                    
                    response = requests.get(url, params=params)
                    response.raise_for_status()
                    result = response.json()
                    
                    if result.get('status') == 'success':
                        credentials_dict = result.get('content')
                        if credentials_dict:
                            bucket_used = custom_bucket_name or "default master bucket"
                            print(f"✅ Successfully downloaded credentials from {bucket_used} for client {client_id}")
                            return credentials_dict
                        else:
                            print(f"❌ No content found in Cloud Run response for client {client_id}")
                            return None
                    else:
                        print(f"❌ Cloud Run service returned error: {result.get('message', 'Unknown error')}")
                        return None
                        
                except requests.exceptions.RequestException as e:
                    print(f"❌ Failed to call Cloud Run service: {e}")
                    print("❌ No fallback method available - Cloud Run service is required")
                    return None
                    
            return None
        finally:
            cursor.close()
    


    def get_credential_path_for_client_legacy(self, client_id: str, connections_type: str) -> Optional[str]:
        """
        (Deprecated for GCS-based credentials. Use get_credential_dict_for_client instead.)
        Fetch credential path for a client and connection type from client_connections table
        """
        conn = psycopg2.connect(os.getenv("DB_URL", "postgresql://data_privacy_user:data_privacy_db123_pass@34.131.224.110:5432/master_data_privacy"))
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT connection_cred
                FROM client_connections
                WHERE client_id = %s AND connections_type = %s
                ORDER BY cli_conn_id DESC
                LIMIT 1
                """,
                (client_id, connections_type)
            )
            row = cursor.fetchone()
            if row:
                cred_json = row[0]
                if isinstance(cred_json, str):
                    import json
                    cred_json = cred_json["path"]
                return cred_json.get("path")
            return None
        finally:
            cursor.close()

    def get_bucket_config_info(self) -> dict:
        """
        Get information about bucket configuration from environment variables
        """
        return {
            'master_bucket_name': os.getenv("MASTER_BUCKET_NAME"),
            'gcp_bucket_name': os.getenv("GCP_BUCKET_NAME"),
            'gcp_project_id': os.getenv("GCP_PROJECT_ID"),
            'cloud_run_url': os.getenv("CLOUD_RUN_SERVICE_URL", "https://risk-analyzer-1071432896229.asia-south2.run.app")
        }

    def get_dataset_id_for_connection(self, client_id: str, connections_type: str, conn_name: str = None) -> Optional[str]:
        """
        Get dataset_id for a specific connection from client_connections table
        
        Args:
            client_id: Client ID
            connections_type: Type of connection (e.g., 'gcp-bucket', 'bigquery', 'mysql')
            conn_name: Optional connection name (uses first if not specified)
            
        Returns:
            Dataset ID string or None if not found
        """
        conn = psycopg2.connect(os.getenv("DB_URL", "postgresql://data_privacy_user:data_privacy_db123_pass@34.131.224.110:5432/master_data_privacy"))
        cursor = conn.cursor()
        try:
            if conn_name:
                # First try to get a non-'test_user_111' dataset_id if available
                cursor.execute(
                    """
                    SELECT dataset_id
                    FROM client_connections
                    WHERE client_id = %s AND connections_type = %s AND conn_name = %s
                      AND dataset_id IS NOT NULL AND dataset_id != 'test_user_111'
                    ORDER BY cli_conn_id ASC
                    LIMIT 1
                    """,
                    (client_id, connections_type, conn_name)
                )
                row = cursor.fetchone()
                
                if row and row[0]:
                    dataset_id = row[0]
                    print(f"✅ Found preferred dataset_id '{dataset_id}' for client {client_id}, type {connections_type}, conn_name {conn_name}")
                    return dataset_id
                
                # If no preferred dataset_id found, get any available one (oldest first)
                cursor.execute(
                    """
                    SELECT dataset_id
                    FROM client_connections
                    WHERE client_id = %s AND connections_type = %s AND conn_name = %s
                      AND dataset_id IS NOT NULL
                    ORDER BY cli_conn_id ASC
                    LIMIT 1
                    """,
                    (client_id, connections_type, conn_name)
                )
            else:
                cursor.execute(
                    """
                    SELECT dataset_id
                    FROM client_connections
                    WHERE client_id = %s AND connections_type = %s
                      AND dataset_id IS NOT NULL
                    ORDER BY cli_conn_id ASC
                    LIMIT 1
                    """,
                    (client_id, connections_type)
                )
            
            row = cursor.fetchone()
            if row and row[0]:
                dataset_id = row[0]
                print(f"✅ Found dataset_id '{dataset_id}' for client {client_id}, type {connections_type}")
                return dataset_id
            else:
                print(f"❌ No dataset_id found for client {client_id}, type {connections_type}")
                return None
        except Exception as e:
            print(f"❌ Error retrieving dataset_id: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

    def get_all_dataset_ids_for_client(self, client_id: str) -> Dict[str, str]:
        """
        Get all dataset_ids for a client from client_connections table
        
        Args:
            client_id: Client ID
            
        Returns:
            Dictionary mapping connection types to dataset_ids
        """
        dataset_ids = {}
        conn = psycopg2.connect(os.getenv("DB_URL", "postgresql://data_privacy_user:data_privacy_db123_pass@34.131.224.110:5432/master_data_privacy"))
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT connections_type, dataset_id, conn_name
                FROM client_connections
                WHERE client_id = %s AND dataset_id IS NOT NULL
                ORDER BY cli_conn_id DESC
                """,
                (client_id,)
            )
            for row in cursor.fetchall():
                connections_type, dataset_id, conn_name = row
                if dataset_id:
                    key = f"{connections_type}_{conn_name}" if conn_name else connections_type
                    dataset_ids[key] = dataset_id
                    print(f"✅ Found dataset_id '{dataset_id}' for {connections_type} ({conn_name})")
        except Exception as e:
            print(f"❌ Error retrieving dataset_ids: {e}")
        finally:
            cursor.close()
            conn.close()
        
        return dataset_ids

    def get_all_credential_paths_for_client(self, client_id: str) -> List[dict]:
        """
        Get all credential paths for a client from the client_connections table.
        This method only retrieves paths, it does not download actual credentials.
        
        Args:
            client_id: Client ID
            
        Returns:
            List of dictionaries containing credential information
        """
        import json
        
        credential_paths = []
        conn = psycopg2.connect(os.getenv("DB_URL", "postgresql://data_privacy_user:data_privacy_db123_pass@34.131.224.110:5432/master_data_privacy"))
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT connections_type, connection_cred, conn_name, dataset_id
                FROM client_connections
                WHERE client_id = %s
                """,
                (client_id,)
            )
            for row in cursor.fetchall():
                connections_type, connection_cred, conn_name, dataset_id = row
                if isinstance(connection_cred, str):
                    cred_json = json.loads(connection_cred)
                else:
                    cred_json = connection_cred
                
                # Extract credential path
                credential_path = cred_json.get('path')
                if credential_path:
                    credential_info = {
                        'connection_type': connections_type,
                        'connection_name': conn_name,
                        'dataset_id': dataset_id,  # Use dataset_id for bucket/database names
                        'credential_path': credential_path,
                        'location': cred_json.get('location', ''),
                        'project_id': cred_json.get('project_id'),
                        'additional_info': {k: v for k, v in cred_json.items() 
                                          if k not in ['path', 'location', 'project_id']}
                    }
                    credential_paths.append(credential_info)
                    print(f"✅ Found credential path for {conn_name} (dataset: {dataset_id}): {credential_path}")
                else:
                    print(f"⚠️  No credential path found for {conn_name}")
        except Exception as e:
            print(f"❌ Error retrieving credential paths: {e}")
        finally:
            cursor.close()
            conn.close()
        
        return credential_paths

    def get_all_data_sources_from_data_stores(self, client_id: str) -> List[DataSourceConfig]:
        """
        Get all data sources for a client from data_stores table.
        This method now uses dataset_id from client_connections table for bucket/database names.
        
        Args:
            client_id: Client ID
            
        Returns:
            List of DataSourceConfig objects
        """
        sources = []
        seen_sources = set()  # Track unique sources to avoid duplicates
        conn = psycopg2.connect(os.getenv("DB_URL", "postgresql://data_privacy_user:data_privacy_db123_pass@34.131.224.110:5432/master_data_privacy"))
        cursor = conn.cursor()
        try:
            # Get data stores and their corresponding dataset_ids and conn_names
            # Use UNION to get both discovered stores AND undiscovered connections
            cursor.execute(
                """
                -- Get discovered data stores with matching connections
                SELECT DISTINCT ON (COALESCE(ds.store_id, cc.cli_conn_id))
                       ds.store_id, ds.store_name, ds.store_type, ds.discovery_timestamp, ds.location,
                       cc.dataset_id, cc.conn_name, 'discovered' as source_type
                FROM data_stores ds
                LEFT JOIN client_connections cc ON ds.client_id = cc.client_id 
                    AND ds.store_type = cc.connections_type
                    AND ds.store_name = cc.dataset_id
                WHERE ds.client_id = %s
                
                UNION
                
                -- Get client connections that don't have matching data stores (undiscovered)
                SELECT DISTINCT ON (cc.cli_conn_id)
                       NULL as store_id, cc.dataset_id as store_name, cc.connections_type as store_type, 
                       NULL as discovery_timestamp, 
                       CASE 
                           WHEN cc.connections_type IN ('gcp-bucket', 'bigquery') THEN 'api-gateway-463207'
                           WHEN cc.connections_type IN ('mysql', 'postgresql') THEN 'localhost'
                           ELSE 'unknown-location'
                       END as location,
                       cc.dataset_id, cc.conn_name, 'undiscovered' as source_type
                FROM client_connections cc
                LEFT JOIN data_stores ds ON cc.client_id = ds.client_id 
                    AND cc.connections_type = ds.store_type
                    AND cc.dataset_id = ds.store_name
                WHERE cc.client_id = %s 
                    AND ds.store_id IS NULL
                    AND cc.dataset_id IS NOT NULL
                
                ORDER BY source_type DESC, store_id DESC NULLS LAST, conn_name
                """,
                (client_id, client_id)
            )
            
            for row in cursor.fetchall():
                store_id, store_name, store_type, discovery_timestamp, ds_location, dataset_id, conn_name, source_type = row
                
                # Use conn_name from client_connections if available, otherwise fallback to store_name
                actual_name = conn_name if conn_name else store_name
                
                # Create a unique identifier for this data source to avoid duplicates
                # Use the actual bucket/database name from store_name for uniqueness
                source_key = f"{actual_name}_{store_type}_{store_name or 'none'}"
                
                if source_key in seen_sources:
                    print(f"⚠️ Skipping duplicate data source: {actual_name} ({store_type})")
                    continue
                
                seen_sources.add(source_key)
                
                # Now store_name contains the actual resource name (bucket, database, etc.)
                # ds_location contains higher-level location info (project_id, host, etc.)
                actual_resource_name = store_name
                actual_location_info = ds_location
                
                # Build DataSourceConfig based on store information
                ds_kwargs = {
                    'name': actual_resource_name,  # Use store_name (actual resource name) as the name
                    'type': store_type,
                    'location': actual_location_info,  # Use ds_location (project_id/host) as location
                    'access_control': 'private'  # Default value since this column doesn't exist
                    # Note: conn_name is not included as DataSourceConfig doesn't support it
                }
                
                # For GCS, store_name contains bucket name, ds_location contains project_id
                if store_type in ['gcs', 'gcp-bucket', 'gcs_bucket']:
                    ds_kwargs['project_id'] = actual_location_info  # This is now project_id
                    if source_type == 'discovered':
                        print(f"🔧 NEW SCHEMA: bucket name '{actual_resource_name}' in project '{actual_location_info}' from connection '{actual_name}'")
                    else:
                        print(f"🔧 NEW SCHEMA: undiscovered bucket '{actual_resource_name}' in project '{actual_location_info}' from connection '{actual_name}'")
                
                # For PostgreSQL, store_name contains database name, ds_location contains host
                elif store_type == 'postgresql':
                    ds_kwargs['host'] = actual_location_info if actual_location_info != 'localhost' else os.getenv("DB_HOST", "localhost")
                    ds_kwargs['port'] = int(os.getenv("DB_PORT", "5432"))
                    ds_kwargs['database_name'] = actual_resource_name
                    ds_kwargs['username'] = os.getenv("DB_USER")
                    ds_kwargs['password'] = os.getenv("DB_PASSWORD")
                    print(f"🔧 NEW SCHEMA: database name '{actual_resource_name}' on host '{actual_location_info}' from connection '{actual_name}'")
                
                # For BigQuery, store_name contains dataset name, ds_location contains project_id
                elif store_type == 'bigquery':
                    ds_kwargs['project_id'] = actual_location_info  # This is now project_id
                    ds_kwargs['database_name'] = actual_resource_name  # Dataset name
                    print(f"🔧 NEW SCHEMA: dataset name '{actual_resource_name}' in project '{actual_location_info}' from connection '{actual_name}'")
                
                sources.append(DataSourceConfig(**ds_kwargs))
                print(f"✅ Found data source from data_stores: {actual_name} ({store_type}) with resource: {actual_resource_name}, location: {actual_location_info}")
                
        except Exception as e:
            print(f"❌ Error retrieving data sources from data_stores: {e}")
        finally:
            cursor.close()
            conn.close()
        
        return sources

    def get_all_data_sources_for_client(self, client_id: str) -> List[DataSourceConfig]:
        """
        Get all data source configurations for a client from client_connections table.
        This always reads from client_connections to get fresh connection configurations.
        
        Args:
            client_id: Client ID
            
        Returns:
            List of DataSourceConfig objects
        """
        # Always read from client_connections table for discovery
        print("🔧 Reading data source configurations from client_connections table")
        return self._get_data_sources_from_client_connections(client_id)
    
    def get_discovered_data_sources_for_client(self, client_id: str) -> List[DataSourceConfig]:
        """
        Get all discovered data sources for a client from data_stores table.
        This is used by scanning agents to get already discovered sources.
        
        Args:
            client_id: Client ID
            
        Returns:
            List of DataSourceConfig objects from data_stores table
        """
        print("🔧 Reading discovered data sources from data_stores table")
        return self.get_all_data_sources_from_data_stores(client_id)
    
    def get_data_stores_with_sequential_ids(self, client_id: str) -> List[Dict[str, Any]]:
        """
        Get data stores with sequential numbering (1, 2, 3, ...) for display purposes
        
        Args:
            client_id: Client ID
            
        Returns:
            List of data store dictionaries with sequential IDs
        """
        print("🔧 Getting data stores with sequential numbering")
        
        conn = psycopg2.connect(os.getenv("DB_URL", "postgresql://data_privacy_user:data_privacy_db123_pass@34.131.224.110:5432/master_data_privacy"))
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    store_id,
                    store_name,
                    store_type,
                    location,
                    discovery_timestamp,
                    ROW_NUMBER() OVER (ORDER BY store_id ASC) as client_sequence_id
                FROM data_stores 
                WHERE client_id = %s
                ORDER BY client_sequence_id ASC
            """, (client_id,))
            
            stores = []
            for row in cursor.fetchall():
                stores.append({
                    'store_id': row[0],
                    'store_name': row[1],
                    'store_type': row[2],
                    'location': row[3],
                    'discovery_timestamp': row[4].isoformat() if row[4] else None,
                    'client_sequence_id': row[5],
                    'display_name': f"Data Store #{row[5]}: {row[1]}",
                    'user_friendly_id': f"DS-{row[5]:03d}"  # DS-001, DS-002, DS-003, etc.
                })
            
            cursor.close()
            conn.close()
            
            print(f"✅ Found {len(stores)} data stores with sequential IDs for client {client_id}")
            return stores
            
        except Exception as e:
            print(f"❌ Error getting sequential data stores: {e}")
            cursor.close()
            conn.close()
            return []
    
    def _get_data_sources_from_client_connections(self, client_id: str) -> List[DataSourceConfig]:
        """
        Get all data sources for a client from client_connections table.
        This returns ALL unique combinations of conn_name and dataset_id.
        """
        sources = []
        conn = psycopg2.connect(os.getenv("DB_URL", "postgresql://data_privacy_user:data_privacy_db123_pass@34.131.224.110:5432/master_data_privacy"))
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT connections_type, connection_cred, conn_name, dataset_id, cli_conn_id
                FROM client_connections
                WHERE client_id = %s
                ORDER BY cli_conn_id
                """,
                (client_id,)
            )
            for row in cursor.fetchall():
                connections_type, connection_cred, conn_name, dataset_id, cli_conn_id = row
                if isinstance(connection_cred, str):
                    import json
                    cred_json = json.loads(connection_cred)
                else:
                    cred_json = connection_cred
                
                # Create a unique name for this specific connection+dataset combination
                unique_name = f"{conn_name}" if not dataset_id or dataset_id == 'None' else f"{conn_name}"
                
                # Build DataSourceConfig based on type
                ds_kwargs = {
                    'name': unique_name,
                    'type': connections_type,
                    'location': cred_json.get('location', ''),
                    'credentials_path': cred_json.get('path', None),
                }
                
                # Use dataset_id for specific data source identifiers
                if dataset_id and dataset_id != 'None':
                    if connections_type in ['gcp-bucket', 'gcs', 'gcs_bucket']:
                        # For GCS buckets, use dataset_id as the bucket name
                        ds_kwargs['location'] = dataset_id
                        print(f"🔧 Using dataset_id '{dataset_id}' as GCS bucket name for connection '{conn_name}' (ID: {cli_conn_id})")
                    elif connections_type == 'bigquery':
                        # For BigQuery, use dataset_id as the dataset name
                        ds_kwargs['database_name'] = dataset_id
                        print(f"🔧 Using dataset_id '{dataset_id}' as BigQuery dataset name for connection '{conn_name}' (ID: {cli_conn_id})")
                    elif connections_type in ['mysql', 'postgresql']:
                        # For databases, use dataset_id as the database name
                        ds_kwargs['database_name'] = dataset_id
                        print(f"🔧 Using dataset_id '{dataset_id}' as database name for connection '{conn_name}' (ID: {cli_conn_id})")
                else:
                    print(f"⚠️ No valid dataset_id for connection '{conn_name}' (ID: {cli_conn_id}), using location from cred_json")
                
                # Optionally add more fields if present, but prioritize environment variables for database connections
                for field in ['project_id', 'database_name', 'host', 'port', 'username', 'password', 'access_control']:
                    if field in cred_json:
                        # For database connection fields, check if we have environment variables first
                        if field in ['host', 'port', 'username', 'password'] and connections_type in ['mysql', 'postgresql']:
                            # Check if we have DB_URL environment variable
                            db_url = os.getenv("DB_URL")
                            if db_url:
                                try:
                                    from urllib.parse import urlparse
                                    url = urlparse(db_url)
                                    if field == 'host' and url.hostname:
                                        ds_kwargs[field] = url.hostname
                                        print(f"🔧 Using DB_URL host ({url.hostname}) instead of database value")
                                    elif field == 'port' and url.port:
                                        ds_kwargs[field] = url.port
                                        print(f"🔧 Using DB_URL port ({url.port}) instead of database value")
                                    elif field == 'username' and url.username:
                                        ds_kwargs[field] = url.username
                                        print(f"🔧 Using DB_URL username instead of database value")
                                    elif field == 'password' and url.password:
                                        ds_kwargs[field] = url.password
                                        print(f"🔧 Using DB_URL password instead of database value")
                                    else:
                                        ds_kwargs[field] = cred_json[field]
                                except Exception as e:
                                    print(f"Warning: Could not parse DB_URL for field {field}: {e}")
                                    ds_kwargs[field] = cred_json[field]
                            else:
                                ds_kwargs[field] = cred_json[field]
                        else:
                            ds_kwargs[field] = cred_json[field]
                
                sources.append(DataSourceConfig(**ds_kwargs))
                print(f"✅ Created DataSourceConfig for {conn_name} ({connections_type}) with dataset_id: {dataset_id} (ID: {cli_conn_id})")
        finally:
            cursor.close()
            conn.close()
        return sources

