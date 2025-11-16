"""
Data Source Connectors
Multi-connector support for various data sources
"""

import sqlite3
import pandas as pd
import os
import json
import yaml
import logging
from typing import Dict, List, Any, Optional, Union
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """Base class for all data connectors"""
    
    @abstractmethod
    def connect(self, source_config: Dict[str, Any]):
        """Establish connection to data source"""
        pass
    
    @abstractmethod
    def get_data(self, connection, query_params: Dict[str, Any] = None):
        """Retrieve data from source"""
        pass
    
    @abstractmethod
    def close(self, connection):
        """Close connection"""
        pass


class DatabaseConnector(BaseConnector):
    """Connector for database sources (SQLite, MySQL, PostgreSQL)"""
    
    def connect(self, source_config: Dict[str, Any]):
        """
        Connect to database based on configuration
        
        Args:
            source_config: Database connection configuration
        
        Returns:
            Database connection object
        """
        db_type = source_config.get('type', 'sqlite').lower()
        
        if db_type == 'sqlite':
            return self._connect_sqlite(source_config)
        elif db_type == 'mysql':
            return self._connect_mysql(source_config)
        elif db_type == 'postgresql':
            return self._connect_postgresql(source_config)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def _connect_sqlite(self, config: Dict[str, Any]):
        """Connect to SQLite database"""
        db_path = config.get('path') or config.get('database')
        if not db_path:
            raise ValueError("SQLite database path not provided")
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"SQLite database not found: {db_path}")
        
        return sqlite3.connect(db_path)
    
    def _connect_mysql(self, config: Dict[str, Any]):
        """Connect to MySQL database"""
        try:
            import mysql.connector
            
            connection_params = {
                'host': config.get('host', 'localhost'),
                'port': config.get('port', 3306),
                'user': config.get('user'),
                'password': config.get('password'),
                'database': config.get('database')
            }
            
            return mysql.connector.connect(**connection_params)
        except ImportError:
            raise ImportError("mysql-connector-python not installed. Install with: pip install mysql-connector-python")
    
    def _connect_postgresql(self, config: Dict[str, Any]):
        """Connect to PostgreSQL database"""
        try:
            import psycopg2
            
            connection_params = {
                'host': config.get('host', 'localhost'),
                'port': config.get('port', 5432),
                'user': config.get('user'),
                'password': config.get('password'),
                'database': config.get('database')
            }
            
            return psycopg2.connect(**connection_params)
        except ImportError:
            raise ImportError("psycopg2 not installed. Install with: pip install psycopg2-binary")
    
    def get_tables(self, connection) -> List[str]:
        """Get list of tables in the database"""
        try:
            if isinstance(connection, sqlite3.Connection):
                cursor = connection.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                cursor.close()
                return tables
            else:
                # For MySQL/PostgreSQL, use pandas to get table list
                query = "SHOW TABLES" if hasattr(connection, 'get_server_info') else "SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema()"
                df = pd.read_sql(query, connection)
                return df.iloc[:, 0].tolist()
        except Exception as e:
            logger.error(f"Error getting tables: {e}")
            return []
    
    def get_columns(self, connection, table_name: str) -> List[Dict[str, str]]:
        """Get column information for a table"""
        try:
            if isinstance(connection, sqlite3.Connection):
                cursor = connection.cursor()
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = []
                for row in cursor.fetchall():
                    columns.append({
                        'name': row[1],
                        'type': row[2],
                        'nullable': not row[3],
                        'primary_key': bool(row[5])
                    })
                cursor.close()
                return columns
            else:
                # For MySQL/PostgreSQL
                query = f"""
                SELECT column_name, data_type, is_nullable, column_key
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                """
                df = pd.read_sql(query, connection)
                columns = []
                for _, row in df.iterrows():
                    columns.append({
                        'name': row['column_name'],
                        'type': row['data_type'],
                        'nullable': row['is_nullable'] == 'YES',
                        'primary_key': row['column_key'] == 'PRI'
                    })
                return columns
        except Exception as e:
            logger.error(f"Error getting columns for table {table_name}: {e}")
            return []
    
    def get_sample_data(self, connection, table_name: str, limit: int = 1000) -> Optional[pd.DataFrame]:
        """Get sample data from a table"""
        try:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            return pd.read_sql(query, connection)
        except Exception as e:
            logger.error(f"Error getting sample data from {table_name}: {e}")
            return None
    
    def get_data(self, connection, query_params: Dict[str, Any] = None) -> Optional[pd.DataFrame]:
        """Execute custom query"""
        if not query_params or 'query' not in query_params:
            return None
        
        try:
            return pd.read_sql(query_params['query'], connection)
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return None
    
    def close(self, connection):
        """Close database connection"""
        try:
            connection.close()
        except Exception as e:
            logger.error(f"Error closing connection: {e}")


