"""
Pattern Management Module
Handles SDE pattern detection and management
"""

import os
import yaml
import re
import logging
import psycopg2
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional, Tuple

# Load environment variables
load_dotenv()
DB_URL = os.getenv("DB_URL")

logger = logging.getLogger(__name__)


class PatternManager:
    """
    Manages SDE detection patterns including regex patterns and built-in functions
    """
    
    def __init__(self, config_path: str = None, use_database: bool = True):
        """
        Initialize pattern manager with configuration path or database
        
        Args:
            config_path: Path to configuration directory (fallback only)
            use_database: Whether to load patterns from database (default: True)
        """
        self.config_path = config_path
        self.use_database = use_database
        
        if use_database:
            self.regex_patterns = self._load_regex_patterns_from_db()
        else:
            # Fallback to YAML files for backward compatibility
            self.regex_patterns = self._load_regex_patterns_from_yaml()
        
        # Remove hardcoded built-in patterns - database is now the primary source
        # Keep only essential validation functions
        self.builtin_patterns = {}
        
        logger.info(f"✅ PatternManager initialized with {len(self.regex_patterns)} database patterns")
        logger.info(f"📊 Data source: {'DATABASE (primary)' if use_database else 'YAML (fallback)'}")
        
        # Log pattern distribution
        if self.regex_patterns:
            sensitivity_counts = {}
            for pattern in self.regex_patterns:
                sensitivity = pattern.get('sensitivity', 'unknown')
                sensitivity_counts[sensitivity] = sensitivity_counts.get(sensitivity, 0) + 1
            logger.info(f"📈 Sensitivity distribution: {sensitivity_counts}")
    
    def _get_database_connection(self):
        """Get database connection"""
        if not DB_URL:
            raise ValueError("DB_URL environment variable not set")
        return psycopg2.connect(DB_URL)
    
    def _load_regex_patterns_from_db(self) -> List[Dict[str, Any]]:
        """
        Load regex patterns from database tables (PRIMARY SOURCE)
        
        Returns:
            List of pattern dictionaries with SDE information
        """
        try:
            conn = self._get_database_connection()
            cursor = conn.cursor()
            
            # Query to join regexes and sde_patterns tables based on your actual schema
            # From screenshots: regexes(regex_id, pattern_name, regex_pattern)
            # From screenshots: sde_patterns(pattern_id, pattern_name, data_type, sensitivity)
            query = """
                SELECT 
                    r.regex_id,
                    r.pattern_name,
                    r.regex_pattern,
                    s.data_type,
                    s.sensitivity,
                    'encryption' as protection_method
                FROM regexes r
                LEFT JOIN sde_patterns s ON r.pattern_name = s.pattern_name
                WHERE r.regex_pattern IS NOT NULL AND r.regex_pattern != ''
                ORDER BY r.pattern_name
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            patterns = []
            for row in rows:
                regex_id, pattern_name, regex_pattern, data_type, sensitivity, protection_method = row
                
                pattern_dict = {
                    'regex_id': regex_id,
                    'pattern_name': pattern_name or 'unknown',
                    'data_type': data_type or pattern_name or 'unknown',  # For backward compatibility
                    'regex_pattern': regex_pattern or '',
                    'sensitivity': sensitivity or 'medium',
                    'protection_method': protection_method or 'encryption'
                }
                patterns.append(pattern_dict)
            
            conn.close()
            logger.info(f"✅ Loaded {len(patterns)} regex patterns from DATABASE (primary source)")
            return patterns
            
        except Exception as e:
            logger.error(f"❌ Error loading regex patterns from database: {e}")
            logger.warning("🔄 Falling back to YAML configuration")
            return self._load_regex_patterns_from_yaml()
    
    def _load_regex_patterns_from_yaml(self) -> List[Dict[str, Any]]:
        """Load regex patterns from YAML configuration (fallback)"""
        if not self.config_path:
            logger.warning("No config path provided for YAML fallback")
            return []
            
        pattern_file = os.path.join(self.config_path, 'regex_patterns.yaml')
        try:
            with open(pattern_file, 'r') as f:
                patterns = yaml.safe_load(f)
                return patterns if isinstance(patterns, list) else []
        except FileNotFoundError:
            logger.warning(f"Regex patterns file not found: {pattern_file}")
            return []
        except Exception as e:
            logger.error(f"Error loading regex patterns from YAML: {e}")
            return []
    
    def _load_regex_patterns(self) -> List[Dict[str, Any]]:
        """Legacy method for backward compatibility"""
        return self._load_regex_patterns_from_yaml()
    
    def _initialize_builtin_patterns(self) -> Dict[str, callable]:
        """
        Initialize built-in pattern detection functions (REMOVED - using database only)
        Database is now the primary and preferred source for all patterns
        """
        # Hardcoded patterns removed as requested - database is primary source
        logger.info("🗑️ Built-in hardcoded patterns removed - using database patterns only")
        return {}
    
    def get_regex_patterns(self) -> List[Dict[str, Any]]:
        """Get all regex patterns"""
        return self.regex_patterns
    
    def reload_patterns_from_database(self) -> bool:
        """
        Reload patterns from database at runtime
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.regex_patterns = self._load_regex_patterns_from_db()
            logger.info("Successfully reloaded patterns from database")
            return True
        except Exception as e:
            logger.error(f"Error reloading patterns from database: {e}")
            return False
    
    def get_sde_pattern_mapping(self) -> Dict[str, Dict[str, Any]]:
        """
        Get mapping of pattern names to their SDE information
        
        Returns:
            Dictionary mapping pattern names to SDE details
        """
        mapping = {}
        for pattern in self.regex_patterns:
            pattern_name = pattern.get('pattern_name', 'unknown')
            mapping[pattern_name] = {
                'regex_id': pattern.get('regex_id'),
                'data_type': pattern.get('data_type', pattern_name),
                'regex_pattern': pattern.get('regex_pattern', ''),
                'sensitivity': pattern.get('sensitivity', 'medium'),
                'protection_method': pattern.get('protection_method', 'none')
            }
        return mapping
    
    def get_patterns_by_sensitivity(self, sensitivity: str) -> List[Dict[str, Any]]:
        """
        Get patterns filtered by sensitivity level
        
        Args:
            sensitivity: Sensitivity level (high, medium, low)
        
        Returns:
            List of patterns matching the sensitivity level
        """
        return [
            pattern for pattern in self.regex_patterns 
            if pattern.get('sensitivity', '').lower() == sensitivity.lower()
        ]
    
    def get_pattern_by_name(self, pattern_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific pattern by name
        
        Args:
            pattern_name: Name of the pattern to retrieve
        
        Returns:
            Pattern dictionary or None if not found
        """
        for pattern in self.regex_patterns:
            if pattern.get('pattern_name') == pattern_name:
                return pattern
        return None
    
    def add_pattern_to_database(self, pattern_name: str, regex_pattern: str, 
                               sensitivity: str = 'medium', 
                               protection_method: str = 'none') -> bool:
        """
        Add a new pattern to the database
        
        Args:
            pattern_name: Name of the pattern
            regex_pattern: Regular expression pattern
            sensitivity: Sensitivity level
            protection_method: Protection method
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate regex pattern
            re.compile(regex_pattern)
            
            conn = self._get_database_connection()
            cursor = conn.cursor()
            
            # Insert into regexes table
            cursor.execute("""
                INSERT INTO regexes (pattern_name, regex_pattern)
                VALUES (%s, %s)
                ON CONFLICT (pattern_name) DO UPDATE SET
                regex_pattern = EXCLUDED.regex_pattern
                RETURNING regex_id
            """, (pattern_name, regex_pattern))
            
            regex_id = cursor.fetchone()[0]
            
            # Insert into sde_patterns table
            cursor.execute("""
                INSERT INTO sde_patterns (pattern_name, sensitivity, protection_method)
                VALUES (%s, %s, %s)
                ON CONFLICT (pattern_name) DO UPDATE SET
                sensitivity = EXCLUDED.sensitivity,
                protection_method = EXCLUDED.protection_method
            """, (pattern_name, sensitivity, protection_method))
            
            conn.commit()
            conn.close()
            
            # Reload patterns to include the new one
            self.reload_patterns_from_database()
            
            logger.info(f"Successfully added pattern '{pattern_name}' to database")
            return True
            
        except re.error as e:
            logger.error(f"Invalid regex pattern '{regex_pattern}': {e}")
            return False
        except Exception as e:
            logger.error(f"Error adding pattern to database: {e}")
            return False
    
    def get_builtin_patterns(self) -> Dict[str, callable]:
        """Get all built-in pattern functions"""
        return self.builtin_patterns
    
    def detect_patterns_in_text(self, text: str, pattern_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Detect all patterns in given text using DATABASE PATTERNS ONLY
        
        Args:
            text: Text to analyze
            pattern_types: Specific pattern types to check (if None, check all)
        
        Returns:
            List of detected patterns with details
        """
        if not text or not isinstance(text, str):
            return []
        
        detections = []
        
        # Check ONLY database regex patterns (primary source)
        patterns_to_check = self.regex_patterns
        if pattern_types:
            patterns_to_check = [
                p for p in self.regex_patterns 
                if p.get('data_type') in pattern_types or p.get('pattern_name') in pattern_types
            ]
        
        for pattern_info in patterns_to_check:
            regex_pattern = pattern_info.get('regex_pattern', '')
            data_type = pattern_info.get('data_type', 'unknown')
            pattern_name = pattern_info.get('pattern_name', data_type)
            
            if regex_pattern:
                try:
                    matches = re.findall(regex_pattern, text)
                    if matches:
                        detections.append({
                            'pattern_type': 'database_regex',
                            'data_type': data_type,
                            'pattern_name': pattern_name,
                            'regex_id': pattern_info.get('regex_id'),
                            'sensitivity': pattern_info.get('sensitivity', 'medium'),
                            'protection_method': pattern_info.get('protection_method', 'encryption'),
                            'matches': matches,
                            'match_count': len(matches),
                            'confidence': min(len(matches) / 10, 1.0),  # Normalize confidence
                            'source': 'database'
                        })
                        logger.debug(f"✅ Detected {len(matches)} matches for pattern '{pattern_name}' (sensitivity: {pattern_info.get('sensitivity')})")
                except re.error as e:
                    logger.error(f"❌ Invalid regex pattern in {pattern_name}: {e}")
        
        # Hardcoded built-in patterns REMOVED as requested
        # Database is now the single source of truth
        
        logger.info(f"🔍 Pattern detection complete: {len(detections)} pattern types detected from database")
        return detections
    
    def validate_pattern(self, pattern: str, test_strings: List[str]) -> Dict[str, Any]:
        """
        Validate a regex pattern against test strings
        
        Args:
            pattern: Regex pattern to validate
            test_strings: List of test strings
        
        Returns:
            Validation results
        """
        try:
            compiled_pattern = re.compile(pattern)
            results = {
                'pattern': pattern,
                'is_valid': True,
                'test_results': []
            }
            
            for test_string in test_strings:
                matches = compiled_pattern.findall(test_string)
                results['test_results'].append({
                    'test_string': test_string,
                    'matches': matches,
                    'match_count': len(matches)
                })
            
            return results
            
        except re.error as e:
            return {
                'pattern': pattern,
                'is_valid': False,
                'error': str(e),
                'test_results': []
            }
    
    # ========================================================================
    # HARDCODED PATTERN METHODS REMOVED AS REQUESTED
    # Database is now the single source of truth for all patterns
    # ========================================================================
    
    # All _detect_* methods have been removed:
    # - _detect_email, _detect_phone, _detect_aadhaar, etc.
    # - _luhn_check for credit card validation
    # 
    # Reason: User requested to remove hardcoded patterns and use database as primary source
    # Database tables (regexes + sde_patterns) now contain all pattern definitions
    
    def _legacy_pattern_notice(self):
        """Notice about removed hardcoded patterns"""
        logger.info("ℹ️ Hardcoded pattern methods removed - using database patterns only")
        logger.info("📊 All patterns now loaded from regexes + sde_patterns tables")
        return "Hardcoded patterns removed - database is primary source"
    
    def add_custom_pattern(self, pattern_name: str, pattern_config: Dict[str, Any]) -> bool:
        """
        Add a custom regex pattern to the database
        
        Args:
            pattern_name: Name of the pattern
            pattern_config: Pattern configuration including regex_pattern, sensitivity, protection_method
        
        Returns:
            True if added successfully, False otherwise
        """
        regex_pattern = pattern_config.get('regex_pattern', '')
        sensitivity = pattern_config.get('sensitivity', 'medium')
        protection_method = pattern_config.get('protection_method', 'none')
        
        return self.add_pattern_to_database(pattern_name, regex_pattern, sensitivity, protection_method)
    
    def remove_pattern_from_database(self, pattern_name: str) -> bool:
        """
        Remove a pattern from the database
        
        Args:
            pattern_name: Name of the pattern to remove
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_database_connection()
            cursor = conn.cursor()
            
            # Remove from sde_patterns table
            cursor.execute("DELETE FROM sde_patterns WHERE pattern_name = %s", (pattern_name,))
            
            # Remove from regexes table
            cursor.execute("DELETE FROM regexes WHERE pattern_name = %s", (pattern_name,))
            
            conn.commit()
            conn.close()
            
            # Reload patterns to reflect the removal
            self.reload_patterns_from_database()
            
            logger.info(f"Successfully removed pattern '{pattern_name}' from database")
            return True
            
        except Exception as e:
            logger.error(f"Error removing pattern from database: {e}")
            return False
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about loaded patterns (DATABASE PRIMARY SOURCE)
        
        Returns:
            Dictionary with pattern statistics
        """
        sensitivity_counts = {}
        protection_method_counts = {}
        
        for pattern in self.regex_patterns:
            # Count by sensitivity
            sensitivity = pattern.get('sensitivity', 'unknown')
            sensitivity_counts[sensitivity] = sensitivity_counts.get(sensitivity, 0) + 1
            
            # Count by protection method
            protection_method = pattern.get('protection_method', 'unknown')
            protection_method_counts[protection_method] = protection_method_counts.get(protection_method, 0) + 1
        
        return {
            'total_database_patterns': len(self.regex_patterns),
            'total_builtin_patterns': 0,  # Removed as requested
            'database_pattern_types': list(set(p.get('data_type', 'unknown') for p in self.regex_patterns)),
            'builtin_pattern_types': [],  # Removed as requested
            'sensitivity_distribution': sensitivity_counts,
            'protection_method_distribution': protection_method_counts,
            'primary_source': 'database',
            'fallback_source': 'yaml' if self.config_path else 'none',
            'hardcoded_patterns_removed': True,
            'config_path': self.config_path
        }
