"""
File Scanner Module
Handles scanning of CSV, JSON, YAML files
"""

import csv
import json
import yaml
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from .base_scanner import BaseScanner

logger = logging.getLogger(__name__)


class FileScanner(BaseScanner):
    """Base scanner for file-based data sources"""
    
    def scan(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scan a file for SDEs based on file type
        
        Args:
            source: File configuration containing path and type
            
        Returns:
            List of SDE findings
        """
        file_path = source.get('file_path')
        if not file_path:
            logger.error("File path not provided")
            return []
        
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.csv':
            return CSVScanner(self.privacy_patterns, self.field_mappings, self.sde_categories).scan(source)
        elif file_extension == '.json':
            return JSONScanner(self.privacy_patterns, self.field_mappings, self.sde_categories).scan(source)
        elif file_extension in ['.yaml', '.yml']:
            return YAMLScanner(self.privacy_patterns, self.field_mappings, self.sde_categories).scan(source)
        else:
            logger.warning(f"Unsupported file type: {file_extension}")
            return []


class CSVScanner(BaseScanner):
    """Scanner for CSV files"""
    
    def scan(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scan CSV file for SDEs
        
        Args:
            source: CSV file configuration
            
        Returns:
            List of SDE findings
        """
        findings = []
        file_path = source.get('file_path')
        
        try:
            # Read CSV with pandas for better handling of different formats
            df = pd.read_csv(file_path, nrows=source.get('content_sample_size', 1000))
            
            # Analyze column names
            for column_name in df.columns:
                field_findings = self.analyze_field_name(
                    column_name, 'string', Path(file_path).name, source
                )
                findings.extend(field_findings)
                
                # Analyze column content if enabled
                if source.get('perform_content_scan', True):
                    content_findings = self._scan_column_content(
                        df[column_name], column_name, source
                    )
                    findings.extend(content_findings)
                    
        except Exception as e:
            logger.error(f"Error scanning CSV file {file_path}: {str(e)}")
            
            # Fallback to basic CSV reader
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    headers = next(reader)
                    
                    # Analyze headers only
                    for header in headers:
                        field_findings = self.analyze_field_name(
                            header, 'string', Path(file_path).name, source
                        )
                        findings.extend(field_findings)
                        
            except Exception as e2:
                logger.error(f"Fallback CSV scanning also failed: {str(e2)}")
        
        return findings
    
    def _scan_column_content(self, column_series, column_name: str, 
                            source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scan column content for SDE patterns
        
        Args:
            column_series: Pandas series containing column data
            column_name: Name of the column
            source: Source configuration
            
        Returns:
            List of content-based findings
        """
        findings = []
        
        # Sample non-null values
        sample_size = min(100, len(column_series))
        non_null_values = column_series.dropna().head(sample_size)
        
        for value in non_null_values:
            content_str = str(value)
            if content_str and len(content_str.strip()) > 0:
                content_findings = self.analyze_field_content(
                    content_str, column_name, source
                )
                findings.extend(content_findings)
        
        return findings


class JSONScanner(BaseScanner):
    """Scanner for JSON files"""
    
    def scan(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scan JSON file for SDEs
        
        Args:
            source: JSON file configuration
            
        Returns:
            List of SDE findings
        """
        findings = []
        file_path = source.get('file_path')
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
            findings = self._scan_json_object(data, source, Path(file_path).name)
                
        except Exception as e:
            logger.error(f"Error scanning JSON file {file_path}: {str(e)}")
        
        return findings
    
    def _scan_json_object(self, obj: Any, source: Dict[str, Any], 
                         object_name: str, path: str = "") -> List[Dict[str, Any]]:
        """
        Recursively scan JSON object for SDEs
        
        Args:
            obj: JSON object or primitive
            source: Source configuration
            object_name: Name of the JSON object/file
            path: Current object path
            
        Returns:
            List of SDE findings
        """
        findings = []
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                # Analyze field name
                field_findings = self.analyze_field_name(
                    key, type(value).__name__, object_name, source, current_path
                )
                findings.extend(field_findings)
                
                # Analyze content if it's a primitive value
                if isinstance(value, (str, int, float)):
                    content_findings = self.analyze_field_content(
                        str(value), key, source, current_path
                    )
                    findings.extend(content_findings)
                
                # Recursively scan nested objects
                elif isinstance(value, (dict, list)):
                    nested_findings = self._scan_json_object(
                        value, source, object_name, current_path
                    )
                    findings.extend(nested_findings)
                    
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                nested_findings = self._scan_json_object(
                    item, source, object_name, current_path
                )
                findings.extend(nested_findings)
        
        return findings


class YAMLScanner(BaseScanner):
    """Scanner for YAML files"""
    
    def scan(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scan YAML file for SDEs
        
        Args:
            source: YAML file configuration
            
        Returns:
            List of SDE findings
        """
        findings = []
        file_path = source.get('file_path')
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                
            findings = self._scan_yaml_object(data, source, Path(file_path).name)
                
        except Exception as e:
            logger.error(f"Error scanning YAML file {file_path}: {str(e)}")
        
        return findings
    
    def _scan_yaml_object(self, obj: Any, source: Dict[str, Any], 
                         object_name: str, path: str = "") -> List[Dict[str, Any]]:
        """
        Recursively scan YAML object for SDEs
        
        Args:
            obj: YAML object or primitive
            source: Source configuration
            object_name: Name of the YAML object/file
            path: Current object path
            
        Returns:
            List of SDE findings
        """
        findings = []
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                # Analyze field name
                field_findings = self.analyze_field_name(
                    key, type(value).__name__, object_name, source, current_path
                )
                findings.extend(field_findings)
                
                # Analyze content if it's a primitive value
                if isinstance(value, (str, int, float)):
                    content_findings = self.analyze_field_content(
                        str(value), key, source, current_path
                    )
                    findings.extend(content_findings)
                
                # Recursively scan nested objects
                elif isinstance(value, (dict, list)):
                    nested_findings = self._scan_yaml_object(
                        value, source, object_name, current_path
                    )
                    findings.extend(nested_findings)
                    
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                nested_findings = self._scan_yaml_object(
                    item, source, object_name, current_path
                )
                findings.extend(nested_findings)
        
        return findings
