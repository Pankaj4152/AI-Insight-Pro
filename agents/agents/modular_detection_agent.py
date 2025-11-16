"""
Modular Detection Agent - Advanced pattern and anomaly detection
Uses configuration-driven approach and enhances findings from scanning
"""

import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import json
from dotenv import load_dotenv
# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from config_manager import AgentConfigManager
from postgresql_db_manager import PostgreSQLCloudScanDBManager

logger = logging.getLogger(__name__)
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "mistralai/mistral-7b-instruct")

class ModularDetectionAgent:
    """
    Configuration-driven detection agent for advanced pattern analysis
    Multi-client aware - all operations are scoped to a specific client_id
    """
    
    def __init__(self, config_manager: AgentConfigManager = None, client_id: str = None):
        """
        Initialize the Detection Agent
        
        Args:
            config_manager: Configuration manager instance
            client_id: Client ID for multi-tenant operations
        """
        self.client_id = client_id
        self.config_manager = config_manager or AgentConfigManager()
        self.db_manager = PostgreSQLCloudScanDBManager(self.config_manager, client_id=client_id)
        self.openai_api_key = self.config_manager.get_openai_api_key()
        # LLM functionality disabled - module removed
        self.llm_client = None
        self.ai_detection_available = False
        print("[LLM] AI detection disabled - risk assessment module removed")
        logger.info("✅ Modular Detection Agent initialized")
    
    def analyze_scan_findings(self, scan_id: int) -> Dict[str, Any]:
        """
        Analyze findings from a specific scan and update confidence scores
        
        Args:
            scan_id: ID of the scan to analyze
            
        Returns:
            Detection analysis results
        """
        print(f"🔎 Analyzing findings from scan ID: {scan_id}")
        
        # Get findings from database
        findings = self.db_manager.get_scan_findings(scan_id)
        
        if not findings:
            logger.warning(f"No findings found for scan ID: {scan_id}")
            return {
                'scan_id': scan_id,
                'total_findings': 0,
                'analysis_results': {},
                'recommendations': [],
                'analysis_timestamp': datetime.now().isoformat()
            }
        
        # Calculate and update confidence scores using TP/TN/FP/FN logic
        print(f"🧮 Calculating confidence scores for {len(findings)} findings...")
        confidence_updates = self._calculate_confidence_scores(findings)
        self._update_confidence_scores(scan_id, confidence_updates)
        
        # Perform analysis
        pattern_analysis = self._analyze_patterns(findings)
        risk_assessment = self._assess_risk_levels(findings)
        anomaly_detection = self._detect_anomalies(findings)
        compliance_analysis = self._analyze_compliance_implications(findings)
        analysis_results = {
            'pattern_analysis': pattern_analysis,
            'risk_assessment': risk_assessment,
            'anomaly_detection': anomaly_detection,  # Return full anomaly details
            'compliance_analysis': compliance_analysis
        }
        # Generate enhanced analysis with AI if available
        if self.ai_detection_available:
            analysis_results['ai_enhanced_analysis'] = self._ai_enhanced_analysis(findings)
        else:
            analysis_results['ai_enhanced_analysis'] = self._mock_ai_analysis(findings)
        # Generate recommendations
        recommendations = self._generate_recommendations(findings, analysis_results)
        results = {
            'scan_id': scan_id,
            'total_findings': len(findings),
            'confidence_updates': len(confidence_updates),  # Number of confidence scores updated
            'analysis_results': analysis_results,
            'recommendations': recommendations,
            'analysis_timestamp': datetime.now().isoformat()
        }
        print(f"✅ Analysis completed. {len(findings)} findings analyzed")
        # Print anomaly details if any
        if anomaly_detection.get('anomaly_count', 0) > 0:
            print(f"[ANOMALY] {anomaly_detection['anomaly_count']} anomalies detected:")
            for k, v in anomaly_detection.items():
                if k != 'anomaly_count' and v:
                    print(f"  {k}: {json.dumps(v, indent=2)}")
        return results
    
    def _analyze_patterns(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in the findings"""
        pattern_stats = {
            'sde_types': {},
            'risk_levels': {},
            'detection_methods': {},
            'source_distribution': {},
            'confidence_distribution': {
                'high': 0,    # > 0.8
                'medium': 0,  # 0.5 - 0.8
                'low': 0      # < 0.5
            }
        }
        
        for finding in findings:
            # SDE types
            sde_type = finding.get('sde_type', 'unknown')
            pattern_stats['sde_types'][sde_type] = pattern_stats['sde_types'].get(sde_type, 0) + 1
            
            # Risk levels
            risk_level = finding.get('risk_level', 'unknown')
            pattern_stats['risk_levels'][risk_level] = pattern_stats['risk_levels'].get(risk_level, 0) + 1
            
            # Detection methods
            detection_method = finding.get('detection_method', 'unknown')
            pattern_stats['detection_methods'][detection_method] = pattern_stats['detection_methods'].get(detection_method, 0) + 1
            
            # Source distribution
            location_metadata = finding.get('location_metadata')
            if isinstance(location_metadata, str):
                try:
                    location_metadata = json.loads(location_metadata)
                except:
                    location_metadata = {}
            
            source_name = location_metadata.get('source_name', 'unknown') if location_metadata else 'unknown'
            pattern_stats['source_distribution'][source_name] = pattern_stats['source_distribution'].get(source_name, 0) + 1
            
            # Confidence distribution
            confidence = finding.get('confidence_score', 0.0)
            if confidence > 0.8:
                pattern_stats['confidence_distribution']['high'] += 1
            elif confidence > 0.5:
                pattern_stats['confidence_distribution']['medium'] += 1
            else:
                pattern_stats['confidence_distribution']['low'] += 1
        
        return pattern_stats
    
    def _assess_risk_levels(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess overall risk levels"""
        risk_assessment = {
            'overall_risk': 'low',
            'critical_findings': 0,
            'high_risk_findings': 0,
            'medium_risk_findings': 0,
            'low_risk_findings': 0,
            'risk_factors': []
        }
        
        high_risk_sde_types = ['ssn', 'credit_card', 'passport', 'driving_license']
        
        for finding in findings:
            risk_level = finding.get('risk_level', 'low')
            sde_type = finding.get('sde_type', '')
            
            if risk_level == 'critical' or sde_type in high_risk_sde_types:
                risk_assessment['critical_findings'] += 1
            elif risk_level == 'high':
                risk_assessment['high_risk_findings'] += 1
            elif risk_level == 'medium':
                risk_assessment['medium_risk_findings'] += 1
            else:
                risk_assessment['low_risk_findings'] += 1
        
        # Determine overall risk
        if risk_assessment['critical_findings'] > 0:
            risk_assessment['overall_risk'] = 'critical'
            risk_assessment['risk_factors'].append('Critical PII data detected')
        elif risk_assessment['high_risk_findings'] > 5:
            risk_assessment['overall_risk'] = 'high'
            risk_assessment['risk_factors'].append('Multiple high-risk findings')
        elif risk_assessment['high_risk_findings'] > 0 or risk_assessment['medium_risk_findings'] > 10:
            risk_assessment['overall_risk'] = 'medium'
            risk_assessment['risk_factors'].append('Significant PII exposure')
        
        return risk_assessment
    
    def _detect_anomalies(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect anomalies in the findings"""
        anomalies = {
            'unusual_patterns': [],
            'suspicious_concentrations': [],
            'data_quality_issues': [],
            'anomaly_count': 0
        }
        
        # Check for unusual concentrations of PII
        sde_counts = {}
        for finding in findings:
            sde_type = finding.get('sde_type', 'unknown')
            sde_counts[sde_type] = sde_counts.get(sde_type, 0) + 1
        
        # Flag unusual concentrations
        total_findings = len(findings)
        for sde_type, count in sde_counts.items():
            if count > total_findings * 0.3:  # More than 30% of one type
                anomalies['suspicious_concentrations'].append({
                    'sde_type': sde_type,
                    'count': count,
                    'percentage': (count / total_findings) * 100,
                    'concern': 'High concentration of specific PII type'
                })
                anomalies['anomaly_count'] += 1
        
        # Check for data quality issues
        low_confidence_count = 0
        for finding in findings:
            confidence = finding.get('confidence_score', 1.0)
            if confidence < 0.5:
                low_confidence_count += 1
        
        if low_confidence_count > total_findings * 0.2:  # More than 20% low confidence
            anomalies['data_quality_issues'].append({
                'issue': 'High number of low-confidence detections',
                'count': low_confidence_count,
                'percentage': (low_confidence_count / total_findings) * 100
            })
            anomalies['anomaly_count'] += 1
        
        return anomalies
    
    def _analyze_compliance_implications(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze compliance implications"""
        compliance = {
            'gdpr_implications': {'affected': False, 'findings': 0},
            'hipaa_implications': {'affected': False, 'findings': 0},
            'pci_implications': {'affected': False, 'findings': 0},
            'ccpa_implications': {'affected': False, 'findings': 0},
            'compliance_recommendations': []
        }
        
        gdpr_types = ['email', 'name', 'address', 'phone', 'ip_address']
        hipaa_types = ['medical', 'health', 'ssn']
        pci_types = ['credit_card', 'bank_account']
        ccpa_types = ['email', 'name', 'address', 'phone', 'ip_address']
        
        for finding in findings:
            sde_type = finding.get('sde_type', '')
            
            if sde_type in gdpr_types:
                compliance['gdpr_implications']['affected'] = True
                compliance['gdpr_implications']['findings'] += 1
            
            if sde_type in hipaa_types:
                compliance['hipaa_implications']['affected'] = True
                compliance['hipaa_implications']['findings'] += 1
            
            if sde_type in pci_types:
                compliance['pci_implications']['affected'] = True
                compliance['pci_implications']['findings'] += 1
            
            if sde_type in ccpa_types:
                compliance['ccpa_implications']['affected'] = True
                compliance['ccpa_implications']['findings'] += 1
        
        # Generate recommendations
        if compliance['gdpr_implications']['affected']:
            compliance['compliance_recommendations'].append(
                'GDPR compliance review required - EU personal data detected'
            )
        
        if compliance['hipaa_implications']['affected']:
            compliance['compliance_recommendations'].append(
                'HIPAA compliance review required - Healthcare data detected'
            )
        
        if compliance['pci_implications']['affected']:
            compliance['compliance_recommendations'].append(
                'PCI DSS compliance review required - Payment card data detected'
            )
        
        if compliance['ccpa_implications']['affected']:
            compliance['compliance_recommendations'].append(
                'CCPA compliance review required - California consumer data detected'
            )
        
        return compliance
    
    def _ai_enhanced_analysis(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """AI enhancement disabled - return basic analysis"""
        try:
            # Since risk assessment module is removed, return basic analysis
            anomalies = self._detect_anomalies(findings)
            
            # Basic risk assessment based on finding count and types
            total_findings = len(findings)
            if total_findings > 50:
                risk_level = "High"
            elif total_findings > 20:
                risk_level = "Medium"
            else:
                risk_level = "Low"
            
            return {
                "analysis_type": "basic",
                "privacy_risk_assessment": risk_level,
                "data_classification": "Requires manual review",
                "immediate_actions": [
                    "Review all findings manually",
                    "Prioritize high-confidence detections",
                    "Verify data handling practices"
                ],
                "long_term_recommendations": [
                    "Implement data governance policies",
                    "Regular privacy audits",
                    "Staff training on data protection"
                ],
                "regulatory_compliance": ["Manual compliance review required"],
                "anomalies": anomalies,
                "total_findings": total_findings
            }
        except Exception as e:
            logger.error(f"AI enhanced analysis failed: {e}")
            return {
                "analysis_type": "error",
                "error": str(e),
                "privacy_risk_assessment": "Unknown",
                "data_classification": "Unknown",
                "immediate_actions": ["Review analysis manually"],
                "long_term_recommendations": ["Investigate scanning issues"],
                "regulatory_compliance": ["Manual compliance review required"]
            }
    
    def _generate_recommendations(self, findings: List[Dict[str, Any]], 
                                analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        recommendations = []
        
        risk_assessment = analysis_results.get('risk_assessment', {})
        overall_risk = risk_assessment.get('overall_risk', 'low')
        
        # Priority 1: Critical/High risk recommendations
        if overall_risk in ['critical', 'high']:
            recommendations.append({
                'priority': 1,
                'category': 'immediate_action',
                'title': 'Immediate Risk Mitigation Required',
                'description': 'High-risk PII detected requiring immediate attention',
                'actions': [
                    'Review data access permissions',
                    'Implement additional security controls',
                    'Consider data minimization strategies'
                ]
            })
        
        # Compliance recommendations
        compliance = analysis_results.get('compliance_analysis', {})
        if compliance.get('compliance_recommendations'):
            recommendations.append({
                'priority': 2,
                'category': 'compliance',
                'title': 'Regulatory Compliance Review',
                'description': 'Multiple compliance frameworks may be affected',
                'actions': compliance['compliance_recommendations']
            })
        
        # Anomaly recommendations
        anomalies = analysis_results.get('anomaly_detection', {})
        if anomalies.get('anomaly_count', 0) > 0:
            recommendations.append({
                'priority': 3,
                'category': 'data_quality',
                'title': 'Data Quality Investigation',
                'description': 'Anomalies detected in data patterns',
                'actions': [
                    'Investigate suspicious data concentrations',
                    'Review data collection practices',
                    'Validate detection accuracy'
                ]
            })
        
        return recommendations
    
    def detect_data_patterns(self, scan_id: int) -> Dict[str, Any]:
        """
        Detect data patterns in scan findings
        
        Args:
            scan_id: ID of the scan to analyze patterns for
            
        Returns:
            Dictionary containing detected patterns
        """
        try:
            # Get findings for the scan
            findings = self.db_manager.get_scan_findings(scan_id=scan_id)
            
            if not findings:
                return {
                    'status': 'success',
                    'patterns_detected': 0,
                    'patterns': {},
                    'message': 'No findings to analyze patterns for'
                }
            
            # Analyze patterns using existing method
            pattern_analysis = self._analyze_patterns(findings)
            
            return {
                'status': 'success',
                'patterns_detected': len(pattern_analysis.get('pattern_analysis', {})),
                'patterns': pattern_analysis,
                'scan_id': scan_id
            }
            
        except Exception as e:
            logger.error(f"Error detecting data patterns for scan {scan_id}: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'patterns_detected': 0
            }
    
    def assess_compliance_risks(self, scan_id: int) -> Dict[str, Any]:
        """
        Assess compliance risks for scan findings
        
        Args:
            scan_id: ID of the scan to assess compliance for
            
        Returns:
            Dictionary containing compliance assessment
        """
        try:
            # Get findings for the scan
            findings = self.db_manager.get_scan_findings(scan_id=scan_id)
            
            if not findings:
                return {
                    'status': 'success',
                    'compliance_issues': 0,
                    'assessment': {},
                    'message': 'No findings to assess compliance for'
                }
            
            # Analyze compliance using existing method
            compliance_analysis = self._analyze_compliance_implications(findings)
            
            return {
                'status': 'success',
                'compliance_issues': len(compliance_analysis.get('compliance_implications', {})),
                'assessment': compliance_analysis,
                'scan_id': scan_id
            }
            
        except Exception as e:
            logger.error(f"Error assessing compliance risks for scan {scan_id}: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'compliance_issues': 0
            }

    def get_scan_ids_for_client(self, client_id: str) -> List[int]:
        """Get all scan IDs for a client from the scan_findings table."""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT scan_id FROM scan_findings WHERE client_id = %s ORDER BY scan_id", (client_id,))
            scan_ids = [row[0] for row in cursor.fetchall()]
            conn.close()
            return scan_ids
        except Exception as e:
            print(f"[DB] Error fetching scan IDs for client {client_id}: {e}")
            return []

    def _calculate_confidence_scores(self, findings: List[Dict[str, Any]]) -> Dict[int, float]:
        """
        Calculate confidence scores using TP/TN/FP/FN classification logic
        
        Args:
            findings: List of scan findings
            
        Returns:
            Dictionary mapping finding_id to calculated confidence score
        """
        confidence_updates = {}
        
        for finding in findings:
            finding_id = finding.get('finding_id')
            pattern_matched = finding.get('pattern_matched', '').lower()
            data_value = finding.get('data_value', '').lower()
            finding_type = finding.get('finding_type', '').lower()
            sde_category = finding.get('sde_category', '')
            detection_method = finding.get('detection_method', '').lower()
            
            # Initialize classification scores
            tp_score = 0.0  # True Positive indicators
            tn_score = 0.0  # True Negative indicators  
            fp_score = 0.0  # False Positive indicators
            fn_score = 0.0  # False Negative indicators
            
            # True Positive indicators (high confidence patterns)
            if self._is_high_confidence_pattern(pattern_matched, data_value, finding_type):
                tp_score += 0.4
            
            if self._has_valid_format(data_value, finding_type):
                tp_score += 0.3
                
            if detection_method == 'regex_pattern_match':
                tp_score += 0.2
                
            if sde_category != 'UNKNOWN' and sde_category:
                tp_score += 0.1
            
            # False Positive indicators (reduce confidence)
            if self._is_common_false_positive(data_value, finding_type):
                fp_score += 0.3
                
            if len(data_value) < 3:  # Very short values likely false positives
                fp_score += 0.2
                
            if self._is_generic_pattern(pattern_matched):
                fp_score += 0.2
                
            # Context-based adjustments
            context_bonus = self._get_context_confidence_bonus(finding)
            
            # Calculate final confidence score
            # Formula: (TP + context_bonus) / (1 + FP) with bounds [0.1, 0.95]
            raw_confidence = (tp_score + context_bonus) / (1 + fp_score)
            confidence_score = max(0.1, min(0.95, raw_confidence))
            
            confidence_updates[finding_id] = confidence_score
            
        return confidence_updates
    
    def _is_high_confidence_pattern(self, pattern: str, data: str, finding_type: str) -> bool:
        """Check if the pattern indicates high confidence match"""
        high_confidence_patterns = [
            'email', 'phone', 'ssn', 'credit_card', 'bank_account',
            'passport', 'driver_license', 'aadhaar', 'pan'
        ]
        return any(hcp in pattern or hcp in finding_type for hcp in high_confidence_patterns)
    
    def _has_valid_format(self, data: str, finding_type: str) -> bool:
        """Check if data has valid format for the finding type"""
        import re
        
        validation_patterns = {
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'phone': r'^\+?[\d\s\-\(\)]+$',
            'ssn': r'^\d{3}-?\d{2}-?\d{4}$',
            'credit_card': r'^\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}$',
            'zip_code': r'^\d{5}(-\d{4})?$',
            'date': r'^\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}$'
        }
        
        for pattern_type, regex in validation_patterns.items():
            if pattern_type in finding_type.lower() or pattern_type in data.lower():
                return bool(re.match(regex, data))
        
        return False
    
    def _is_common_false_positive(self, data: str, finding_type: str) -> bool:
        """Check for common false positive patterns"""
        false_positive_indicators = [
            'test', 'example', 'sample', 'dummy', 'placeholder',
            '123456', '000000', 'null', 'none', 'n/a'
        ]
        return any(fp in data.lower() for fp in false_positive_indicators)
    
    def _is_generic_pattern(self, pattern: str) -> bool:
        """Check if pattern is too generic"""
        generic_patterns = ['text', 'string', 'number', 'integer', 'content']
        return any(gp in pattern.lower() for gp in generic_patterns)
    
    def _get_context_confidence_bonus(self, finding: Dict[str, Any]) -> float:
        """Calculate context-based confidence bonus"""
        bonus = 0.0
        
        object_path = finding.get('object_path', '').lower()
        matches_found = finding.get('matches_found', 0)
        
        # File/table context bonus
        sensitive_contexts = [
            'user', 'customer', 'personal', 'private', 'confidential',
            'pii', 'sensitive', 'protected', 'secure'
        ]
        
        if any(context in object_path for context in sensitive_contexts):
            bonus += 0.15
            
        # Multiple matches indicate higher confidence
        if matches_found > 1:
            bonus += min(0.1, matches_found * 0.02)
            
        return bonus
    
    def _update_confidence_scores(self, scan_id: int, confidence_updates: Dict[int, float]):
        """
        Update confidence scores in the scan_findings table
        
        Args:
            scan_id: Scan ID to update
            confidence_updates: Dictionary mapping finding_id to new confidence score
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Batch update confidence scores
            update_data = [(score, finding_id) for finding_id, score in confidence_updates.items()]
            
            cursor.executemany("""
                UPDATE scan_findings 
                SET confidence_score = %s 
                WHERE finding_id = %s
            """, update_data)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"✅ Updated confidence scores for {len(confidence_updates)} findings in scan {scan_id}")
            logger.info(f"Updated confidence scores for {len(confidence_updates)} findings in scan {scan_id}")
            
        except Exception as e:
            logger.error(f"Error updating confidence scores: {e}")
            print(f"❌ Error updating confidence scores: {e}")

    def analyze_all_scans_for_client(self, client_id: str) -> List[Dict[str, Any]]:
        """Analyze findings for all scans belonging to a client."""
        scan_ids = self.get_scan_ids_for_client(client_id)
        all_results = []
        for scan_id in scan_ids:
            result = self.analyze_scan_findings(scan_id)
            all_results.append(result)
        return all_results

    def analyze_latest_scan_for_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Analyze findings for the latest scan of a client."""
        scan_ids = self.get_scan_ids_for_client(client_id)
        if not scan_ids:
            print(f"[INFO] No scans found for client {client_id}")
            return None
        latest_scan_id = max(scan_ids)
        return self.analyze_scan_findings(latest_scan_id)