class FileConnector(BaseConnector):
    """Connector for file sources (CSV, Excel, JSON, YAML)"""
    
    def connect(self, source_config: Dict[str, Any]):
        """For files, connection is just validation"""
        file_path = source_config.get('file_path') or source_config.get('path')
        if not file_path:
            raise ValueError("File path not provided")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        return file_path
    
    def load_file(self, source_config: Dict[str, Any]) -> Union[pd.DataFrame, str, Dict, List]:
        """
        Load file based on its type
        
        Args:
            source_config: File configuration
        
        Returns:
            Loaded data in appropriate format
        """
        file_path = self.connect(source_config)
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext == '.csv':
                return pd.read_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                return pd.read_excel(file_path)
            elif file_ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert to DataFrame if it's a list of dicts
                    if isinstance(data, list) and data and isinstance(data[0], dict):
                        return pd.DataFrame(data)
                    return data
            elif file_ext in ['.yaml', '.yml']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    # Convert to DataFrame if possible
                    if isinstance(data, list) and data and isinstance(data[0], dict):
                        return pd.DataFrame(data)
                    return data
            elif file_ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                # Try to read as text
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {e}")
            return None
    
    def get_data(self, connection, query_params: Dict[str, Any] = None):
        """For files, return the loaded data"""
        return self.load_file({'file_path': connection})
    
    def close(self, connection):
        """No connection to close for files"""
        pass


class CloudConnector(BaseConnector):
    """Connector for cloud sources (GCP, BigQuery, AWS, Azure)"""
    
    def connect(self, source_config: Dict[str, Any]):
        """
        Connect to cloud service
        
        Args:
            source_config: Cloud service configuration
        
        Returns:
            Cloud service client
        """
        service_type = source_config.get('service', '').lower()
        
        if service_type == 'bigquery':
            return self._connect_bigquery(source_config)
        elif service_type == 'gcs':
            return self._connect_gcs(source_config)
        elif service_type == 'aws_s3':
            return self._connect_s3(source_config)
        else:
            raise ValueError(f"Unsupported cloud service: {service_type}")
    
    def _connect_bigquery(self, config: Dict[str, Any]):
        """Connect to Google BigQuery"""
        try:
            from google.cloud import bigquery
            
            project_id = config.get('project_id')
            credentials_path = config.get('credentials_path')
            
            if credentials_path and os.path.exists(credentials_path):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            
            client = bigquery.Client(project=project_id)
            return client
        except ImportError:
            raise ImportError("google-cloud-bigquery not installed. Install with: pip install google-cloud-bigquery")
    
    def _connect_gcs(self, config: Dict[str, Any]):
        """Connect to Google Cloud Storage"""
        try:
            from google.cloud import storage
            
            project_id = config.get('project_id')
            credentials_path = config.get('credentials_path')
            
            if credentials_path and os.path.exists(credentials_path):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            
            client = storage.Client(project=project_id)
            return client
        except ImportError:
            raise ImportError("google-cloud-storage not installed. Install with: pip install google-cloud-storage")
    
    def _connect_s3(self, config: Dict[str, Any]):
        """Connect to AWS S3"""
        try:
            import boto3
            
            client = boto3.client(
                's3',
                aws_access_key_id=config.get('access_key_id'),
                aws_secret_access_key=config.get('secret_access_key'),
                region_name=config.get('region', 'us-east-1')
            )
            return client
        except ImportError:
            raise ImportError("boto3 not installed. Install with: pip install boto3")
    
    def get_bigquery_datasets(self, client) -> List[str]:
        """Get list of BigQuery datasets"""
        try:
            datasets = list(client.list_datasets())
            return [dataset.dataset_id for dataset in datasets]
        except Exception as e:
            logger.error(f"Error getting BigQuery datasets: {e}")
            return []
    
    def get_bigquery_tables(self, client, dataset_id: str) -> List[str]:
        """Get list of tables in a BigQuery dataset"""
        try:
            dataset_ref = client.dataset(dataset_id)
            tables = list(client.list_tables(dataset_ref))
            return [table.table_id for table in tables]
        except Exception as e:
            logger.error(f"Error getting BigQuery tables: {e}")
            return []
    
    def query_bigquery(self, client, query: str) -> Optional[pd.DataFrame]:
        """Execute BigQuery query"""
        try:
            return client.query(query).to_dataframe()
        except Exception as e:
            logger.error(f"Error executing BigQuery query: {e}")
            return None
    
    def get_data(self, connection, query_params: Dict[str, Any] = None) -> Optional[pd.DataFrame]:
        """Get data from cloud service"""
        if not query_params:
            return None
        
        service_type = query_params.get('service_type', '').lower()
        
        if service_type == 'bigquery':
            query = query_params.get('query')
            if query:
                return self.query_bigquery(connection, query)
        
        return None
    
    def close(self, connection):
        """Close cloud connection"""
        # Most cloud clients don't need explicit closing
        pass


class ConnectorFactory:
    """Factory class to create appropriate connectors"""
    
    @staticmethod
    def create_connector(source_type: str) -> BaseConnector:
        """
        Create appropriate connector based on source type
        
        Args:
            source_type: Type of data source
        
        Returns:
            Appropriate connector instance
        """
        source_type = source_type.lower()
        
        if source_type in ['sqlite', 'mysql', 'postgresql', 'database']:
            return DatabaseConnector()
        elif source_type in ['csv', 'excel', 'json', 'yaml', 'txt', 'file']:
            return FileConnector()
        elif source_type in ['bigquery', 'gcs', 'aws_s3', 'cloud']:
            return CloudConnector()
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
    
    @staticmethod
    def get_supported_types() -> Dict[str, List[str]]:
        """Get list of supported source types"""
        return {
            'database': ['sqlite', 'mysql', 'postgresql'],
            'file': ['csv', 'excel', 'json', 'yaml', 'txt'],
            'cloud': ['bigquery', 'gcs', 'aws_s3']
        }
