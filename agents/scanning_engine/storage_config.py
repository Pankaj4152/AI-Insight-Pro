"""
Storage Configuration for Modular Scanner
Maps scanner findings to database schema
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DB_URL")

class ScannerStorageManager:
    """
    Manages storage of scanning results in the PostgreSQL database
    """
    
    def __init__(self):
        self.ensure_schema_compatibility()

    def get_conn(self):
        return psycopg2.connect(DB_URL)

    def ensure_schema_compatibility(self):
        """
        Ensure database schema can handle modular scanner output
        """
        conn = self.get_conn()
        cursor = conn.cursor()
        # Add new columns to scan_findings if they don't exist
        new_columns = [
            ('finding_type', 'TEXT'),
            ('is_sde', 'BOOLEAN'),
            ('sde_category', 'TEXT'),
            ('risk_level', 'TEXT'),
            ('field_type', 'TEXT'),
            ('object_path', 'TEXT'),
            ('confidence_score', 'REAL'),
            ('detection_method', 'TEXT'),
            ('pattern_matched', 'TEXT'),
            ('matches_found', 'INTEGER'),
            ('sample_matches', 'TEXT'),
            ('location_metadata', 'TEXT'),
            ('privacy_implications', 'TEXT'),
            ('scan_timestamp', 'TEXT')
        ]
        for column_name, column_type in new_columns:
            try:
                cursor.execute(f"ALTER TABLE scan_findings ADD COLUMN {column_name} {column_type}")
                conn.commit()
            except psycopg2.errors.DuplicateColumn:
                conn.rollback()
            except Exception:
                conn.rollback()
        cursor.close()
        conn.close()

    def store_scan_results(self, scan_results: Dict[str, Any]) -> int:
        """
        Store complete scan results in database
        Args:
            scan_results: Results from MultiConnectorScanner.scan_sources()
        Returns:
            scan_id: ID of the stored scan
        """
        conn = self.get_conn()
        cursor = conn.cursor()
        try:
            scan_metadata = {
                'total_findings': scan_results.get('total_findings', 0),
                'scan_timestamp': scan_results.get('scan_timestamp'),
                'source_summaries': scan_results.get('source_summaries', []),
                'overall_summary': scan_results.get('overall_summary', {})
            }
            cursor.execute(
                "INSERT INTO scans (store_id, scan_data, status) VALUES (%s, %s, %s) RETURNING scan_id",
                (1, json.dumps(scan_metadata), 'completed')
            )
            scan_id = cursor.fetchone()[0]
            for finding in scan_results.get('findings', []):
                self._store_single_finding(cursor, scan_id, finding)
            conn.commit()
            return scan_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def _store_single_finding(self, cursor, scan_id: int, finding: Dict[str, Any]):
        sde_id = self._get_or_create_sde(cursor, finding)
        finding_data = {
            'scan_id': scan_id,
            'sde_id': sde_id,
            'data_value': finding.get('sample_matches', [''])[0] if finding.get('sample_matches') else '',
            'sensitivity': finding.get('risk_level', 'UNKNOWN').lower(),
            'finding_type': finding.get('finding_type'),
            'is_sde': finding.get('is_sde', False),
            'sde_category': finding.get('sde_category'),
            'risk_level': finding.get('risk_level'),
            'field_type': finding.get('field_type'),
            'object_path': finding.get('object_path'),
            'confidence_score': finding.get('confidence_score'),
            'detection_method': finding.get('detection_method'),
            'pattern_matched': finding.get('pattern_matched'),
            'matches_found': finding.get('matches_found'),
            'sample_matches': json.dumps(finding.get('sample_matches', [])),
            'location_metadata': json.dumps(finding.get('location_metadata', {})),
            'privacy_implications': json.dumps(finding.get('privacy_implications', [])),
            'scan_timestamp': finding.get('timestamp', datetime.now().isoformat())
        }
        cursor.execute("""
            INSERT INTO scan_findings (
                scan_id, sde_id, data_value, sensitivity,
                finding_type, is_sde, sde_category, risk_level,
                field_type, object_path, confidence_score,
                detection_method, pattern_matched, matches_found,
                sample_matches, location_metadata, privacy_implications,
                scan_timestamp
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            finding_data['scan_id'], finding_data['sde_id'],
            finding_data['data_value'], finding_data['sensitivity'],
            finding_data['finding_type'], finding_data['is_sde'],
            finding_data['sde_category'], finding_data['risk_level'],
            finding_data['field_type'], finding_data['object_path'],
            finding_data['confidence_score'], finding_data['detection_method'],
            finding_data['pattern_matched'], finding_data['matches_found'],
            finding_data['sample_matches'], finding_data['location_metadata'],
            finding_data['privacy_implications'], finding_data['scan_timestamp']
        ))

    def _get_or_create_sde(self, cursor, finding: Dict[str, Any]) -> int:
        location_metadata = finding.get('location_metadata', {})
        cursor.execute("""
            SELECT sde_id FROM sdes 
            WHERE dataset_name = %s AND column_name = %s AND data_type = %s
        """, (
            finding.get('table_name', location_metadata.get('source_name', 'unknown')),
            finding.get('field_name', ''),
            finding.get('sde_type', 'unknown')
        ))
        result = cursor.fetchone()
        if result:
            return result[0]
        cursor.execute("""
            INSERT INTO sdes (store_id, dataset_name, data_type, column_name, sensitivity, protection_method)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING sde_id
        """, (
            1,
            finding.get('table_name', location_metadata.get('source_name', 'unknown')),
            finding.get('sde_type', 'unknown'),
            finding.get('field_name', ''),
            finding.get('risk_level', 'UNKNOWN').lower(),
            'none'
        ))
        return cursor.fetchone()[0]

    def register_data_source(self, source_config: Dict[str, Any]) -> int:
        conn = self.get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO data_stores (store_name, location, type, access_control)
            VALUES (%s, %s, %s, %s) RETURNING store_id
        """, (
            source_config.get('name', 'unknown'),
            source_config.get('file_path', source_config.get('connection_string', '')),
            source_config.get('type', 'unknown'),
            source_config.get('access_control', 'read')
        ))
        store_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return store_id

    def get_scan_results(self, scan_id: int) -> Dict[str, Any]:
        conn = self.get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT scan_data FROM scans WHERE scan_id = %s", (scan_id,))
        scan_data = cursor.fetchone()
        if not scan_data:
            cursor.close()
            conn.close()
            return {}
        cursor.execute("""
            SELECT f.*, s.dataset_name, s.column_name, s.data_type
            FROM scan_findings f
            JOIN sdes s ON f.sde_id = s.sde_id
            WHERE f.scan_id = %s
        """, (scan_id,))
        findings = []
        for row in cursor.fetchall():
            finding = {
                'finding_id': row[0],
                'scan_id': row[1],
                'sde_id': row[2],
                'data_value': row[3],
                'sensitivity': row[4],
                'dataset_name': row[-3],
                'column_name': row[-2],
                'data_type': row[-1]
            }
            findings.append(finding)
        cursor.close()
        conn.close()
        return {
            'scan_metadata': json.loads(scan_data[0]) if scan_data[0] else {},
            'findings': findings
        }


# Column mapping for reference
SCANNER_TO_DB_MAPPING = {
    # Scanner Finding Fields -> Database Columns
    'finding_id': 'Custom generated ID',
    'finding_type': 'finding_type (NEW)',
    'is_sde': 'is_sde (NEW)',
    'sde_type': 'sdes.data_type',
    'sde_category': 'sde_category (NEW)',
    'risk_level': 'risk_level (NEW)',
    'field_name': 'sdes.column_name',
    'table_name': 'sdes.dataset_name',
    'confidence_score': 'confidence_score (NEW)',
    'detection_method': 'detection_method (NEW)',
    'pattern_matched': 'pattern_matched (NEW)',
    'matches_found': 'matches_found (NEW)',
    'sample_matches': 'sample_matches (NEW, JSON)',
    'location_metadata': 'location_metadata (NEW, JSON)',
    'privacy_implications': 'privacy_implications (NEW, JSON)',
    'timestamp': 'scan_timestamp (NEW)'
}

# Required database schema updates
SCHEMA_UPDATES = """
-- Add these columns to scan_findings table:
ALTER TABLE scan_findings ADD COLUMN finding_type TEXT;
ALTER TABLE scan_findings ADD COLUMN is_sde BOOLEAN;
ALTER TABLE scan_findings ADD COLUMN sde_category TEXT;
ALTER TABLE scan_findings ADD COLUMN risk_level TEXT;
ALTER TABLE scan_findings ADD COLUMN field_type TEXT;
ALTER TABLE scan_findings ADD COLUMN object_path TEXT;
ALTER TABLE scan_findings ADD COLUMN confidence_score REAL;
ALTER TABLE scan_findings ADD COLUMN detection_method TEXT;
ALTER TABLE scan_findings ADD COLUMN pattern_matched TEXT;
ALTER TABLE scan_findings ADD COLUMN matches_found INTEGER;
ALTER TABLE scan_findings ADD COLUMN sample_matches TEXT;
ALTER TABLE scan_findings ADD COLUMN location_metadata TEXT;
ALTER TABLE scan_findings ADD COLUMN privacy_implications TEXT;
ALTER TABLE scan_findings ADD COLUMN scan_timestamp TEXT;
"""
