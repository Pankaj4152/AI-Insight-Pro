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

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

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
    
    def get_client_selected_sdes(self, client_id: str) -> List[Dict[str, Any]]:
        """
        Get client-selected SDEs from client_selected_sdes table
        
        Args:
            client_id: Client ID to get selected SDEs for
            
        Returns:
            List of dictionaries containing SDE information
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT id, client_id, pattern_name, sensitivity, protection_method, 
                   selected_at, sde_id, data_type
            FROM client_selected_sdes 
            WHERE client_id = %s
            ORDER BY selected_at DESC
            """
            
            cursor.execute(query, (client_id,))
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # Convert to list of dictionaries
            sdes = []
            for row in results:
                sde_dict = {
                    'id': row[0],
                    'client_id': row[1],
                    'name': row[2],  # Use 'name' for compatibility
                    'pattern_name': row[2],
                    'sensitivity': row[3],
                    'protection_method': row[4],
                    'selected_at': row[5],
                    'sde_id': row[6],
                    'data_type': row[7] if len(row) > 7 else 'string'
                }
                sdes.append(sde_dict)
            
            logger.debug(f"Found {len(sdes)} selected SDEs for client {client_id}")
            return sdes
            
        except Exception as e:
            logger.error(f"Error getting client selected SDEs: {e}")
            return []
    
    def _get_connection_config(self) -> Dict[str, Any]:
        """
        Get PostgreSQL connection configuration from various sources
        
        Returns:
            Connection configuration dictionary
        """
        # Priority order: hardcoded DB_URL, environment variables, config manager, default config file
        
        # Option 1: Hardcoded DB_URL (highest priority)
        hardcoded_db_url = "postgresql://data_privacy_user:data_privacy_db123_pass@34.131.224.110:5432/master_data_privacy"
        if hardcoded_db_url:
            # Parse DATABASE_URL (common in cloud deployments)
            url = urlparse(hardcoded_db_url)
            return {
                'host': url.hostname,
                'port': url.port or 5432,
                'database': url.path[1:],  # Remove leading /
                'user': url.username,
                'password': url.password,
                'sslmode': 'require'
            }
        
        # Option 2: Environment variables (Cloud deployment)
        if os.getenv('DB_URL'):
            # Parse DATABASE_URL (common in cloud deployments)
            url = urlparse(os.getenv('DB_URL'))
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
        
        # Option 4: Default config file
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
        logger.warning("No PostgreSQL configuration found, using localhost defaults")
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
            logger.info(f"Connected to PostgreSQL: {version[0]}")
            
            # Ensure required tables exist
            self._ensure_tables_exist(cursor)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("PostgreSQL database connection verified")
            
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            raise
    
    def get_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(**self.connection_config)
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
            
            exists = cursor.fetchone()[0]
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
        logger.info(f"🔧 add_data_store called with: store_name={store_name}, location={location}, store_type={store_type}, client_id={client_id}")
        
        # Use provided client_id or fall back to instance client_id
        effective_client_id = client_id or self.client_id
        logger.info(f"🔧 Effective client_id: {effective_client_id}")
        
        if not effective_client_id:
            logger.error(f"❌ client_id is required for multi-tenant operations")
            raise ValueError("client_id is required for multi-tenant operations")
            
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
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
        logger.info(f"🔧 create_scan called with store_id={store_id} (type: {type(store_id)})")
        logger.info(f"🔧 scan_data: {scan_data}")
        
        if store_id is None:
            logger.error(f"❌ create_scan: store_id is None")
            return None
            
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
            logger.info(f"🔧 Available columns in scans table: {available_columns}")
            
            # Prepare data for insertion
            insert_data = {
                'store_id': store_id,
                'scan_data': json.dumps(scan_data) if isinstance(scan_data, dict) else scan_data,
                'status': scan_data.get('status', 'pending')
            }
            logger.info(f"🔧 Initial insert_data: {insert_data}")
            
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
            
            # Add pattern_id if column exists - get a valid pattern ID from isde_catalogue
            if 'pattern_id' in available_columns:
                # Get a valid pattern ID from isde_catalogue table
                cursor.execute("SELECT id FROM isde_catalogue LIMIT 1")
                pattern_result = cursor.fetchone()
                if pattern_result:
                    insert_data['pattern_id'] = pattern_result[0]
                    logger.info(f"🔧 Added pattern_id: {pattern_result[0]}")
                else:
                    # If no patterns exist, skip pattern_id (let it be NULL)
                    logger.warning("No patterns found in isde_catalogue table, skipping pattern_id")
            else:
                logger.info(f"🔧 pattern_id column not found in scans table")
            
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
            
            logger.info(f"🔧 Final columns: {columns}")
            logger.info(f"🔧 Final values: {values}")
            logger.info(f"🔧 SQL: INSERT INTO scans ({columns_sql}) VALUES ({values_sql})")
            
            cursor.execute(f"""
                INSERT INTO scans ({columns_sql})
                VALUES ({values_sql})
                RETURNING scan_id
            """, values)
            
            scan_id = cursor.fetchone()[0]
            logger.info(f"🔧 INSERT successful, scan_id: {scan_id}")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Created new scan with ID: {scan_id}")
            return scan_id
            
        except Exception as e:
            logger.error(f"❌ Error creating scan: {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
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
            
            # Determine proper SDE category based on pattern and context
            sde_category = self._determine_sde_category(finding_data)
            
            # Calculate initial confidence score instead of hardcoding 0.5
            initial_confidence = self._calculate_initial_confidence(finding_data, sde_category)
            
            # Debug: Log the values being stored
            logger.info(f"🔍 Storing scan finding with values:")
            logger.info(f"  - sensitivity: '{finding_data.get('sensitivity')}' (strict database-only policy)")
            logger.info(f"  - risk_level: '{finding_data.get('risk_level')}' (strict database-only policy)")
            logger.info(f"  - sde_category: '{sde_category}'")
            logger.info(f"  - sde_type: '{finding_data.get('sde_type')}'")
            logger.info(f"  - data_value: '{finding_data.get('data_value', '')[:50]}...'")
            
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
                finding_data.get('sensitivity'),  # No default - only database sources
                finding_data.get('finding_type', 'pattern_match'),
                finding_data.get('is_sde', True),  # Default to True for PII findings
                sde_category,  # Use properly determined category
                finding_data.get('risk_level'),  # No default - only database sources
                finding_data.get('field_type', 'text'),
                finding_data.get('object_path', ''),
                initial_confidence,  # Calculated initial confidence score
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
        Add multiple scan findings efficiently using batch processing, now with clint_id and store_id in sde_id.
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

            print(f"📊 Processing {len(findings)} findings in batches for client_id={client_id}, store_id={store_id}...")

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

                    # Determine proper SDE category based on pattern and context
                    sde_category = self._determine_sde_category(finding)

                    sample_matches = finding.get('sample_matches', [])
                    sample_matches_json = json.dumps(sample_matches) if isinstance(sample_matches, (list, dict)) else json.dumps([sample_matches])

                    location_metadata = finding.get('location_metadata', {})
                    location_metadata_json = json.dumps(location_metadata) if isinstance(location_metadata, dict) else json.dumps({})

                    privacy_implications = finding.get('privacy_implications', [])
                    privacy_implications_json = json.dumps(privacy_implications) if isinstance(privacy_implications, (list, dict)) else json.dumps([])

                    # Debug print for each finding
                    # print(f"Inserting finding for client_id={client_id}, scan_id={scan_id}, sde_id(store_id)={sde_id}")

                    # Calculate initial confidence score for this finding
                    initial_confidence = self._calculate_initial_confidence(finding, sde_category)

                    batch_data.append((
                        client_id,
                        scan_id,
                        sde_id,
                        finding.get('data_value', ''),
                        finding.get('sensitivity'),  # No default - only database sources
                        finding.get('finding_type', 'pattern_match'),
                        finding.get('is_sde', True),
                        sde_category,  # Use properly determined category
                        finding.get('risk_level'),  # No default - only database sources
                        finding.get('field_type', 'text'),
                        finding.get('object_path', ''),
                        initial_confidence,  # Calculated initial confidence score
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

            print(f"✅ Successfully added {len(finding_ids)} findings to scan {scan_id}")
            logger.info(f"Added {len(finding_ids)} findings to scan {scan_id}")
            return finding_ids

        except Exception as e:
            logger.error(f"Error adding scan findings: {e}")
            return []
    
    def _determine_sde_category(self, finding_data: Dict[str, Any]) -> str:
        """
        Determine the appropriate SDE category based on the finding data
        
        Args:
            finding_data: Dictionary containing finding information
            
        Returns:
            SDE category string
        """
        pattern_matched = finding_data.get('pattern_matched', '').lower()
        finding_type = finding_data.get('finding_type', '').lower()
        data_value = finding_data.get('data_value', '').lower()
        
        # Define SDE category mappings
        category_mappings = {
            # Personal Identifiers
            'Personal Identifiers': [
                'email', 'phone', 'name', 'full_name', 'person_name', 
                'email_address', 'phone_number', 'mobile_number', 'contact'
            ],
            
            # Government IDs
            'Government IDs': [
                'ssn', 'social_security', 'passport', 'driver_license', 'driving_license',
                'voter_id', 'aadhaar', 'pan', 'tax_id', 'national_id'
            ],
            
            # Financial Information
            'Financial Information': [
                'credit_card', 'bank_account', 'account_number', 'routing_number',
                'iban', 'swift', 'ifsc', 'card_number', 'cvv', 'financial'
            ],
            
            # Health Information
            'Health Information': [
                'medical', 'health', 'diagnosis', 'prescription', 'patient',
                'medical_record', 'hipaa', 'phi', 'health_record'
            ],
            
            # Location Data
            'Location Data': [
                'address', 'location', 'zip_code', 'postal_code', 'pin_code',
                'coordinates', 'latitude', 'longitude', 'gps', 'geolocation'
            ],
            
            # Personal Demographics
            'Personal Demographics': [
                'date_of_birth', 'dob', 'birth_date', 'age', 'gender', 
                'race', 'ethnicity', 'nationality', 'marital_status'
            ],
            
            # Network/Technical
            'Network Information': [
                'ip_address', 'mac_address', 'device_id', 'session_id',
                'cookie', 'token', 'api_key', 'network'
            ],
            
            # Employment/Professional
            'Employment Information': [
                'employee_id', 'salary', 'job_title', 'department',
                'company', 'employer', 'work', 'employment'
            ]
        }
        
        # Check pattern_matched first
        for category, patterns in category_mappings.items():
            for pattern in patterns:
                if pattern in pattern_matched or pattern in finding_type:
                    return category
        
        # Check data_value for context clues
        if '@' in data_value:
            return 'Personal Identifiers'
        elif any(char.isdigit() for char in data_value) and len(data_value) >= 10:
            if '-' in data_value or ' ' in data_value:
                return 'Financial Information'  # Likely credit card or phone
            else:
                return 'Government IDs'  # Likely ID number
        
        # Default category
        return 'Personal Identifiers'

    def _calculate_initial_confidence(self, finding_data: Dict[str, Any], sde_category: str) -> float:
        """
        Calculate initial confidence score for a finding based on pattern quality and context
        
        Args:
            finding_data: Dictionary containing finding information
            sde_category: Determined SDE category
            
        Returns:
            Initial confidence score between 0.1 and 0.95
        """
        pattern_matched = finding_data.get('pattern_matched', '').lower()
        data_value = finding_data.get('data_value', '').lower()
        finding_type = finding_data.get('finding_type', '').lower()
        detection_method = finding_data.get('detection_method', '').lower()
        matches_found = finding_data.get('matches_found', 1)
        
        # Start with base confidence
        confidence = 0.5
        
        # High-confidence patterns get boost
        high_confidence_patterns = [
            'email', 'phone', 'ssn', 'credit_card', 'bank_account',
            'passport', 'driver_license', 'aadhaar', 'pan'
        ]
        if any(hcp in pattern_matched or hcp in finding_type for hcp in high_confidence_patterns):
            confidence += 0.2
        
        # Known SDE category gets boost
        if sde_category != 'UNKNOWN' and sde_category != 'Personal Identifiers':
            confidence += 0.1
        
        # Regex detection method gets boost
        if detection_method == 'regex_pattern_match':
            confidence += 0.1
        
        # Multiple matches increase confidence
        if matches_found > 1:
            confidence += min(0.1, matches_found * 0.02)
        
        # Penalize common false positives
        false_positive_indicators = [
            'test', 'example', 'sample', 'dummy', 'placeholder',
            '123456', '000000', 'null', 'none', 'n/a'
        ]
        if any(fp in data_value for fp in false_positive_indicators):
            confidence -= 0.2
        
        # Penalize very short values
        if len(data_value) < 3:
            confidence -= 0.1
        
        # Email format validation
        if 'email' in pattern_matched and '@' not in data_value:
            confidence -= 0.2
        elif 'email' in pattern_matched and '@' in data_value:
            confidence += 0.1
        
        # Phone format validation
        if 'phone' in pattern_matched:
            # Basic phone validation
            digit_count = sum(c.isdigit() for c in data_value)
            if digit_count >= 10:
                confidence += 0.1
            else:
                confidence -= 0.1
        
        # Bound the confidence score
        return max(0.1, min(0.95, confidence))

    def _create_or_get_sde_cached(self, store_id: int, finding_data: Dict[str, Any], cursor) -> Optional[int]:
        """Get SDE ID from client_selected_sdes table based on pattern matched"""
        # Get the pattern name from the finding data
        pattern_matched = finding_data.get('pattern_matched', '')
        data_type = finding_data.get('sde_type', finding_data.get('finding_type', ''))
        finding_type = finding_data.get('finding_type', '')
        
        # Initialize warning counter for this client if not exists
        if not hasattr(self, '_sde_warning_count'):
            self._sde_warning_count = {}
        
        client_warning_key = f"{self.client_id}_sde_warnings"
        
        # Check if we've already warned about this client having no SDE selections
        if client_warning_key in self._sde_warning_count and self._sde_warning_count[client_warning_key] >= 5:
            # After 5 warnings, just return None silently to avoid log spam
            return None
        
        # Map regex patterns to SDE pattern names
        pattern_to_sde_map = {
            # Email patterns
            r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b': 'email',
            r'\b[a-zA-Z0-9.\-]+@[a-zA-Z0-9.\-]+\b': 'email',
            
            # Phone patterns
            r'\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}(?:\d+)?\b': 'phone',
            
            # Credit card patterns  
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b': 'credit_card',
            r'\b\d{13,19}\b': 'credit_card',
            
            # Bank account patterns
            r'\b\d{9,18}\b': 'bank_account',
            
            # Date patterns
            r'\b(?:\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2})\b': 'date_of_birth',
            
            # Name patterns
            r'\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)\b': 'name',
            
            # SSN patterns
            r'\b\d{3}-?\d{2}-?\d{4}\b': 'ssn',
            
            # PAN patterns
            r'\b[A-Z]{5}\d{4}[A-Z]\b': 'pan',
            
            # Aadhaar patterns
            r'\b\d{4}\s?\d{4}\s?\d{4}\b': 'aadhaar',
            
            # Passport patterns
            r'\b[A-Z][0-9]{7}\b': 'passport',
            r'\b[A-Z]{3}[0-9]{7}\b': 'passport',
            
            # IFSC patterns
            r'\b[A-Z]{4}0[A-Z0-9]{6}\b': 'ifsc',
            
            # PIN code patterns
            r'\b\d{6}\b': 'address',  # Could be PIN code or address related
            
            # Driving license patterns
            r'\b[A-Z]{2}\d{2}[A-Z0-9]{11}\b': 'driving_license',
            
            # Voter ID patterns
            r'\b[A-Z]{3}\d{7}\b': 'voter_id',
            
            # IP address patterns
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b': 'ip_address'
        }
        
        # Pattern name normalization mapping
        pattern_name_map = {
            'credit_card_number': 'credit_card',
            'credit_card_num': 'credit_card',
            'cc_number': 'credit_card',
            'card_number': 'credit_card',
            'date': 'date_of_birth',
            'dob': 'date_of_birth',
            'birth_date': 'date_of_birth',
            'full_name': 'name',
            'person_name': 'name',
            'customer_name': 'name',
            'email_address': 'email',
            'phone_number': 'phone',
            'mobile_number': 'phone',
            'contact_number': 'phone',
            'account_number': 'bank_account',
            'acc_number': 'bank_account',
            'bank_acc': 'bank_account',
            'postal_code': 'address',
            'zip_code': 'address',
            'pin_code': 'address',
            'location': 'address',
            'mention': None,  # Skip mention patterns
            'integer': None,  # Skip generic data types
            'string': None,   # Skip generic data types
            'text': None,     # Skip generic data types
            'number': None,   # Skip generic data types
        }
        
        # First, try to match by regex pattern
        pattern_to_search = None
        if pattern_matched:
            for regex_pattern, sde_name in pattern_to_sde_map.items():
                if pattern_matched == regex_pattern:
                    pattern_to_search = sde_name
                    break
        
        # If no regex match, try using the data_type with normalization
        if not pattern_to_search:
            # Normalize the pattern name
            normalized_pattern = pattern_name_map.get(data_type, data_type)
            if normalized_pattern is not None:  # None means skip this pattern
                pattern_to_search = normalized_pattern
        
        # For field_name_sde findings, try to infer from field names
        if not pattern_to_search and finding_type == 'field_name_sde':
            field_name = finding_data.get('field_name', '').lower()
            if 'email' in field_name:
                pattern_to_search = 'email'
            elif 'phone' in field_name or 'mobile' in field_name:
                pattern_to_search = 'phone'
            elif 'name' in field_name:
                pattern_to_search = 'name'
            elif 'address' in field_name:
                pattern_to_search = 'address'
            elif 'date' in field_name or 'birth' in field_name or 'dob' in field_name:
                pattern_to_search = 'date_of_birth'
        
        if not pattern_to_search or not self.client_id:
            # Only log warning if it's not a skipped pattern type
            if pattern_to_search is not None:
                logger.warning(f"No pattern to search ({pattern_to_search}) or client_id ({self.client_id}) for SDE lookup")
            return None
        
        # Cache key for this client and pattern
        cache_key = f"{self.client_id}_{pattern_to_search}"
        
        # Use a simple class-level cache
        if not hasattr(self, '_sde_cache'):
            self._sde_cache = {}
        
        if cache_key in self._sde_cache:
            return self._sde_cache[cache_key]
        
        # Look up the SDE ID from client_selected_sdes table
        try:
            cursor.execute("""
                SELECT id FROM client_selected_sdes 
                WHERE client_id = %s AND pattern_name = %s
                LIMIT 1
            """, (self.client_id, pattern_to_search))
            
            result = cursor.fetchone()
            
            if result:
                sde_id = result[0]
                logger.info(f"Found SDE ID {sde_id} for client {self.client_id} and pattern {pattern_to_search}")
            else:
                # Try partial match if exact match fails
                cursor.execute("""
                    SELECT id FROM client_selected_sdes 
                    WHERE client_id = %s AND (
                        pattern_name ILIKE %s OR 
                        %s ILIKE pattern_name OR
                        pattern_name ILIKE %s
                    )
                    LIMIT 1
                """, (self.client_id, f'%{pattern_to_search}%', f'%{pattern_to_search}%', f'%{data_type}%'))
                
                result = cursor.fetchone()
                if result:
                    sde_id = result[0]
                    logger.info(f"Found SDE ID {sde_id} for client {self.client_id} with partial match for pattern {pattern_to_search}")
                else:
                    # Increment warning counter
                    if client_warning_key not in self._sde_warning_count:
                        self._sde_warning_count[client_warning_key] = 0
                    
                    self._sde_warning_count[client_warning_key] += 1
                    
                    # Only show warning for first few times to avoid log spam
                    if self._sde_warning_count[client_warning_key] <= 3:
                        logger.warning(f"No SDE found in client_selected_sdes for client {self.client_id} and pattern {pattern_to_search}")
                    elif self._sde_warning_count[client_warning_key] == 4:
                        logger.warning(f"No SDE patterns found for client {self.client_id}. Suppressing further SDE lookup warnings for this client.")
                    
                    return None
            
            # Cache the result
            self._sde_cache[cache_key] = sde_id
            return sde_id
            
        except Exception as e:
            logger.error(f"Error looking up SDE from client_selected_sdes: {e}")
            return None
    
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

    def get_all_data_stores_for_client(self, client_id: str = None) -> List[Dict[str, Any]]:
        """
        Get all data stores for a specific client from the data_stores table
        
        Args:
            client_id: Client ID (uses instance client_id if not provided)
            
        Returns:
            List of dictionaries containing data store information
        """
        # Use provided client_id or fall back to instance client_id
        effective_client_id = client_id or self.client_id
        if not effective_client_id:
            raise ValueError("client_id is required for multi-tenant operations")
            
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT store_id, store_name, location, store_type, discovery_timestamp,
                       ROW_NUMBER() OVER (ORDER BY store_id ASC) as client_sequence_id
                FROM data_stores 
                WHERE client_id = %s
                ORDER BY store_id DESC
            """, (effective_client_id,))
            
            stores = []
            for row in cursor.fetchall():
                store_info = {
                    'store_id': row[0],
                    'store_name': row[1],
                    'location': row[2],
                    'type': row[3],
                    'access_control': 'private',  # Default value since this column doesn't exist
                    'discovery_timestamp': row[4],
                    'client_sequence_id': row[5]  # Sequential ID for this client (1, 2, 3, ...)
                }
                stores.append(store_info)
            
            cursor.close()
            conn.close()
            
            logger.info(f"Found {len(stores)} data stores for client {effective_client_id}")
            return stores
            
        except Exception as e:
            logger.error(f"Error getting data stores for client {effective_client_id}: {e}")
            return []

    def get_data_store_by_id(self, store_id: int, client_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Get data store information by store_id for a specific client
        
        Args:
            store_id: Store ID
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
            elif 'store_type' in all_columns:
                select_columns.append('store_type as type')
            else:
                select_columns.append("'unknown' as type")
            
            # Add access_control column if it exists
            if 'access_control' in all_columns:
                select_columns.append('access_control')
            else:
                select_columns.append("'private' as access_control")
            
            # Add discovery_timestamp column if it exists
            if 'discovery_timestamp' in all_columns:
                select_columns.append('discovery_timestamp')
            else:
                select_columns.append("NULL as discovery_timestamp")
            
            columns_sql = ', '.join(select_columns)
            
            cursor.execute(f"""
                SELECT {columns_sql}
                FROM data_stores 
                WHERE store_id = %s AND client_id = %s
            """, (store_id, effective_client_id))
            
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if row:
                store_info = {
                    'store_id': row[0],
                    'store_name': row[1],
                    'location': row[2],
                    'type': row[3],
                    'access_control': row[4],
                    'discovery_timestamp': row[5] if len(row) > 5 else None
                }
                return store_info
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting data store {store_id} for client {effective_client_id}: {e}")
            return None

    def get_latest_data_store_for_client(self, client_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Get the latest (most recently discovered) data store for a client
        
        Args:
            client_id: Client ID (uses instance client_id if not provided)
            
        Returns:
            Dictionary with latest data store information or None if not found
        """
        effective_client_id = client_id or self.client_id
        if not effective_client_id:
            raise ValueError("client_id is required for multi-tenant operations")
            
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT store_id, store_name, location, type, discovery_timestamp
                FROM data_stores 
                WHERE client_id = %s
                ORDER BY discovery_timestamp DESC NULLS LAST, store_id DESC
                LIMIT 1
            """, (effective_client_id,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                return {
                    'store_id': result[0],
                    'store_name': result[1],
                    'location': result[2],
                    'store_type': result[3],
                    'discovery_timestamp': result[4].isoformat() if result[4] else None
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest data store for client {effective_client_id}: {e}")
            return None

    def get_all_data_stores_for_client(self, client_id: str = None) -> List[Dict[str, Any]]:
        """
        Get all data stores for a client
        
        Args:
            client_id: Client ID (uses instance client_id if not provided)
            
        Returns:
            List of dictionaries with data store information
        """
        effective_client_id = client_id or self.client_id
        if not effective_client_id:
            raise ValueError("client_id is required for multi-tenant operations")
            
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT store_id, store_name, location, type, discovery_timestamp,
                       ROW_NUMBER() OVER (ORDER BY store_id ASC) as client_sequence_id
                FROM data_stores 
                WHERE client_id = %s
                ORDER BY discovery_timestamp DESC NULLS LAST, store_id DESC
            """, (effective_client_id,))
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            data_stores = []
            for result in results:
                data_stores.append({
                    'store_id': result[0],
                    'store_name': result[1],
                    'location': result[2],
                    'store_type': result[3],
                    'discovery_timestamp': result[4].isoformat() if result[4] else None,
                    'client_sequence_id': result[5]  # Sequential ID for this client
                })
            
            return data_stores
            
        except Exception as e:
            logger.error(f"Error getting data stores for client {effective_client_id}: {e}")
            return []
    
    def get_data_stores_with_sequence(self, client_id: str = None) -> List[Dict[str, Any]]:
        """
        Get all data stores for a client with sequential numbering (1, 2, 3, ...)
        
        Args:
            client_id: Client ID (uses instance client_id if not provided)
            
        Returns:
            List of dictionaries with data store information including client_sequence_id
        """
        effective_client_id = client_id or self.client_id
        if not effective_client_id:
            raise ValueError("client_id is required for multi-tenant operations")
            
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT store_id, store_name, location, 
                       COALESCE(store_type, type, 'unknown') as store_type, 
                       discovery_timestamp,
                       ROW_NUMBER() OVER (ORDER BY store_id ASC) as client_sequence_id
                FROM data_stores 
                WHERE client_id = %s
                ORDER BY client_sequence_id ASC
            """, (effective_client_id,))
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            data_stores = []
            for result in results:
                data_stores.append({
                    'store_id': result[0],
                    'store_name': result[1],
                    'location': result[2],
                    'store_type': result[3],
                    'discovery_timestamp': result[4].isoformat() if result[4] else None,
                    'client_sequence_id': result[5],  # Sequential: 1, 2, 3, ...
                    'display_name': f"Data Store {result[5]}: {result[1]}"  # User-friendly name
                })
            
            logger.info(f"Found {len(data_stores)} data stores for client {effective_client_id} with sequential IDs")
            return data_stores
            
        except Exception as e:
            logger.error(f"Error getting sequenced data stores for client {effective_client_id}: {e}")
            return []
    
    def _normalize_object_data(self, object_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize object data to remove redundancy and create unified structure
        
        Args:
            object_data: Raw object data from discovery
            
        Returns:
            Normalized object data with unified field names
        """
        # Extract the primary values, preferring the most specific names
        name = (
            object_data.get('name') or 
            object_data.get('object_name') or 
            object_data.get('file_name') or 
            'unknown'
        )
        
        path = (
            object_data.get('path') or 
            object_data.get('object_path') or 
            object_data.get('file_path') or 
            ''
        )
        
        object_type = (
            object_data.get('type') or 
            object_data.get('object_type') or 
            object_data.get('file_type') or 
            'file'
        )
        
        size_bytes = (
            object_data.get('size_bytes') or 
            object_data.get('size') or 
            object_data.get('object_size') or 
            0
        )
        
        last_modified = (
            object_data.get('last_modified') or 
            object_data.get('modified') or 
            None
        )
        
        # Extract file extension from name or path if not provided
        file_extension = object_data.get('file_extension') or object_data.get('extension') or ''
        if not file_extension and '.' in name:
            file_extension = name.split('.')[-1]
        
        # Determine MIME type based on object type and extension
        mime_type = object_data.get('mime_type') or object_data.get('content_type')
        if not mime_type:
            if object_type == 'table':
                if 'bigquery' in path.lower():
                    mime_type = 'application/x-bigquery-table'
                elif 'postgresql' in path.lower() or '.' in path:
                    mime_type = 'application/x-postgresql-table'
                else:
                    mime_type = 'application/x-database-table'
            elif file_extension:
                # Basic MIME type mapping
                mime_mapping = {
                    'csv': 'text/csv',
                    'json': 'application/json',
                    'txt': 'text/plain',
                    'pdf': 'application/pdf',
                    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'xls': 'application/vnd.ms-excel'
                }
                mime_type = mime_mapping.get(file_extension.lower(), 'application/octet-stream')
            else:
                mime_type = 'application/octet-stream'
        
        # Create normalized structure
        normalized = {
            'name': name,
            'path': path,
            'type': object_type,
            'parent_path': object_data.get('parent_path', ''),
            'size_bytes': int(size_bytes) if size_bytes else 0,
            'last_modified': last_modified,
            'file_extension': file_extension,
            'checksum': object_data.get('checksum'),
            'mime_type': mime_type,
            'is_accessible': object_data.get('is_accessible', True),
            'access_error': object_data.get('access_error'),
            'metadata': object_data.get('metadata', {})
        }
        
        return normalized

    def add_discovered_object(self, store_id: int, client_id: str, object_data: Dict[str, Any]) -> Optional[int]:
        """
        Add a discovered object (file/data) to the discovered_objects table
        
        Args:
            store_id: ID of the data store where object was discovered
            client_id: Client ID
            object_data: Dictionary containing object information
            
        Returns:
            object_id of the created entry or None if failed
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Normalize the object data to remove redundancy
            normalized_data = self._normalize_object_data(object_data)
            
            # Handle metadata as JSON string if it's a dict
            metadata = normalized_data['metadata']
            if isinstance(metadata, dict):
                import json
                metadata = json.dumps(metadata)
            
            # Insert into optimized database table (no redundancy)
            cursor.execute("""
                INSERT INTO discovered_objects_optimized (
                    store_id, client_id, cli_conn_id,
                    name, type, path, parent_path,
                    size_bytes, last_modified, metadata,
                    file_extension, is_accessible, access_error, 
                    checksum, mime_type, discovered_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                ) RETURNING object_id
            """, (
                store_id, client_id, 1,  # Using 1 as default cli_conn_id
                normalized_data['name'],        # name
                normalized_data['type'],        # type  
                normalized_data['path'],        # path
                normalized_data['parent_path'], # parent_path
                normalized_data['size_bytes'],  # size_bytes
                normalized_data['last_modified'], # last_modified
                metadata,                       # metadata
                normalized_data['file_extension'], # file_extension
                normalized_data['is_accessible'], # is_accessible
                normalized_data['access_error'], # access_error
                normalized_data['checksum'],    # checksum
                normalized_data['mime_type']    # mime_type
            ))
            
            object_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Added discovered object: {normalized_data['name']} with ID {object_id}")
            return object_id
            
        except Exception as e:
            logger.error(f"Error adding discovered object: {e}")
            return None
    
    def add_discovered_objects_batch(self, store_id: int, client_id: str, objects_data: List[Dict[str, Any]]) -> List[int]:
        """
        Add multiple discovered objects in batch for efficiency
        
        Args:
            store_id: ID of the data store
            client_id: Client ID  
            objects_data: List of object data dictionaries
            
        Returns:
            List of object_ids that were created
        """
        if not objects_data:
            return []
            
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            object_ids = []
            
            for object_data in objects_data:
                # Normalize the object data to remove redundancy
                normalized_data = self._normalize_object_data(object_data)
                
                # Handle metadata as JSON string
                metadata = normalized_data['metadata']
                if isinstance(metadata, dict):
                    import json
                    metadata = json.dumps(metadata)
                
                cursor.execute("""
                    INSERT INTO discovered_objects_optimized (
                        store_id, client_id, cli_conn_id,
                        name, type, path, parent_path,
                        size_bytes, last_modified, metadata,
                        file_extension, is_accessible, access_error, 
                        checksum, mime_type, discovered_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                    ) RETURNING object_id
                """, (
                    store_id, client_id, 1,  # Using 1 as default cli_conn_id
                    normalized_data['name'],        # name
                    normalized_data['type'],        # type
                    normalized_data['path'],        # path
                    normalized_data['parent_path'], # parent_path
                    normalized_data['size_bytes'],  # size_bytes
                    normalized_data['last_modified'], # last_modified
                    metadata,                       # metadata
                    normalized_data['file_extension'], # file_extension
                    normalized_data['is_accessible'], # is_accessible
                    normalized_data['access_error'], # access_error
                    normalized_data['checksum'],    # checksum
                    normalized_data['mime_type']    # mime_type
                ))
                
                object_id = cursor.fetchone()[0]
                object_ids.append(object_id)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Added {len(object_ids)} discovered objects for store_id {store_id}")
            return object_ids
            
        except Exception as e:
            logger.error(f"Error adding discovered objects batch: {e}")
            return []
    
    def get_discovered_objects(self, store_id: int = None, client_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get discovered objects from the database
        
        Args:
            store_id: Filter by store ID (optional)
            client_id: Filter by client ID (optional, uses instance client_id if not provided)
            limit: Maximum number of objects to return
            
        Returns:
            List of discovered objects
        """
        effective_client_id = client_id or self.client_id
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Build WHERE clause
            where_conditions = []
            params = []
            
            if effective_client_id:
                where_conditions.append("client_id = %s")
                params.append(effective_client_id)
            
            if store_id:
                where_conditions.append("store_id = %s")
                params.append(store_id)
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            cursor.execute(f"""
                SELECT object_id, store_id, client_id, cli_conn_id, name, type, path,
                       parent_path, size_bytes, last_modified, metadata, discovered_at,
                       file_extension, is_accessible, access_error, checksum, mime_type
                FROM discovered_objects_optimized 
                {where_clause}
                ORDER BY discovered_at DESC
                LIMIT %s
            """, params + [limit])
            
            objects = []
            for row in cursor.fetchall():
                # Return normalized object structure without redundancy
                objects.append({
                    'object_id': row[0],
                    'store_id': row[1],
                    'client_id': row[2],
                    'cli_conn_id': row[3],
                    'name': row[4],  # name (unified field)
                    'type': row[5],  # type (unified field)
                    'path': row[6],  # path (unified field)
                    'parent_path': row[7],
                    'size_bytes': row[8],  # size_bytes (unified field)
                    'last_modified': row[9],
                    'metadata': row[10],
                    'discovered_at': row[11],
                    'file_extension': row[12],
                    'is_accessible': row[13],
                    'access_error': row[14],
                    'checksum': row[15],
                    'mime_type': row[16]
                })
            
            cursor.close()
            conn.close()
            
            logger.info(f"Retrieved {len(objects)} discovered objects")
            return objects
            
        except Exception as e:
            logger.error(f"Error getting discovered objects: {e}")
            return []
    
    def clear_discovered_objects(self, store_id: int, client_id: str = None) -> bool:
        """
        Clear discovered objects for a specific store before re-discovery
        
        Args:
            store_id: Store ID to clear objects for
            client_id: Client ID (optional, uses instance client_id if not provided)
            
        Returns:
            True if successful
        """
        effective_client_id = client_id or self.client_id
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM discovered_objects_optimized 
                WHERE store_id = %s AND client_id = %s
            """, (store_id, effective_client_id))
            
            deleted_count = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Cleared {deleted_count} discovered objects for store_id {store_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing discovered objects: {e}")
            return False
    
    def create_optimized_discovered_objects_table(self) -> bool:
        """
        Create an optimized version of the discovered_objects table without redundancy
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if optimized table already exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'discovered_objects_optimized'
                )
            """)
            
            if cursor.fetchone()[0]:
                logger.info("Optimized table already exists")
                cursor.close()
                conn.close()
                return True
            
            logger.info("Creating optimized discovered_objects table...")
            
            # Create optimized table structure
            cursor.execute("""
                CREATE TABLE discovered_objects_optimized (
                    object_id SERIAL PRIMARY KEY,
                    store_id INTEGER NOT NULL,
                    client_id VARCHAR(255) NOT NULL,
                    cli_conn_id INTEGER DEFAULT 1,
                    
                    -- Unified object information (no redundancy)
                    name VARCHAR(500) NOT NULL,
                    type VARCHAR(100) NOT NULL,
                    path TEXT,
                    parent_path TEXT,
                    size_bytes BIGINT DEFAULT 0,
                    
                    -- Metadata and attributes
                    last_modified TIMESTAMP,
                    file_extension VARCHAR(50),
                    is_accessible BOOLEAN DEFAULT TRUE,
                    access_error TEXT,
                    checksum VARCHAR(255),
                    mime_type VARCHAR(255),
                    metadata JSONB DEFAULT '{}',
                    
                    -- Audit fields
                    discovered_at TIMESTAMP DEFAULT NOW(),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Create indexes for better performance
            indexes = [
                "CREATE INDEX idx_discovered_objects_opt_store_client ON discovered_objects_optimized(store_id, client_id)",
                "CREATE INDEX idx_discovered_objects_opt_type ON discovered_objects_optimized(type)",
                "CREATE INDEX idx_discovered_objects_opt_name ON discovered_objects_optimized(name)",
                "CREATE INDEX idx_discovered_objects_opt_discovered_at ON discovered_objects_optimized(discovered_at DESC)"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("Optimized discovered_objects table created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating optimized table: {e}")
            return False
    
    def migrate_to_optimized_table(self) -> bool:
        """
        Migrate data from current discovered_objects table to optimized structure
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # First create the optimized table if it doesn't exist
            if not self.create_optimized_discovered_objects_table():
                return False
            
            logger.info("Migrating data to optimized table...")
            
            # Migrate data with deduplication and proper type casting
            cursor.execute("""
                INSERT INTO discovered_objects_optimized (
                    store_id, client_id, cli_conn_id, name, type, path, parent_path, 
                    size_bytes, last_modified, file_extension, is_accessible, 
                    access_error, checksum, mime_type, metadata, discovered_at
                )
                SELECT DISTINCT ON (store_id, client_id, COALESCE(object_name, file_name), COALESCE(object_path, file_path))
                    store_id, 
                    client_id, 
                    cli_conn_id,
                    COALESCE(object_name, file_name, 'unknown') as name,
                    COALESCE(object_type, file_type, 'file') as type,
                    COALESCE(object_path, file_path) as path,
                    parent_path,
                    COALESCE(object_size, size_bytes, 0) as size_bytes,
                    last_modified,
                    file_extension,
                    COALESCE(is_accessible, true),
                    access_error,
                    checksum,
                    mime_type,
                    CASE 
                        WHEN metadata IS NULL OR metadata = '' THEN '{}'::jsonb
                        ELSE 
                            CASE 
                                WHEN metadata::text ~ '^\\s*\\{.*\\}\\s*$' THEN metadata::jsonb
                                ELSE ('{"data": "' || replace(metadata::text, '"', '\\"') || '"}')::jsonb
                            END
                    END as metadata,
                    discovered_at
                FROM discovered_objects
                WHERE NOT EXISTS (
                    SELECT 1 FROM discovered_objects_optimized opt 
                    WHERE opt.name = COALESCE(discovered_objects.object_name, discovered_objects.file_name)
                    AND opt.path = COALESCE(discovered_objects.object_path, discovered_objects.file_path)
                    AND opt.store_id = discovered_objects.store_id
                    AND opt.client_id = discovered_objects.client_id
                )
                ORDER BY store_id, client_id, COALESCE(object_name, file_name), COALESCE(object_path, file_path), discovered_at DESC
            """)
            
            migrated_rows = cursor.rowcount
            conn.commit()
            
            cursor.close()
            conn.close()
            
            logger.info(f"Successfully migrated {migrated_rows} records to optimized table")
            return True
            
        except Exception as e:
            logger.error(f"Error migrating to optimized table: {e}")
            return False

    # ==================== SELECTED OBJECTS MANAGEMENT ====================
    
    def add_selected_objects(self, client_id: str, scan_session_id: str, object_ids: List[int]) -> bool:
        """
        Add objects to the selected_objects table for selective scanning
        
        Args:
            client_id: Client ID
            scan_session_id: Unique session ID for this scan selection
            object_ids: List of object IDs from discovered_objects_optimized table
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Clear existing selections for this session
            cursor.execute("""
                DELETE FROM selected_objects 
                WHERE client_id = %s AND scan_session_id = %s
            """, (client_id, scan_session_id))
            
            # Insert new selections
            for object_id in object_ids:
                # Get object details from discovered_objects_optimized
                cursor.execute("""
                    SELECT store_id, name, type, path
                    FROM discovered_objects_optimized 
                    WHERE object_id = %s AND client_id = %s
                """, (object_id, client_id))
                
                result = cursor.fetchone()
                if result:
                    cursor.execute("""
                        INSERT INTO selected_objects (
                            client_id, scan_session_id, object_id, store_id,
                            object_name, object_type, object_path
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (client_id, scan_session_id, object_id) DO NOTHING
                    """, (
                        client_id,
                        scan_session_id,
                        object_id,
                        result[0],  # store_id
                        result[1],  # name
                        result[2],  # type
                        result[3]   # path
                    ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Added {len(object_ids)} selected objects for client {client_id}, session {scan_session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding selected objects: {e}")
            return False

    def get_selected_objects(self, client_id: str, scan_session_id: str = None) -> List[Dict[str, Any]]:
        """
        Get selected objects for a client and optional scan session
        
        Args:
            client_id: Client ID
            scan_session_id: Optional scan session ID (if None, gets latest session)
            
        Returns:
            List of selected objects
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if scan_session_id:
                # Get objects for specific session
                cursor.execute("""
                    SELECT so.object_id, so.store_id, so.object_name, so.object_type, 
                           so.object_path, so.selected_at, so.scan_session_id
                    FROM selected_objects so
                    WHERE so.client_id = %s AND so.scan_session_id = %s
                    ORDER BY so.selected_at DESC
                """, (client_id, scan_session_id))
            else:
                # Get objects from the most recent session
                cursor.execute("""
                    SELECT so.object_id, so.store_id, so.object_name, so.object_type, 
                           so.object_path, so.selected_at, so.scan_session_id
                    FROM selected_objects so
                    WHERE so.client_id = %s 
                    AND so.scan_session_id = (
                        SELECT scan_session_id 
                        FROM selected_objects 
                        WHERE client_id = %s 
                        ORDER BY selected_at DESC 
                        LIMIT 1
                    )
                    ORDER BY so.selected_at DESC
                """, (client_id, client_id))
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            selected_objects = []
            for row in results:
                selected_objects.append({
                    'object_id': row[0],
                    'store_id': row[1],
                    'object_name': row[2],
                    'object_type': row[3],
                    'object_path': row[4],
                    'selected_at': row[5],
                    'scan_session_id': row[6]
                })
            
            logger.info(f"Retrieved {len(selected_objects)} selected objects for client {client_id}")
            return selected_objects
            
        except Exception as e:
            logger.error(f"Error getting selected objects: {e}")
            return []

    def get_selected_objects_for_scanning(self, client_id: str, scan_session_id: str = None) -> List[Dict[str, Any]]:
        """
        Get selected objects with full details for scanning purposes
        
        Args:
            client_id: Client ID
            scan_session_id: Optional scan session ID (if None, gets latest session)
            
        Returns:
            List of selected objects with full discovered object details
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if scan_session_id:
                cursor.execute("""
                    SELECT dobj.object_id, dobj.store_id, dobj.client_id, dobj.name, dobj.type, 
                           dobj.path, dobj.parent_path, dobj.size_bytes, dobj.last_modified,
                           dobj.metadata, dobj.file_extension, dobj.is_accessible, 
                           dobj.access_error, dobj.checksum, dobj.mime_type, so.scan_session_id
                    FROM selected_objects so
                    JOIN discovered_objects_optimized dobj ON so.object_id = dobj.object_id
                    WHERE so.client_id = %s AND so.scan_session_id = %s
                    ORDER BY so.selected_at DESC
                """, (client_id, scan_session_id))
            else:
                cursor.execute("""
                    SELECT dobj.object_id, dobj.store_id, dobj.client_id, dobj.name, dobj.type, 
                           dobj.path, dobj.parent_path, dobj.size_bytes, dobj.last_modified,
                           dobj.metadata, dobj.file_extension, dobj.is_accessible, 
                           dobj.access_error, dobj.checksum, dobj.mime_type, so.scan_session_id
                    FROM selected_objects so
                    JOIN discovered_objects_optimized dobj ON so.object_id = dobj.object_id
                    WHERE so.client_id = %s 
                    AND so.scan_session_id = (
                        SELECT scan_session_id 
                        FROM selected_objects 
                        WHERE client_id = %s 
                        ORDER BY selected_at DESC 
                        LIMIT 1
                    )
                    ORDER BY so.selected_at DESC
                """, (client_id, client_id))
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            selected_objects = []
            for row in results:
                selected_objects.append({
                    'object_id': row[0],
                    'store_id': row[1],
                    'client_id': row[2],
                    'name': row[3],
                    'type': row[4],
                    'path': row[5],
                    'parent_path': row[6],
                    'size_bytes': row[7],
                    'last_modified': row[8],
                    'metadata': row[9],
                    'file_extension': row[10],
                    'is_accessible': row[11],
                    'access_error': row[12],
                    'checksum': row[13],
                    'mime_type': row[14],
                    'scan_session_id': row[15]
                })
            
            logger.info(f"Retrieved {len(selected_objects)} selected objects for scanning for client {client_id}")
            return selected_objects
            
        except Exception as e:
            logger.error(f"Error getting selected objects for scanning: {e}")
            return []

    def clear_selected_objects(self, client_id: str, scan_session_id: str = None) -> bool:
        """
        Clear selected objects for a client
        
        Args:
            client_id: Client ID
            scan_session_id: Optional scan session ID (if None, clears all for client)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if scan_session_id:
                cursor.execute("""
                    DELETE FROM selected_objects 
                    WHERE client_id = %s AND scan_session_id = %s
                """, (client_id, scan_session_id))
            else:
                cursor.execute("""
                    DELETE FROM selected_objects 
                    WHERE client_id = %s
                """, (client_id,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Cleared {deleted_count} selected objects for client {client_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing selected objects: {e}")
            return False

    def has_selected_objects(self, client_id: str, scan_session_id: str = None) -> bool:
        """
        Check if client has any selected objects
        
        Args:
            client_id: Client ID
            scan_session_id: Optional scan session ID (if None, checks latest session only)
            
        Returns:
            True if client has selected objects, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if scan_session_id:
                cursor.execute("""
                    SELECT COUNT(*) FROM selected_objects 
                    WHERE client_id = %s AND scan_session_id = %s
                """, (client_id, scan_session_id))
            else:
                # Only check the most recent session to avoid accumulation issues
                cursor.execute("""
                    SELECT COUNT(*) FROM selected_objects 
                    WHERE client_id = %s 
                    AND scan_session_id = (
                        SELECT scan_session_id 
                        FROM selected_objects 
                        WHERE client_id = %s 
                        ORDER BY selected_at DESC 
                        LIMIT 1
                    )
                """, (client_id, client_id))
            
            count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            return count > 0
            
        except Exception as e:
            logger.error(f"Error checking selected objects: {e}")
            return False

    def get_latest_scan_session_id(self, client_id: str) -> str:
        """
        Get the most recent scan session ID for a client
        
        Args:
            client_id: Client ID
            
        Returns:
            Latest scan session ID or None if no sessions found
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT scan_session_id 
                FROM selected_objects 
                WHERE client_id = %s 
                ORDER BY selected_at DESC 
                LIMIT 1
            """, (client_id,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Error getting latest scan session ID: {e}")
            return None

    def clear_all_selected_objects(self, client_id: str) -> bool:
        """
        Clear all selected objects for a client (across all sessions)
        
        Args:
            client_id: Client ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM selected_objects 
                WHERE client_id = %s
            """, (client_id,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Cleared {deleted_count} selected objects for client {client_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing all selected objects: {e}")
            return False

    def save_file_selections(self, client_id: str, scan_session_id: str, selected_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Save file selections directly to selected_objects table
        
        Args:
            client_id: Client ID
            scan_session_id: Unique session ID for this scan selection
            selected_files: List of file dictionaries with keys:
                          - file_name: name of the file
                          - store_id: ID of the data store
                          - path: path to the file (optional)
                          - object_id: existing object_id if known (optional)
                          - object_type: type of object (default: 'file')
                          - metadata: additional metadata (optional)
        
        Returns:
            Dictionary with success status, count of saved files, and any errors
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Clear existing selections for this session
            cursor.execute("""
                DELETE FROM selected_objects 
                WHERE client_id = %s AND scan_session_id = %s
            """, (client_id, scan_session_id))
            
            saved_count = 0
            errors = []
            duplicate_count = 0
            
            for file_data in selected_files:
                try:
                    # Extract file information
                    file_name = file_data.get('file_name')
                    store_id = file_data.get('store_id')
                    file_path = file_data.get('path', '')
                    object_id = file_data.get('object_id')
                    object_type = file_data.get('object_type', 'file')
                    
                    if not file_name or not store_id:
                        errors.append(f"Missing required fields (file_name: {file_name}, store_id: {store_id}) for file: {file_data}")
                        continue
                    
                    # If object_id is not provided, try to find it in discovered_objects_optimized
                    if not object_id:
                        cursor.execute("""
                            SELECT object_id FROM discovered_objects_optimized 
                            WHERE client_id = %s AND store_id = %s AND name = %s
                            LIMIT 1
                        """, (client_id, store_id, file_name))
                        
                        result = cursor.fetchone()
                        if result:
                            object_id = result[0]
                    
                    # Check for duplicates within the same session
                    cursor.execute("""
                        SELECT COUNT(*) FROM selected_objects 
                        WHERE client_id = %s AND scan_session_id = %s AND store_id = %s AND object_name = %s
                    """, (client_id, scan_session_id, store_id, file_name))
                    
                    existing_count = cursor.fetchone()[0]
                    if existing_count > 0:
                        duplicate_count += 1
                        continue
                    
                    # Insert the selection
                    cursor.execute("""
                        INSERT INTO selected_objects (
                            client_id, scan_session_id, object_id, store_id,
                            object_name, object_type, object_path
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        client_id,
                        scan_session_id,
                        object_id,  # This might be None if not found
                        store_id,
                        file_name,
                        object_type,
                        file_path
                    ))
                    
                    saved_count += 1
                    
                except Exception as file_error:
                    errors.append(f"Error processing file {file_data}: {str(file_error)}")
                    continue
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Saved {saved_count} file selections for client {client_id}, session {scan_session_id}")
            
            return {
                'success': True,
                'saved_count': saved_count,
                'duplicate_count': duplicate_count,
                'error_count': len(errors),
                'errors': errors,
                'message': f"Successfully saved {saved_count} file selections"
            }
            
        except Exception as e:
            logger.error(f"Error saving file selections: {e}")
            return {
                'success': False,
                'saved_count': 0,
                'duplicate_count': 0,
                'error_count': 1,
                'errors': [str(e)],
                'message': f"Failed to save file selections: {str(e)}"
            }

# Alias for backward compatibility
CloudScanDBManager = PostgreSQLCloudScanDBManager
