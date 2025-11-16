"""
Modular Discovery Agent - Discovers and catalogs data sources
Uses configuration-driven approach for data source discovery
"""

import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import json
from dotenv import load_dotenv
load_dotenv()
DB_URL = os.getenv("DB_URL")
print(DB_URL)

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from config_manager import AgentConfigManager, DataSourceConfig
from postgresql_db_manager import PostgreSQLCloudScanDBManager

import psycopg2


logger = logging.getLogger(__name__)

# Removed duplicate credential function - using ConfigManager instead

class ModularDiscoveryAgent:
    """
    Configuration-driven discovery agent for finding and cataloging data sources
    Multi-client aware - all operations are scoped to a specific client_id
    """
    
    def __init__(self, config_manager: AgentConfigManager = None, client_id: str = None):
        """
        Initialize the Discovery Agent
        
        Args:
            config_manager: Configuration manager instance
            client_id: Client ID for multi-tenant operations
        """
        self.client_id = client_id
        self.config_manager = config_manager or AgentConfigManager()
        
        # Try to initialize database manager, but don't fail if connection fails
        try:
            self.db_manager = PostgreSQLCloudScanDBManager(self.config_manager, client_id=client_id)
            self.db_available = True
            logger.info("✅ Database connection established")
        except Exception as e:
            logger.warning(f"⚠️ Database connection failed: {e}")
            logger.warning("Discovery will continue without database operations")
            self.db_manager = None
            self.db_available = False
        
        self.openai_api_key = self.config_manager.get_openai_api_key()
        
        # Initialize AI discovery if LLM is available
        try:
            from llm_client import get_llm_client
            self.llm_client = get_llm_client()
            self.ai_discovery_available = False  # Force disable AI to prevent hanging
            logger.info(f"LLM client initialized: {self.llm_client.provider} (AI disabled)")
        except Exception as e:
            self.llm_client = None
            self.ai_discovery_available = False
            logger.warning(f"LLM client initialization failed: {e}")
            logger.warning("Using basic discovery without AI enhancement")
        
        logger.info("✅ Modular Discovery Agent initialized")
    
    def discover_all_sources(self) -> Dict[str, Any]:
        """
        Discover all configured data sources
        
        Returns:
            Discovery results with source information
        """
        print("🔍 Starting data source discovery...")
        
        data_sources = self.config_manager.get_all_data_sources_for_client(self.client_id)
        print(f"📋 Config manager returned {len(data_sources)} data source configurations")
        
        # Log the data sources to see duplicates
        for i, source in enumerate(data_sources):
            print(f"  Source {i+1}: name='{source.name}', type='{source.type}', location='{source.location}'")
        
        discovery_results = {
            'sources_discovered': [],
            'total_sources': len(data_sources),
            'discovery_timestamp': datetime.now().isoformat(),
            'status': 'completed'
        }
        
        for source_config in data_sources:
            print(f"🔎 Discovering source: {source_config.name}")
            print(source_config)
            
            source_info = self._discover_single_source(source_config)
            if source_info:
                discovery_results['sources_discovered'].append(source_info)
                
                # Register in database with new schema - check for duplicates first
                if self.db_manager:
                    logger.info(f"🔧 Checking for existing data source '{source_config.name}' in database")
                    
                    # Map fields according to new schema:
                    # store_name = actual resource name (bucket, database, dataset)
                    # location = higher-level location info (project_id, host, etc.)
                    
                    if source_config.type in ['gcp-bucket', 'gcs']:
                        # For GCS: store_name = bucket name, location = project_id
                        actual_store_name = source_info.get('location', source_config.location)  # bucket name
                        actual_location = source_info.get('project_id', source_config.project_id)  # project_id
                    elif source_config.type == 'bigquery':
                        # For BigQuery: store_name = dataset_id, location = project_id  
                        actual_store_name = source_info.get('dataset_id', source_config.database_name or source_config.location)
                        actual_location = source_info.get('project_id', source_config.project_id)
                    elif source_config.type in ['postgresql', 'mysql']:
                        # For databases: store_name = database name, location = host
                        actual_store_name = source_info.get('database_name', source_config.database_name or source_config.location)
                        actual_location = source_info.get('host', source_config.host or 'localhost')
                    else:
                        # For other types: use original mapping
                        actual_store_name = source_config.name
                        actual_location = source_config.location
                    
                    # Check if data store already exists
                    existing_store = self.db_manager.get_data_store_by_name(actual_store_name, self.client_id)
                    
                    if existing_store:
                        # Store already exists, just update the info
                        store_id = existing_store['store_id']
                        source_info['store_id'] = store_id
                        source_info['already_exists'] = True
                        logger.info(f"✅ Found existing data source '{actual_store_name}' with store_id: {store_id}")
                        
                        # Store discovered files/objects in the database
                        discovered_items = source_info.get('discovered_files') or source_info.get('discovered_objects') or []
                        if discovered_items:
                            item_type = "files" if source_info.get('discovered_files') else "objects"
                            logger.info(f"🗃️ Storing {len(discovered_items)} discovered {item_type} for existing store_id {store_id}")
                            try:
                                # Clear existing discovered objects for this store (in case of re-discovery)
                                self.db_manager.clear_discovered_objects(store_id, self.client_id)
                                
                                # Add discovered items in batch
                                object_ids = self.db_manager.add_discovered_objects_batch(
                                    store_id, 
                                    self.client_id, 
                                    discovered_items
                                )
                                
                                if object_ids:
                                    source_info['objects_stored'] = len(object_ids)
                                    logger.info(f"✅ Stored {len(object_ids)} discovered {item_type} in database")
                                else:
                                    logger.warning(f"⚠️ Failed to store discovered {item_type}")
                                    source_info['objects_stored'] = 0
                                    
                            except Exception as e:
                                logger.error(f"❌ Error storing discovered files: {e}")
                                source_info['objects_stored'] = 0
                        else:
                            source_info['objects_stored'] = 0
                    else:
                        # Create new data store
                        logger.info(f"🔧 Creating new data store: store_name='{actual_store_name}', location='{actual_location}'")
                        
                        store_id = self.db_manager.add_data_store(
                            store_name=actual_store_name,  # Actual resource name
                            location=actual_location,      # Project/host/region info
                            store_type=source_config.type,
                            access_control=source_config.access_control or 'private',
                            client_id=self.client_id,
                            discovery_timestamp=datetime.now()
                        )
                        if store_id:
                            source_info['store_id'] = store_id
                            source_info['already_exists'] = False
                            logger.info(f"✅ Successfully created new data source '{actual_store_name}' with store_id: {store_id}")
                        else:
                            logger.error(f"❌ Failed to create data source '{actual_store_name}' in database")
                    
                    # Store discovered files/objects in the database
                    discovered_items = source_info.get('discovered_files') or source_info.get('discovered_objects') or []
                    if store_id and discovered_items:
                        item_type = "files" if source_info.get('discovered_files') else "objects"
                        logger.info(f"🗃️ Storing {len(discovered_items)} discovered {item_type} for store_id {store_id}")
                        try:
                            # Clear existing discovered objects for this store (in case of re-discovery)
                            self.db_manager.clear_discovered_objects(store_id, self.client_id)
                            
                            # Add discovered items in batch
                            object_ids = self.db_manager.add_discovered_objects_batch(
                                store_id, 
                                self.client_id, 
                                discovered_items
                            )
                            
                            if object_ids:
                                source_info['objects_stored'] = len(object_ids)
                                logger.info(f"✅ Stored {len(object_ids)} discovered {item_type} in database")
                            else:
                                logger.warning(f"⚠️ Failed to store discovered {item_type}")
                                source_info['objects_stored'] = 0
                                
                        except Exception as e:
                            logger.error(f"❌ Error storing discovered {item_type}: {e}")
                            source_info['objects_stored'] = 0
                    else:
                        source_info['objects_stored'] = 0
                else:
                    logger.warning(f"Skipping database registration for {source_config.name} due to failed DB connection.")
        
        # Update the total_sources to reflect actual unique sources processed
        discovery_results['total_sources'] = len(discovery_results['sources_discovered'])
        discovery_results['total_configurations'] = len(data_sources)  # Original count from config
        
        # Add AI-enhanced analysis if sources were discovered
        if discovery_results['sources_discovered'] and self.ai_discovery_available:
            print("🤖 Performing AI-enhanced source analysis...")
            discovery_results['ai_analysis'] = self._ai_enhanced_source_analysis(discovery_results['sources_discovered'])
        elif discovery_results['sources_discovered']:
            print("📊 Performing basic source analysis...")
            discovery_results['ai_analysis'] = self._mock_ai_source_analysis(discovery_results['sources_discovered'])
        else:
            print("📊 Skipping AI analysis - no sources discovered or AI not available")
            discovery_results['ai_analysis'] = {"analysis_type": "skipped", "reason": "no_sources_or_ai_unavailable"}
        
        print(f"✅ Discovery completed. Found {len(discovery_results['sources_discovered'])} sources")
        return discovery_results
    
    def _discover_single_source(self, source_config: DataSourceConfig) -> Optional[Dict[str, Any]]:
        """
        Discover a single data source
        
        Args:
            source_config: Configuration for the data source
            
        Returns:
            Source information dictionary or None if discovery failed
        """
        try:
            if source_config.type == 'gcp-bucket':
                return self._discover_gcs_source(source_config)
            elif source_config.type == 'postgresql':
                return self._discover_postgresql_source(source_config)
            elif source_config.type == 'bigquery':
                return self._discover_bigquery_source(source_config)
            elif source_config.type in ['csv', 'json', 'yaml']:
                return self._discover_file_source(source_config)
            else:
                logger.warning(f"Unknown source type: {source_config.type}")
                return None
                
        except Exception as e:
            logger.error(f"Error discovering source {source_config.name}: {e}")
            return None
    
    def _discover_gcs_source(self, source_config: DataSourceConfig) -> Dict[str, Any]:
        """Discover GCS bucket source"""
        try:
            # Fetch credentials dict for this client and type
            credentials_dict = self.config_manager.get_credential_dict_for_client(self.client_id, "gcp-bucket")
            from google.cloud import storage
            from google.oauth2 import service_account
            
            # Get project_id from credentials or source_config
            project_id = None
            if credentials_dict:
                project_id = credentials_dict.get('project_id')
                credentials = service_account.Credentials.from_service_account_info(credentials_dict)
                client = storage.Client(project=project_id, credentials=credentials)
            else:
                project_id = source_config.project_id
                client = storage.Client(project=project_id)
            
            # Use dataset_id from source_config.location (which contains the correct bucket name)
            bucket_name = source_config.location
            dataset_id = bucket_name  # Keep for consistency in response
            
            if not bucket_name:
                raise ValueError(f"No bucket name found in source_config.location for {source_config.name}")
                
            print(f"🔧 Using bucket name '{bucket_name}' from source_config.location for discovery")
            print(f"🔧 Using project_id '{project_id}' from credentials")
            
            bucket = client.bucket(bucket_name)
            # Get bucket metadata
            bucket.reload()
            blobs = list(bucket.list_blobs())
            
            # Analyze file types and prepare file information for storage
            file_types = {}
            total_size = 0
            discovered_files = []
            
            for blob in blobs:
                if blob.name.endswith('/'):  # Skip directories
                    continue
                    
                file_ext = blob.name.split('.')[-1].lower() if '.' in blob.name else 'unknown'
                file_types[file_ext] = file_types.get(file_ext, 0) + 1
                total_size += blob.size or 0
                
                # Prepare file information for discovered_objects table
                file_info = {
                    'name': blob.name,
                    'object_name': blob.name,
                    'file_name': blob.name.split('/')[-1],  # Just the filename
                    'path': f"gs://{bucket_name}/{blob.name}",
                    'file_path': f"gs://{bucket_name}/{blob.name}",
                    'object_path': f"gs://{bucket_name}/{blob.name}",
                    'parent_path': '/'.join(blob.name.split('/')[:-1]) if '/' in blob.name else '',
                    'type': 'file',
                    'object_type': 'file',
                    'file_type': file_ext,
                    'file_extension': file_ext,
                    'size': blob.size,
                    'size_bytes': blob.size,
                    'object_size': blob.size,
                    'modified': blob.updated,
                    'last_modified': blob.updated,
                    'checksum': blob.md5_hash,
                    'mime_type': blob.content_type,
                    'metadata': {
                        'storage_class': blob.storage_class,
                        'cache_control': blob.cache_control,
                        'content_encoding': blob.content_encoding,
                        'content_language': blob.content_language,
                        'etag': blob.etag,
                        'generation': blob.generation,
                        'metageneration': blob.metageneration,
                        'custom_metadata': dict(blob.metadata) if blob.metadata else {}
                    },
                    'is_accessible': True
                }
                discovered_files.append(file_info)
            
            source_info = {
                'name': source_config.name,
                'type': 'gcs',
                'location': bucket_name,  # Use the actual bucket name used for discovery
                'project_id': project_id,  # Use project_id from credentials
                'dataset_id': dataset_id,  # Include dataset_id in the response
                'status': 'accessible',
                'metadata': {
                    'total_files': len(blobs),
                    'total_size_bytes': total_size,
                    'file_types': file_types,
                    'created': bucket.time_created.isoformat() if bucket.time_created else None,
                    'location': bucket.location
                },
                'scanning_priority': self._calculate_priority(file_types, total_size),
                'discovery_timestamp': datetime.now().isoformat(),
                'discovered_files': discovered_files  # Add discovered files to response
            }
            print(f"  ✅ GCS bucket discovered: {len(blobs)} files, {total_size} bytes")
            return source_info
        except Exception as e:
            logger.error(f"Error discovering GCS source: {e}")
            return {
                'name': source_config.name,
                'type': 'gcs',
                'location': source_config.location,
                'status': 'error',
                'error': str(e),
                'discovery_timestamp': datetime.now().isoformat()
            }
    
    def _discover_postgresql_source(self, source_config: DataSourceConfig) -> Dict[str, Any]:
        """Discover PostgreSQL database source"""
        try:
            import psycopg2
            
            # Use database_name from source_config.database_name (which contains the correct database name)
            database_name = source_config.database_name or source_config.location
            dataset_id = database_name  # Keep for consistency in response
            
            if not database_name:
                raise ValueError(f"No database name found in source_config for {source_config.name}")
                
            print(f"🔧 Using database name '{database_name}' from source_config for discovery")
            
            conn = psycopg2.connect(
                host=source_config.host,
                port=source_config.port or 5432,
                database=database_name,
                user=source_config.username,
                password=source_config.password
            )
            
            cursor = conn.cursor()
            
            # Get database metadata with detailed table information
            cursor.execute("""
                SELECT schemaname, tablename, tableowner 
                FROM pg_tables 
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
            """)
            tables = cursor.fetchall()
            
            # Get detailed table information including size and column count
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    tableowner,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size,
                    pg_total_relation_size(schemaname||'.'||tablename) as table_size_bytes
                FROM pg_tables 
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                ORDER BY schemaname, tablename
            """)
            detailed_tables = cursor.fetchall()
            
            # Get column information for each table
            discovered_objects = []
            for schema, table, owner, table_size, table_size_bytes in detailed_tables:
                # Get column details for this table
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                """, (schema, table))
                columns = cursor.fetchall()
                
                # Create discovered object for the table
                table_object = {
                    'name': table,
                    'object_name': table,
                    'file_name': table,
                    'path': f"{database_name}.{schema}.{table}",
                    'file_path': f"{database_name}.{schema}.{table}",
                    'object_path': f"{database_name}.{schema}.{table}",
                    'parent_path': f"{database_name}.{schema}",
                    'type': 'table',
                    'object_type': 'table',
                    'file_type': 'table',
                    'file_extension': '',
                    'size': table_size_bytes or 0,
                    'size_bytes': table_size_bytes or 0,
                    'object_size': table_size_bytes or 0,
                    'modified': None,
                    'last_modified': None,
                    'checksum': None,
                    'mime_type': 'application/x-postgresql-table',
                    'metadata': {
                        'schema': schema,
                        'owner': owner,
                        'table_size_human': table_size,
                        'column_count': len(columns),
                        'columns': [
                            {
                                'name': col[0],
                                'data_type': col[1],
                                'is_nullable': col[2],
                                'column_default': col[3]
                            } for col in columns
                        ]
                    },
                    'is_accessible': True
                }
                discovered_objects.append(table_object)
            
            # Get database size
            cursor.execute(f"SELECT pg_size_pretty(pg_database_size('{database_name}'))")
            db_size = cursor.fetchone()[0]
            
            conn.close()
            
            source_info = {
                'name': source_config.name,
                'type': 'postgresql',
                'location': f"{source_config.host}:{source_config.port}/{database_name}",  # For display/logging
                'database_name': database_name,  # This will be used as store_name
                'host': source_config.host,      # This will be used as location
                'dataset_id': dataset_id,        # Include dataset_id in the response
                'status': 'accessible',
                'metadata': {
                    'total_tables': len(tables),
                    'total_objects': len(discovered_objects),
                    'database_size': db_size,
                    'database_name': database_name,
                    'schemas': list(set([table[0] for table in tables]))
                },
                'discovered_objects': discovered_objects,  # Add discovered database objects
                'scanning_priority': 'high' if len(tables) > 0 else 'low',
                'discovery_timestamp': datetime.now().isoformat()
            }
            
            print(f"  ✅ PostgreSQL database discovered: {len(tables)} tables, {len(discovered_objects)} objects in database '{database_name}'")
            return source_info
            
        except Exception as e:
            logger.error(f"Error discovering PostgreSQL source: {e}")
            return {
                'name': source_config.name,
                'type': 'postgresql',
                'location': f"{source_config.host}:{source_config.port}/{source_config.database_name}",
                'status': 'error',
                'error': str(e),
                'discovery_timestamp': datetime.now().isoformat()
            }
    
    def _discover_bigquery_source(self, source_config: DataSourceConfig) -> Dict[str, Any]:
        """Discover BigQuery dataset source"""
        try:
            # Fetch credentials dict for this client and type
            credentials_dict = self.config_manager.get_credential_dict_for_client(self.client_id, "bigquery")
            from google.cloud import bigquery
            from google.oauth2 import service_account
            
            # Get project_id from credentials or source_config
            project_id = None
            if credentials_dict:
                project_id = credentials_dict.get('project_id')
                credentials = service_account.Credentials.from_service_account_info(credentials_dict)
                client = bigquery.Client(project=project_id, credentials=credentials)
            else:
                project_id = source_config.project_id
                client = bigquery.Client(project=project_id)
            
            # Get dataset_id from client_connections table - this is the ONLY source for dataset name
            dataset_id = self.config_manager.get_dataset_id_for_connection(
                self.client_id, "bigquery", source_config.name
            )
            
            # Use dataset_id as dataset name - no fallbacks
            if not dataset_id:
                raise ValueError(f"No dataset_id found for client {self.client_id}, connection type bigquery, name {source_config.name}")
            
            print(f"🔧 Using dataset_id '{dataset_id}' from client_connections")
            print(f"🔧 Using project_id '{project_id}' from credentials")
            
            # Discover the specific dataset using dataset_id
            print(f"🔧 Using dataset_id '{dataset_id}' as BigQuery dataset name for discovery")
            try:
                dataset_ref = client.dataset(dataset_id)
                dataset = client.get_dataset(dataset_ref)
                tables = list(client.list_tables(dataset_ref))
                total_tables = len(tables)
                
                # Collect detailed table information as discovered objects
                discovered_objects = []
                for table_ref in tables:
                    try:
                        table = client.get_table(table_ref)
                        
                        # Get schema information
                        schema_fields = []
                        for field in table.schema:
                            schema_fields.append({
                                'name': field.name,
                                'field_type': field.field_type,
                                'mode': field.mode,
                                'description': field.description
                            })
                        
                        # Create discovered object for the table
                        table_object = {
                            'name': table.table_id,
                            'object_name': table.table_id,
                            'file_name': table.table_id,
                            'path': f"{project_id}.{dataset_id}.{table.table_id}",
                            'file_path': f"{project_id}.{dataset_id}.{table.table_id}",
                            'object_path': f"{project_id}.{dataset_id}.{table.table_id}",
                            'parent_path': f"{project_id}.{dataset_id}",
                            'type': 'table',
                            'object_type': 'table',
                            'file_type': 'bigquery_table',
                            'file_extension': '',
                            'size': table.num_bytes or 0,
                            'size_bytes': table.num_bytes or 0,
                            'object_size': table.num_bytes or 0,
                            'modified': table.modified.isoformat() if table.modified else None,
                            'last_modified': table.modified.isoformat() if table.modified else None,
                            'checksum': table.etag,
                            'mime_type': 'application/x-bigquery-table',
                            'metadata': {
                                'project_id': project_id,
                                'dataset_id': dataset_id,
                                'table_type': table.table_type,
                                'num_rows': table.num_rows,
                                'num_bytes': table.num_bytes,
                                'created': table.created.isoformat() if table.created else None,
                                'expires': table.expires.isoformat() if table.expires else None,
                                'schema_fields': schema_fields,
                                'field_count': len(schema_fields)
                            },
                            'is_accessible': True
                        }
                        discovered_objects.append(table_object)
                        
                    except Exception as table_error:
                        logger.warning(f"Error getting details for table {table_ref.table_id}: {table_error}")
                        # Add basic table object even if detailed info fails
                        basic_table_object = {
                            'name': table_ref.table_id,
                            'object_name': table_ref.table_id,
                            'file_name': table_ref.table_id,
                            'path': f"{project_id}.{dataset_id}.{table_ref.table_id}",
                            'file_path': f"{project_id}.{dataset_id}.{table_ref.table_id}",
                            'object_path': f"{project_id}.{dataset_id}.{table_ref.table_id}",
                            'parent_path': f"{project_id}.{dataset_id}",
                            'type': 'table',
                            'object_type': 'table',
                            'file_type': 'bigquery_table',
                            'file_extension': '',
                            'size': 0,
                            'size_bytes': 0,
                            'object_size': 0,
                            'modified': None,
                            'last_modified': None,
                            'checksum': None,
                            'mime_type': 'application/x-bigquery-table',
                            'metadata': {
                                'project_id': project_id,
                                'dataset_id': dataset_id,
                                'access_error': str(table_error)
                            },
                            'is_accessible': False,
                            'access_error': str(table_error)
                        }
                        discovered_objects.append(basic_table_object)
                
                source_info = {
                    'name': source_config.name,
                    'type': 'bigquery',
                    'location': f"{project_id}.{dataset_id}",  # For display/logging
                    'dataset_id': dataset_id,    # This will be used as store_name
                    'project_id': project_id,    # This will be used as location (from credentials)
                    'status': 'accessible',
                    'metadata': {
                        'total_datasets': 1,
                        'total_tables': total_tables,
                        'total_objects': len(discovered_objects),
                        'project_id': project_id,
                        'dataset_id': dataset_id,
                        'dataset_created': dataset.created.isoformat() if dataset.created else None,
                        'dataset_modified': dataset.modified.isoformat() if dataset.modified else None
                    },
                    'discovered_objects': discovered_objects,  # Add discovered database objects
                    'scanning_priority': 'high' if total_tables > 0 else 'low',
                    'discovery_timestamp': datetime.now().isoformat()
                }
                print(f"  ✅ BigQuery dataset discovered: {total_tables} tables, {len(discovered_objects)} objects in dataset '{dataset_id}'")
                return source_info
            except Exception as dataset_error:
                logger.error(f"Error discovering BigQuery dataset '{dataset_id}': {dataset_error}")
                raise
        except Exception as e:
            logger.error(f"Error discovering BigQuery source: {e}")
            return {
                'name': source_config.name,
                'type': 'bigquery',
                'location': project_id or 'unknown',  # Use project_id from credentials
                'status': 'error',
                'error': str(e),
                'discovery_timestamp': datetime.now().isoformat()
            }
    
    def _discover_file_source(self, source_config: DataSourceConfig) -> Dict[str, Any]:
        """Discover file-based source"""
        try:
            file_path = source_config.location
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            file_size = os.path.getsize(file_path)
            file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            source_info = {
                'name': source_config.name,
                'type': source_config.type,
                'location': file_path,
                'status': 'accessible',
                'metadata': {
                    'file_size_bytes': file_size,
                    'last_modified': file_modified.isoformat(),
                    'file_extension': source_config.type
                },
                'scanning_priority': 'medium',
                'discovery_timestamp': datetime.now().isoformat()
            }
            
            print(f"  ✅ File discovered: {file_size} bytes")
            return source_info
            
        except Exception as e:
            logger.error(f"Error discovering file source: {e}")
            return {
                'name': source_config.name,
                'type': source_config.type,
                'location': source_config.location,
                'status': 'error',
                'error': str(e),
                'discovery_timestamp': datetime.now().isoformat()
            }
    
    def _calculate_priority(self, file_types: Dict[str, int], total_size: int) -> str:
        """Calculate scanning priority based on file types and size"""
        # High priority for data files
        high_priority_types = {'csv', 'json', 'yaml', 'yml', 'xml', 'xlsx', 'sql'}
        
        high_priority_files = sum(count for ext, count in file_types.items() 
                                if ext in high_priority_types)
        
        if high_priority_files > 10 or total_size > 100 * 1024 * 1024:  # > 100MB
            return 'high'
        elif high_priority_files > 0:
            return 'medium'
        else:
            return 'low'
    
    def get_source_recommendations(self, discovery_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get scanning recommendations based on discovery results
        
        Args:
            discovery_results: Results from discover_all_sources()
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        for source in discovery_results.get('sources_discovered', []):
            if source.get('status') == 'accessible':
                if source.get('scanning_priority') == 'high':
                    recommendations.append({
                        'source_name': source['name'],
                        'recommendation': 'Immediate scanning recommended',
                        'reason': 'High-priority data source with significant content',
                        'priority': 1
                    })
                elif source.get('scanning_priority') == 'medium':
                    recommendations.append({
                        'source_name': source['name'],
                        'recommendation': 'Schedule regular scanning',
                        'reason': 'Medium-priority data source',
                        'priority': 2
                    })
            else:
                recommendations.append({
                    'source_name': source['name'],
                    'recommendation': 'Check connectivity and credentials',
                    'reason': f"Source not accessible: {source.get('error', 'Unknown error')}",
                    'priority': 3
                })
        
        # Sort by priority
        recommendations.sort(key=lambda x: x['priority'])
        
        print(f"📋 Generated {len(recommendations)} recommendations")
        return recommendations
    
    def _ai_enhanced_source_analysis(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use OpenAI for enhanced source analysis"""
        if not self.ai_discovery_available:
            return self._mock_ai_source_analysis(sources)
        
        try:
            # Prepare sources summary for AI analysis
            sources_summary = []
            for source in sources[:5]:  # Limit to first 5 for token efficiency
                sources_summary.append({
                    'name': source.get('name', 'unknown'),
                    'type': source.get('type', 'unknown'),
                    'status': source.get('status', 'unknown'),
                    'files_count': source.get('metadata', {}).get('total_files', 0),
                    'size_bytes': source.get('metadata', {}).get('total_size_bytes', 0)
                })
            
            prompt = f"""
            Analyze these discovered data sources and provide expert insights:
            
            Sources Summary: {json.dumps(sources_summary, indent=2)}
            Total Sources: {len(sources)}
            
            Please provide:
            1. Data sensitivity classification for each source
            2. Privacy risk assessment (Critical/High/Medium/Low)
            3. Recommended scanning priority order
            4. Potential compliance implications
            5. Data governance recommendations
            
            Format as JSON with actionable insights.
            """
            
            messages = [
                {"role": "system", "content": "You are a data governance and privacy expert specializing in data source classification and risk assessment."},
                {"role": "user", "content": prompt}
            ]
            
            ai_response = self.llm_client.chat_completion(
                messages=messages,
                max_tokens=600,
                temperature=0.3
            )
            
            try:
                return json.loads(ai_response)
            except json.JSONDecodeError:
                return {
                    "analysis_type": "ai_enhanced",
                    "raw_analysis": ai_response,
                    "risk_assessment": "Medium",
                    "recommendations": ["Review AI analysis manually"]
                }
                
        except Exception as e:
            logger.error(f"AI enhanced source analysis failed: {e}")
            return self._mock_ai_source_analysis(sources)
    
    def _mock_ai_source_analysis(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Provide mock AI analysis when OpenAI is not available"""
        gcs_sources = [s for s in sources if s.get('type') == 'gcs']
        db_sources = [s for s in sources if s.get('type') in ['postgresql', 'bigquery']]
        
        # Determine risk based on source types and sizes
        total_files = sum(s.get('metadata', {}).get('total_files', 0) for s in gcs_sources)
        total_tables = sum(s.get('metadata', {}).get('total_tables', 0) for s in db_sources)
        
        if total_files > 100 or total_tables > 20:
            risk_level = "High"
            priority_actions = [
                "Prioritize comprehensive scanning",
                "Implement strict access controls",
                "Conduct immediate privacy assessment"
            ]
        elif total_files > 20 or total_tables > 5:
            risk_level = "Medium"
            priority_actions = [
                "Schedule regular security scans",
                "Review data access policies",
                "Monitor data usage patterns"
            ]
        else:
            risk_level = "Low"
            priority_actions = [
                "Maintain standard monitoring",
                "Periodic compliance checks",
                "Document data sources properly"
            ]
        
        return {
            "analysis_type": "mock_ai",
            "data_sensitivity_assessment": risk_level,
            "source_classifications": {
                "cloud_storage": f"{len(gcs_sources)} sources - Potential PII exposure",
                "databases": f"{len(db_sources)} sources - Structured data analysis needed"
            },
            "priority_recommendations": priority_actions,
            "compliance_considerations": [
                "GDPR compliance review for personal data",
                "Data retention policy enforcement",
                "Regular access audit requirements"
            ],
            "governance_insights": [
                "Implement data classification standards",
                "Establish source monitoring procedures", 
                "Create data lineage documentation",
                "Deploy automated compliance scanning"
            ]
        }


def test_discovery_agent():
    """Test function for Discovery Agent"""
    print("🧪 Testing Modular Discovery Agent...")
    
    # Initialize agent
    agent = ModularDiscoveryAgent()
    
    # Discover all sources
    results = agent.discover_all_sources()
    
    print(f"\n📊 Discovery Results:")
    print(f"- Total sources configured: {results['total_sources']}")
    print(f"- Sources discovered: {len(results['sources_discovered'])}")
    
    for source in results['sources_discovered']:
        print(f"  • {source['name']} ({source['type']}): {source['status']}")
        if source.get('metadata'):
            if source['type'] == 'gcs':
                print(f"    Files: {source['metadata'].get('total_files', 0)}")
                print(f"    Size: {source['metadata'].get('total_size_bytes', 0)} bytes")
            elif source['type'] == 'postgresql':
                print(f"    Tables: {source['metadata'].get('total_tables', 0)}")
    
    # Get recommendations
    recommendations = agent.get_source_recommendations(results)
    
    print(f"\n💡 Recommendations:")
    for rec in recommendations[:3]:  # Show top 3
        print(f"  {rec['priority']}. {rec['source_name']}: {rec['recommendation']}")
        print(f"     Reason: {rec['reason']}")
    
    print("\n✅ Discovery Agent test completed!")
    return results, recommendations


if __name__ == "__main__":
    test_discovery_agent()
