"""
PostgreSQL Database Manager for Data Protection Agents
Handles all database operations for storing scan results and findings using PostgreSQL
"""

import psycopg2
import psycopg2.extras
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import os
from urllib.parse import urlparse
from dotenv import load_dotenv
import yaml

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

logger = logging.getLogger(__name__)

class PostgreSQLCloudScanDBManager:
    """
    Manages all database operations using PostgreSQL for cloud scan results
    Multi-client aware - all operations are scoped to a specific client_id
    """
    
    def __init__(self, config_manager=None, connection_config: Dict[str, Any] = None, client_id: str = None):
        """
        Initialize PostgreSQL database manager
        
        Args:
            config_manager: Configuration manager instance
            connection_config: Direct connection configuration
            client_id: Client ID for multi-tenant operations
        """
        self.config_manager = config_manager
        self.client_id = client_id
        self.connection_config = connection_config or self._get_connection_config()
        self.connection_pool = None
        self._sde_cache = {}  # Cache for SDE lookups
        self._test_connection()
    
    def set_client_id(self, client_id: str):
        """Set the client ID for all subsequent operations"""
        self.client_id = client_id
        self._sde_cache = {}  # Clear cache when switching clients
    
    def get_client_connection_credentials(self, client_id: str, conn_name: str = None) -> Dict[str, Any]:
        """
        Get database connection credentials for a specific client
        
        Args:
            client_id: Client ID
            conn_name: Optional connection name (uses first if not specified)
            
        Returns:
            Connection credentials dictionary
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if conn_name:
                cursor.execute("""
                    SELECT connection_cred FROM client_connections 
                    WHERE client_id = %s AND conn_name = %s
                """, (client_id, conn_name))
            else:
                cursor.execute("""
                    SELECT connection_cred FROM client_connections 
                    WHERE client_id = %s LIMIT 1
                """, (client_id,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result and result[0]:
                return result[0]  # JSON column
            return None
            
        except Exception as e:
            logger.error(f"Error getting client connection credentials: {e}")
            return None
    
    def _get_connection_config(self) -> Dict[str, Any]:
        """
        Get PostgreSQL connection configuration from various sources
        
        Returns:
            Connection configuration dictionary
        """
        # Priority order: environment variables, config manager, default config file
        
        # Option 1: Environment variables (Cloud deployment)
        if os.getenv('DB_URL'):
            # Parse DATABASE_URL (common in cloud deployments)
            url = urlparse(os.getenv('DB_URL'))
            logger.info(f"🔗 Using DB_URL from environment: {url.hostname}:{url.port}/{url.path[1:]}")
            return {
                'host': url.hostname,
                'port': url.port or 5432,
                'database': url.path[1:],  # Remove leading /
                'user': url.username,
                'password': url.password,
                'sslmode': 'require'
            }
        
        # Option 2: Individual environment variables
        if os.getenv('POSTGRES_HOST'):
            logger.info(f"🔗 Using POSTGRES_HOST from environment: {os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT', 5432)}/{os.getenv('POSTGRES_DATABASE')}")
            return {
                'host': os.getenv('POSTGRES_HOST'),
                'port': int(os.getenv('POSTGRES_PORT', 5432)),
                'database': os.getenv('POSTGRES_DATABASE'),
                'user': os.getenv('POSTGRES_USER'),
                'password': os.getenv('POSTGRES_PASSWORD'),
                'sslmode': os.getenv('POSTGRES_SSL_MODE', 'prefer')
            }
        
        # Option 3: Config manager
        if self.config_manager:
            postgres_config = self.config_manager.get_database_config().get('postgresql', {})
            if postgres_config:
                return postgres_config
        
        # Option 4: YAML configuration file
        try:
            import yaml
            config_path = os.path.join(os.path.dirname(__file__), 'agent_config.yaml')
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            
            db_config = config['database']['postgresql']
            logger.info(f"Using config file: {db_config['host']}:{db_config['port']}/{db_config['database']}")
            return db_config
        except Exception as e:
            logger.debug(f"Could not load YAML config: {e}")
        
        # Option 5: Default config file
        try:
            from postgress_db.config import CONFIG
            return {
                'host': CONFIG.get('host', 'localhost'),
                'port': CONFIG.get('port', 5432),
                'database': CONFIG.get('database_name'),
                'user': CONFIG.get('database_user'),
                'password': CONFIG.get('db_password'),
                'sslmode': CONFIG.get('sslmode', 'prefer')
            }
        except ImportError:
            pass
        
        # Option 5: Default localhost configuration
        logger.warning("WARNING: No PostgreSQL configuration found, using localhost defaults")
        return {
            'host': 'localhost',
            'port': 5432,
            'database': 'data_protection',
            'user': 'postgres',
            'password': 'password',
            'sslmode': 'prefer'
        }
    
    def _test_connection(self):
        """Test database connection and create tables if needed"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT version()")
            version = cursor.fetchone()
            # Handle both dict and tuple responses
            if isinstance(version, dict) and "version" in version:
                version_str = version["version"]
            elif isinstance(version, (list, tuple)) and len(version) > 0:
                version_str = version[0]
            else:
                version_str = str(version)
            logger.info(f"Connected to PostgreSQL: {version_str}")
            
            # Ensure required tables exist
            self._ensure_tables_exist(cursor)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("PostgreSQL database connection verified")
            
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            raise
    
    def get_connection(self, use_dict_cursor: bool = True):
        """Get database connection"""
        try:
            conn = psycopg2.connect(**self.connection_config)
            if use_dict_cursor:
                # Set the cursor factory to RealDictCursor for dictionary-like access
                conn.cursor_factory = psycopg2.extras.RealDictCursor
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def _ensure_tables_exist(self, cursor):
        """Ensure all required tables exist - using existing schema"""
        
        # Check if tables exist, but don't create them since they already exist in your database
        # Just verify the main tables are there
        
        required_tables = ['data_stores', 'scans', 'scan_findings', 'scan_baselines', 'regexes']
        
        for table in required_tables:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s AND table_schema = 'public'
                )
            """, (table,))
            
            result = cursor.fetchone()
            # Handle both dict and tuple responses
            if isinstance(result, dict) and "exists" in result:
                exists = result["exists"]
            elif isinstance(result, (list, tuple)) and len(result) > 0:
                exists = result[0]
            else:
                exists = False
                
            if not exists:
                logger.warning(f"Required table {table} does not exist in database")
            else:
                logger.debug(f"Table {table} exists")
        
        logger.info("Using existing PostgreSQL tables")
    
    def add_data_store(self, store_name: str, location: str, store_type: str, access_control: str = 'private', client_id: str = None, discovery_timestamp: datetime = None) -> int:
        """
        Add a data store entry
        
        Args:
            store_name: Name of the data store
            location: Location/path of the data store
            store_type: Type of store (gcs, postgresql, etc.)
            access_control: Access control level
            client_id: Client ID (uses instance client_id if not provided)
            discovery_timestamp: Timestamp when the store was discovered
            
        Returns:
            store_id of the created entry
        """
        # Use provided client_id or fall back to instance client_id
        effective_client_id = client_id or self.client_id
        if not effective_client_id:
            raise ValueError("client_id is required for multi-tenant operations")
            
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if store already exists for this client
            cursor.execute("""
                SELECT store_id FROM data_stores 
                WHERE store_name = %s AND location = %s AND client_id = %s
            """, (store_name, location, effective_client_id))
            
            existing = cursor.fetchone()
            
            if existing:
                store_id = existing[0]
                logger.info(f"Data store already exists with ID: {store_id}")
            else:
                # Check what columns exist in the data_stores table for INSERT
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'data_stores' AND table_schema = 'public'
                    ORDER BY ordinal_position
                """)
                
                available_columns = [row[0] for row in cursor.fetchall()]
                
                # Build INSERT query based on available columns
                insert_columns = ['store_name', 'location', 'client_id']
                insert_values = [store_name, location, effective_client_id]
                placeholders = ['%s', '%s', '%s']
                
                # Add type column
                if 'type' in available_columns:
                    insert_columns.append('type')
                    insert_values.append(store_type)
                    placeholders.append('%s')
                elif 'store_type' in available_columns:
                    insert_columns.append('store_type')
                    insert_values.append(store_type)
                    placeholders.append('%s')
                
                # Add access_control column if it exists
                if 'access_control' in available_columns:
                    insert_columns.append('access_control')
                    insert_values.append(access_control)
                    placeholders.append('%s')
                
                # Add discovery_timestamp column if it exists
                if 'discovery_timestamp' in available_columns:
                    insert_columns.append('discovery_timestamp')
                    timestamp_value = discovery_timestamp or datetime.now()
                    insert_values.append(timestamp_value)
                    placeholders.append('%s')
                
                columns_sql = ', '.join(insert_columns)
                placeholders_sql = ', '.join(placeholders)
                
                cursor.execute(f"""
                    INSERT INTO data_stores ({columns_sql})
                    VALUES ({placeholders_sql})
                    RETURNING store_id
                """, tuple(insert_values))
                
                store_id = cursor.fetchone()[0]
                logger.info(f"Created new data store with ID: {store_id} for client: {effective_client_id}")
            
            conn.commit()
            cursor.close()
            conn.close()
            return store_id
            
        except Exception as e:
            logger.error(f"Error adding data store: {e}")
            return None
    
    def get_data_store_by_name(self, store_name: str, client_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Get data store information by name for a specific client
        
        Args:
            store_name: Name of the data store
            client_id: Client ID (uses instance client_id if not provided)
            
        Returns:
            Dictionary with data store information or None if not found
        """
        # Use provided client_id or fall back to instance client_id
        effective_client_id = client_id or self.client_id
        if not effective_client_id:
            raise ValueError("client_id is required for multi-tenant operations")
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check what columns exist in the data_stores table
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'data_stores' AND table_schema = 'public'
                ORDER BY ordinal_position
            """)
            
            all_columns = [row[0] for row in cursor.fetchall()]
            
            # Build the SELECT query based on available columns
            select_columns = ['store_id', 'store_name', 'location']
            
            # Add type column (could be 'type' or 'store_type')
            if 'type' in all_columns:
                select_columns.append('type')
                type_column_index = 3
            elif 'store_type' in all_columns:
                select_columns.append('store_type')
                type_column_index = 3
            else:
                # Add a placeholder
                select_columns.append("'unknown' as type")
                type_column_index = 3
            
            # Add access_control column if it exists
            if 'access_control' in all_columns:
                select_columns.append('access_control')
                access_control_index = 4
            else:
                select_columns.append("'private' as access_control")
                access_control_index = 4
            
            select_sql = ', '.join(select_columns)
            
            cursor.execute(f"""
                SELECT {select_sql}
                FROM data_stores 
                WHERE store_name = %s AND client_id = %s
            """, (store_name, effective_client_id))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                return {
                    'store_id': result[0],
                    'store_name': result[1],
                    'location': result[2],
                    'store_type': result[3],
                    'access_control': result[4]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting data store by name {store_name}: {e}")
            return None
    
    def create_scan(self, store_id: int, scan_data: Dict[str, Any]) -> int:
        """
        Create a new scan entry
        
        Args:
            store_id: ID of the data store being scanned
            scan_data: Scan configuration and metadata
            
        Returns:
            scan_id of the created entry
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get available columns in scans table
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'scans' 
                ORDER BY ordinal_position
            """)
            available_columns = [row[0] for row in cursor.fetchall()]
            
            # Prepare data for insertion
            insert_data = {
                'store_id': store_id,
                'scan_data': json.dumps(scan_data) if isinstance(scan_data, dict) else scan_data,
                'status': scan_data.get('status', 'pending')
            }
            
            # Add regex_id if column exists - get a default regex pattern
            if 'regex_id' in available_columns:
                # Try to get a generic pattern or the first available one
                cursor.execute("SELECT regex_id FROM regexes WHERE pattern_name IN ('email', 'phone', 'general') LIMIT 1")
                regex_result = cursor.fetchone()
                if regex_result:
                    insert_data['regex_id'] = regex_result[0]
                else:
                    # Get any available regex as fallback
                    cursor.execute("SELECT regex_id FROM regexes LIMIT 1")
                    fallback_regex = cursor.fetchone()
                    if fallback_regex:
                        insert_data['regex_id'] = fallback_regex[0]
            
            # Add pattern_id if column exists - since data_patterns table doesn't exist, we'll leave it NULL or create a dummy value
            if 'pattern_id' in available_columns:
                # For now, we'll set it to 1 as a default pattern ID
                # You might want to create proper pattern entries in your database
                insert_data['pattern_id'] = 1
            
            # Add optional timestamp columns if they exist
            if 'created_at' in available_columns:
                insert_data['created_at'] = 'CURRENT_TIMESTAMP'
            if 'started_at' in available_columns:
                insert_data['started_at'] = 'CURRENT_TIMESTAMP'
                
            # Build dynamic INSERT query
            columns = [col for col in insert_data.keys() if col in available_columns]
            values_placeholders = []
            values = []
            
            for col in columns:
                if insert_data[col] == 'CURRENT_TIMESTAMP':
                    values_placeholders.append('CURRENT_TIMESTAMP')
                else:
                    values_placeholders.append('%s')
                    values.append(insert_data[col])
            
            columns_sql = ', '.join(columns)
            values_sql = ', '.join(values_placeholders)
            
            cursor.execute(f"""
                INSERT INTO scans ({columns_sql})
                VALUES ({values_sql})
                RETURNING scan_id
            """, values)
            
            scan_id = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Created new scan with ID: {scan_id}")
            return scan_id
            
        except Exception as e:
            logger.error(f"Error creating scan: {e}")
            return None
    
    def add_scan_finding(self, scan_id: int, finding_data: Dict[str, Any]) -> int:
        """
        Add a scan finding
        
        Args:
            scan_id: ID of the scan
            finding_data: Finding details
            
        Returns:
            finding_id of the created entry
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get store_id from scan_id
            cursor.execute("SELECT store_id FROM scans WHERE scan_id = %s", (scan_id,))
            scan_result = cursor.fetchone()
            if not scan_result:
                logger.error(f"Scan {scan_id} not found")
                return None
            
            store_id = scan_result[0]
            
            # Create SDE entry if needed and not provided
            sde_id = finding_data.get('sde_id')
            if not sde_id and finding_data.get('is_sde', True):
                sde_id = self.create_sde_entry(store_id, finding_data)
                # Close and reconnect since create_sde_entry opened its own connection
                cursor.close()
                conn.close()
                conn = self.get_connection()
                cursor = conn.cursor()
            
            # Handle JSON fields safely
            sample_matches = finding_data.get('sample_matches', [])
            if isinstance(sample_matches, (list, dict)):
                sample_matches_json = json.dumps(sample_matches)
            else:
                sample_matches_json = json.dumps([sample_matches])
            
            location_metadata = finding_data.get('location_metadata', {})
            if isinstance(location_metadata, dict):
                location_metadata_json = json.dumps(location_metadata)
            else:
                location_metadata_json = json.dumps({})
            
            privacy_implications = finding_data.get('privacy_implications', [])
            if isinstance(privacy_implications, (list, dict)):
                privacy_implications_json = json.dumps(privacy_implications)
            else:
                privacy_implications_json = json.dumps([])
            
            cursor.execute("""
                INSERT INTO scan_findings (
                    scan_id, sde_id, data_value, sensitivity, finding_type,
                    is_sde, sde_category, risk_level, field_type, object_path,
                    confidence_score, detection_method, pattern_matched,
                    matches_found, sample_matches, location_metadata,
                    privacy_implications, scan_timestamp
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
                )
                RETURNING finding_id
            """, (
                scan_id,
                sde_id,  # Now properly handled
                finding_data.get('data_value', ''),
                finding_data.get('sensitivity', 'medium'),  # Default to medium instead of unknown
                finding_data.get('finding_type', 'pattern_match'),
                finding_data.get('is_sde', True),  # Default to True for PII findings
                finding_data.get('sde_category', 'PII'),  # Default to PII
                finding_data.get('risk_level', 'medium'),
                finding_data.get('field_type', 'text'),
                finding_data.get('object_path', ''),
                finding_data.get('confidence_score', 0.8),  # Default to higher confidence
                finding_data.get('detection_method', 'regex'),
                finding_data.get('pattern_matched', ''),
                finding_data.get('matches_found', 1),
                sample_matches_json,
                location_metadata_json,
                privacy_implications_json
            ))
            
            finding_id = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.debug(f"Added scan finding with ID: {finding_id}")
            return finding_id
            
        except Exception as e:
            logger.error(f"Error adding scan finding: {e}")
            logger.error(f"Finding data: {finding_data}")
            return None
    
    def update_scan_status(self, scan_id: int, status: str, error_message: str = None):
        """Update scan status"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE scans 
                SET status = %s
                WHERE scan_id = %s
            """, (status, scan_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Updated scan {scan_id} status to: {status}")
            
        except Exception as e:
            logger.error(f"Error updating scan status: {e}")
    
    def add_scan_findings(self, scan_id: int, findings: List[Dict[str, Any]]) -> List[int]:
        """
        Add multiple scan findings efficiently using batch processing, now with client_id and store_id in sde_id.
        """
        if not findings:
            return []

        finding_ids = []

        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Get store_id and client_id once for all findings
            cursor.execute("SELECT store_id FROM scans WHERE scan_id = %s", (scan_id,))
            scan_result = cursor.fetchone()
            if not scan_result:
                logger.error(f"Scan {scan_id} not found")
                return []

            store_id = scan_result[0]

            cursor.execute("SELECT client_id FROM data_stores WHERE store_id = %s", (store_id,))
            client_result = cursor.fetchone()
            if not client_result:
                logger.error(f"Client for store {store_id} not found")
                return []

            client_id = client_result[0]

            print(f"Processing {len(findings)} findings in batches for client_id={client_id}, store_id={store_id}...")

            batch_size = 50
            for i in range(0, len(findings), batch_size):
                batch = findings[i:i + batch_size]
                print(f"   Processing batch {i//batch_size + 1}/{(len(findings)-1)//batch_size + 1} ({len(batch)} findings)")

                batch_data = []
                for finding in batch:
                    # Instead of SDE logic, use store_id as sde_id
                    sde_id = finding.get('sde_id')
                    if not sde_id and finding.get('is_sde', True):
                        sde_id = self._create_or_get_sde_cached(store_id, finding, cursor)

                    sample_matches = finding.get('sample_matches', [])
                    sample_matches_json = json.dumps(sample_matches) if isinstance(sample_matches, (list, dict)) else json.dumps([sample_matches])

                    location_metadata = finding.get('location_metadata', {})
                    location_metadata_json = json.dumps(location_metadata) if isinstance(location_metadata, dict) else json.dumps({})

                    privacy_implications = finding.get('privacy_implications', [])
                    privacy_implications_json = json.dumps(privacy_implications) if isinstance(privacy_implications, (list, dict)) else json.dumps([])

                    # Debug print for each finding
                    # print(f"Inserting finding for client_id={client_id}, scan_id={scan_id}, sde_id(store_id)={sde_id}")

                    batch_data.append((
                        client_id,
                        scan_id,
                        sde_id,
                        finding.get('data_value', ''),
                        finding.get('sensitivity', 'medium'),
                        finding.get('finding_type', 'pattern_match'),
                        finding.get('is_sde', True),
                        finding.get('sde_category', 'PII'),
                        finding.get('risk_level', 'medium'),
                        finding.get('field_type', 'text'),
                        finding.get('object_path', ''),
                        finding.get('confidence_score', 0.8),
                        finding.get('detection_method', 'regex'),
                        finding.get('pattern_matched', ''),
                        finding.get('matches_found', 1),
                        sample_matches_json,
                        location_metadata_json,
                        privacy_implications_json
                    ))

                cursor.executemany("""
                    INSERT INTO scan_findings (
                        client_id, scan_id, sde_id, data_value, sensitivity, finding_type,
                        is_sde, sde_category, risk_level, field_type, object_path,
                        confidence_score, detection_method, pattern_matched,
                        matches_found, sample_matches, location_metadata,
                        privacy_implications, scan_timestamp
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
                    )
                """, batch_data)

                # Get the finding IDs (PostgreSQL doesn't support RETURNING with executemany)
                cursor.execute("""
                    SELECT finding_id FROM scan_findings 
                    WHERE scan_id = %s 
                    ORDER BY finding_id DESC 
                    LIMIT %s
                """, (scan_id, len(batch_data)))

                batch_ids = [row[0] for row in cursor.fetchall()]
                finding_ids.extend(reversed(batch_ids))

            conn.commit()
            cursor.close()
            conn.close()

            print(f"SUCCESS: Successfully added {len(finding_ids)} findings to scan {scan_id}")
            logger.info(f"Added {len(finding_ids)} findings to scan {scan_id}")
            return finding_ids

        except Exception as e:
            logger.error(f"Error adding scan findings: {e}")
            return []
    
    def _create_or_get_sde_cached(self, store_id: int, finding_data: Dict[str, Any], cursor) -> Optional[int]:
        """Create or get SDE entry with basic caching to avoid duplicates in same batch"""
        # Simple cache key based on main SDE attributes
        dataset_name = finding_data.get('object_path', finding_data.get('dataset_name', 'unknown_dataset'))
        data_type = finding_data.get('sde_type', finding_data.get('finding_type', 'unknown'))
        
        cache_key = f"{store_id}_{dataset_name}_{data_type}"
        
        # Use a simple class-level cache
        if not hasattr(self, '_sde_cache'):
            self._sde_cache = {}
        
        if cache_key in self._sde_cache:
            return self._sde_cache[cache_key]
        
        # Check if SDE exists
        cursor.execute("""
            SELECT sde_id FROM sdes 
            WHERE store_id = %s AND dataset_name = %s 
            LIMIT 1
        """, (store_id, dataset_name))
        
        existing = cursor.fetchone()
        
        if existing:
            sde_id = existing[0]
        else:
            # Create new SDE - use dynamic column detection like create_sde_entry
            # Check what columns exist in the sdes table
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'sdes' AND table_schema = 'public'
                ORDER BY ordinal_position
            """)
            
            available_columns = [row[0] for row in cursor.fetchall()]
            
            # Build SDE data based on available columns
            sde_data = {'store_id': store_id}
            
            if 'dataset_name' in available_columns:
                sde_data['dataset_name'] = dataset_name
            
            if 'data_type' in available_columns:
                sde_data['data_type'] = data_type
            
            if 'column_name' in available_columns:
                sde_data['column_name'] = finding_data.get('field_name', 'unknown_field')
            
            if 'sensitivity' in available_columns:
                sde_data['sensitivity'] = finding_data.get('sensitivity', 'medium')
            
            if 'protection_method' in available_columns:
                sde_data['protection_method'] = 'none'
            
            # Build INSERT query dynamically
            insert_columns = list(sde_data.keys())
            insert_values = list(sde_data.values())
            placeholders = ['%s'] * len(insert_values)
            
            columns_sql = ', '.join(insert_columns)
            placeholders_sql = ', '.join(placeholders)
            
            cursor.execute(f"""
                INSERT INTO sdes ({columns_sql})
                VALUES ({placeholders_sql})
                RETURNING sde_id
            """, insert_values)
            
            sde_id = cursor.fetchone()[0]
        
        # Cache the result
        self._sde_cache[cache_key] = sde_id
        return sde_id
    
    def get_scan_findings(self, scan_id: int = None, store_id: int = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get scan findings
        
        Args:
            scan_id: Specific scan ID (optional)
            store_id: Specific store ID (optional)
            limit: Maximum number of results
            
        Returns:
            List of findings
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            where_clauses = []
            params = []
            
            if scan_id:
                where_clauses.append("scan_id = %s")
                params.append(scan_id)
            
            if store_id:
                where_clauses.append("store_id = %s")
                params.append(store_id)
            
            where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            cursor.execute(f"""
                SELECT * FROM scan_findings
                {where_sql}
                ORDER BY scan_timestamp DESC
                LIMIT %s
            """, params + [limit])
            
            findings = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # Convert to list of dictionaries
            return [dict(finding) for finding in findings]
            
        except Exception as e:
            logger.error(f"Error getting scan findings: {e}")
            return []
    
    def get_scan_statistics(self, store_id: int = None) -> Dict[str, Any]:
        """Get scan statistics"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            where_clause = "WHERE store_id = %s" if store_id else ""
            params = [store_id] if store_id else []
            
            # Total scans
            cursor.execute(f"SELECT COUNT(*) FROM scans {where_clause}", params)
            total_scans = cursor.fetchone()[0]
            
            # Total findings
            cursor.execute(f"SELECT COUNT(*) FROM scan_findings {where_clause}", params)
            total_findings = cursor.fetchone()[0]
            
            # Findings by type
            cursor.execute(f"""
                SELECT finding_type, COUNT(*) 
                FROM scan_findings {where_clause}
                GROUP BY finding_type
                ORDER BY COUNT(*) DESC
            """, params)
            findings_by_type = dict(cursor.fetchall())
            
            # Recent scan status
            cursor.execute(f"""
                SELECT status, COUNT(*) 
                FROM scans {where_clause}
                GROUP BY status
            """, params)
            scan_status_counts = dict(cursor.fetchall())
            
            cursor.close()
            conn.close()
            
            return {
                'total_scans': total_scans,
                'total_findings': total_findings,
                'findings_by_type': findings_by_type,
                'scan_status_counts': scan_status_counts,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting scan statistics: {e}")
            return {}
    
    def get_scan_info(self, scan_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific scan
        
        Args:
            scan_id: ID of the scan to get info for
            
        Returns:
            Dictionary containing scan information
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get scan details
            cursor.execute("""
                SELECT s.scan_id, s.store_id, s.created_at, s.status, s.scan_data,
                       ds.store_name, ds.location, ds.type
                FROM scans s
                LEFT JOIN data_stores ds ON s.store_id = ds.store_id
                WHERE s.scan_id = %s
            """, (scan_id,))
            
            scan_result = cursor.fetchone()
            
            if not scan_result:
                cursor.close()
                conn.close()
                return {}
            
            # Get finding counts for this scan
            cursor.execute("""
                SELECT COUNT(*) as total_findings,
                       COUNT(CASE WHEN sensitivity = 'high' THEN 1 END) as high_sensitivity,
                       COUNT(CASE WHEN sensitivity = 'medium' THEN 1 END) as medium_sensitivity,
                       COUNT(CASE WHEN sensitivity = 'low' THEN 1 END) as low_sensitivity
                FROM scan_findings 
                WHERE scan_id = %s
            """, (scan_id,))
            
            finding_stats = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            scan_info = {
                'scan_id': scan_result[0],
                'store_id': scan_result[1],
                'created_at': scan_result[2].isoformat() if scan_result[2] else None,
                'status': scan_result[3],
                'scan_data': scan_result[4] if scan_result[4] else {},
                'store_name': scan_result[5],
                'store_location': scan_result[6],
                'store_type': scan_result[7],
                'total_findings': finding_stats[0] if finding_stats else 0,
                'findings_by_sensitivity': {
                    'high': finding_stats[1] if finding_stats else 0,
                    'medium': finding_stats[2] if finding_stats else 0,
                    'low': finding_stats[3] if finding_stats else 0
                }
            }
            
            return scan_info
            
        except Exception as e:
            logger.error(f"Error getting scan info for scan {scan_id}: {e}")
            return {}
    
    def create_sde_entry(self, store_id: int, finding_data: Dict[str, Any]) -> Optional[int]:
        """
        Create an SDE (Structured Data Entity) entry for a finding
        
        Args:
            store_id: ID of the data store
            finding_data: Finding data to create SDE from
            
        Returns:
            sde_id of the created entry or None if failed
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check what columns exist in the sdes table
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'sdes' AND table_schema = 'public'
                ORDER BY ordinal_position
            """)
            
            available_columns = [row[0] for row in cursor.fetchall()]
            
            # Build SDE data based on available columns
            sde_data = {'store_id': store_id}
            
            if 'dataset_name' in available_columns:
                sde_data['dataset_name'] = finding_data.get('object_path', finding_data.get('dataset_name', 'unknown_dataset'))
            
            if 'data_type' in available_columns:
                sde_data['data_type'] = finding_data.get('sde_type', finding_data.get('finding_type', 'unknown'))
            
            if 'column_name' in available_columns:
                sde_data['column_name'] = finding_data.get('field_name', finding_data.get('field_type', 'unknown_field'))
            
            if 'sensitivity' in available_columns:
                sde_data['sensitivity'] = finding_data.get('sensitivity', 'medium')
            
            if 'protection_method' in available_columns:
                sde_data['protection_method'] = 'none'  # Default protection method
            
            # Create WHERE clause for checking existing SDE (use available columns)
            where_conditions = ['store_id = %s']
            where_values = [store_id]
            
            if 'dataset_name' in sde_data:
                where_conditions.append('dataset_name = %s')
                where_values.append(sde_data['dataset_name'])
            
            if 'data_type' in sde_data:
                where_conditions.append('data_type = %s')
                where_values.append(sde_data['data_type'])
            
            where_clause = ' AND '.join(where_conditions)
            
            # Check if SDE already exists
            cursor.execute(f"""
                SELECT sde_id FROM sdes 
                WHERE {where_clause}
                LIMIT 1
            """, where_values)
            
            existing = cursor.fetchone()
            
            if existing:
                sde_id = existing[0]
                logger.debug(f"Using existing SDE with ID: {sde_id}")
            else:
                # Build INSERT query based on available columns
                insert_columns = list(sde_data.keys())
                insert_values = list(sde_data.values())
                placeholders = ['%s'] * len(insert_values)
                
                columns_sql = ', '.join(insert_columns)
                placeholders_sql = ', '.join(placeholders)
                
                cursor.execute(f"""
                    INSERT INTO sdes ({columns_sql})
                    VALUES ({placeholders_sql})
                    RETURNING sde_id
                """, insert_values)
                
                sde_id = cursor.fetchone()[0]
                logger.debug(f"Created new SDE with ID: {sde_id}")
            
            conn.commit()
            cursor.close()
            conn.close()
            return sde_id
            
        except Exception as e:
            logger.error(f"Error creating SDE entry: {e}")
            return None
    
    def cleanup_old_scans(self, days_old: int = 30):
        """Clean up old scan data"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Delete old findings first (due to foreign key)
            cursor.execute("""
                DELETE FROM scan_findings 
                WHERE scan_timestamp < CURRENT_TIMESTAMP - INTERVAL '%s days'
            """, (days_old,))
            
            findings_deleted = cursor.rowcount
            
            # Delete old scans
            cursor.execute("""
                DELETE FROM scans 
                WHERE started_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
            """, (days_old,))
            
            scans_deleted = cursor.rowcount
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Cleaned up {scans_deleted} old scans and {findings_deleted} old findings")
            
        except Exception as e:
            logger.error(f"Error cleaning up old scans: {e}")
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    def get_scan_summary(self, scan_id: int) -> dict:
        """
        Return a summary of findings for a given scan_id.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as total_findings,
                       COUNT(CASE WHEN sensitivity = 'high' THEN 1 END) as high_sensitivity,
                       COUNT(CASE WHEN sensitivity = 'medium' THEN 1 END) as medium_sensitivity,
                       COUNT(CASE WHEN sensitivity = 'low' THEN 1 END) as low_sensitivity
                FROM scan_findings
                WHERE scan_id = %s
            """, (scan_id,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            if row:
                return {
                    'total_findings': row[0],
                    'high_sensitivity': row[1],
                    'medium_sensitivity': row[2],
                    'low_sensitivity': row[3]
                }
            return {}
        except Exception as e:
            logger.error(f"Error in get_scan_summary: {e}")
            return {}
