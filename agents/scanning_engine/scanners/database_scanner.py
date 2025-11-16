"""
Database Scanner Module
Handles scanning of MySQL, PostgreSQL, SQLite databases
"""

import sqlite3
import logging
from typing import Dict, List, Any, Optional
from .base_scanner import BaseScanner

# Optional database connectors
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

try:
    import psycopg2
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

logger = logging.getLogger(__name__)


class DatabaseScanner(BaseScanner):
    """Scanner for relational databases (MySQL, PostgreSQL, SQLite)"""
    
    def scan(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scan a database for SDEs
        
        Args:
            source: Database configuration containing connection details
            
        Returns:
            List of SDE findings
        """
        try:
            db_type = source.get('type', '').lower()
            
            if 'sqlite' in db_type:
                return self._scan_sqlite(source)
            elif 'mysql' in db_type:
                return self._scan_mysql(source)
            elif 'postgresql' in db_type or 'postgres' in db_type:
                return self._scan_postgresql(source)
            else:
                logger.warning(f"Unsupported database type: {db_type}")
                return []
                
        except Exception as e:
            logger.error(f"Error scanning database {source.get('name')}: {str(e)}")
            return []
    
    def _scan_sqlite(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan SQLite database"""
        findings = []
        file_path = source.get('file_path')
        
        if not file_path:
            logger.error("SQLite file path not provided")
            return findings
        
        try:
            conn = sqlite3.connect(file_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            for table_row in tables:
                table_name = table_row[0]
                
                # Get table schema
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                
                for column in columns:
                    cid, column_name, data_type, not_null, default_value, pk = column
                    
                    # Analyze field name
                    field_findings = self.analyze_field_name(
                        column_name, data_type, table_name, source
                    )
                    findings.extend(field_findings)
                    
                    # Sample data for content analysis
                    if source.get('perform_content_scan', True):
                        content_findings = self._scan_table_content(
                            cursor, table_name, column_name, source
                        )
                        findings.extend(content_findings)
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error scanning SQLite database: {str(e)}")
        
        return findings
    
    def _scan_mysql(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan MySQL database"""
        findings = []
        
        if not MYSQL_AVAILABLE:
            logger.error("MySQL connector not available. Install mysql-connector-python for MySQL support.")
            return findings
        
        try:
            connection_config = {
                'host': source.get('host', 'localhost'),
                'port': source.get('port', 3306),
                'database': source.get('database'),
                'user': source.get('username'),
                'password': source.get('password')
            }
            
            conn = mysql.connector.connect(**connection_config)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            for table_row in tables:
                table_name = table_row[0]
                
                # Get table schema
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                
                for column in columns:
                    column_name, data_type, null, key, default, extra = column
                    
                    # Analyze field name
                    field_findings = self.analyze_field_name(
                        column_name, data_type, table_name, source
                    )
                    findings.extend(field_findings)
                    
                    # Sample data for content analysis
                    if source.get('perform_content_scan', True):
                        content_findings = self._scan_table_content(
                            cursor, table_name, column_name, source
                        )
                        findings.extend(content_findings)
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error scanning MySQL database: {str(e)}")
        
        return findings
    
    def _scan_postgresql(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan PostgreSQL database"""
        findings = []
        
        if not POSTGRESQL_AVAILABLE:
            logger.error("PostgreSQL connector not available. Install psycopg2 for PostgreSQL support.")
            return findings
        
        try:
            connection_config = {
                'host': source.get('host', 'localhost'),
                'port': source.get('port', 5432),
                'database': source.get('database'),
                'user': source.get('username'),
                'password': source.get('password')
            }
            
            conn = psycopg2.connect(**connection_config)
            cursor = conn.cursor()
            
            # Get all tables in public schema
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = cursor.fetchall()
            
            for table_row in tables:
                table_name = table_row[0]
                
                # Get table schema
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = %s
                """, (table_name,))
                columns = cursor.fetchall()
                
                for column in columns:
                    column_name, data_type = column
                    
                    # Analyze field name
                    field_findings = self.analyze_field_name(
                        column_name, data_type, table_name, source
                    )
                    findings.extend(field_findings)
                    
                    # Sample data for content analysis
                    if source.get('perform_content_scan', True):
                        content_findings = self._scan_table_content(
                            cursor, table_name, column_name, source
                        )
                        findings.extend(content_findings)
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error scanning PostgreSQL database: {str(e)}")
        
        return findings
    
    def _scan_table_content(self, cursor, table_name: str, column_name: str, 
                           source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scan table content for SDE patterns
        
        Args:
            cursor: Database cursor
            table_name: Name of the table
            column_name: Name of the column
            source: Source configuration
            
        Returns:
            List of content-based findings
        """
        findings = []
        
        try:
            # Sample a limited number of rows for content analysis
            sample_size = source.get('content_sample_size', 100)
            
            # Use appropriate LIMIT syntax based on database type
            db_type = source.get('type', '').lower()
            if 'sqlite' in db_type or 'mysql' in db_type:
                query = f"SELECT {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL LIMIT {sample_size}"
            else:  # PostgreSQL
                query = f'SELECT "{column_name}" FROM "{table_name}" WHERE "{column_name}" IS NOT NULL LIMIT {sample_size}'
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                content = str(row[0]) if row[0] is not None else ""
                
                if content and len(content.strip()) > 0:
                    content_findings = self.analyze_field_content(
                        content, column_name, source
                    )
                    findings.extend(content_findings)
                    
        except Exception as e:
            logger.warning(f"Error scanning content for {table_name}.{column_name}: {str(e)}")
        
        return findings
