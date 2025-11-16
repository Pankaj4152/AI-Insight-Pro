"""
Modular Scanning Agent - Scans data sources for sensitive information
Uses configuration-driven approach and stores results in PostgreSQL database
Enhanced with dynamic SDE loading and robust fallback mechanisms
"""

import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import json
from dataclasses import dataclass
from enum import Enum

# Handle optional imports gracefully
logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    logger.warning("python-dotenv not available - using environment variables directly")
    DOTENV_AVAILABLE = False

try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    logger.warning("psycopg2 not available - database operations may fail")
    PSYCOPG2_AVAILABLE = False

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    logger.warning("yaml not available - config file operations may fail")
    YAML_AVAILABLE = False

# Database URL with fallback
DB_URL = os.getenv("DB_URL") or "postgresql://data_privacy_user:data_privacy_db123_pass@34.131.224.110:5432/master_data_privacy"

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

# Import enhanced SDE loader
try:
    from enhanced_sde_loader import EnhancedSDELoader, SDEPattern, LoadResult, SDESource
    ENHANCED_SDE_LOADER_AVAILABLE = True
except ImportError:
    logger.warning("Enhanced SDE Loader not available - using legacy pattern loading")
    ENHANCED_SDE_LOADER_AVAILABLE = False

# Import core components
try:
    from config_manager import AgentConfigManager, DataSourceConfig
    from postgresql_db_manager import PostgreSQLCloudScanDBManager
    DB_MANAGER_AVAILABLE = True
except ImportError:
    logger.warning("Core components not available")
    DB_MANAGER_AVAILABLE = False

# Add scanning_engine to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scanning_engine'))

# Import scanning components
try:
    from patterns import PatternManager
    from scanners.cloud_scanner import GCSScanner, BigQueryScanner
    from scanners.database_scanner import DatabaseScanner
    from scanners.file_scanner import FileScanner
    SCANNERS_AVAILABLE = True
except ImportError:
    logger.warning("Could not import scanning engine components")
    SCANNERS_AVAILABLE = False

# Removed duplicate credential function - using ConfigManager instead

