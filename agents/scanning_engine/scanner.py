"""
Refactored Scanner Module with Simple Baseline Support
Lightweight scanner.py that imports specialized scanner modules and includes baseline tracking
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import specialized scanners
try:
    from .scanners import (
        DatabaseScanner,
        FileScanner, 
        CloudScanner,
        CSVScanner,
        JSONScanner,
        YAMLScanner,
        BigQueryScanner,
        GCSScanner
    )
    from .baseline_manager import SimpleBaselineManager
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append(str(Path(__file__).parent))
    from scanners import (
        DatabaseScanner,
        FileScanner, 
        CloudScanner,
        CSVScanner,
        JSONScanner,
        YAMLScanner,
        BigQueryScanner,
        GCSScanner
    )
    from baseline_manager import SimpleBaselineManager

logger = logging.getLogger(__name__)


class MultiConnectorScanner:
    """
    Lightweight main scanner that delegates to specialized scanner modules
    """
    
    def __init__(self, config_path: str = None, enable_baseline: bool = False):
        """
        Initialize the multi-connector scanner
        
        Args:
            config_path: Path to configuration file
            enable_baseline: Enable baseline tracking for incremental scanning
        """
        self.config_path = config_path or "config/config_sqlite.yaml"
        self.config = self._load_config()
        self.enable_baseline = enable_baseline
        
        # Load patterns and mappings
        self.privacy_patterns = self._load_patterns()
        self.field_mappings = self._load_field_mappings()
        self.sde_categories = self._load_sde_categories()
        
        # Initialize baseline manager if enabled
        if self.enable_baseline:
            self.baseline_manager = SimpleBaselineManager()
        else:
            self.baseline_manager = None
        
        # Initialize specialized scanners
        self._init_scanners()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load scanner configuration"""
        try:
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return {}
    
    def _load_patterns(self) -> Dict[str, Any]:
        """Load privacy detection patterns"""
        try:
            patterns_path = self.config.get('patterns_file', 'config/regex_patterns.yaml')
            with open(patterns_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Error loading patterns: {str(e)}")
            return {}
    
    def _load_field_mappings(self) -> Dict[str, Any]:
        """Load field name to SDE mappings"""
        try:
            sde_path = self.config.get('sde_definitions_file', 'config/sde_definitions.yaml')
            with open(sde_path, 'r') as file:
                sde_data = yaml.safe_load(file)
                return sde_data.get('field_mappings', {})
        except Exception as e:
            logger.error(f"Error loading field mappings: {str(e)}")
            return {}
    
    def _load_sde_categories(self) -> Dict[str, Any]:
        """Load SDE category definitions"""
        try:
            sde_path = self.config.get('sde_definitions_file', 'config/sde_definitions.yaml')
            with open(sde_path, 'r') as file:
                sde_data = yaml.safe_load(file)
                return sde_data.get('sde_categories', {})
        except Exception as e:
            logger.error(f"Error loading SDE categories: {str(e)}")
            return {}
    
    def _init_scanners(self):
        """Initialize specialized scanner instances"""
        scanner_args = (self.privacy_patterns, self.field_mappings, self.sde_categories)
        
        self.database_scanner = DatabaseScanner(*scanner_args)
        self.file_scanner = FileScanner(*scanner_args)
        self.cloud_scanner = CloudScanner(*scanner_args)
        self.csv_scanner = CSVScanner(*scanner_args)
        self.json_scanner = JSONScanner(*scanner_args)
        self.yaml_scanner = YAMLScanner(*scanner_args)
        self.bigquery_scanner = BigQueryScanner(*scanner_args)
        self.gcs_scanner = GCSScanner(*scanner_args)
    
    def scan_sources(self, sources: List[Dict[str, Any]], force_full: bool = False) -> Dict[str, Any]:
        """
        Scan multiple data sources for SDEs with optional baseline support
        
        Args:
            sources: List of source configurations
            force_full: Force full scan even if baseline suggests skipping
            
        Returns:
            Comprehensive scan results
        """
        all_findings = []
        source_summaries = []
        baseline_used = False
        
        for source in sources:
            try:
                # Check baseline if enabled
                should_scan = True
                skip_reason = "not_checked"
                
                if self.baseline_manager and not force_full:
                    should_scan, skip_reason = self.baseline_manager.should_scan_source(source)
                    baseline_used = True
                
                if should_scan or force_full:
                    # Execute scan
                    from datetime import datetime
                    scan_start = datetime.now()
                    
                    source_findings = self.scan_single_source(source)
                    all_findings.extend(source_findings)
                    
                    scan_duration = (datetime.now() - scan_start).total_seconds()
                    
                    # Update baseline if enabled
                    if self.baseline_manager:
                        scan_results = {
                            'total_findings': len(source_findings),
                            'findings': source_findings
                        }
                        self.baseline_manager.update_baseline(source, scan_results, scan_duration)
                    
                    # Create source summary
                    summary = self._create_source_summary(source, source_findings)
                    summary['scan_duration'] = scan_duration
                    summary['baseline_reason'] = skip_reason if baseline_used else 'baseline_disabled'
                    source_summaries.append(summary)
                else:
                    # Skipped scan
                    summary = {
                        'source_name': source.get('name', 'unknown'),
                        'source_type': source.get('type', 'unknown'),
                        'total_findings': 0,
                        'sde_findings': 0,
                        'scan_status': 'skipped',
                        'skip_reason': skip_reason,
                        'scan_duration': 0
                    }
                    source_summaries.append(summary)
                
            except Exception as e:
                logger.error(f"Error scanning source {source.get('name', 'unknown')}: {str(e)}")
        
        # Generate overall summary
        overall_summary = self._create_overall_summary(all_findings, source_summaries)
        overall_summary['baseline_enabled'] = self.enable_baseline
        overall_summary['baseline_used'] = baseline_used
        
        return {
            'findings': all_findings,
            'source_summaries': source_summaries,
            'overall_summary': overall_summary,
            'total_findings': len(all_findings),
            'scan_timestamp': self._get_timestamp(),
            'baseline_enabled': self.enable_baseline
        }
    
    def scan_single_source(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scan a single data source using appropriate specialized scanner
        
        Args:
            source: Source configuration
            
        Returns:
            List of findings from the source
        """
        source_type = source.get('type', '').lower()
        
        try:
            # Route to appropriate scanner based on source type
            if any(db_type in source_type for db_type in ['sqlite', 'mysql', 'postgresql', 'postgres']):
                return self.database_scanner.scan(source)
            
            elif 'bigquery' in source_type:
                return self.bigquery_scanner.scan(source)
            
            elif 'gcs' in source_type or 'cloud_storage' in source_type:
                return self.gcs_scanner.scan(source)
            
            elif source_type == 'file' or 'file_path' in source:
                file_path = source.get('file_path', '')
                extension = Path(file_path).suffix.lower()
                
                if extension == '.csv':
                    return self.csv_scanner.scan(source)
                elif extension == '.json':
                    return self.json_scanner.scan(source)
                elif extension in ['.yaml', '.yml']:
                    return self.yaml_scanner.scan(source)
                else:
                    return self.file_scanner.scan(source)
            
            else:
                logger.warning(f"Unsupported source type: {source_type}")
                return []
                
        except Exception as e:
            logger.error(f"Error in scan_single_source: {str(e)}")
            return []
    
    def _create_source_summary(self, source: Dict[str, Any], findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create summary for a single source"""
        sde_count = len([f for f in findings if f.get('is_sde', False)])
        
        # Count by risk level
        risk_counts = {}
        for finding in findings:
            if finding.get('is_sde', False):
                risk_level = finding.get('risk_level', 'UNKNOWN')
                risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
        
        # Count by SDE category
        category_counts = {}
        for finding in findings:
            if finding.get('is_sde', False):
                category = finding.get('sde_category', 'UNKNOWN')
                category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            'source_name': source.get('name', 'unknown'),
            'source_type': source.get('type', 'unknown'),
            'total_findings': len(findings),
            'sde_findings': sde_count,
            'risk_level_distribution': risk_counts,
            'category_distribution': category_counts,
            'scan_status': 'completed'
        }
    
    def _create_overall_summary(self, all_findings: List[Dict[str, Any]], 
                               source_summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create overall scan summary"""
        total_sdes = len([f for f in all_findings if f.get('is_sde', False)])
        
        # Aggregate risk levels
        overall_risk_counts = {}
        for finding in all_findings:
            if finding.get('is_sde', False):
                risk_level = finding.get('risk_level', 'UNKNOWN')
                overall_risk_counts[risk_level] = overall_risk_counts.get(risk_level, 0) + 1
        
        # Aggregate categories
        overall_category_counts = {}
        for finding in all_findings:
            if finding.get('is_sde', False):
                category = finding.get('sde_category', 'UNKNOWN')
                overall_category_counts[category] = overall_category_counts.get(category, 0) + 1
        
        # Privacy compliance analysis
        compliance_analysis = self._analyze_privacy_compliance(all_findings)
        
        return {
            'total_sources_scanned': len(source_summaries),
            'total_findings': len(all_findings),
            'total_sde_findings': total_sdes,
            'overall_risk_distribution': overall_risk_counts,
            'overall_category_distribution': overall_category_counts,
            'privacy_compliance_analysis': compliance_analysis,
            'recommendations': self._generate_recommendations(all_findings)
        }
    
    def _analyze_privacy_compliance(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze privacy compliance implications"""
        compliance_issues = []
        
        for finding in findings:
            if finding.get('is_sde', False):
                implications = finding.get('privacy_implications', [])
                compliance_issues.extend(implications)
        
        # Count unique compliance requirements
        unique_requirements = list(set(compliance_issues))
        
        return {
            'total_compliance_requirements': len(unique_requirements),
            'requirements_identified': unique_requirements,
            'high_risk_count': len([f for f in findings if f.get('risk_level') in ['HIGH', 'CRITICAL']]),
            'requires_immediate_attention': len([f for f in findings if f.get('risk_level') == 'CRITICAL']) > 0
        }
    
    def _generate_recommendations(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate privacy and security recommendations"""
        recommendations = []
        
        critical_count = len([f for f in findings if f.get('risk_level') == 'CRITICAL'])
        high_count = len([f for f in findings if f.get('risk_level') == 'HIGH'])
        
        if critical_count > 0:
            recommendations.append(f"URGENT: {critical_count} critical SDE findings require immediate attention")
        
        if high_count > 0:
            recommendations.append(f"HIGH PRIORITY: {high_count} high-risk SDE findings need review")
        
        # Category-specific recommendations
        categories = [f.get('sde_category') for f in findings if f.get('is_sde', False)]
        if 'PII' in categories:
            recommendations.append("Implement data minimization for PII fields")
        if 'FINANCIAL' in categories:
            recommendations.append("Ensure PCI DSS compliance for financial data")
        if 'MEDICAL' in categories:
            recommendations.append("Verify HIPAA compliance for medical information")
        
        return recommendations
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for scan results"""
        from datetime import datetime
        return datetime.now().isoformat()


# Convenience functions for backward compatibility
def perform_deep_data_scan(sources: List[Dict[str, Any]], config_path: str = None) -> Dict[str, Any]:
    """
    Perform comprehensive SDE scanning across multiple sources
    
    Args:
        sources: List of data source configurations
        config_path: Path to scanner configuration file
        
    Returns:
        Comprehensive scan results
    """
    scanner = MultiConnectorScanner(config_path)
    return scanner.scan_sources(sources)


def scan_single_database(source: Dict[str, Any], config_path: str = None) -> List[Dict[str, Any]]:
    """
    Scan a single database source
    
    Args:
        source: Database source configuration
        config_path: Path to scanner configuration file
        
    Returns:
        List of findings
    """
    scanner = MultiConnectorScanner(config_path)
    return scanner.scan_single_source(source)
