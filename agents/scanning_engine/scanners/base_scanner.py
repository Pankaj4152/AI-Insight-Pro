"""
Base Scanner Class
Abstract base class for all specialized scanners
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseScanner(ABC):
    """
    Abstract base class for all specialized scanners
    Provides common functionality for SDE detection and analysis
    """
    
    def __init__(self, privacy_patterns: Dict[str, Any], field_mappings: Dict[str, Any], 
                 sde_categories: Dict[str, Any], pattern_sensitivity_mapping: Dict[str, str] = None,
                 scanning_agent=None):
        """
        Initialize base scanner with patterns and configurations
        
        Args:
            privacy_patterns: Regex patterns for content analysis
            field_mappings: Field name to SDE type mappings
            sde_categories: SDE category definitions with risk levels
            pattern_sensitivity_mapping: Mapping of pattern types to their sensitivity levels from client_selected_sde
            scanning_agent: Reference to the scanning agent for database sensitivity lookup
        """
        self.privacy_patterns = privacy_patterns
        self.field_mappings = field_mappings
        self.sde_categories = sde_categories
        self.pattern_sensitivity_mapping = pattern_sensitivity_mapping or {}
        self.scanning_agent = scanning_agent  # Reference for database sensitivity lookup
        logger.info(f"BaseScanner initialized with {len(self.privacy_patterns)} pattern types and {len(self.pattern_sensitivity_mapping)} sensitivity mappings")
        
    @abstractmethod
    def scan(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scan a data source for SDEs
        
        Args:
            source: Source configuration dictionary
            
        Returns:
            List of findings
        """
        pass
    
    def analyze_field_name(self, field_name: str, field_type: str, table_name: str,
                          source_info: Dict[str, Any], object_path: str = None) -> List[Dict[str, Any]]:
        """
        Advanced field name analysis with SDE classification
        
        Args:
            field_name: Name of the field
            field_type: Data type of the field
            table_name: Name of table/file
            source_info: Source configuration
            object_path: JSON object path (for nested structures)
        
        Returns:
            List of detailed findings
        """
        findings = []
        field_lower = field_name.lower()
        
        # Check against field mappings
        for pattern, mapping_info in self.field_mappings.items():
            if pattern.lower() in field_lower or field_lower == pattern.lower():
                confidence = 1.0 if field_lower == pattern.lower() else 0.8
                
                # Determine pattern type for risk level calculation
                data_type = mapping_info.get('data_type', pattern)
                pattern_type = f"{data_type}_patterns"
                risk_level = self._get_risk_level_for_pattern(pattern_type)
                
                # Get sensitivity using strict database lookup
                sde_type = mapping_info.get('data_type', pattern)
                sensitivity = self._get_sensitivity_from_database(sde_type, pattern_type)
                
                finding = {
                    'finding_id': f"field_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(field_name + table_name) % 10000}",
                    'finding_type': 'field_name_sde',
                    'is_sde': True,
                    'sde_type': sde_type,
                    'sde_category': mapping_info.get('category', 'UNKNOWN'),
                    'sensitivity': sensitivity,  # From database lookup only
                    'risk_level': risk_level,  # Use client sensitivity instead of hardcoded 'MEDIUM'
                    'field_name': field_name,
                    'field_type': field_type,
                    'table_name': table_name,
                    'object_path': object_path,
                    'location_metadata': {
                        'source_name': source_info.get('name', 'unknown'),
                        'source_type': source_info.get('type', 'unknown'),
                        'file_path': source_info.get('file_path'),
                        'database_name': source_info.get('database'),
                        'schema_name': source_info.get('schema')
                    },
                    'confidence_score': confidence,
                    'detection_method': 'field_name_mapping',
                    'privacy_implications': self._get_privacy_implications(mapping_info.get('category')),
                    'timestamp': datetime.now().isoformat()
                }
                findings.append(finding)
                break
        
        return findings
    
    def analyze_field_content(self, content: str, field_name: str, 
                             source_info: Dict[str, Any], object_path: str = None) -> List[Dict[str, Any]]:
        """Analyze field content using regex patterns"""
        findings = []
        
        # Check content against privacy patterns
        for pattern_type, patterns in self.privacy_patterns.items():
            if isinstance(patterns, list):
                for pattern in patterns:
                    matches = re.findall(pattern, str(content))
                    if matches:
                        # Determine SDE category based on pattern type
                        sde_category = self._pattern_to_category(pattern_type)
                        risk_level = self._get_risk_level_for_pattern(pattern_type)
                        
                        # Get sensitivity using strict database lookup
                        sde_type = pattern_type.replace('_patterns', '')
                        sensitivity = self._get_sensitivity_from_database(sde_type, pattern_type)
                        
                        finding = {
                            'finding_id': f"content_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(content + field_name) % 10000}",
                            'finding_type': 'content_pattern_match',
                            'is_sde': True,
                            'sde_type': sde_type,
                            'sde_category': sde_category,
                            'sensitivity': sensitivity,  # From database lookup only
                            'risk_level': risk_level,
                            'field_name': field_name,
                            'object_path': object_path,
                            'pattern_matched': pattern,
                            'matches_found': len(matches),
                            'sample_matches': matches[:3],  # First 3 matches
                            'location_metadata': {
                                'source_name': source_info.get('name', 'unknown'),
                                'source_type': source_info.get('type', 'unknown'),
                                'file_path': source_info.get('file_path')
                            },
                            'confidence_score': min(len(matches) / 10, 1.0),
                            'detection_method': 'regex_pattern_match',
                            'privacy_implications': self._get_privacy_implications(sde_category),
                            'timestamp': datetime.now().isoformat()
                        }
                        findings.append(finding)
        
        return findings
    
    def _pattern_to_category(self, pattern_type: str) -> str:
        """Map pattern type to SDE category"""
        mapping = {
            'email_patterns': 'PII',
            'phone_patterns': 'PII', 
            'ssn_patterns': 'PII',
            'credit_card_patterns': 'FINANCIAL',
            'ip_address_patterns': 'LOCATION'
        }
        return mapping.get(pattern_type, 'UNKNOWN')
    
    def _get_risk_level_for_pattern(self, pattern_type: str) -> str:
        """Get risk level for pattern type, using client-selected sensitivity first"""
        
        # First, check if we have a client-selected sensitivity for this pattern type
        if pattern_type in self.pattern_sensitivity_mapping:
            client_sensitivity = self.pattern_sensitivity_mapping[pattern_type]
            logger.debug(f"🎯 Using client-selected sensitivity for {pattern_type}: {client_sensitivity}")
            return client_sensitivity
        
        # Check for partial matches in pattern_sensitivity_mapping
        for mapped_pattern, risk_level in self.pattern_sensitivity_mapping.items():
            if any(term in pattern_type.lower() for term in mapped_pattern.lower().split('_')):
                logger.debug(f"🎯 Using partial match client-selected sensitivity for {pattern_type} -> {mapped_pattern}: {risk_level}")
                return risk_level
        
        # Fallback to pattern-based risk mapping
        risk_mapping = {
            'email_patterns': 'HIGH',
            'phone_patterns': 'HIGH',
            'mobile_patterns': 'HIGH',  # Added for mobile numbers
            'id_patterns': 'HIGH',      # Added for ID numbers (can be sensitive)
            'ssn_patterns': 'CRITICAL', 
            'credit_card_patterns': 'CRITICAL',
            'passport_patterns': 'CRITICAL',
            'driver_license_patterns': 'HIGH',
            'bank_account_patterns': 'CRITICAL',
            'salary_patterns': 'HIGH',  # Added for salary/compensation data
            'name_patterns': 'MEDIUM',
            'address_patterns': 'MEDIUM',
            'ip_address_patterns': 'MEDIUM'
        }
        
        # Check exact match first
        if pattern_type in risk_mapping:
            fallback_risk = risk_mapping[pattern_type]
            logger.debug(f"🔄 Using exact fallback risk mapping for {pattern_type}: {fallback_risk}")
            return fallback_risk
        
        # Check for partial matches in fallback mapping
        for mapped_pattern, risk_level in risk_mapping.items():
            if any(term in pattern_type.lower() for term in mapped_pattern.replace('_patterns', '').split('_')):
                logger.debug(f"🔄 Using partial fallback risk mapping for {pattern_type} -> {mapped_pattern}: {risk_level}")
                return risk_level
        
        # Final fallback
        logger.debug(f"🔄 Using default fallback risk mapping for {pattern_type}: MEDIUM")
        return 'MEDIUM'
    
    def _get_sensitivity_from_database(self, sde_type: str, pattern_type: str) -> Optional[str]:
        """
        Get sensitivity level strictly from database sources via scanning agent
        
        Args:
            sde_type: Original SDE type (e.g., 'ssalary', 'personal_email')
            pattern_type: Normalized pattern type (e.g., 'salary_patterns', 'email_patterns')
            
        Returns:
            Sensitivity level string or None if not found in database sources
        """
        if self.scanning_agent and hasattr(self.scanning_agent, '_get_sensitivity_from_database'):
            return self.scanning_agent._get_sensitivity_from_database(sde_type, pattern_type)
        else:
            logger.warning("⚠️ No scanning agent available for database sensitivity lookup")
            return None
    
    def _get_privacy_implications(self, category: str) -> List[str]:
        """Get privacy compliance implications for SDE category"""
        implications = {
            'PII': ['GDPR Article 4', 'CCPA Personal Information', 'DPDP Personal Data'],
            'SPI': ['GDPR Special Categories', 'CCPA Sensitive PI', 'DPDP Sensitive Personal Data'],
            'FINANCIAL': ['PCI DSS', 'GDPR Article 4', 'Financial Privacy Rules'],
            'MEDICAL': ['HIPAA', 'GDPR Special Categories', 'Medical Privacy Laws'],
            'DEMOGRAPHIC': ['Equal Opportunity Laws', 'GDPR Profiling'],
            'LOCATION': ['Location Privacy Laws', 'GDPR Geolocation']
        }
        return implications.get(category, ['General Privacy Laws'])
    
    def create_finding(self, finding_type: str, field_name: str, table_name: str, 
                      source_info: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Create a standardized finding dictionary
        
        Args:
            finding_type: Type of finding
            field_name: Name of the field
            table_name: Name of table/file
            source_info: Source information
            **kwargs: Additional finding properties
            
        Returns:
            Standardized finding dictionary
        """
        finding = {
            'finding_id': f"{finding_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(field_name + table_name) % 10000}",
            'finding_type': finding_type,
            'field_name': field_name,
            'table_name': table_name,
            'location_metadata': {
                'source_name': source_info.get('name', 'unknown'),
                'source_type': source_info.get('type', 'unknown'),
                'file_path': source_info.get('file_path'),
                'database_name': source_info.get('database'),
                'schema_name': source_info.get('schema')
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Add any additional properties
        finding.update(kwargs)
        
        return finding