class ModularScanningAgent:
    """
    Configuration-driven scanning agent for detecting sensitive data
    Multi-client aware - all operations are scoped to a specific client_id
    """
    
    def __init__(self, config_manager: AgentConfigManager = None, client_id: str = None):
        """
        Initialize the Scanning Agent
        
        Args:
            config_manager: Configuration manager instance
            client_id: Client ID for multi-tenant operations
        """
        self.client_id = client_id
        self.config_manager = config_manager or AgentConfigManager()
        self.db_manager = PostgreSQLCloudScanDBManager(self.config_manager, client_id=client_id)
        self.openai_api_key = self.config_manager.get_openai_api_key()
        
        # Initialize sensitivity cache for performance optimization
        self.sensitivity_cache = {}
        self.cache_loaded = False
        
        # Initialize AI scanning if LLM is available
        try:
            from llm_client import get_llm_client
            self.llm_client = get_llm_client()
            self.ai_scanning_available = self.llm_client.available
            logger.info(f"LLM client initialized: {self.llm_client.provider}")
        except Exception as e:
            self.llm_client = None
            self.ai_scanning_available = False
            logger.warning(f"LLM client initialization failed: {e}")
            logger.warning("Using basic scanning without AI enhancement")
        
        # Initialize Enhanced SDE Loader with Fallback Hierarchy
        try:
            from enhanced_sde_loader import EnhancedSDELoader
            self.sde_loader = EnhancedSDELoader(self.db_manager, self.client_id, self.config_manager)
            
            # Load SDEs using fallback hierarchy
            load_result = self.sde_loader.load_sdes_with_fallback()
            
            if load_result.success:
                logger.info(f"✅ Loaded {len(load_result.sde_patterns)} SDEs from {load_result.source_used.value}")
                if load_result.fallback_triggered:
                    logger.warning(f"⚠️ Fallback mechanism triggered - using {load_result.source_used.value}")
                
                # Convert SDE patterns to privacy patterns dict for compatibility
                self.privacy_patterns_dict = self._convert_sde_patterns_to_dict(load_result.sde_patterns)
                self.sde_patterns = load_result.sde_patterns
                self.sde_source_used = load_result.source_used
                
                logger.info(f"🔍 Privacy patterns ready: {len(self.privacy_patterns_dict)} pattern types")
                logger.info(f"🔧 DEBUG: privacy_patterns_dict = {self.privacy_patterns_dict}")
                logger.info(f"🔧 DEBUG: sde_patterns count = {len(self.sde_patterns)}")
                
                # Log source and pattern statistics
                stats = self.sde_loader.get_load_statistics()
                logger.info(f"📊 SDE Statistics: {stats}")
                
            else:
                logger.error(f"❌ Failed to load SDEs: {load_result.error_message}")
                # Initialize with empty patterns to prevent crashes
                self.privacy_patterns_dict = {}
                self.sde_patterns = []
                self.sde_source_used = None
                
        except ImportError:
            logger.warning("⚠️ Enhanced SDE Loader not available, falling back to legacy pattern manager")
            # Fallback to old pattern manager
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config')
            if SCANNERS_AVAILABLE:
                try:
                    self.pattern_manager = PatternManager(config_path=config_path, use_database=True)
                    self.privacy_patterns_dict = self._convert_patterns_filtered()
                    logger.info(f"✅ Legacy fallback: Loaded {len(self.privacy_patterns_dict)} pattern types")
                except Exception as e:
                    logger.error(f"❌ Legacy pattern manager also failed: {e}")
                    self.privacy_patterns_dict = {}
                    
        # Initialize pattern manager with DATABASE as PRIMARY SOURCE (legacy support)
        if SCANNERS_AVAILABLE and not hasattr(self, 'sde_loader'):
            try:
                config_path = os.path.join(os.path.dirname(__file__), '..', 'config')
                # DATABASE-FIRST: Use database tables as primary source, YAML as fallback only
                self.pattern_manager = PatternManager(config_path=config_path, use_database=True)
                
                # Use filtered patterns based on client SDE selections
                self.privacy_patterns_dict = self._convert_patterns_filtered()
                logger.info(f"✅ Loaded {len(self.privacy_patterns_dict)} filtered pattern types for client {self.client_id}")
                
                # Log pattern filtering results
                all_patterns = self._convert_patterns()
                if len(self.privacy_patterns_dict) < len(all_patterns):
                    logger.info(f"🔍 Pattern filtering active: {len(self.privacy_patterns_dict)}/{len(all_patterns)} patterns selected")
                else:
                    logger.info(f"📊 No pattern filtering: using all {len(self.privacy_patterns_dict)} patterns")
                
                # Log enhanced pattern source information
                stats = self.pattern_manager.get_pattern_statistics()
                logger.info(f"📁 Pattern source: {stats.get('primary_source', 'unknown')} (primary)")
                logger.info(f"🔒 Sensitivity distribution: {stats.get('sensitivity_distribution', {})}")
                logger.info(f"🛡️ Protection methods: {stats.get('protection_method_distribution', {})}")
                logger.info(f"🗑️ Hardcoded patterns removed: {stats.get('hardcoded_patterns_removed', False)}")
                
                if stats.get('total_database_patterns', 0) > 0:
                    logger.info(f"✅ DATABASE-PRIMARY mode active: {stats['total_database_patterns']} patterns loaded")
                else:
                    logger.warning(f"⚠️ No database patterns loaded - check database connection")
                    
            except Exception as e:
                logger.error(f"❌ Error loading patterns: {e}")
                self.privacy_patterns_dict = {}
        else:
            self.privacy_patterns_dict = {}
        
        logger.info(f"✅ Modular Scanning Agent initialized for client: {client_id or 'default'}")
    
    def set_client_id(self, client_id: str):
        """Set the client ID for all subsequent operations"""
        self.client_id = client_id
        self.db_manager.set_client_id(client_id)
    
    def get_client_selected_sdes(self, client_id: str = None) -> List[str]:
        """
        Get the list of SDE pattern names that the client has selected for scanning
        
        Args:
            client_id: Client ID to get selected SDEs for (optional, uses instance client_id if not provided)
            
        Returns:
            List of pattern names selected by the client
        """
        target_client_id = client_id or self.client_id
        if not target_client_id:
            logger.warning("No client_id provided for SDE selection")
            return []
            
        try:
            # Use the new database method to get client SDEs
            if hasattr(self, 'db_manager') and self.db_manager:
                client_sdes = self.db_manager.get_client_selected_sdes(target_client_id)
                selected_patterns = [sde.get('name', '') for sde in client_sdes if sde.get('name')]
                logger.info(f"Client {target_client_id} has {len(selected_patterns)} selected SDEs from database: {selected_patterns}")
                return selected_patterns
            
            # Fallback to old table structure if database method fails
            with psycopg2.connect(DB_URL) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT DISTINCT pattern_name 
                        FROM client_selected_sdes 
                        WHERE client_id = %s
                        ORDER BY pattern_name
                    """, (target_client_id,))
                    
                    results = cursor.fetchall()
                    selected_patterns = [row[0] for row in results]
                    
                    logger.info(f"Client {target_client_id} has {len(selected_patterns)} selected SDEs (fallback): {selected_patterns}")
                    return selected_patterns
                    
        except Exception as e:
            logger.error(f"Error fetching client selected SDEs: {e}")
            return []
    
    def _convert_patterns(self) -> Dict[str, List[str]]:
        """Convert pattern manager patterns to scanner format"""
        # If enhanced SDE loader is available, use it
        if hasattr(self, 'privacy_patterns_dict') and self.privacy_patterns_dict:
            logger.debug("🔄 Using enhanced SDE patterns instead of pattern manager")
            return self.privacy_patterns_dict
        
        # Fallback to legacy pattern manager
        if not hasattr(self, 'pattern_manager') or not self.pattern_manager:
            logger.warning("⚠️ No pattern manager or enhanced SDE patterns available")
            return {}
            
        patterns_dict = {}
        for pattern in self.pattern_manager.regex_patterns:
            if isinstance(pattern, dict) and 'data_type' in pattern and 'regex_pattern' in pattern:
                pattern_type = f"{pattern['data_type']}_patterns"
                if pattern_type not in patterns_dict:
                    patterns_dict[pattern_type] = []
                patterns_dict[pattern_type].append(pattern['regex_pattern'])
        return patterns_dict
    
    def _convert_patterns_filtered(self, client_id: str = None) -> Dict[str, List[str]]:
        """
        Convert pattern manager patterns to scanner format, filtered by client-selected SDEs
        
        Args:
            client_id: Client ID to filter patterns for (optional, uses instance client_id if not provided)
            
        Returns:
            Dictionary of patterns filtered by client SDE selections
        """
        target_client_id = client_id or self.client_id
        
        # If enhanced SDE loader is available, it already handles client filtering
        if hasattr(self, 'sde_patterns') and self.sde_patterns:
            logger.info(f"✅ Using enhanced SDE patterns for client {target_client_id} - already filtered")
            logger.info(f"🔍 Enhanced SDE patterns available: {len(self.sde_patterns)} patterns")
            logger.info(f"🔍 privacy_patterns_dict content: {self.privacy_patterns_dict}")
            logger.info(f"🔍 privacy_patterns_dict keys: {list(self.privacy_patterns_dict.keys()) if self.privacy_patterns_dict else 'None'}")
            logger.info(f"🔍 privacy_patterns_dict type: {type(self.privacy_patterns_dict)}")
            logger.info(f"🔍 privacy_patterns_dict length: {len(self.privacy_patterns_dict) if self.privacy_patterns_dict else 0}")
            
            # Debug: Let's re-convert the patterns if privacy_patterns_dict is empty
            if not self.privacy_patterns_dict:
                logger.warning(f"⚠️ privacy_patterns_dict is empty, re-converting {len(self.sde_patterns)} SDE patterns")
                self.privacy_patterns_dict = self._convert_sde_patterns_to_dict(self.sde_patterns)
                logger.info(f"🔧 Re-converted privacy_patterns_dict: {self.privacy_patterns_dict}")
            
            return self.privacy_patterns_dict
        
        # Legacy pattern manager fallback
        if not hasattr(self, 'pattern_manager') or not self.pattern_manager:
            logger.warning(f"⚠️ No pattern manager available for client {target_client_id}")
            return {}
        
        # Get client-selected SDEs
        selected_sdes = self.get_client_selected_sdes(target_client_id)
        
        # If no SDEs selected, return all patterns (backward compatibility)
        if not selected_sdes:
            logger.info(f"No SDE selections found for client {target_client_id}, using all patterns")
            return self._convert_patterns()
        
        # Filter patterns based on client selections
        patterns_dict = {}
        filtered_count = 0
        total_count = 0
        
        for pattern in self.pattern_manager.regex_patterns:
            total_count += 1
            if isinstance(pattern, dict) and 'data_type' in pattern and 'regex_pattern' in pattern:
                # Use data_type as pattern identifier since pattern_name doesn't exist in YAML
                data_type = pattern.get('data_type', '')
                
                # Check if this data_type matches any of the selected SDEs
                # We'll match by data_type or if the SDE pattern_name contains the data_type
                match_found = False
                for selected_sde in selected_sdes:
                    if (data_type == selected_sde or 
                        selected_sde in data_type or 
                        data_type in selected_sde):
                        match_found = True
                        break
                
                if match_found:
                    pattern_type = f"{pattern['data_type']}_patterns"
                    if pattern_type not in patterns_dict:
                        patterns_dict[pattern_type] = []
                    patterns_dict[pattern_type].append(pattern['regex_pattern'])
                    filtered_count += 1
                    logger.debug(f"✅ Included pattern: {data_type} (matched SDE selection)")
                else:
                    logger.debug(f"❌ Excluded pattern: {data_type} (not in client SDE selection)")
        
        logger.info(f"Filtered patterns: {filtered_count}/{total_count} patterns selected for client {target_client_id}")
        logger.info(f"Selected SDEs: {selected_sdes}")
        logger.info(f"Resulting pattern types: {list(patterns_dict.keys())}")
        return patterns_dict
    
    def _convert_sde_patterns_to_dict(self, sde_patterns: List) -> Dict[str, List[str]]:
        """
        Convert SDE patterns from Enhanced SDE Loader to privacy patterns dictionary
        
        Args:
            sde_patterns: List of SDEPattern objects
            
        Returns:
            Dictionary of regex patterns grouped by SDE name for scanning compatibility
        """
        patterns_dict = {}
        # Create a mapping of pattern types to their sensitivity levels from client_selected_sde
        self.pattern_sensitivity_mapping = {}
        
        logger.info(f"🔍 Converting {len(sde_patterns)} SDE patterns to scanner format")
        
        for i, sde_pattern in enumerate(sde_patterns):
            logger.info(f"🔍 Pattern {i+1}: sde_name={sde_pattern.sde_name}, regex={sde_pattern.regex_pattern[:100] if sde_pattern.regex_pattern else 'None'}...")
            logger.info(f"🔍 Pattern {i+1} details: source={sde_pattern.source}, data_type={sde_pattern.data_type}, sensitivity={sde_pattern.sensitivity_level}")
            
            # Normalize pattern type to match base scanner's risk mapping expectations
            pattern_type = self._normalize_pattern_type(sde_pattern.sde_name, sde_pattern.data_type)
            
            # Store the sensitivity level for this pattern type from client_selected_sde
            if hasattr(sde_pattern, 'sensitivity_level') and sde_pattern.sensitivity_level:
                # Convert sensitivity to uppercase risk level for base scanner compatibility
                risk_level = self._convert_sensitivity_to_risk_level(sde_pattern.sensitivity_level)
                self.pattern_sensitivity_mapping[pattern_type] = risk_level
                logger.info(f"🎯 Stored sensitivity mapping: {pattern_type} -> {risk_level} (from {sde_pattern.sensitivity_level})")
            
            # Initialize list if not exists
            if pattern_type not in patterns_dict:
                patterns_dict[pattern_type] = []
            
            # Add regex pattern - be more permissive with patterns
            if sde_pattern.regex_pattern and sde_pattern.regex_pattern.strip():
                regex_clean = sde_pattern.regex_pattern.strip()
                
                # Skip only truly generic patterns but be more permissive
                if regex_clean not in ['.*', '.+', '.*?', '', 'null', 'NULL']:
                    patterns_dict[pattern_type].append(regex_clean)
                    logger.info(f"✅ Added pattern for {sde_pattern.sde_name}: {regex_clean[:100]}...")
                else:
                    logger.warning(f"⚠️ Skipped generic/empty pattern for {sde_pattern.sde_name}: '{regex_clean}'")
            else:
                logger.warning(f"⚠️ No valid regex pattern for {sde_pattern.sde_name}")
        
        # Remove empty pattern types
        patterns_dict_before = len(patterns_dict)
        patterns_dict = {k: v for k, v in patterns_dict.items() if v}
        patterns_dict_after = len(patterns_dict)
        
        if patterns_dict_before != patterns_dict_after:
            logger.warning(f"🗑️ Removed {patterns_dict_before - patterns_dict_after} empty pattern types")
        
        logger.info(f"🔍 Converted {len(sde_patterns)} SDE patterns to {len(patterns_dict)} pattern types")
        logger.info(f"📋 Pattern types created: {list(patterns_dict.keys())}")
        logger.info(f"🎯 Sensitivity mappings created: {self.pattern_sensitivity_mapping}")
        
        # Debug: Show first few patterns for verification
        for i, (pattern_type, patterns) in enumerate(patterns_dict.items()):
            if i < 5:  # Show first 5 pattern types
                logger.debug(f"📝 {pattern_type}: {len(patterns)} patterns - {patterns[0][:50] if patterns else 'empty'}...")
        
        return patterns_dict
    
    def _normalize_pattern_type(self, sde_name: str, data_type: str = None) -> str:
        """
        Normalize pattern type to match base scanner's risk mapping expectations
        
        Args:
            sde_name: SDE name from database
            data_type: Data type from database
            
        Returns:
            Normalized pattern type that base scanner can recognize
        """
        sde_lower = sde_name.lower()
        
        # Map various SDE names to standard pattern types that base scanner recognizes
        if any(term in sde_lower for term in ['email', 'e-mail', 'mail']):
            return 'email_patterns'
        elif any(term in sde_lower for term in ['phone', 'telephone', 'mobile', 'cell']):
            return 'phone_patterns'
        elif any(term in sde_lower for term in ['ssn', 'social_security', 'social security']):
            return 'ssn_patterns'
        elif any(term in sde_lower for term in ['credit_card', 'credit card', 'creditcard', 'card']):
            return 'credit_card_patterns'
        elif any(term in sde_lower for term in ['passport', 'passport_number']):
            return 'passport_patterns'
        elif any(term in sde_lower for term in ['ip', 'ip_address', 'ip address']):
            return 'ip_address_patterns'
        elif any(term in sde_lower for term in ['driver', 'license', 'driving']):
            return 'driver_license_patterns'
        elif any(term in sde_lower for term in ['bank', 'account', 'routing']):
            return 'bank_account_patterns'
        elif any(term in sde_lower for term in ['name', 'first_name', 'last_name']):
            return 'name_patterns'
        elif any(term in sde_lower for term in ['address', 'street', 'postal']):
            return 'address_patterns'
        elif any(term in sde_lower for term in ['salary', 'wage', 'income', 'compensation']):
            return 'salary_patterns'
        else:
            # Fallback to using the original sde_name with _patterns suffix
            return f"{sde_name.lower()}_patterns"

    def _load_sensitivity_cache(self) -> bool:
        """
        Load all sensitivity mappings into cache to avoid repeated database queries.
        This dramatically improves performance during scanning.
        
        Returns:
            bool: True if cache loaded successfully, False otherwise
        """
        if self.cache_loaded:
            logger.debug("📋 Sensitivity cache already loaded")
            return True
            
        if not self.client_id:
            logger.warning("⚠️ No client_id available for sensitivity cache loading")
            return False
            
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            logger.info("📋 Loading sensitivity cache from database...")
            
            # Load from client_selected_sdes first (higher priority)
            client_query = """
            SELECT pattern_name, sensitivity 
            FROM client_selected_sdes 
            WHERE client_id = %s 
              AND sensitivity IS NOT NULL
            ORDER BY selected_at DESC
            """
            
            cursor.execute(client_query, (self.client_id,))
            client_results = cursor.fetchall()
            
            # Load from isde_catalogue (fallback)
            catalogue_query = """
            SELECT name, sensitivity 
            FROM isde_catalogue 
            WHERE sensitivity IS NOT NULL
            """
            
            cursor.execute(catalogue_query)
            catalogue_results = cursor.fetchall()
            
            # Build cache with client preferences taking priority
            cache_count = 0
            
            # Add catalogue sensitivities first (lower priority)
            for name, sensitivity in catalogue_results:
                if name and sensitivity:
                    # Store both the original name and common variations
                    cache_key = name.lower()
                    self.sensitivity_cache[cache_key] = sensitivity
                    
                    # Also store pattern variations
                    pattern_key = f"{cache_key}_patterns"
                    self.sensitivity_cache[pattern_key] = sensitivity
                    
                    cache_count += 1
            
            # Add client-selected sensitivities (higher priority - overwrites catalogue)
            for pattern_name, sensitivity in client_results:
                if pattern_name and sensitivity:
                    cache_key = pattern_name.lower()
                    self.sensitivity_cache[cache_key] = sensitivity
                    
                    # Also store without _patterns suffix if it exists
                    if cache_key.endswith('_patterns'):
                        base_key = cache_key.replace('_patterns', '')
                        self.sensitivity_cache[base_key] = sensitivity
                    
                    cache_count += 1
            
            cursor.close()
            conn.close()
            
            self.cache_loaded = True
            logger.info(f"✅ Sensitivity cache loaded successfully: {cache_count} entries from client_selected_sdes={len(client_results)}, isde_catalogue={len(catalogue_results)}")
            
            # Log a sample of cache contents for debugging
            if logger.isEnabledFor(logging.DEBUG):
                sample_keys = list(self.sensitivity_cache.keys())[:5]
                logger.debug(f"🔧 Cache sample: {[(k, self.sensitivity_cache[k]) for k in sample_keys]}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading sensitivity cache: {e}")
            self.cache_loaded = False
            return False
    
    def _get_sensitivity_from_database(self, sde_type: str, pattern_type: str) -> Optional[str]:
        """
        Get sensitivity level from cache (loaded once at scan start).
        Falls back to direct database lookup only if cache is not loaded.
        
        Args:
            sde_type: Original SDE type (e.g., 'ssalary', 'personal_email')
            pattern_type: Normalized pattern type (e.g., 'salary_patterns', 'email_patterns')
            
        Returns:
            Sensitivity level string or None if not found
        """
        # Ensure cache is loaded
        if not self.cache_loaded:
            if not self._load_sensitivity_cache():
                logger.warning("⚠️ Failed to load sensitivity cache, falling back to direct database lookup")
                return self._get_sensitivity_from_database_direct(sde_type, pattern_type)
        
        # Try cache lookup with multiple key variations
        possible_keys = [
            sde_type.lower(),
            pattern_type.lower(), 
            sde_type.lower().replace('_patterns', ''),
            pattern_type.lower().replace('_patterns', '')
        ]
        
        for key in possible_keys:
            if key in self.sensitivity_cache:
                sensitivity = self.sensitivity_cache[key]
                # Reduced logging - only log cache misses, not every hit
                return sensitivity
        
        # Only log when we don't find anything
        logger.debug(f"❌ No sensitivity found in cache for {sde_type}")
        return None

    def _get_sensitivity_from_database_direct(self, sde_type: str, pattern_type: str) -> Optional[str]:
        """
        Direct database lookup for sensitivity (used as fallback when cache fails).
        This method performs the original database queries.
        """
        if not self.client_id:
            logger.warning("⚠️ No client_id available for sensitivity lookup")
            return None
            
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # STEP 1: Check client_selected_sdes table first
            logger.debug(f"🔍 Direct DB lookup: Checking client_selected_sdes for pattern '{pattern_type}' or sde '{sde_type}'")
            
            # Try both the normalized pattern type and original SDE type
            client_query = """
            SELECT sensitivity 
            FROM client_selected_sdes 
            WHERE client_id = %s 
              AND (pattern_name = %s OR pattern_name = %s)
            ORDER BY selected_at DESC
            LIMIT 1
            """
            
            cursor.execute(client_query, (self.client_id, pattern_type, sde_type))
            client_result = cursor.fetchone()
            
            if client_result and client_result[0]:
                sensitivity = client_result[0]
                logger.debug(f"✅ Found sensitivity in client_selected_sdes (direct): {sde_type} → {sensitivity}")
                cursor.close()
                conn.close()
                return sensitivity
            
            logger.debug(f"❌ No sensitivity found in client_selected_sdes for {sde_type}")
            
            # STEP 2: Check isde_catalogue table
            logger.debug(f"🔍 Direct DB lookup: Checking isde_catalogue for sde '{sde_type}'")
            
            catalogue_query = """
            SELECT sensitivity 
            FROM isde_catalogue 
            WHERE name = %s
            LIMIT 1
            """
            
            cursor.execute(catalogue_query, (sde_type,))
            catalogue_result = cursor.fetchone()
            
            if catalogue_result and catalogue_result[0]:
                sensitivity = catalogue_result[0]
                logger.debug(f"✅ Found sensitivity in isde_catalogue (direct): {sde_type} → {sensitivity}")
                cursor.close()
                conn.close()
                return sensitivity
            
            logger.debug(f"❌ No sensitivity found in isde_catalogue for {sde_type}")
            
            cursor.close()
            conn.close()
            
            # STEP 3: Return None - no other fallbacks allowed
            logger.warning(f"⚠️ No sensitivity found in database sources for {sde_type} - returning None")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error fetching sensitivity from database: {e}")
            return None

    def _convert_sensitivity_to_risk_level(self, sensitivity: str) -> str:
        """
        Convert sensitivity level to risk level for base scanner compatibility
        
        Args:
            sensitivity: Sensitivity level from database (critical, high, medium, low)
            
        Returns:
            Risk level in uppercase (CRITICAL, HIGH, MEDIUM, LOW)
        """
        sensitivity_lower = sensitivity.lower().strip()
        
        if sensitivity_lower in ['critical', 'very high']:
            return 'CRITICAL'
        elif sensitivity_lower in ['high']:
            return 'HIGH'
        elif sensitivity_lower in ['medium', 'moderate']:
            return 'MEDIUM'
        elif sensitivity_lower in ['low']:
            return 'LOW'
        else:
            logger.warning(f"⚠️ Unknown sensitivity level: {sensitivity}, defaulting to MEDIUM")
            return 'MEDIUM'
    
    def refresh_sde_patterns(self) -> bool:
        """
        Refresh SDE patterns using the enhanced loader
        
        Returns:
            True if patterns were successfully refreshed
        """
        if not hasattr(self, 'sde_loader'):
            logger.warning("⚠️ Enhanced SDE Loader not available for refresh")
            return False
        
        try:
            logger.info(f"🔄 Refreshing SDE patterns for client {self.client_id}")
            
            # Clear cache and reload
            self.sde_loader.clear_cache()
            load_result = self.sde_loader.load_sdes_with_fallback()
            
            if load_result.success:
                # Update patterns
                self.privacy_patterns_dict = self._convert_sde_patterns_to_dict(load_result.sde_patterns)
                self.sde_patterns = load_result.sde_patterns
                self.sde_source_used = load_result.source_used
                
                logger.info(f"✅ Refreshed: {len(load_result.sde_patterns)} SDEs from {load_result.source_used.value}")
                if load_result.fallback_triggered:
                    logger.warning(f"⚠️ Fallback triggered during refresh - using {load_result.source_used.value}")
                
                return True
            else:
                logger.error(f"❌ Failed to refresh SDE patterns: {load_result.error_message}")
                return False
                
        except Exception as e:
            logger.error(f"❌ SDE pattern refresh failed: {e}")
            return False
    
    def force_config_fallback_mode(self, enable: bool = True):
        """
        Force the agent to use config file fallback for testing
        
        Args:
            enable: True to force config fallback, False to disable
        """
        if hasattr(self, 'sde_loader'):
            self.sde_loader.force_config_fallback(enable)
            
            if enable:
                logger.warning("🔧 Forced config fallback mode enabled - will use config file instead of database")
                # Refresh patterns to apply the change
                self.refresh_sde_patterns()
            else:
                logger.info("🔧 Config fallback mode disabled - will use normal fallback hierarchy")
                self.refresh_sde_patterns()
        else:
            logger.warning("⚠️ Enhanced SDE Loader not available for config fallback")
    
    def get_sde_source_info(self) -> Dict[str, Any]:
        """
        Get information about the current SDE source being used
        
        Returns:
            Dictionary with SDE source information
        """
        if hasattr(self, 'sde_loader') and hasattr(self, 'sde_source_used'):
            stats = self.sde_loader.get_load_statistics()
            return {
                'current_source': self.sde_source_used.value if self.sde_source_used else 'unknown',
                'patterns_loaded': len(self.sde_patterns) if hasattr(self, 'sde_patterns') else 0,
                'pattern_types': len(self.privacy_patterns_dict),
                'cache_valid': stats.get('cache_valid', False),
                'force_fallback_enabled': stats.get('force_fallback_enabled', False),
                'statistics': stats
            }
        else:
            return {
                'current_source': 'legacy_pattern_manager',
                'patterns_loaded': 0,
                'pattern_types': len(self.privacy_patterns_dict),
                'enhanced_loader_available': False
            }
    
    def validate_sde_setup(self) -> Dict[str, Any]:
        """
        Validate the SDE setup and all fallback sources
        
        Returns:
            Validation results
        """
        if hasattr(self, 'sde_loader'):
            validation = self.sde_loader.validate_sde_sources()
            validation['agent_setup'] = {
                'enhanced_loader_available': True,
                'patterns_loaded': len(self.privacy_patterns_dict),
                'current_source': self.sde_source_used.value if hasattr(self, 'sde_source_used') and self.sde_source_used else 'unknown'
            }
            return validation
        else:
            return {
                'agent_setup': {
                    'enhanced_loader_available': False,
                    'patterns_loaded': len(self.privacy_patterns_dict),
                    'current_source': 'legacy_pattern_manager'
                },
                'overall_health': 'legacy_mode',
                'validation_timestamp': datetime.now().isoformat()
            }

    def _load_field_mappings(self) -> Dict[str, Any]:
        """
        Skip field mappings entirely if only using regex scanning
        Return empty dict to disable field-name-based detection
        """
        logger.info("📋 Field mappings disabled - using regex-only detection mode")
        return {}
    
    def get_client_regex_patterns_only(self, client_id: str = None) -> Dict[str, List[str]]:
        """
        Get only regex patterns from client-selected SDEs for regex-only scanning
        
        Args:
            client_id: Client ID to get patterns for
            
        Returns:
            Dictionary of regex patterns grouped by data type
        """
        # If enhanced SDE loader is available, use it
        if hasattr(self, 'sde_patterns'):
            patterns_dict = {}
            for sde_pattern in self.sde_patterns:
                pattern_type = f"{sde_pattern.data_type}_patterns"
                if pattern_type not in patterns_dict:
                    patterns_dict[pattern_type] = []
                if sde_pattern.regex_pattern and sde_pattern.regex_pattern != '.*':
                    patterns_dict[pattern_type].append(sde_pattern.regex_pattern)
            
            logger.info(f"🔍 Enhanced loader: Built {len(patterns_dict)} regex pattern types")
            return patterns_dict
        
        # Fallback to legacy method
        target_client_id = client_id or self.client_id
        if not target_client_id:
            logger.warning("No client_id provided for regex pattern retrieval")
            return {}
        
        try:
            if hasattr(self, 'db_manager') and self.db_manager:
                client_sdes = self.db_manager.get_client_selected_sdes(target_client_id)
                logger.info(f"🔍 Building regex patterns from {len(client_sdes)} client SDEs")
                
                patterns_dict = {}
                for sde in client_sdes:
                    data_type = sde.get('data_type', 'string')
                    regex_pattern = sde.get('regex', '')
                    
                    if regex_pattern and regex_pattern != '.*':  # Skip empty or generic patterns
                        pattern_type = f"{data_type}_patterns"
                        if pattern_type not in patterns_dict:
                            patterns_dict[pattern_type] = []
                        patterns_dict[pattern_type].append(regex_pattern)
                        logger.debug(f"✅ Added regex pattern for {data_type}: {regex_pattern[:50]}...")
                
                logger.info(f"🔍 Built {len(patterns_dict)} regex pattern types for client {target_client_id}")
                return patterns_dict
            
            logger.warning("Database manager not available for regex pattern retrieval")
            return {}
            
        except Exception as e:
            logger.error(f"Error getting client regex patterns: {e}")
            return {}
    
    def _load_sde_categories(self) -> Dict[str, Any]:
        """Load SDE categories from SDE definitions file - DON'T hardcode risk levels"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config')
            sde_file = os.path.join(config_path, 'sde_definitions.yaml')
            
            if os.path.exists(sde_file):
                with open(sde_file, 'r') as f:
                    sde_data = yaml.safe_load(f)
                    # Create SDE categories based on the data structure
                    # IMPORTANT: Remove hardcoded risk_level to use client-selected sensitivity
                    sde_categories = {
                        'PII': {
                            'name': 'Personal Identifiable Information',
                            'compliance_frameworks': ['GDPR', 'CCPA', 'DPDP'],
                            'protection_requirements': ['Data minimization', 'Purpose limitation', 'Consent management']
                        },
                        'FINANCIAL': {
                            'name': 'Financial Data',
                            'compliance_frameworks': ['PCI-DSS', 'SOX', 'GDPR'],
                            'protection_requirements': ['Encryption', 'Access control', 'Audit logging']
                        },
                        'IDENTIFICATION': {
                            'name': 'Government Identification',
                            'compliance_frameworks': ['GDPR', 'CCPA', 'DPDP'],
                            'protection_requirements': ['Secure storage', 'Limited access', 'Audit trails']
                        },
                        'MEDICAL': {
                            'name': 'Healthcare Information',
                            'compliance_frameworks': ['HIPAA', 'GDPR', 'CCPA'],
                            'protection_requirements': ['Encryption', 'Access control', 'Audit logging', 'Consent management']
                        },
                        'LOCATION': {
                            'name': 'Location Data',
                            'compliance_frameworks': ['GDPR', 'CCPA'],
                            'protection_requirements': ['Purpose limitation', 'Consent management']
                        }
                    }
                    logger.info(f"✅ Loaded {len(sde_categories)} SDE categories WITHOUT hardcoded risk levels")
                    return sde_categories
            else:
                logger.warning(f"SDE definitions file not found: {sde_file}")
                return {}
        except Exception as e:
            logger.error(f"Error loading SDE categories: {e}")
            return {}
    
    def _get_category_from_sensitivity(self, sensitivity: str) -> str:
        """Map sensitivity levels to SDE categories"""
        sensitivity_lower = sensitivity.lower()
        if sensitivity_lower in ['critical', 'high']:
            return 'FINANCIAL' if 'financial' in sensitivity_lower else 'MEDICAL' if 'medical' in sensitivity_lower else 'IDENTIFICATION'
        elif sensitivity_lower == 'medium':
            return 'PII'
        else:
            return 'LOCATION'
    
    def _enhance_findings(self, findings: List[Dict[str, Any]], source_config: DataSourceConfig, source_type: str) -> List[Dict[str, Any]]:
        """
        Enhance findings from scanners to ensure all required fields are present
        
        Args:
            findings: Raw findings from scanner
            source_config: Source configuration
            source_type: Type of source being scanned
            
        Returns:
            Enhanced findings with all required fields
        """
        enhanced_findings = []
        
        for finding in findings:
            enhanced_finding = finding.copy()
            
            # DO NOT use any fallback sensitivity - only database sources allowed
            # The base scanner should have populated sensitivity from database lookup
            if 'sensitivity' not in enhanced_finding or not enhanced_finding['sensitivity']:
                # Scanner didn't find sensitivity in database sources - this is allowed
                logger.info(f"📊 No sensitivity found in database sources for {enhanced_finding.get('sde_type')} - leaving empty")
                # Do not set any fallback values - sensitivity will remain None/empty
            else:
                logger.debug(f"✅ Using database-sourced sensitivity: {enhanced_finding.get('sensitivity')} for {enhanced_finding.get('sde_type')}")
            
            # DO NOT use any fallback risk_level - only database sources allowed  
            if 'risk_level' not in enhanced_finding or not enhanced_finding['risk_level']:
                # If no risk_level from scanner, try to convert sensitivity if available
                if enhanced_finding.get('sensitivity'):
                    enhanced_finding['risk_level'] = self._convert_sensitivity_to_risk_level(enhanced_finding['sensitivity'])
                    logger.debug(f"✅ Converted sensitivity to risk_level: {enhanced_finding.get('sensitivity')} → {enhanced_finding.get('risk_level')}")
                else:
                    logger.info(f"📊 No risk_level or sensitivity found in database sources for {enhanced_finding.get('sde_type')} - leaving empty")
                    # Do not set any fallback values - risk_level will remain None/empty
            else:
                logger.debug(f"✅ Using database-sourced risk_level: {enhanced_finding.get('risk_level')} for {enhanced_finding.get('sde_type')}")
            
            # Ensure is_sde field
            if 'is_sde' not in enhanced_finding:
                enhanced_finding['is_sde'] = True
            
            # Ensure sde_category field
            if 'sde_category' not in enhanced_finding or not enhanced_finding['sde_category']:
                sde_type = enhanced_finding.get('sde_type', '').lower()
                if sde_type in ['credit_card', 'bank_account', 'routing_number']:
                    enhanced_finding['sde_category'] = 'FINANCIAL'
                elif sde_type in ['ssn', 'passport', 'driver_license']:
                    enhanced_finding['sde_category'] = 'IDENTIFICATION'
                elif sde_type in ['medical_record', 'health_insurance']:
                    enhanced_finding['sde_category'] = 'MEDICAL'
                else:
                    enhanced_finding['sde_category'] = 'PII'
            
            # Ensure location_metadata is properly structured
            if 'location_metadata' not in enhanced_finding or not enhanced_finding['location_metadata']:
                enhanced_finding['location_metadata'] = {
                    'source_name': source_config.name,
                    'source_type': source_type,
                    'location': source_config.location
                }
            elif isinstance(enhanced_finding['location_metadata'], str):
                try:
                    enhanced_finding['location_metadata'] = json.loads(enhanced_finding['location_metadata'])
                except:
                    enhanced_finding['location_metadata'] = {
                        'source_name': source_config.name,
                        'source_type': source_type,
                        'location': source_config.location,
                        'raw_metadata': enhanced_finding['location_metadata']
                    }
            
            # Add source info to location_metadata if missing
            if isinstance(enhanced_finding['location_metadata'], dict):
                enhanced_finding['location_metadata'].update({
                    'source_name': source_config.name,
                    'source_type': source_type
                })
            
            # Ensure privacy_implications
            if 'privacy_implications' not in enhanced_finding or not enhanced_finding['privacy_implications']:
                implications = []
                sensitivity = enhanced_finding.get('sensitivity', 'medium')
                sde_category = enhanced_finding.get('sde_category', 'PII')
                
                if sensitivity == 'critical':
                    implications.extend([
                        'Contains highly sensitive personal data',
                        'Requires immediate protection and encryption',
                        'Subject to strict compliance regulations'
                    ])
                elif sensitivity == 'high':
                    implications.extend([
                        'Contains personally identifiable information',
                        'Subject to privacy regulations (GDPR, CCPA)',
                        'Requires data protection measures'
                    ])
                else:
                    implications.extend([
                        'Contains personal information',
                        'Should be handled according to privacy policies'
                    ])
                
                if sde_category == 'FINANCIAL':
                    implications.append('PCI DSS compliance may be required')
                elif sde_category == 'MEDICAL':
                    implications.append('HIPAA compliance required')
                
                enhanced_finding['privacy_implications'] = implications
            
            # Ensure other required fields have defaults
            enhanced_finding.setdefault('finding_type', 'pattern_match')
            enhanced_finding.setdefault('confidence_score', 0.8)
            enhanced_finding.setdefault('detection_method', 'regex')
            enhanced_finding.setdefault('matches_found', 1)
            enhanced_finding.setdefault('sample_matches', [enhanced_finding.get('data_value', '')])
            
            # Ensure data_value is preserved and not empty
            if not enhanced_finding.get('data_value'):
                # Try to get from sample_matches if available
                sample_matches = enhanced_finding.get('sample_matches', [])
                if sample_matches and sample_matches[0]:
                    enhanced_finding['data_value'] = sample_matches[0]
                else:
                    # Generate a sample value based on SDE type
                    sde_type = enhanced_finding.get('sde_type', '').lower()
                    if sde_type == 'email':
                        enhanced_finding['data_value'] = 'user@example.com'
                    elif sde_type == 'phone':
                        enhanced_finding['data_value'] = '+1-555-0123'
                    elif sde_type == 'credit_card':
                        enhanced_finding['data_value'] = '****-****-****-1234'
                    elif sde_type == 'ssn':
                        enhanced_finding['data_value'] = '***-**-****'
                    else:
                        enhanced_finding['data_value'] = f"sample_{sde_type}_value"
            
            # Ensure object_path is set
            if not enhanced_finding.get('object_path'):
                # Generate object_path from location metadata or source info
                location_meta = enhanced_finding.get('location_metadata', {})
                if isinstance(location_meta, dict):
                    file_path = location_meta.get('file_path', '')
                    column_name = location_meta.get('column_name', enhanced_finding.get('field_name', 'unknown_field'))
                    if file_path and column_name:
                        enhanced_finding['object_path'] = f"{file_path}/{column_name}"
                    elif file_path:
                        enhanced_finding['object_path'] = f"{file_path}/{enhanced_finding.get('field_name', 'unknown_field')}"
                    else:
                        enhanced_finding['object_path'] = f"{source_config.location}/{enhanced_finding.get('field_name', 'unknown_field')}"
                else:
                    enhanced_finding['object_path'] = f"{source_config.location}/{enhanced_finding.get('field_name', 'unknown_field')}"
            
            enhanced_findings.append(enhanced_finding)
        
        return enhanced_findings
    
    def scan_data_source(self, source_name: str) -> Dict[str, Any]:
        """
        Scan a specific data source by name
        
        Args:
            source_name: Name of the data source to scan
            
        Returns:
            Scan results for the data source
        """
        logger.info(f"🔍 Starting scan for data source: {source_name}")
        
        # Load sensitivity cache for performance optimization
        if not self.cache_loaded:
            logger.info("📋 Preloading sensitivity cache for optimal scan performance...")
            cache_success = self._load_sensitivity_cache()
            if cache_success:
                logger.info("✅ Sensitivity cache loaded successfully - scan will be much faster!")
            else:
                logger.warning("⚠️ Failed to load sensitivity cache - scan will use direct DB lookups")
        
        try:
            # Get source configuration
            logger.info(f"🔧 Getting source configuration for: {source_name}")
            source_config = self.config_manager.get_data_source_config(source_name)
            
            if not source_config:
                logger.warning(f"⚠️ Source configuration not found for '{source_name}' in get_data_source_config. Trying fallback search in all sources.")
                
                # Fallback: search in all sources
                all_sources = self.config_manager.get_discovered_data_sources_for_client(self.client_id)
                logger.info(f"🔍 Searching through {len(all_sources)} available sources")
                
                for source in all_sources:
                    logger.info(f"  Checking source: name={source.name}, type={source.type}")
                    if source.name == source_name:
                        source_config = source
                        logger.info(f"✅ Found source config for '{source_name}' in fallback search: type={source.type}, location={source.location}")
                        break
                
                if not source_config:
                    error_msg = f"Source '{source_name}' not found in any available sources"
                    logger.error(f"❌ {error_msg}")
                    return {
                        'error': error_msg,
                        'source_name': source_name,
                        'status': 'not_found'
                    }
            
            logger.info(f"✅ Source config found: type={source_config.type}, location={source_config.location}")
            
            # Get or create store info in database
            logger.info(f"🔧 Getting store info from database for source: {source_name}")
            store_info = self.db_manager.get_data_store_by_name(source_name, self.client_id)
            
            if store_info:
                store_id = store_info['store_id']
                logger.info(f"✅ Found existing store_info for '{source_name}': store_id={store_id}")
            else:
                logger.info(f"🔧 Creating new store_info for '{source_name}'")
                store_id = self.db_manager.add_data_store(
                    store_name=source_name,
                    store_type=source_config.type,
                    location=source_config.location,
                    access_control=source_config.access_control or 'private',
                    client_id=self.client_id
                )
                logger.info(f"✅ Created new store_info for '{source_name}': store_id={store_id}")
            
            # Create scan entry
            logger.info(f"🔧 Creating scan entry for '{source_name}': store_id={store_id}")
            logger.info(f"🔧 Store ID type: {type(store_id)}, value: {store_id}")
            logger.info(f"🔧 Client ID: {self.client_id}")
            
            scan_metadata = {
                'status': 'started',
                'source_type': source_config.type,
                'source_location': source_config.location,
                'scan_started': datetime.now().isoformat(),
                'scanning_config': self.config_manager.get_scanning_config()
            }
            logger.info(f"🔧 Scan metadata: {scan_metadata}")
            
            # Debug: Check if store_id is valid
            if store_id is None:
                logger.error(f"❌ CRITICAL: store_id is None for source '{source_name}'")
                logger.error(f"❌ This will cause scan creation to fail")
                return {
                    'error': f"Failed to create store for source '{source_name}'",
                    'source_name': source_name,
                    'status': 'failed'
                }
            
            scan_id = self.db_manager.create_scan(store_id, scan_metadata)
            logger.info(f"🔧 create_scan returned: {scan_id} (type: {type(scan_id)})")
            
            if scan_id is None:
                logger.error(f"❌ CRITICAL: create_scan returned None for store_id={store_id}")
                logger.error(f"❌ This means scan creation failed in database")
                return {
                    'error': f"Failed to create scan in database for source '{source_name}'",
                    'source_name': source_name,
                    'status': 'failed'
                }
            
            logger.info(f"✅ Created scan entry for '{source_name}': scan_id={scan_id}")
            
            # Perform the actual scan
            logger.info(f"🔍 Performing scan for '{source_name}' with scan_id={scan_id}")
            scan_results = self._perform_scan(source_config, scan_id)
            logger.info(f"✅ Scan completed for '{source_name}'. Found {len(scan_results.get('findings', []))} findings")
            
            # Store findings in database
            if scan_results.get('findings'):
                self.db_manager.add_scan_findings(scan_id, scan_results['findings'])
                logger.info(f"✅ Added {len(scan_results['findings'])} findings to DB for scan_id={scan_id}")
            else:
                logger.info(f"📝 No findings to add to DB for scan_id={scan_id}")
            
            # Update scan status
            scan_metadata['scan_completed'] = datetime.now().isoformat()
            scan_metadata['total_findings'] = len(scan_results.get('findings', []))
            self.db_manager.update_scan_status(scan_id, 'completed')
            logger.info(f"✅ Updated scan status to 'completed' for scan_id={scan_id}")
            
            # Add AI-enhanced analysis if findings were found
            if scan_results.get('findings') and self.ai_scanning_available:
                logger.info("🤖 Performing AI-enhanced findings analysis...")
                scan_results['ai_analysis'] = self._ai_enhanced_findings_analysis(scan_results['findings'])
            elif scan_results.get('findings'):
                logger.info("📊 Performing basic findings analysis...")
                scan_results['ai_analysis'] = self._mock_ai_findings_analysis(scan_results['findings'])
            
            # Add database info to results
            scan_results['scan_id'] = scan_id
            scan_results['store_id'] = store_id
            scan_results['database_stored'] = True
            
            return scan_results
            
        except Exception as e:
            logger.error(f"❌ Error scanning data source '{source_name}': {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return {
                'error': str(e),
                'source_name': source_name,
                'status': 'failed'
            }
    
    def scan_data_source_with_config(self, source_config: DataSourceConfig) -> Dict[str, Any]:
        """
        Scan a specific data source using provided configuration
        
        Args:
            source_config: DataSourceConfig object with all necessary information
            
        Returns:
            Scan results for the data source
        """
        logger.info(f"🔍 Starting scan for data source with config: {source_config.name}")
        logger.info(f"✅ Using provided source config: type={source_config.type}, location={source_config.location}")
        
        # Load sensitivity cache for performance optimization
        if not self.cache_loaded:
            logger.info("📋 Preloading sensitivity cache for optimal scan performance...")
            cache_success = self._load_sensitivity_cache()
            if cache_success:
                logger.info("✅ Sensitivity cache loaded successfully - scan will be much faster!")
            else:
                logger.warning("⚠️ Failed to load sensitivity cache - scan will use direct DB lookups")
        
        try:
            # Get or create store info in database
            logger.info(f"🔧 Getting store info from database for source: {source_config.name}")
            store_info = self.db_manager.get_data_store_by_name(source_config.name, self.client_id)
            
            if store_info:
                store_id = store_info['store_id']
                logger.info(f"✅ Found existing store_info for '{source_config.name}': store_id={store_id}")
            else:
                logger.info(f"🔧 Creating new store_info for '{source_config.name}'")
                store_id = self.db_manager.add_data_store(
                    store_name=source_config.name,
                    store_type=source_config.type,
                    location=source_config.location,
                    access_control=source_config.access_control or 'private',
                    client_id=self.client_id
                )
                logger.info(f"✅ Created new store_info for '{source_config.name}': store_id={store_id}")
            
            # Create scan entry
            logger.info(f"🔧 Creating scan entry for '{source_config.name}': store_id={store_id}")
            logger.info(f"🔧 Store ID type: {type(store_id)}, value: {store_id}")
            logger.info(f"🔧 Client ID: {self.client_id}")
            
            scan_metadata = {
                'status': 'started',
                'source_type': source_config.type,
                'source_location': source_config.location,
                'scan_started': datetime.now().isoformat(),
                'scanning_config': self.config_manager.get_scanning_config()
            }
            logger.info(f"🔧 Scan metadata: {scan_metadata}")
            
            # Debug: Check if store_id is valid
            if store_id is None:
                logger.error(f"❌ CRITICAL: store_id is None for source '{source_config.name}'")
                logger.error(f"❌ This will cause scan creation to fail")
                return {
                    'error': f"Failed to create store for source '{source_config.name}'",
                    'source_name': source_config.name,
                    'status': 'failed'
                }
            
            scan_id = self.db_manager.create_scan(store_id, scan_metadata)
            logger.info(f"🔧 create_scan returned: {scan_id} (type: {type(scan_id)})")
            
            if scan_id is None:
                logger.error(f"❌ CRITICAL: create_scan returned None for store_id={store_id}")
                logger.error(f"❌ This means scan creation failed in database")
                return {
                    'error': f"Failed to create scan in database for source '{source_config.name}'",
                    'source_name': source_config.name,
                    'status': 'failed'
                }
            
            logger.info(f"✅ Created scan entry for '{source_config.name}': scan_id={scan_id}")
            
            # Perform the actual scan
            logger.info(f"🔍 Performing scan for '{source_config.name}' with scan_id={scan_id}")
            scan_results = self._perform_scan(source_config, scan_id)
            logger.info(f"✅ Scan completed for '{source_config.name}'. Found {len(scan_results.get('findings', []))} findings")
            
            # Store findings in database
            if scan_results.get('findings'):
                self.db_manager.add_scan_findings(scan_id, scan_results['findings'])
                logger.info(f"✅ Added {len(scan_results['findings'])} findings to DB for scan_id={scan_id}")
            else:
                logger.info(f"📝 No findings to add to DB for scan_id={scan_id}")
            
            # Update scan status
            scan_metadata['scan_completed'] = datetime.now().isoformat()
            scan_metadata['total_findings'] = len(scan_results.get('findings', []))
            self.db_manager.update_scan_status(scan_id, 'completed')
            logger.info(f"✅ Updated scan status to 'completed' for scan_id={scan_id}")
            
            # Add AI-enhanced analysis if findings were found
            if scan_results.get('findings') and self.ai_scanning_available:
                logger.info("🤖 Performing AI-enhanced findings analysis...")
                scan_results['ai_analysis'] = self._ai_enhanced_findings_analysis(scan_results['findings'])
            elif scan_results.get('findings'):
                logger.info("📊 Performing basic findings analysis...")
                scan_results['ai_analysis'] = self._mock_ai_findings_analysis(scan_results['findings'])
            
            # Add database info to results
            scan_results['scan_id'] = scan_id
            scan_results['store_id'] = store_id
            scan_results['database_stored'] = True
            
            return scan_results
            
        except Exception as e:
            logger.error(f"❌ Error scanning data source '{source_config.name}': {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return {
                'error': str(e),
                'source_name': source_config.name,
                'status': 'failed'
            }

    def scan_selected_objects(self, scan_session_id: str = None) -> Dict[str, Any]:
        """
        Scan only the objects selected by the user in the selected_objects table
        
        Args:
            scan_session_id: Optional scan session ID (if None, uses latest session)
            
        Returns:
            Scan results for selected objects only
        """
        logger.info(f"🎯 Starting selective scan for client {self.client_id}")
        
        try:
            # Check if client has selected objects
            has_selections = self.db_manager.has_selected_objects(self.client_id, scan_session_id)
            
            if not has_selections:
                logger.info(f"📋 No selected objects found for client {self.client_id}, falling back to full scan")
                return self.scan_all_discovered_objects()
            
            # Get selected objects for scanning
            selected_objects = self.db_manager.get_selected_objects_for_scanning(self.client_id, scan_session_id)
            logger.info(f"🎯 Found {len(selected_objects)} selected objects for scanning")
            
            if not selected_objects:
                logger.warning(f"⚠️ Selected objects table has entries but no objects retrieved, falling back to full scan")
                return self.scan_all_discovered_objects()
            
            # Group selected objects by store_id and data source type
            objects_by_store = {}
            for obj in selected_objects:
                store_id = obj['store_id']
                if store_id not in objects_by_store:
                    # Get store info to determine data source type
                    store_info = self.db_manager.get_data_store_by_id(store_id, self.client_id)
                    if store_info:
                        objects_by_store[store_id] = {
                            'store_info': store_info,
                            'objects': []
                        }
                
                if store_id in objects_by_store:
                    objects_by_store[store_id]['objects'].append(obj)
            
            logger.info(f"🗂️ Selected objects grouped into {len(objects_by_store)} data stores")
            
            # Scan each store's selected objects
            all_findings = []
            scan_results = {
                'findings': [],
                'total_findings': 0,
                'scan_timestamp': datetime.now().isoformat(),
                'source_type': 'selective_scan',
                'scanned_stores': [],
                'selected_objects_count': len(selected_objects),
                'status': 'completed'
            }
            
            for store_id, store_data in objects_by_store.items():
                store_info = store_data['store_info']
                objects = store_data['objects']
                
                logger.info(f"🔍 Scanning store {store_id} ({store_info['store_name']}) with {len(objects)} selected objects")
                
                try:
                    # Create source config from store info
                    source_config = DataSourceConfig(
                        name=store_info['store_name'],
                        type=store_info.get('type', store_info.get('store_type', 'unknown')),
                        location=store_info['location'],
                        access_control=store_info.get('access_control', 'private')
                    )
                    
                    # Create scan entry for this selective scan
                    scan_metadata = {
                        'status': 'started',
                        'source_type': source_config.type,
                        'source_location': source_config.location,
                        'scan_type': 'selective',
                        'selected_objects_count': len(objects),
                        'scan_session_id': scan_session_id or 'latest',
                        'scan_started': datetime.now().isoformat()
                    }
                    
                    scan_id = self.db_manager.create_scan(store_id, scan_metadata)
                    logger.info(f"✅ Created selective scan entry: scan_id={scan_id}")
                    
                    # For now, use existing scanning methods (can be enhanced later for true selective scanning)
                    store_results = self._perform_scan(source_config, scan_id)
                    
                    # Store findings in database
                    if store_results.get('findings'):
                        self.db_manager.add_scan_findings(scan_id, store_results['findings'])
                        logger.info(f"✅ Added {len(store_results['findings'])} findings to DB for scan_id={scan_id}")
                    
                    # Update scan status
                    self.db_manager.update_scan_status(scan_id, 'completed')
                    
                    # Accumulate results
                    all_findings.extend(store_results.get('findings', []))
                    scan_results['scanned_stores'].append({
                        'store_id': store_id,
                        'store_name': store_info['store_name'],
                        'store_type': source_config.type,
                        'selected_objects_count': len(objects),
                        'findings_count': len(store_results.get('findings', [])),
                        'scan_id': scan_id,
                        'status': store_results.get('status', 'completed')
                    })
                    
                except Exception as e:
                    logger.error(f"❌ Error scanning store {store_id}: {e}")
                    scan_results['scanned_stores'].append({
                        'store_id': store_id,
                        'store_name': store_info.get('store_name', 'Unknown'),
                        'selected_objects_count': len(objects),
                        'findings_count': 0,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            # Final results
            scan_results['findings'] = all_findings
            scan_results['total_findings'] = len(all_findings)
            
            logger.info(f"🎯 Selective scan completed: {len(all_findings)} total findings across {len(objects_by_store)} stores")
            return scan_results
            
        except Exception as e:
            logger.error(f"❌ Error in selective scanning: {e}")
            return {
                'error': str(e),
                'status': 'failed',
                'scan_type': 'selective'
            }

    def scan_all_discovered_objects(self) -> Dict[str, Any]:
        """
        Fallback method to scan all discovered objects when no selections are made
        
        Returns:
            Scan results for all discovered objects
        """
        logger.info(f"🔍 Starting full scan of all discovered objects for client {self.client_id}")
        
        try:
            # Get all discovered objects for the client
            all_objects = self.db_manager.get_discovered_objects(client_id=self.client_id, limit=1000)
            logger.info(f"📋 Found {len(all_objects)} total discovered objects")
            
            if not all_objects:
                logger.warning("⚠️ No discovered objects found for full scan")
                return {
                    'findings': [],
                    'total_findings': 0,
                    'scan_timestamp': datetime.now().isoformat(),
                    'status': 'completed',
                    'message': 'No discovered objects to scan'
                }
            
            # Group by store_id for efficient scanning
            objects_by_store = {}
            for obj in all_objects:
                store_id = obj['store_id']
                if store_id not in objects_by_store:
                    objects_by_store[store_id] = []
                objects_by_store[store_id].append(obj)
            
            # Scan each store using existing methods
            all_findings = []
            scan_results = {
                'findings': [],
                'total_findings': 0,
                'scan_timestamp': datetime.now().isoformat(),
                'source_type': 'full_scan',
                'scanned_stores': [],
                'total_objects_count': len(all_objects),
                'status': 'completed'
            }
            
            for store_id, objects in objects_by_store.items():
                try:
                    # Get store info
                    store_info = self.db_manager.get_data_store_by_id(store_id, self.client_id)
                    if not store_info:
                        logger.warning(f"⚠️ Store info not found for store_id {store_id}")
                        continue
                    
                    logger.info(f"🔍 Scanning store {store_id} ({store_info['store_name']}) with {len(objects)} objects")
                    
                    # Use existing scan_data_source method
                    store_results = self.scan_data_source(store_info['store_name'])
                    
                    if store_results.get('findings'):
                        all_findings.extend(store_results['findings'])
                    
                    scan_results['scanned_stores'].append({
                        'store_id': store_id,
                        'store_name': store_info['store_name'],
                        'objects_count': len(objects),
                        'findings_count': len(store_results.get('findings', [])),
                        'status': store_results.get('status', 'completed')
                    })
                    
                except Exception as e:
                    logger.error(f"❌ Error scanning store {store_id}: {e}")
                    scan_results['scanned_stores'].append({
                        'store_id': store_id,
                        'objects_count': len(objects),
                        'findings_count': 0,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            scan_results['findings'] = all_findings
            scan_results['total_findings'] = len(all_findings)
            
            logger.info(f"🔍 Full scan completed: {len(all_findings)} total findings across {len(objects_by_store)} stores")
            return scan_results
            
        except Exception as e:
            logger.error(f"❌ Error in full scanning: {e}")
            return {
                'error': str(e),
                'status': 'failed',
                'scan_type': 'full'
            }

    def _perform_scan(self, source_config: DataSourceConfig, scan_id: int) -> Dict[str, Any]:
        """
        Perform the actual scanning based on source type
        
        Args:
            source_config: Configuration for the data source
            scan_id: ID of the scan in database
            
        Returns:
            Scan results
        """
        logger.info(f"🔧 _perform_scan called with type: '{source_config.type}'")
        
        # Handle both hyphen and underscore variants
        if source_config.type in ['gcp-bucket', 'gcp_bucket', 'gcs']:
            logger.info(f"🔧 Using GCS scanner for type: {source_config.type}")
            return self._scan_gcs_source(source_config)
        elif source_config.type == 'bigquery':
            return self._scan_bigquery_source(source_config)
        elif source_config.type == 'postgresql':
            return self._scan_postgresql_source(source_config)
        elif source_config.type == 'mysql':
            return self._scan_mysql_source(source_config)
        elif source_config.type in ['csv', 'json', 'yaml']:
            return self._scan_file_source(source_config)
        else:
            raise ValueError(f"Unsupported source type: {source_config.type}")
    
    def _scan_gcs_source(self, source_config: DataSourceConfig) -> Dict[str, Any]:
        """Scan GCS bucket source"""
        if not SCANNERS_AVAILABLE:
            logger.error("🔧 SCANNERS_AVAILABLE is False, cannot scan GCS source")
            return {
                'findings': [],
                'total_findings': 0,
                'scan_timestamp': datetime.now().isoformat(),
                'source_type': 'gcp-bucket',
                'source_name': source_config.name,
                'status': 'failed',
                'error': 'Scanning engines not available'
            }
        
        logger.info(f"🔍 Starting GCS scan for source: {source_config.name}")
        logger.info(f"🔧 Source config: type={source_config.type}, location={source_config.location}, project_id={source_config.project_id}")
        
        try:
            # Fetch credentials dict for this client and type
            logger.info(f"🔑 Fetching credentials for client_id={self.client_id}, type=gcp-bucket")
            credentials_dict = self.config_manager.get_credential_dict_for_client(self.client_id, "gcp-bucket")
            
            if credentials_dict:
                logger.info(f"✅ Credentials found: type={credentials_dict.get('type', 'unknown')}, project_id={credentials_dict.get('project_id', 'unknown')}")
            else:
                logger.warning("⚠️ No credentials found, will use default credentials")
            
            from google.cloud import storage
            from google.oauth2 import service_account
            
            if credentials_dict:
                logger.info("🔧 Creating service account credentials from dict")
                credentials = service_account.Credentials.from_service_account_info(credentials_dict)
                logger.info(f"✅ Service account credentials created: {credentials.service_account_email}")
                client = storage.Client(project=source_config.project_id, credentials=credentials)
                logger.info(f"✅ GCS client created with project: {source_config.project_id}")
            else:
                logger.info("🔧 Creating GCS client with default credentials")
                client = storage.Client(project=source_config.project_id)
                logger.info(f"✅ GCS client created with default credentials for project: {source_config.project_id}")
            
            # Load field mappings and SDE categories
            field_mappings = self._load_field_mappings()
            sde_categories = self._load_sde_categories()
            
            # Get filtered patterns based on client SDE selections
            filtered_patterns = self._convert_patterns_filtered(self.client_id)
            logger.info(f"🔍 Filtered patterns result: {filtered_patterns}")
            logger.info(f"🔍 Pattern types available: {list(filtered_patterns.keys()) if filtered_patterns else 'None'}")
            
            # Initialize GCS scanner
            logger.info("🔧 Initializing GCS scanner with filtered patterns")
            gcs_scanner = GCSScanner(
                privacy_patterns=filtered_patterns,
                field_mappings=field_mappings,
                sde_categories=sde_categories,
                pattern_sensitivity_mapping=getattr(self, 'pattern_sensitivity_mapping', {}),
                scanning_agent=self
            )
            logger.info(f"✅ GCS scanner initialized with {len(filtered_patterns)} filtered pattern types for client {self.client_id}")
            logger.info(f"🎯 Sensitivity mappings passed to scanner: {getattr(self, 'pattern_sensitivity_mapping', {})}")
            
            # In the new schema: source_config.name = bucket name, source_config.location = project_id
            bucket_name = source_config.name  # Use store_name (actual bucket name)
            logger.info(f"🔍 GCS Scanning: Using source_config.name '{source_config.name}' as bucket name (NEW SCHEMA)")
            logger.info(f"🔍 GCS Scanning: Project ID from location: '{source_config.location}'")
            logger.info(f"🔍 GCS Scanning: Final bucket name: '{bucket_name}'")
            
            # Test bucket access
            logger.info(f"🔧 Testing access to bucket: {bucket_name}")
            try:
                bucket = client.bucket(bucket_name)
                bucket.reload()  # This will fail if we don't have access
                logger.info(f"✅ Successfully accessed bucket: {bucket_name}")
                logger.info(f"📊 Bucket info: location={bucket.location}, created={bucket.time_created}")
            except Exception as e:
                logger.error(f"❌ Failed to access bucket {bucket_name}: {e}")
                raise
            
            # Configure scan parameters
            scan_config = {
                'bucket_name': bucket_name,
                'project_id': source_config.project_id,
                'client_id': self.client_id,  # Add client_id for credential lookup fallback
                'credentials': credentials if credentials_dict else None,
                **self.config_manager.get_scanning_config()
            }
            logger.info(f"🔧 Scan config prepared: bucket_name={scan_config['bucket_name']}, project_id={scan_config['project_id']}")
            logger.info(f"🔧 Credentials in scan_config: {'present' if scan_config.get('credentials') else 'not present'}")
            
            # Perform scan
            logger.info("🔍 Starting GCS scanner scan operation")
            findings = gcs_scanner.scan(scan_config)
            logger.info(f"✅ GCS scanner completed. Found {len(findings)} findings")
            
            # Log some sample findings for debugging
            if findings:
                logger.info("📋 Sample findings:")
                for i, finding in enumerate(findings[:3]):  # Show first 3 findings
                    logger.info(f"  Finding {i+1}: {finding.get('data_type', 'unknown')} - {finding.get('field_name', 'unknown')}")
            
            # Enhance findings with missing metadata
            logger.info("🔧 Enhancing findings with metadata")
            enhanced_findings = self._enhance_findings(findings, source_config, 'gcp-bucket')
            logger.info(f"✅ Enhanced {len(enhanced_findings)} findings")
            
            return {
                'findings': enhanced_findings,
                'total_findings': len(enhanced_findings),
                'scan_timestamp': datetime.now().isoformat(),
                'source_type': 'gcs',
                'source_name': source_config.name,
                'status': 'completed'
            }
        except Exception as e:
            logger.error(f"❌ Error scanning GCS source: {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            raise
    
    def _scan_bigquery_source(self, source_config: DataSourceConfig) -> Dict[str, Any]:
        """Scan BigQuery dataset source"""
        if not SCANNERS_AVAILABLE:
            logger.error("🔧 SCANNERS_AVAILABLE is False, cannot scan BigQuery source")
            return {
                'findings': [],
                'total_findings': 0,
                'scan_timestamp': datetime.now().isoformat(),
                'source_type': 'bigquery',
                'source_name': source_config.name,
                'status': 'failed',
                'error': 'Scanning engines not available'
            }
        
        logger.info(f"🔍 Starting BigQuery scan for source: {source_config.name}")
        logger.info(f"🔧 Source config: type={source_config.type}, location={source_config.location}, project_id={source_config.project_id}")
        
        try:
            # Fetch credentials dict for this client and type
            logger.info(f"🔑 Fetching credentials for client_id={self.client_id}, type=bigquery")
            credentials_dict = self.config_manager.get_credential_dict_for_client(self.client_id, "bigquery")
            
            if credentials_dict:
                logger.info(f"✅ Credentials found: type={credentials_dict.get('type', 'unknown')}, project_id={credentials_dict.get('project_id', 'unknown')}")
            else:
                logger.warning("⚠️ No credentials found, will use default credentials")
            
            # Initialize BigQuery scanner
            # Load field mappings and SDE categories
            field_mappings = self._load_field_mappings()
            sde_categories = self._load_sde_categories()
            
            # Get filtered patterns based on client SDE selections
            filtered_patterns = self._convert_patterns_filtered(self.client_id)
            
            logger.info("🔧 Initializing BigQuery scanner with filtered patterns")
            bigquery_scanner = BigQueryScanner(
                privacy_patterns=filtered_patterns,
                field_mappings=field_mappings,
                sde_categories=sde_categories,
                pattern_sensitivity_mapping=getattr(self, 'pattern_sensitivity_mapping', {}),
                scanning_agent=self
            )
            logger.info(f"✅ BigQuery scanner initialized with {len(filtered_patterns)} filtered pattern types for client {self.client_id}")
            
            # In the new schema: source_config.name = dataset_id, source_config.location = project_id
            dataset_name = source_config.name  # Use store_name (actual dataset_id)
            logger.info(f"🔍 BigQuery Scanning: Using source_config.name '{source_config.name}' as dataset_id (NEW SCHEMA)")
            logger.info(f"🔍 BigQuery Scanning: Project ID from location: '{source_config.location}'")
            logger.info(f"🔍 BigQuery Scanning: Final dataset name: '{dataset_name}'")
            
            # Configure scan parameters
            scan_config = {
                'project_id': source_config.location,  # Use location (project_id) instead of source_config.project_id
                'dataset_id': dataset_name,
                'client_id': self.client_id,
                'credentials': credentials_dict,
                **self.config_manager.get_scanning_config()
            }
            logger.info(f"🔧 Scan config prepared: project_id={scan_config['project_id']}, dataset_id={scan_config['dataset_id']}")
            logger.info(f"🔧 Credentials in scan_config: {'present' if scan_config.get('credentials') else 'not present'}")
            
            # Perform scan
            logger.info("🔍 Starting BigQuery scanner scan operation")
            findings = bigquery_scanner.scan(scan_config)
            logger.info(f"✅ BigQuery scanner completed. Found {len(findings)} findings")
            
            # Log some sample findings for debugging
            if findings:
                logger.info("📋 Sample findings:")
                for i, finding in enumerate(findings[:3]):  # Show first 3 findings
                    logger.info(f"  Finding {i+1}: {finding.get('data_type', 'unknown')} - {finding.get('field_name', 'unknown')}")
            
            # Enhance findings with missing metadata
            logger.info("🔧 Enhancing findings with metadata")
            enhanced_findings = self._enhance_findings(findings, source_config, 'bigquery')
            logger.info(f"✅ Enhanced {len(enhanced_findings)} findings")
            
            return {
                'findings': enhanced_findings,
                'total_findings': len(enhanced_findings),
                'scan_timestamp': datetime.now().isoformat(),
                'source_type': 'bigquery',
                'source_name': source_config.name,
                'status': 'completed'
            }
        except Exception as e:
            logger.error(f"❌ Error scanning BigQuery source: {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            raise
    
    def _scan_postgresql_source(self, source_config: DataSourceConfig) -> Dict[str, Any]:
        """Scan PostgreSQL database source"""
        if not SCANNERS_AVAILABLE:
            logger.error("🔧 SCANNERS_AVAILABLE is False, cannot scan PostgreSQL source")
            return {
                'findings': [],
                'total_findings': 0,
                'scan_timestamp': datetime.now().isoformat(),
                'source_type': 'postgresql',
                'source_name': source_config.name,
                'status': 'failed',
                'error': 'Scanning engines not available'
            }
        
        logger.info(f"🔍 Starting PostgreSQL scan for source: {source_config.name}")
        logger.info(f"🔧 Source config: type={source_config.type}, location={source_config.location}")
        
        try:
            # Fetch credentials dict for this client and type
            logger.info(f"🔑 Fetching credentials for client_id={self.client_id}, type=postgresql")
            credentials_dict = self.config_manager.get_credential_dict_for_client(self.client_id, "postgresql")
            
            if credentials_dict:
                logger.info(f"✅ Credentials found: type={credentials_dict.get('type', 'unknown')}")
                # Extract connection details from credentials
                host = credentials_dict.get('host', source_config.host)
                port = credentials_dict.get('port', source_config.port or 5432)
                database = credentials_dict.get('database', source_config.database_name)
                username = credentials_dict.get('user', source_config.username)
                password = credentials_dict.get('password', source_config.password)
            else:
                logger.warning("⚠️ No credentials found, using source_config defaults")
                host = source_config.host
                port = source_config.port or 5432
                # In new schema: source_config.name = database name, source_config.location = host  
                database = source_config.database_name or source_config.name  # Use store_name if database_name not set
                username = source_config.username
                password = source_config.password
            
            logger.info(f"🔍 PostgreSQL Scanning: Using database name '{database}' (NEW SCHEMA)")
            logger.info(f"🔍 PostgreSQL Scanning: Host from location/config: '{host}'")
            logger.info(f"🔍 PostgreSQL Scanning: Store name: '{source_config.name}'")
            
            # Load field mappings and SDE categories
            field_mappings = self._load_field_mappings()
            sde_categories = self._load_sde_categories()
            
            # Get filtered patterns based on client SDE selections
            filtered_patterns = self._convert_patterns_filtered(self.client_id)
            
            # Initialize database scanner
            logger.info("🔧 Initializing PostgreSQL scanner with filtered patterns")
            db_scanner = DatabaseScanner(
                privacy_patterns=filtered_patterns,
                field_mappings=field_mappings,
                sde_categories=sde_categories,
                pattern_sensitivity_mapping=getattr(self, 'pattern_sensitivity_mapping', {}),
                scanning_agent=self
            )
            logger.info(f"✅ PostgreSQL scanner initialized with {len(filtered_patterns)} filtered pattern types for client {self.client_id}")
            logger.info(f"🎯 Sensitivity mappings passed to database scanner: {getattr(self, 'pattern_sensitivity_mapping', {})}")
            
            # Configure scan parameters
            scan_config = {
                'type': 'postgresql',
                'host': host,
                'port': port,
                'database': database,
                'user': username,
                'password': password,
                'client_id': self.client_id,
                **self.config_manager.get_scanning_config()
            }
            logger.info(f"🔧 Scan config prepared: host={scan_config['host']}, database={scan_config['database']}")
            
            # Perform scan
            logger.info("🔍 Starting PostgreSQL scanner scan operation")
            findings = db_scanner.scan(scan_config)
            logger.info(f"✅ PostgreSQL scanner completed. Found {len(findings)} findings")
            
            # Log some sample findings for debugging
            if findings:
                logger.info("📋 Sample findings:")
                for i, finding in enumerate(findings[:3]):  # Show first 3 findings
                    logger.info(f"  Finding {i+1}: {finding.get('data_type', 'unknown')} - {finding.get('field_name', 'unknown')}")
            
            # Enhance findings with missing metadata
            logger.info("🔧 Enhancing findings with metadata")
            enhanced_findings = self._enhance_findings(findings, source_config, 'postgresql')
            logger.info(f"✅ Enhanced {len(enhanced_findings)} findings")
            
            return {
                'findings': enhanced_findings,
                'total_findings': len(enhanced_findings),
                'scan_timestamp': datetime.now().isoformat(),
                'source_type': 'postgresql',
                'source_name': source_config.name,
                'status': 'completed'
            }
        except Exception as e:
            logger.error(f"❌ Error scanning PostgreSQL source: {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            raise
    
    def _scan_mysql_source(self, source_config: DataSourceConfig) -> Dict[str, Any]:
        """Scan MySQL database source"""
        if not SCANNERS_AVAILABLE:
            logger.error("🔧 SCANNERS_AVAILABLE is False, cannot scan MySQL source")
            return {
                'findings': [],
                'total_findings': 0,
                'scan_timestamp': datetime.now().isoformat(),
                'source_type': 'mysql',
                'source_name': source_config.name,
                'status': 'failed',
                'error': 'Scanning engines not available'
            }
        
        logger.info(f"🔍 Starting MySQL scan for source: {source_config.name}")
        logger.info(f"🔧 Source config: type={source_config.type}, location={source_config.location}")
        
        try:
            # Fetch credentials dict for this client and type
            logger.info(f"🔑 Fetching credentials for client_id={self.client_id}, type=mysql")
            credentials_dict = self.config_manager.get_credential_dict_for_client(self.client_id, "mysql")
            
            if credentials_dict:
                logger.info(f"✅ Credentials found: type={credentials_dict.get('type', 'unknown')}")
                # Extract connection details from credentials
                host = credentials_dict.get('host', source_config.host)
                port = credentials_dict.get('port', source_config.port or 3306)
                database = credentials_dict.get('database', source_config.database_name)
                username = credentials_dict.get('user', source_config.username)
                password = credentials_dict.get('password', source_config.password)
            else:
                logger.warning("⚠️ No credentials found, using source_config defaults")
                host = source_config.host
                port = source_config.port or 3306
                database = source_config.database_name
                username = source_config.username
                password = source_config.password
            
            # Load field mappings and SDE categories
            field_mappings = self._load_field_mappings()
            sde_categories = self._load_sde_categories()
            
            # Get filtered patterns based on client SDE selections
            filtered_patterns = self._convert_patterns_filtered(self.client_id)
            
            # Initialize database scanner
            logger.info("🔧 Initializing MySQL scanner with filtered patterns")
            db_scanner = DatabaseScanner(
                privacy_patterns=filtered_patterns,
                field_mappings=field_mappings,
                sde_categories=sde_categories,
                pattern_sensitivity_mapping=getattr(self, 'pattern_sensitivity_mapping', {}),
                scanning_agent=self
            )
            logger.info(f"✅ MySQL scanner initialized with {len(filtered_patterns)} filtered pattern types for client {self.client_id}")
            logger.info(f"🎯 Sensitivity mappings passed to MySQL scanner: {getattr(self, 'pattern_sensitivity_mapping', {})}")
            
            # Configure scan parameters
            scan_config = {
                'type': 'mysql',
                'host': host,
                'port': port,
                'database': database,
                'user': username,
                'password': password,
                'client_id': self.client_id,
                **self.config_manager.get_scanning_config()
            }
            logger.info(f"🔧 Scan config prepared: host={scan_config['host']}, database={scan_config['database']}")
            
            # Perform scan
            logger.info("🔍 Starting MySQL scanner scan operation")
            findings = db_scanner.scan(scan_config)
            logger.info(f"✅ MySQL scanner completed. Found {len(findings)} findings")
            
            # Log some sample findings for debugging
            if findings:
                logger.info("📋 Sample findings:")
                for i, finding in enumerate(findings[:3]):  # Show first 3 findings
                    logger.info(f"  Finding {i+1}: {finding.get('data_type', 'unknown')} - {finding.get('field_name', 'unknown')}")
            
            # Enhance findings with missing metadata
            logger.info("🔧 Enhancing findings with metadata")
            enhanced_findings = self._enhance_findings(findings, source_config, 'mysql')
            logger.info(f"✅ Enhanced {len(enhanced_findings)} findings")
            
            return {
                'findings': enhanced_findings,
                'total_findings': len(enhanced_findings),
                'scan_timestamp': datetime.now().isoformat(),
                'source_type': 'mysql',
                'source_name': source_config.name,
                'status': 'completed'
            }
        except Exception as e:
            logger.error(f"❌ Error scanning MySQL source: {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            raise
    
    def _scan_file_source(self, source_config: DataSourceConfig) -> Dict[str, Any]:
        """Scan file-based source"""
        if not SCANNERS_AVAILABLE:
            logger.error("🔧 SCANNERS_AVAILABLE is False, cannot scan file source")
            return {
                'findings': [],
                'total_findings': 0,
                'scan_timestamp': datetime.now().isoformat(),
                'source_type': 'file',
                'source_name': source_config.name,
                'status': 'failed',
                'error': 'Scanning engines not available'
            }
        
        try:
            # Load field mappings and SDE categories
            field_mappings = self._load_field_mappings()
            sde_categories = self._load_sde_categories()
            
            # Get filtered patterns based on client SDE selections
            filtered_patterns = self._convert_patterns_filtered(self.client_id)
            
            # Initialize file scanner
            file_scanner = FileScanner(
                privacy_patterns=filtered_patterns,
                field_mappings=field_mappings,
                sde_categories=sde_categories,
                pattern_sensitivity_mapping=getattr(self, 'pattern_sensitivity_mapping', {}),
                scanning_agent=self
            )
            
            # Configure scan parameters
            scan_config = {
                'type': source_config.type,
                'file_path': source_config.location,
                **self.config_manager.get_scanning_config()
            }
            
            # Perform scan
            findings = file_scanner.scan(scan_config)
            
            # Enhance findings with missing metadata
            enhanced_findings = self._enhance_findings(findings, source_config, source_config.type)
            
            return {
                'findings': enhanced_findings,
                'total_findings': len(enhanced_findings),
                'scan_timestamp': datetime.now().isoformat(),
                'source_type': source_config.type,
                'source_name': source_config.name,
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Error scanning file source: {e}")
            raise
    
    def scan_latest_database(self, client_id: str = None) -> Dict[str, Any]:
        """
        Scan only the latest (most recently discovered) database for a client
        
        Args:
            client_id: Client ID (uses instance client_id if not provided)
            
        Returns:
            Scan results for the latest database
        """
        effective_client_id = client_id or self.client_id
        if not effective_client_id:
            raise ValueError("client_id is required for scanning operations")
            
        logger.info(f"🔍 Starting scan of latest database for client: {effective_client_id}")
        
        # Get the latest data source (most recently discovered)
        latest_source = self._get_latest_data_source(effective_client_id)
        
        if not latest_source:
            return {
                'status': 'no_sources',
                'message': 'No data sources found for client',
                'total_findings': 0,
                'scan_timestamp': datetime.now().isoformat(),
                'client_id': effective_client_id
            }
        
        logger.info(f"📋 Found latest database: {latest_source.name} ({latest_source.type})")
        
        # Scan the latest source using specific configuration
        scan_result = self.scan_data_source_with_config(latest_source)
        
        return {
            'status': 'completed',
            'scan_type': 'latest_database',
            'source_scanned': {
                'store_name': latest_source.name,  # Use store_name
                'type': latest_source.type,
                'location': latest_source.location
            },
            'total_findings': scan_result.get('total_findings', 0),
            'scan_timestamp': datetime.now().isoformat(),
            'client_id': effective_client_id,
            'scan_details': scan_result
        }
    
    def scan_all_databases(self, client_id: str = None) -> Dict[str, Any]:
        """
        Scan all databases for a client
        
        Args:
            client_id: Client ID (uses instance client_id if not provided)
            
        Returns:
            Scan results for all databases
        """
        effective_client_id = client_id or self.client_id
        if not effective_client_id:
            raise ValueError("client_id is required for scanning operations")
            
        logger.info(f"🔍 Starting scan of all databases for client: {effective_client_id}")
        
        # Get all data sources for this client
        data_sources = self.config_manager.get_discovered_data_sources_for_client(effective_client_id)
        logger.info(f"📋 Found {len(data_sources)} databases for client {effective_client_id}")
        
        if not data_sources:
            return {
                'status': 'no_sources',
                'message': 'No data sources found for client',
                'total_findings': 0,
                'sources_scanned': 0,
                'scan_timestamp': datetime.now().isoformat(),
                'client_id': effective_client_id
            }
        
        all_findings = []
        sources_scanned = 0
        scan_errors = []
        scan_details = []
        
        for source_config in data_sources:
            try:
                logger.info(f"🔍 Scanning database: {source_config.name} ({source_config.type})")
                
                # Scan this source
                result = self.scan_data_source(source_config.name)
                
                if result.get('status') == 'completed':
                    sources_scanned += 1
                    findings = result.get('findings', [])
                    all_findings.extend(findings)
                    
                    scan_details.append({
                        'store_name': source_config.name,  # Use store_name
                        'source_type': source_config.type,
                        'location': source_config.location,
                        'findings_count': len(findings),
                        'status': 'completed'
                    })
                    
                    logger.info(f"✅ Completed scan of {source_config.name}: {len(findings)} findings")
                else:
                    scan_errors.append(f"Failed to scan {source_config.name}: {result.get('error', 'Unknown error')}")
                    scan_details.append({
                        'store_name': source_config.name,  # Use store_name
                        'source_type': source_config.type,
                        'location': source_config.location,
                        'findings_count': 0,
                        'status': 'failed',
                        'error': result.get('error', 'Unknown error')
                    })
                    
            except Exception as e:
                scan_errors.append(f"Error scanning {source_config.name}: {str(e)}")
                scan_details.append({
                    'store_name': source_config.name,  # Use store_name
                    'source_type': source_config.type,
                    'location': source_config.location,
                    'findings_count': 0,
                    'status': 'error',
                    'error': str(e)
                })
                logger.error(f"❌ Error scanning {source_config.name}: {e}")
        
        total_findings = len(all_findings)
        logger.info(f"✅ Scan completed. Total findings: {total_findings}, Sources scanned: {sources_scanned}")
        
        return {
            'status': 'completed' if not scan_errors else 'completed_with_errors',
            'scan_type': 'all_databases',
            'message': f'Scanned {sources_scanned} databases, found {total_findings} findings',
            'total_findings': total_findings,
            'sources_scanned': sources_scanned,
            'total_sources': len(data_sources),
            'scan_timestamp': datetime.now().isoformat(),
            'client_id': effective_client_id,
            'errors': scan_errors,
            'scan_details': scan_details
        }
    
    def _get_latest_data_source(self, client_id: str) -> Optional[DataSourceConfig]:
        """
        Get the latest (most recently discovered) data source for a client
        
        Args:
            client_id: Client ID
            
        Returns:
            Latest DataSourceConfig or None if not found
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Get the most recent data source based on discovery_timestamp
            cursor.execute("""
                SELECT store_id, store_name, store_type, discovery_timestamp, location
                FROM data_stores 
                WHERE client_id = %s
                ORDER BY discovery_timestamp DESC NULLS LAST, store_id DESC
                LIMIT 1
            """, (client_id,))
            
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if row:
                store_id, store_name, store_type, discovery_timestamp, location = row
                
                return DataSourceConfig(
                    name=store_name,
                    type=store_type,
                    location=location,  # Use location directly from data_stores
                    credentials_path=None  # Will be resolved when needed
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest data source for client {client_id}: {e}")
            return None
        """
        Scan all configured data sources for the current client
        
        Returns:
            Dictionary with scan results
        """
        logger.info(f"🔍 Starting scan of all configured data sources for client: {self.client_id}")
        
        # Get all data sources for this client
        data_sources = self.config_manager.get_discovered_data_sources_for_client(self.client_id)
        logger.info(f"📋 Found {len(data_sources)} data sources for client {self.client_id}")
        
        if not data_sources:
            logger.warning(f"⚠️ No data sources found for client {self.client_id}")
            return {
                'status': 'no_sources',
                'message': f'No data sources found for client {self.client_id}',
                'total_findings': 0,
                'sources_scanned': 0,
                'scan_timestamp': datetime.now().isoformat()
            }
        
        # Log data sources for debugging
        for i, source in enumerate(data_sources):
            logger.info(f"  Source {i+1}: name={source.name}, type={source.type}, location={source.location}")
        
        all_findings = []
        sources_scanned = 0
        scan_errors = []
        
        for source_config in data_sources:
            logger.info(f"🔍 Scanning source: {source_config.name} (type: {source_config.type})")
            try:
                scan_result = self.scan_data_source(source_config.name)
                if scan_result.get('findings'):
                    all_findings.extend(scan_result['findings'])
                    logger.info(f"✅ Source {source_config.name} completed with {len(scan_result['findings'])} findings")
                else:
                    logger.info(f"✅ Source {source_config.name} completed with 0 findings")
                sources_scanned += 1
            except Exception as e:
                error_msg = f"Failed to scan source {source_config.name}: {e}"
                logger.error(f"❌ {error_msg}")
                scan_errors.append(error_msg)
        
        total_findings = len(all_findings)
        logger.info(f"✅ Scan completed. Total findings: {total_findings}, Sources scanned: {sources_scanned}")
        
        if scan_errors:
            logger.warning(f"⚠️ {len(scan_errors)} scan errors occurred")
            for error in scan_errors:
                logger.warning(f"  Error: {error}")
        
        return {
            'status': 'completed' if not scan_errors else 'completed_with_errors',
            'message': f'Scanned {sources_scanned} sources, found {total_findings} findings',
            'total_findings': total_findings,
            'sources_scanned': sources_scanned,
            'scan_timestamp': datetime.now().isoformat(),
            'errors': scan_errors
        }
    
    def get_scan_results_from_db(self, scan_id: int) -> Dict[str, Any]:
        """
        Retrieve scan results from database
        
        Args:
            scan_id: ID of the scan
            
        Returns:
            Scan results from database
        """
        findings = self.db_manager.get_scan_findings(scan_id)
        summary = self.db_manager.get_scan_summary(scan_id)
        
        return {
            'scan_id': scan_id,
            'findings': findings,
            'summary': summary,
            'total_findings': len(findings)
        }
    
    def _ai_enhanced_findings_analysis(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use OpenAI for enhanced findings analysis"""
        if not self.ai_scanning_available:
            return self._mock_ai_findings_analysis(findings)
        
        try:
            # Prepare findings summary for AI analysis
            findings_summary = []
            for finding in findings[:8]:  # Limit to first 8 for token efficiency
                findings_summary.append({
                    'type': finding.get('sde_type', 'unknown'),
                    'content_preview': finding.get('content', '')[:50],  # First 50 chars
                    'confidence': finding.get('confidence_score', 0.0),
                    'location': finding.get('file_path', ''),
                    'size': finding.get('content_size', 0)
                })
            
            prompt = f"""
            Analyze these sensitive data findings from a privacy scan:
            
            Findings Summary: {json.dumps(findings_summary, indent=2)}
            Total Findings: {len(findings)}
            
            Please provide:
            1. Data sensitivity risk assessment (Critical/High/Medium/Low)
            2. Pattern analysis and anomaly detection
            3. Immediate remediation recommendations  
            4. Data classification suggestions
            5. Compliance impact assessment
            
            Format as JSON with actionable security recommendations.
            """
            
            messages = [
                {"role": "system", "content": "You are a cybersecurity expert specializing in data privacy, sensitive data detection, and compliance remediation."},
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
            logger.error(f"AI enhanced findings analysis failed: {e}")
            return {
                "analysis_type": "error",
                "error": str(e),
                "pattern_analysis": {
                    "total_findings": len(findings),
                    "high_confidence": 0,
                    "medium_confidence": 0,
                    "sde_type_distribution": {}
                },
                "immediate_actions": ["Review scan results manually"],
                "data_classification": "Unknown"
            }

    def scan_specific_database(self, client_id: str = None, store_name: str = None, 
                             tables: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Scan a specific database and optionally specific tables within it
        
        Args:
            client_id: Client ID (uses instance client_id if not provided)
            store_name: Name of the specific resource to scan (bucket name, dataset name, database name)
            tables: Optional list of specific tables to scan. If None, scans all tables in the database
            
        Returns:
            Scan results for the specific database and tables
        """
        effective_client_id = client_id or self.client_id
        if not effective_client_id:
            raise ValueError("client_id is required for scanning operations")
            
        if not store_name:
            raise ValueError("store_name must be provided")
            
        logger.info(f"🔍 Starting specific database scan for client: {effective_client_id}")
        logger.info(f"📋 Target store_name: {store_name}")
        if tables:
            logger.info(f"📊 Target tables: {tables}")
        else:
            logger.info(f"📊 Scanning all tables in database")
        
        # Find the matching data source by store_name (which is the actual resource name)
        target_source = None
        data_sources = self.config_manager.get_discovered_data_sources_for_client(effective_client_id)
        
        for source in data_sources:
            # Match by store_name (which contains the actual resource name)
            if source.name == store_name:
                target_source = source
                logger.info(f"✅ Found matching database: {source.name} ({source.type}) at {source.location}")
                break
        
        if not target_source:
            # If not found in discovered sources, check if it exists in data_stores table
            logger.info(f"🔍 Database not found in discovered sources, checking data_stores...")
            try:
                # Look up in data_stores table using store_name
                target_source = self._create_source_config_from_data_stores(effective_client_id, store_name)
                if target_source:
                    logger.info(f"✅ Found database in data_stores: {target_source.name} at {target_source.location}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to find database in data_stores: {e}")
        
        if not target_source:
            available_sources = [s.name for s in data_sources]  # Use store_name (source.name)
            return {
                'status': 'not_found',
                'message': f'Database not found. Available store_names: {available_sources}',
                'total_findings': 0,
                'scan_timestamp': datetime.now().isoformat(),
                'client_id': effective_client_id,
                'target_store_name': store_name,
                'available_store_names': available_sources
            }
        
        # Perform the scan with table filtering if specified
        try:
            if tables:
                # For table-specific scanning, we need to modify the scanning behavior
                logger.info(f"🔍 Scanning specific tables: {tables}")
                scan_result = self._scan_specific_tables(target_source, tables)
            else:
                # Scan the entire database
                logger.info(f"🔍 Scanning entire database: {target_source.name}")
                scan_result = self.scan_data_source_with_config(target_source)
            
            return {
                'status': 'completed',
                'scan_type': 'specific_database',
                'database_scanned': {
                    'store_name': target_source.name,  # Use store_name
                    'type': target_source.type,
                    'location': target_source.location
                },
                'tables_scanned': tables if tables else 'all',
                'total_findings': scan_result.get('total_findings', 0),
                'scan_timestamp': datetime.now().isoformat(),
                'client_id': effective_client_id,
                'scan_details': scan_result
            }
            
        except Exception as e:
            logger.error(f"❌ Error scanning specific database {target_source.name}: {e}")
            return {
                'status': 'error',
                'scan_type': 'specific_database',
                'database_scanned': {
                    'store_name': target_source.name,  # Use store_name
                    'type': target_source.type,
                    'location': target_source.location
                },
                'tables_scanned': tables if tables else 'all',
                'total_findings': 0,
                'scan_timestamp': datetime.now().isoformat(),
                'client_id': effective_client_id,
                'error': str(e)
            }

    def _create_source_config_from_data_stores(self, client_id: str, store_name: str) -> Optional[DataSourceConfig]:
        """
        Create a DataSourceConfig for a database that exists in data_stores table
        
        Args:
            client_id: Client ID
            store_name: Store name (actual resource name) to search for
            
        Returns:
            DataSourceConfig if found, None otherwise
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Get the data store using store_name
            cursor.execute("""
                SELECT store_name, store_type, location
                FROM data_stores 
                WHERE client_id = %s AND store_name = %s
                LIMIT 1
            """, (client_id, store_name))
            
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if row:
                store_name_db, store_type, location = row
                
                # Create DataSourceConfig with the new schema
                ds_kwargs = {
                    'name': store_name_db,  # store_name is the actual resource name
                    'type': store_type,
                    'location': location,   # location contains project_id/host info
                    'access_control': 'private'  # Default value
                }
                
                # Add additional fields based on type
                if store_type in ['gcs', 'gcp-bucket', 'gcs_bucket']:
                    ds_kwargs['project_id'] = location  # location contains project_id
                elif store_type == 'bigquery':
                    ds_kwargs['project_id'] = location  # location contains project_id
                    ds_kwargs['database_name'] = store_name_db  # store_name is dataset_id
                elif store_type == 'postgresql':
                    ds_kwargs['host'] = location  # location contains host
                    ds_kwargs['port'] = int(os.getenv("DB_PORT", "5432"))
                    ds_kwargs['database_name'] = store_name_db  # store_name is database name
                    ds_kwargs['username'] = os.getenv("DB_USER")
                    ds_kwargs['password'] = os.getenv("DB_PASSWORD")
                
                return DataSourceConfig(**ds_kwargs)
                
        except Exception as e:
            logger.error(f"❌ Error creating source config from data_stores: {e}")
            
        return None

    def _scan_specific_tables(self, source_config: DataSourceConfig, tables: List[str]) -> Dict[str, Any]:
        """
        Scan specific tables within a database
        
        Args:
            source_config: DataSourceConfig for the database
            tables: List of table names to scan
            
        Returns:
            Scan results for the specific tables
        """
        logger.info(f"🔍 Starting table-specific scan for {len(tables)} tables in {source_config.name}")
        
        all_findings = []
        table_results = []
        scan_errors = []
        
        for table_name in tables:
            try:
                logger.info(f"📊 Scanning table: {table_name}")
                
                # For now, we'll use the regular scan but note which table we're targeting
                # This could be enhanced to actually filter by table in the future
                result = self.scan_data_source_with_config(source_config)
                
                if result.get('status') == 'completed':
                    findings = result.get('findings', [])
                    
                    # Filter findings by table name if possible
                    table_findings = []
                    for finding in findings:
                        # Check if finding is related to this table
                        if self._is_finding_from_table(finding, table_name):
                            table_findings.append(finding)
                    
                    all_findings.extend(table_findings)
                    table_results.append({
                        'table_name': table_name,
                        'findings_count': len(table_findings),
                        'status': 'completed'
                    })
                    
                    logger.info(f"✅ Table {table_name}: {len(table_findings)} findings")
                else:
                    table_results.append({
                        'table_name': table_name,
                        'findings_count': 0,
                        'status': 'failed',
                        'error': result.get('error', 'Unknown error')
                    })
                    scan_errors.append(f"Failed to scan table {table_name}")
                    
            except Exception as e:
                table_results.append({
                    'table_name': table_name,
                    'findings_count': 0,
                    'status': 'error',
                    'error': str(e)
                })
                scan_errors.append(f"Error scanning table {table_name}: {str(e)}")
                logger.error(f"❌ Error scanning table {table_name}: {e}")
        
        return {
            'status': 'completed' if not scan_errors else 'completed_with_errors',
            'total_findings': len(all_findings),
            'findings': all_findings,
            'table_results': table_results,
            'errors': scan_errors,
            'tables_scanned': len(tables)
        }

    def _is_finding_from_table(self, finding: Dict[str, Any], table_name: str) -> bool:
        """
        Check if a finding is from a specific table
        
        Args:
            finding: Finding dictionary
            table_name: Table name to check against
            
        Returns:
            True if finding is from the specified table
        """
        # This is a basic implementation - can be enhanced based on your finding structure
        finding_location = finding.get('location', '')
        finding_file_path = finding.get('file_path', '')
        finding_source = finding.get('source', '')
        
        # Check various fields for table name
        return (table_name.lower() in finding_location.lower() or 
                table_name.lower() in finding_file_path.lower() or
                table_name.lower() in finding_source.lower())
