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
        self.base_path = Path(__file__).parent
        # For Docker compatibility, try multiple paths for config file
        if config_file:
            self.config_file = config_file
        else:
            # Try current directory first (Docker), then parent directory
            possible_paths = [
                str(Path.cwd() / "agent_config.yaml"),
                str(self.base_path / "agent_config.yaml"),
                "/app/agent_config.yaml"  # Docker container path
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    self.config_file = path
                    break
            else:
                self.config_file = str(self.base_path / "agent_config.yaml")
        
        # For Docker compatibility, try multiple paths for env file
        if env_file:
            self.env_file = env_file
        else:
            # Try current directory first (Docker), then parent directory
            possible_env_paths = [
                str(Path.cwd() / ".env"),
                str(self.base_path / ".env"),
                "/app/.env"  # Docker container path
            ]
            for path in possible_env_paths:
                if os.path.exists(path):
                    self.env_file = path
                    break
            else:
                self.env_file = str(self.base_path / ".env")
        
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
        return {
            'database': {
                'type': 'postgresql',
                'postgresql': {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'data_protection',
                    'user': 'postgres',
                    'password': 'password',
                    'sslmode': 'prefer'
                }
            },
            'credentials': {
                'openai_api_key_env': 'OPENAI_API_KEY'
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
        
        return DataSourceConfig(
            name=source_data.get('name'),
            type=source_data.get('type'),
            location=source_data.get('location'),
            project_id=source_data.get('project_id'),
            credentials_path=source_data.get('credentials_path'),
            database_name=source_data.get('database_name'),
            host=source_data.get('host'),
            port=source_data.get('port'),
            username=source_data.get('username'),
            password=source_data.get('password'),
            access_control=source_data.get('access_control', 'private')
        )
    
    # def get_all_data_sources(self) -> List[DataSourceConfig]:
    #     """Get all configured data sources"""
    #     sources = []
    #     for source_name in self.config.get('data_sources', {}):
    #         source_config = self.get_data_source_config(source_name)
    #         if source_config:
    #             sources.append(source_config)
    #     return sources
    
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
            print(f"ERROR: Error adding data source: {e}")
            return False
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.config.get('database', {})

    def get_credential_path_for_client(self, client_id: str, connections_type: str) -> Optional[str]:
        """Fetch credential path for a client and connection type from client_connections table"""
        conn = psycopg2.connect("postgresql://data_privacy_user:data_privacy_db123_pass@34.131.227.103:5432/master_data_privacy")
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

    def get_all_data_sources_for_client(self, client_id: str) -> List[DataSourceConfig]:
        """Get all data sources for a client from client_connections table"""
        sources = []
        conn = psycopg2.connect("postgresql://data_privacy_user:data_privacy_db123_pass@34.131.227.103:5432/master_data_privacy")
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT connections_type, connection_cred, conn_name
                FROM client_connections
                WHERE client_id = %s
                """,
                (client_id,)
            )
            for row in cursor.fetchall():
                connections_type, connection_cred, conn_name = row
                if isinstance(connection_cred, str):
                    import json
                    cred_json = json.loads(connection_cred)
                else:
                    cred_json = connection_cred
                # Build DataSourceConfig based on type
                ds_kwargs = {
                    'name': conn_name,
                    'type': connections_type,
                    'location': cred_json.get('location', ''),
                    'credentials_path': cred_json.get('path', None),
                }
                # Optionally add more fields if present
                for field in ['project_id', 'database_name', 'host', 'port', 'username', 'password', 'access_control']:
                    if field in cred_json:
                        ds_kwargs[field] = cred_json[field]
                sources.append(DataSourceConfig(**ds_kwargs))
        finally:
            cursor.close()
            conn.close()
        return sources

