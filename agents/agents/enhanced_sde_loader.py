"""
Enhanced SDE Loader with Fallback Hierarchy
Implements robust SDE loading with database and file fallbacks
"""

import os
import sys
import yaml
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from config_manager import AgentConfigManager
from postgresql_db_manager import PostgreSQLCloudScanDBManager

logger = logging.getLogger(__name__)

class SDESource(Enum):
    """Enumeration of SDE data sources"""
    CLIENT_SELECTED = "client_selected_sde"
    GLOBAL_CATALOGUE = "isde_catalogue"
    LOCAL_CONFIG = "sde_config.yaml"
    FALLBACK_HARDCODED = "hardcoded_fallback"

@dataclass
class SDEPattern:
    """Represents an SDE pattern with regex"""
    sde_name: str
    data_type: str
    regex_pattern: str
    sensitivity_level: str
    confidence_weight: float
    source: SDESource
    client_id: Optional[str] = None
    description: Optional[str] = None

@dataclass
class LoadResult:
    """Result of SDE loading operation"""
    success: bool
    source_used: SDESource
    sde_patterns: List[SDEPattern]
    error_message: Optional[str] = None
    fallback_triggered: bool = False
    load_timestamp: str = None

class EnhancedSDELoader:
    """
    Enhanced SDE Loader with robust fallback hierarchy:
    1. Client-selected SDEs (client_selected_sde table)
    2. Global SDEs (isde_catalogue table)  
    3. Local config file (sde_config.yaml)
    4. Hardcoded fallback (minimal patterns)
    """
    
    def __init__(self, db_manager: PostgreSQLCloudScanDBManager, client_id: str, 
                 config_manager: AgentConfigManager = None):
        """
        Initialize Enhanced SDE Loader
        
        Args:
            db_manager: Database manager instance
            client_id: Client ID for multi-tenant operations
            config_manager: Configuration manager (optional)
        """
        self.db_manager = db_manager
        self.client_id = client_id
        self.config_manager = config_manager or AgentConfigManager()
        
        # Configuration
        self.force_fallback_to_config = False  # Manual override flag
        self.enable_hardcoded_fallback = True
        self.cache_loaded_sdes = True
        self.cache_ttl_seconds = 300  # 5 minutes
        
        # Cache
        self._cached_sdes: Optional[List[SDEPattern]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._last_source_used: Optional[SDESource] = None
        
        # Paths
        self.config_path = os.path.join(os.path.dirname(__file__), '..', 'config')
        self.sde_config_file = os.path.join(self.config_path, 'sde_config.yaml')
        
        logger.info(f"✅ Enhanced SDE Loader initialized for client {client_id}")
    
    def load_sdes_with_fallback(self) -> LoadResult:
        """
        🔄 Load SDEs using the prioritized fallback mechanism:
        
        1. PRIMARY SOURCE: client_selected_sde table (using pattern_name column)
        2. FALLBACK 1: isde_catalogue table (using name column) 
        3. FALLBACK 2: sde_definitions.yaml config file
        4. FINAL FALLBACK: hardcoded patterns (if enabled)
        
        🔍 For each SDE source, regex patterns are loaded from the regex table
        
        Returns:
            LoadResult with SDE patterns and source information
        """
        logger.info(f"🔄 Loading SDEs for client {self.client_id} using prioritized fallback hierarchy")
        
        # Check cache first
        if self.cache_loaded_sdes and self._is_cache_valid():
            logger.info(f"📋 Using cached SDEs from {self._last_source_used.value}")
            return LoadResult(
                success=True,
                source_used=self._last_source_used,
                sde_patterns=self._cached_sdes,
                load_timestamp=self._cache_timestamp.isoformat()
            )
        
        # Manual override to config file
        if self.force_fallback_to_config:
            logger.warning("🔧 Manual override: Forcing fallback to config file")
            return self._load_from_config_file(is_fallback=False)
        
        # 🔄 PRIMARY SOURCE: Client-selected SDEs from client_selected_sde table
        logger.info("🔄 PRIMARY SOURCE: Attempting to load from client_selected_sde table")
        result = self._load_client_selected_sdes()
        if result.success and result.sde_patterns:
            logger.info(f"✅ PRIMARY SOURCE SUCCESS: Loaded {len(result.sde_patterns)} SDEs from client_selected_sde")
            self._update_cache(result)
            return result
        
        logger.warning("⚠️ PRIMARY SOURCE: No client-selected SDEs found, triggering FALLBACK 1")
        
        # 🔄 FALLBACK 1: Global SDEs from isde_catalogue table
        logger.info("🔄 FALLBACK 1: Attempting to load from isde_catalogue table")
        result = self._load_global_sdes()
        if result.success and result.sde_patterns:
            logger.info(f"✅ FALLBACK 1 SUCCESS: Loaded {len(result.sde_patterns)} SDEs from isde_catalogue")
            result.fallback_triggered = True
            self._update_cache(result)
            return result
        
        logger.warning("⚠️ Global SDEs not available, triggering Fallback 2")
        
        # Fallback 2: Local config file
        result = self._load_from_config_file(is_fallback=True)
        if result.success and result.sde_patterns:
            logger.info(f"✅ Fallback 2: Loaded {len(result.sde_patterns)} SDEs from config file")
            result.fallback_triggered = True
            self._update_cache(result)
            return result
        
        logger.warning("⚠️ FALLBACK 1: No global SDEs found, triggering FALLBACK 2")
        
        # 🔄 FALLBACK 2: Local config file (sde_definitions.yaml)
        logger.info("🔄 FALLBACK 2: Attempting to load from sde_definitions.yaml config file")
        result = self._load_from_config_file(is_fallback=True)
        if result.success and result.sde_patterns:
            logger.info(f"✅ FALLBACK 2 SUCCESS: Loaded {len(result.sde_patterns)} SDEs from config file")
            result.fallback_triggered = True
            self._update_cache(result)
            return result
        
        logger.error("❌ FALLBACK 2: Config file loading failed, triggering FINAL FALLBACK")
        
        # 🔄 FINAL FALLBACK: Hardcoded minimal patterns (if enabled)
        if self.enable_hardcoded_fallback:
            logger.info("🔄 FINAL FALLBACK: Using hardcoded patterns")
            result = self._load_hardcoded_fallback()
            logger.warning(f"⚠️ FINAL FALLBACK: Using {len(result.sde_patterns)} hardcoded patterns")
            result.fallback_triggered = True
            self._update_cache(result)
            return result
        
        # Complete failure - all sources exhausted
        logger.error("❌ ALL FALLBACKS FAILED: No SDE sources available")
        return LoadResult(
            success=False,
            source_used=SDESource.CLIENT_SELECTED,
            sde_patterns=[],
            error_message="All SDE loading sources failed: client_selected_sde, isde_catalogue, config file, and hardcoded fallback",
            fallback_triggered=True,
            load_timestamp=datetime.now().isoformat()
        )
    
    def _load_client_selected_sdes(self) -> LoadResult:
        """
        🔄 PRIMARY SOURCE: Load SDEs from client_selected_sde table for the specific client
        Uses column 'pattern_name' to identify SDEs selected by the client, then loads regex from regex table
        
        Returns:
            LoadResult with client-specific SDEs and their regex patterns
        """
        logger.info(f"🔍 Loading client-selected SDEs for client '{self.client_id}'")
        
        if not self.client_id:
            return LoadResult(
                success=False,
                source_used=SDESource.CLIENT_SELECTED,
                sde_patterns=[],
                error_message="No client_id provided for client-selected SDEs"
            )
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Step 1: Get SDEs from client_selected_sde table using pattern_name column
            client_sde_query = """
            SELECT DISTINCT pattern_name, sensitivity, protection_method, selected_at
            FROM client_selected_sdes 
            WHERE client_id = %s
            ORDER BY selected_at DESC
            """
            
            logger.debug(f"🔍 Step 1: Getting client SDEs from client_selected_sde table")
            cursor.execute(client_sde_query, (self.client_id,))
            client_sdes = cursor.fetchall()
            
            logger.info(f"📊 Found {len(client_sdes)} client-selected SDEs for client '{self.client_id}'")
            
            if not client_sdes:
                cursor.close()
                conn.close()
                logger.warning(f"📊 No client-selected SDEs found for client '{self.client_id}' - triggering fallback")
                return LoadResult(
                    success=True,
                    source_used=SDESource.CLIENT_SELECTED,
                    sde_patterns=[],
                    error_message=f"No client-selected SDEs found for client '{self.client_id}'"
                )
            
            # Step 2: For each selected SDE, load corresponding regex patterns from regex table
            sde_patterns = []
            for row in client_sdes:
                pattern_name, sensitivity, protection_method, selected_at = row
                
                logger.debug(f"🔍 Step 2: Loading regex patterns for SDE '{pattern_name}'")
                
                # Load regex patterns for this SDE from regex table
                regex_query = """
                SELECT pattern_name, regex_pattern
                FROM regexes 
                WHERE pattern_name = %s
                ORDER BY pattern_name
                """
                
                try:
                    cursor.execute(regex_query, (pattern_name,))
                    regex_results = cursor.fetchall()
                except Exception as regex_error:
                    logger.warning(f"⚠️ Regex table not available ({regex_error}), using backup method")
                    regex_results = []
                
                if regex_results:
                    for regex_row in regex_results:
                        pattern_name_db, regex_pattern = regex_row
                        
                        if regex_pattern and regex_pattern.strip():
                            sde_pattern = SDEPattern(
                                sde_name=pattern_name,
                                data_type='string',  # Default data type
                                regex_pattern=regex_pattern.strip(),
                                sensitivity_level=sensitivity,  # Use actual database value, no fallback
                                confidence_weight=self._map_sensitivity_to_confidence(sensitivity) if sensitivity else 0.5,
                                source=SDESource.CLIENT_SELECTED,
                                client_id=self.client_id,
                                description=f"Client-selected SDE pattern for {pattern_name}"
                            )
                            sde_patterns.append(sde_pattern)
                            logger.info(f"✅ Added client SDE: {pattern_name} with regex pattern")
                            break  # Use first regex pattern
                else:
                    # If no regex found, try isde_catalogue as backup for this specific SDE
                    logger.debug(f"🔍 No regex found for {pattern_name} in regex table, checking isde_catalogue")
                    backup_query = """
                    SELECT data_type, regex
                    FROM isde_catalogue 
                    WHERE name = %s
                    """
                    cursor.execute(backup_query, (pattern_name,))
                    backup_result = cursor.fetchone()
                    
                    if backup_result and backup_result[1]:
                        data_type, regex_pattern = backup_result
                        logger.info(f"🔍 Found backup regex for {pattern_name}: {regex_pattern[:100] if regex_pattern else 'None'}...")
                        
                        if regex_pattern and regex_pattern.strip():
                            sde_pattern = SDEPattern(
                                sde_name=pattern_name,
                                data_type=data_type or 'string',
                                regex_pattern=regex_pattern.strip(),
                                sensitivity_level=sensitivity,  # Use actual database value, no fallback
                                confidence_weight=self._map_sensitivity_to_confidence(sensitivity) if sensitivity else 0.5,
                                source=SDESource.CLIENT_SELECTED,
                                client_id=self.client_id,
                                description=f"Client-selected SDE with backup regex from catalogue"
                            )
                            sde_patterns.append(sde_pattern)
                            logger.info(f"✅ Added client SDE: {pattern_name} with backup regex from catalogue")
                        else:
                            logger.warning(f"⚠️ Backup regex for {pattern_name} is empty or invalid")
                    else:
                        logger.warning(f"⚠️ No regex pattern found for client SDE: {pattern_name}")
                        # Add a basic pattern as fallback to ensure the SDE is included
                        basic_patterns = {
                            'id': r'\b[A-Za-z0-9]{6,20}\b',
                            'mobile': r'\b[0-9]{10}\b',
                            'phone': r'\b[0-9]{10}\b',
                            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
                        }
                        
                        if pattern_name.lower() in basic_patterns:
                            sde_pattern = SDEPattern(
                                sde_name=pattern_name,
                                data_type='string',
                                regex_pattern=basic_patterns[pattern_name.lower()],
                                sensitivity_level=sensitivity,  # Use actual database value, no fallback
                                confidence_weight=self._map_sensitivity_to_confidence(sensitivity) if sensitivity else 0.5,
                                source=SDESource.CLIENT_SELECTED,
                                client_id=self.client_id,
                                description=f"Client-selected SDE with hardcoded fallback pattern"
                            )
                            sde_patterns.append(sde_pattern)
                            logger.info(f"✅ Added client SDE: {pattern_name} with hardcoded fallback pattern")
                        else:
                            logger.warning(f"⚠️ No fallback pattern available for {pattern_name}")
            
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Loaded {len(sde_patterns)} client-selected SDE patterns for client '{self.client_id}'")
            
            return LoadResult(
                success=True,
                source_used=SDESource.CLIENT_SELECTED,
                sde_patterns=sde_patterns,
                load_timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to load client-selected SDEs: {e}")
            return LoadResult(
                success=False,
                source_used=SDESource.CLIENT_SELECTED,
                sde_patterns=[],
                error_message=f"Database error: {str(e)}"
            )
    
    def _load_global_sdes(self) -> LoadResult:
        """
        🔄 FALLBACK 1: Load all SDEs from isde_catalogue table (global patterns)
        Uses column 'name' to identify available SDEs, then loads regex from regex table
        
        Returns:
            LoadResult with global SDEs and their regex patterns
        """
        logger.info("🌍 Fallback 1: Loading global SDEs from isde_catalogue table")
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Step 1: Get all available SDEs from isde_catalogue using 'name' column
            global_sde_query = """
            SELECT DISTINCT name, data_type, sensitivity, classification_level, 
                   industry_classification, sde_key, regex
            FROM isde_catalogue
            ORDER BY name ASC
            """
            
            logger.debug("🔍 Step 1: Getting all SDEs from isde_catalogue table")
            cursor.execute(global_sde_query)
            global_sdes = cursor.fetchall()
            
            logger.info(f"📊 Found {len(global_sdes)} global SDEs in isde_catalogue")
            
            if not global_sdes:
                cursor.close()
                conn.close()
                logger.warning("📊 No global SDEs found in isde_catalogue - triggering next fallback")
                return LoadResult(
                    success=True,
                    source_used=SDESource.GLOBAL_CATALOGUE,
                    sde_patterns=[],
                    error_message="No global SDEs found in isde_catalogue"
                )
            
            # Step 2: For each global SDE, load corresponding regex patterns from regex table
            sde_patterns = []
            for row in global_sdes:
                sde_name, data_type, sensitivity, classification_level, industry_classification, sde_key, direct_regex = row
                
                logger.debug(f"🔍 Step 2: Loading regex patterns for global SDE '{sde_name}'")
                
                # First try to load regex patterns from regex table
                regex_query = """
                SELECT pattern_name, regex_pattern
                FROM regexes 
                WHERE pattern_name = %s
                ORDER BY pattern_name
                """
                
                try:
                    cursor.execute(regex_query, (sde_name,))
                    regex_results = cursor.fetchall()
                except Exception as regex_error:
                    logger.warning(f"⚠️ Regex table not available ({regex_error}), using direct regex from catalogue")
                    regex_results = []
                
                regex_found = False
                if regex_results:
                    for regex_row in regex_results:
                        pattern_name_db, regex_pattern = regex_row
                        
                        if regex_pattern and regex_pattern.strip():
                            sde_pattern = SDEPattern(
                                sde_name=sde_name,
                                data_type=data_type or 'string',
                                regex_pattern=regex_pattern.strip(),
                                sensitivity_level=sensitivity,  # Use actual database value, no fallback
                                confidence_weight=self._map_sensitivity_to_confidence(sensitivity) if sensitivity else 0.5,
                                source=SDESource.GLOBAL_CATALOGUE,
                                description=f"Global SDE pattern for {sde_name}"
                            )
                            sde_patterns.append(sde_pattern)
                            logger.debug(f"✅ Added global SDE: {sde_name} with regex from regex table")
                            regex_found = True
                            break  # Use first regex pattern
                
                # If no regex found in regex table, use direct regex from isde_catalogue
                if not regex_found and direct_regex and direct_regex.strip():
                    sde_pattern = SDEPattern(
                        sde_name=sde_name,
                        data_type=data_type or 'string',
                        regex_pattern=direct_regex.strip(),
                        sensitivity_level=sensitivity,  # Use actual database value, no fallback
                        confidence_weight=self._map_sensitivity_to_confidence(sensitivity) if sensitivity else 0.5,
                        source=SDESource.GLOBAL_CATALOGUE,
                        description=f"Global SDE pattern from catalogue for {sde_name}"
                    )
                    sde_patterns.append(sde_pattern)
                    logger.debug(f"✅ Added global SDE: {sde_name} with direct regex from catalogue")
                elif not regex_found:
                    logger.warning(f"⚠️ No regex pattern found for global SDE: {sde_name}")
            
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Loaded {len(sde_patterns)} global SDE patterns from isde_catalogue")
            
            return LoadResult(
                success=True,
                source_used=SDESource.GLOBAL_CATALOGUE,
                sde_patterns=sde_patterns,
                load_timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to load global SDEs: {e}")
            return LoadResult(
                success=False,
                source_used=SDESource.GLOBAL_CATALOGUE,
                sde_patterns=[],
                error_message=f"Database error: {str(e)}"
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to load global SDEs: {e}")
            return LoadResult(
                success=False,
                source_used=SDESource.GLOBAL_CATALOGUE,
                sde_patterns=[],
                error_message=f"Database error: {str(e)}"
            )
    
    def _load_regex_patterns_for_sde(self, sde_name: str) -> List[Dict[str, Any]]:
        """Load regex patterns from regex table for specific SDE"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Query regex patterns for this SDE - simplified for actual table schema
            query = """
            SELECT regex_pattern
            FROM regexes
            WHERE pattern_name = %s
            ORDER BY pattern_name
            """
            
            cursor.execute(query, (sde_name,))
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            regex_patterns = []
            for row in results:
                regex_pattern = row[0]  # Only regex_pattern column
                regex_patterns.append({
                    'pattern': regex_pattern,
                    'confidence': 0.8,  # Default confidence
                    'description': f'Pattern for {sde_name}',
                    'source': 'database'
                })
            
            return regex_patterns
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to load regex patterns for {sde_name}: {e}")
            return []
    
    def _select_best_regex_pattern(self, catalogue_patterns_json: str, 
                                 regex_table_patterns: List[Dict[str, Any]]) -> Optional[str]:
        """Select the best regex pattern from available sources"""
        all_patterns = []
        
        # Add patterns from isde_catalogue
        if catalogue_patterns_json:
            try:
                catalogue_patterns = json.loads(catalogue_patterns_json)
                validation_patterns = catalogue_patterns.get('validation', [])
                for pattern in validation_patterns:
                    all_patterns.append({
                        'pattern': pattern,
                        'confidence': 0.8,  # Default confidence for catalogue patterns
                        'source': 'catalogue'
                    })
            except json.JSONDecodeError:
                logger.warning("⚠️ Invalid JSON in catalogue regex patterns")
        
        # Add patterns from regex table
        all_patterns.extend(regex_table_patterns)
        
        # Select pattern with highest confidence
        if all_patterns:
            best_pattern = max(all_patterns, key=lambda x: x.get('confidence', 0))
            return best_pattern['pattern']
        
        return None
    
    def _load_from_config_file(self, is_fallback: bool = False) -> LoadResult:
        """
        🔄 FALLBACK 2: Load SDE definitions from local sde_definitions.yaml file
        
        Args:
            is_fallback: Whether this is being called as a fallback mechanism
            
        Returns:
            LoadResult with SDEs loaded from config file
        """
        fallback_msg = "Fallback 2: " if is_fallback else ""
        logger.info(f"📁 {fallback_msg}Loading SDE definitions from local config file")
        
        try:
            # Look for sde_definitions.yaml specifically as per your specification
            sde_definitions_file = os.path.join(self.config_path, 'sde_definitions.yaml')
            
            if not os.path.exists(sde_definitions_file):
                # Try alternative locations
                alternative_paths = [
                    os.path.join(os.path.dirname(__file__), '..', 'config', 'sde_definitions.yaml'),
                    os.path.join(os.path.dirname(__file__), 'sde_definitions.yaml'),
                    self.sde_config_file  # Original fallback
                ]
                
                config_file_found = None
                for alt_path in alternative_paths:
                    if os.path.exists(alt_path):
                        config_file_found = alt_path
                        logger.info(f"📁 Found sde_definitions.yaml at: {alt_path}")
                        break
                
                if not config_file_found:
                    logger.warning(f"📁 sde_definitions.yaml not found - triggering next fallback")
                    return LoadResult(
                        success=True,
                        source_used=SDESource.LOCAL_CONFIG,
                        sde_patterns=[],
                        error_message="sde_definitions.yaml config file not found"
                    )
                
                sde_definitions_file = config_file_found
            
            logger.debug(f"📁 Loading SDE definitions from: {sde_definitions_file}")
            
            with open(sde_definitions_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            sde_patterns = []
            
            # Process sde_definitions.yaml format
            if 'sde_definitions' in config_data:
                sde_definitions = config_data['sde_definitions']
                logger.info(f"📊 Found {len(sde_definitions)} SDE categories in config file")
                
                for category, sdes in sde_definitions.items():
                    if isinstance(sdes, dict):
                        logger.debug(f"📁 Processing category: {category} with {len(sdes)} SDEs")
                        
                        for sde_name, sde_config in sdes.items():
                            if isinstance(sde_config, dict) and 'regex' in sde_config:
                                pattern = SDEPattern(
                                    sde_name=sde_name,
                                    data_type=sde_config.get('data_type', 'string'),
                                    regex_pattern=sde_config.get('regex', '.*'),
                                    sensitivity_level=sde_config.get('sensitivity', 'medium'),
                                    confidence_weight=self._map_sensitivity_to_confidence(sde_config.get('sensitivity', 'medium')),
                                    source=SDESource.LOCAL_CONFIG,
                                    description=f"Config file SDE from {category} category"
                                )
                                sde_patterns.append(pattern)
                                logger.debug(f"✅ Added config SDE: {sde_name} from {category}")
                            else:
                                logger.warning(f"⚠️ Invalid SDE config for {sde_name} in {category}")
            
            elif isinstance(config_data, dict) and any(key for key in config_data.keys() if isinstance(config_data[key], dict)):
                # Direct category format (without sde_definitions wrapper)
                logger.info(f"📊 Found direct category format with {len(config_data)} categories")
                
                for category, sdes in config_data.items():
                    if isinstance(sdes, dict):
                        logger.debug(f"📁 Processing direct category: {category} with {len(sdes)} SDEs")
                        
                        for sde_name, sde_config in sdes.items():
                            if isinstance(sde_config, dict) and 'regex' in sde_config:
                                pattern = SDEPattern(
                                    sde_name=sde_name,
                                    data_type=sde_config.get('data_type', 'string'),
                                    regex_pattern=sde_config.get('regex', '.*'),
                                    sensitivity_level=sde_config.get('sensitivity', 'medium'),
                                    confidence_weight=self._map_sensitivity_to_confidence(sde_config.get('sensitivity', 'medium')),
                                    source=SDESource.LOCAL_CONFIG,
                                    description=f"Config file SDE from {category} category"
                                )
                                sde_patterns.append(pattern)
                                logger.debug(f"✅ Added config SDE: {sde_name} from {category}")
            
            else:
                logger.warning("📁 Unsupported config file format - expected sde_definitions structure")
                return LoadResult(
                    success=True,
                    source_used=SDESource.LOCAL_CONFIG,
                    sde_patterns=[],
                    error_message="Unsupported config file format"
                )
            
            logger.info(f"✅ Loaded {len(sde_patterns)} SDE patterns from config file")
            
            return LoadResult(
                success=True,
                source_used=SDESource.LOCAL_CONFIG,
                sde_patterns=sde_patterns,
                load_timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to load SDEs from config file: {e}")
            return LoadResult(
                success=False,
                source_used=SDESource.LOCAL_CONFIG,
                sde_patterns=[],
                error_message=f"Config file error: {str(e)}"
            )
    
    def _load_hardcoded_fallback(self) -> LoadResult:
        """Load minimal hardcoded patterns as final fallback"""
        logger.warning("⚠️ Using hardcoded fallback patterns")
        
        hardcoded_patterns = [
            SDEPattern(
                sde_name='email',
                data_type='string',
                regex_pattern=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
                sensitivity_level='high',
                confidence_weight=0.9,
                source=SDESource.FALLBACK_HARDCODED,
                description='Hardcoded email pattern'
            ),
            SDEPattern(
                sde_name='phone',
                data_type='string',
                regex_pattern=r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                sensitivity_level='medium',
                confidence_weight=0.8,
                source=SDESource.FALLBACK_HARDCODED,
                description='Hardcoded phone pattern'
            ),
            SDEPattern(
                sde_name='ssn',
                data_type='string',
                regex_pattern=r'\b\d{3}-\d{2}-\d{4}\b',
                sensitivity_level='critical',
                confidence_weight=0.95,
                source=SDESource.FALLBACK_HARDCODED,
                description='Hardcoded SSN pattern'
            ),
            SDEPattern(
                sde_name='credit_card',
                data_type='string',
                regex_pattern=r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
                sensitivity_level='critical',
                confidence_weight=0.9,
                source=SDESource.FALLBACK_HARDCODED,
                description='Hardcoded credit card pattern'
            )
        ]
        
        return LoadResult(
            success=True,
            source_used=SDESource.FALLBACK_HARDCODED,
            sde_patterns=hardcoded_patterns,
            fallback_triggered=True,
            load_timestamp=datetime.now().isoformat()
        )
    
    def _map_sensitivity_to_confidence(self, sensitivity: str) -> float:
        """Map sensitivity level to confidence weight"""
        sensitivity_map = {
            'critical': 0.95,
            'high': 0.85,
            'medium': 0.75,
            'low': 0.65
        }
        return sensitivity_map.get(sensitivity.lower(), 0.75)
    
    def _is_cache_valid(self) -> bool:
        """Check if cached SDEs are still valid"""
        if not self._cached_sdes or not self._cache_timestamp:
            return False
        
        age_seconds = (datetime.now() - self._cache_timestamp).total_seconds()
        return age_seconds < self.cache_ttl_seconds
    
    def _update_cache(self, result: LoadResult):
        """Update the SDE cache"""
        if self.cache_loaded_sdes and result.success:
            self._cached_sdes = result.sde_patterns
            self._cache_timestamp = datetime.now()
            self._last_source_used = result.source_used
            logger.debug(f"📋 Updated SDE cache with {len(result.sde_patterns)} patterns from {result.source_used.value}")
    
    def force_config_fallback(self, enable: bool = True):
        """Manually force fallback to config file for testing"""
        self.force_fallback_to_config = enable
        self.clear_cache()
        logger.info(f"🔧 Force config fallback: {'enabled' if enable else 'disabled'}")
    
    def clear_cache(self):
        """Clear the SDE cache"""
        self._cached_sdes = None
        self._cache_timestamp = None
        self._last_source_used = None
        logger.debug("🗑️ SDE cache cleared")
    
    def get_load_statistics(self) -> Dict[str, Any]:
        """Get statistics about SDE loading"""
        return {
            'client_id': self.client_id,
            'cache_valid': self._is_cache_valid(),
            'cached_patterns_count': len(self._cached_sdes) if self._cached_sdes else 0,
            'last_source_used': self._last_source_used.value if self._last_source_used else None,
            'cache_timestamp': self._cache_timestamp.isoformat() if self._cache_timestamp else None,
            'force_fallback_enabled': self.force_fallback_to_config,
            'hardcoded_fallback_enabled': self.enable_hardcoded_fallback,
            'cache_ttl_seconds': self.cache_ttl_seconds,
            'config_file_path': self.sde_config_file
        }
    
    def validate_sde_sources(self) -> Dict[str, Any]:
        """Validate all SDE sources"""
        validation_results = {
            'client_id': self.client_id,
            'validation_timestamp': datetime.now().isoformat(),
            'sources': {},
            'overall_health': 'unknown'
        }
        
        # Test client-selected SDEs
        try:
            result = self._load_client_selected_sdes()
            validation_results['sources']['client_selected'] = {
                'accessible': result.success,
                'patterns_count': len(result.sde_patterns),
                'error': result.error_message
            }
        except Exception as e:
            validation_results['sources']['client_selected'] = {
                'accessible': False,
                'patterns_count': 0,
                'error': str(e)
            }
        
        # Test global SDEs
        try:
            result = self._load_global_sdes()
            validation_results['sources']['global_catalogue'] = {
                'accessible': result.success,
                'patterns_count': len(result.sde_patterns),
                'error': result.error_message
            }
        except Exception as e:
            validation_results['sources']['global_catalogue'] = {
                'accessible': False,
                'patterns_count': 0,
                'error': str(e)
            }
        
        # Test config file
        try:
            result = self._load_from_config_file()
            validation_results['sources']['config_file'] = {
                'accessible': result.success,
                'patterns_count': len(result.sde_patterns),
                'file_path': self.sde_config_file,
                'error': result.error_message
            }
        except Exception as e:
            validation_results['sources']['config_file'] = {
                'accessible': False,
                'patterns_count': 0,
                'error': str(e)
            }
        
        # Test hardcoded fallback
        try:
            result = self._load_hardcoded_fallback()
            validation_results['sources']['hardcoded_fallback'] = {
                'accessible': result.success,
                'patterns_count': len(result.sde_patterns),
                'error': result.error_message
            }
        except Exception as e:
            validation_results['sources']['hardcoded_fallback'] = {
                'accessible': False,
                'patterns_count': 0,
                'error': str(e)
            }
        
        # Determine overall health
        accessible_sources = sum(1 for source in validation_results['sources'].values() if source['accessible'])
        total_sources = len(validation_results['sources'])
        
        if accessible_sources == total_sources:
            validation_results['overall_health'] = 'excellent'
        elif accessible_sources >= 2:
            validation_results['overall_health'] = 'good'
        elif accessible_sources >= 1:
            validation_results['overall_health'] = 'poor'
        else:
            validation_results['overall_health'] = 'critical'
        
        validation_results['accessible_sources'] = accessible_sources
        validation_results['total_sources'] = total_sources
        
        return validation_results
