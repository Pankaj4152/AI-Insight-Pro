"""
AI-Powered Pattern Detection Module
Enhanced pattern recognition with ML-based confidence scoring and unknown PII detection
"""

import asyncio
import re
import logging
import yaml
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
from datetime import datetime
from collections import Counter
import joblib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PatternConfidence(Enum):
    """Confidence levels for pattern detection"""
    VERY_LOW = (0.0, 0.3)
    LOW = (0.3, 0.5)
    MEDIUM = (0.5, 0.7)
    HIGH = (0.7, 0.9)
    VERY_HIGH = (0.9, 1.0)


class RiskLevel(Enum):
    """Risk levels for detected patterns"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PatternMatch:
    """Enhanced pattern match with AI metadata"""
    text: str
    data_type: str
    pattern_name: str
    confidence_score: float
    start_position: int
    end_position: int
    context: str
    validation_passed: bool
    risk_level: RiskLevel
    ml_features: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    false_positive_score: float = 0.0


@dataclass
class DetectionResult:
    """Complete detection result with enhanced analytics"""
    total_matches: int
    matches_by_confidence: Dict[str, List[PatternMatch]]
    matches_by_type: Dict[str, List[PatternMatch]]
    unknown_patterns: List[PatternMatch]
    false_positive_candidates: List[PatternMatch]
    processing_time: float
    data_analyzed_bytes: int
    risk_summary: Dict[str, int]


class AIPatternDetector:
    """
    AI-Enhanced Pattern Detection Engine
    Combines existing regex patterns with ML-based validation and unknown pattern discovery
    """
    
    def __init__(self, regex_patterns_path: str, config: Optional[Dict] = None):
        """
        Initialize the AI pattern detector
        
        Args:
            regex_patterns_path: Path to existing regex patterns YAML file
            config: Configuration dictionary
        """
        self.config = config or self._default_config()
        self.regex_patterns = self._load_regex_patterns(regex_patterns_path)
        self.custom_patterns = {}
        self.ml_models = {}
        self.pattern_stats = {}
        self.false_positive_history = []
        
        # Initialize ML components
        self._initialize_ml_components()
        
        logger.info(f"AI Pattern Detector initialized with {len(self.regex_patterns)} patterns")
    
    def _default_config(self) -> Dict:
        """Default configuration for the detector"""
        return {
            'confidence_threshold': 0.7,
            'enable_ml_validation': True,
            'enable_unknown_detection': True,
            'enable_context_analysis': True,
            'context_window_size': 100,
            'false_positive_threshold': 0.3,
            'batch_size': 1000,
            'enable_learning': True,
            'unknown_pattern_min_confidence': 0.8,
            'risk_weights': {
                'critical': ['aadhaar', 'pan', 'credit_card', 'passport'],
                'high': ['phone', 'email', 'driving_license', 'bank_account'],
                'medium': ['voter_id', 'ifsc', 'dob'],
                'low': ['name', 'address', 'ip_address']
            }
        }
    
    def _load_regex_patterns(self, patterns_path: str) -> List[Dict]:
        """Load existing regex patterns from YAML file"""
        try:
            with open(patterns_path, 'r') as f:
                patterns = yaml.safe_load(f)
            logger.info(f"Loaded {len(patterns)} regex patterns")
            return patterns
        except Exception as e:
            logger.error(f"Failed to load regex patterns: {e}")
            return []
    
    def _initialize_ml_components(self):
        """Initialize machine learning components"""
        # Feature extractors for different pattern types
        self.feature_extractors = {
            'text_features': self._extract_text_features,
            'context_features': self._extract_context_features,
            'pattern_features': self._extract_pattern_features
        }
        
        # Initialize confidence scorer
        self.confidence_scorer = MLConfidenceScorer(self.config)
        
        # Initialize unknown pattern detector
        self.unknown_detector = UnknownPatternDetector(self.config)
        
        # Initialize false positive reducer
        self.fp_reducer = FalsePositiveReducer(self.config)
    
    async def detect_patterns(self, 
                            text: str, 
                            data_types: Optional[List[str]] = None,
                            enable_unknown_detection: bool = True) -> DetectionResult:
        """
        Main pattern detection method with AI enhancements
        
        Args:
            text: Input text to analyze
            data_types: Specific data types to detect (None = all)
            enable_unknown_detection: Whether to detect unknown patterns
            
        Returns:
            Enhanced detection result with confidence scores and risk assessment
        """
        start_time = asyncio.get_event_loop().time()
        
        # Filter patterns by data types if specified
        patterns_to_use = self.regex_patterns
        if data_types:
            patterns_to_use = [p for p in self.regex_patterns if p['data_type'] in data_types]
        
        all_matches = []
        
        # 1. Traditional regex-based detection with AI enhancement
        for pattern_config in patterns_to_use:
            matches = await self._detect_with_pattern(text, pattern_config)
            all_matches.extend(matches)
        
        # 2. Custom pattern detection
        for custom_pattern in self.custom_patterns.values():
            matches = await self._detect_with_pattern(text, custom_pattern)
            all_matches.extend(matches)
        
        # 3. Unknown pattern detection using ML
        unknown_matches = []
        if enable_unknown_detection and self.config['enable_unknown_detection']:
            unknown_matches = await self.unknown_detector.detect_unknown_patterns(text)
        
        # 4. Enhance all matches with ML confidence scoring
        enhanced_matches = await self._enhance_matches_with_ml(text, all_matches)
        
        # 5. Reduce false positives
        filtered_matches = await self.fp_reducer.filter_false_positives(enhanced_matches)
        
        # 6. Process unknown patterns
        enhanced_unknown = await self._process_unknown_patterns(text, unknown_matches)
        
        # 7. Generate comprehensive result
        processing_time = asyncio.get_event_loop().time() - start_time
        
        return self._generate_detection_result(
            filtered_matches, enhanced_unknown, processing_time, len(text)
        )
    
    async def _detect_with_pattern(self, text: str, pattern_config: Dict) -> List[PatternMatch]:
        """Detect patterns using regex with initial confidence scoring"""
        regex_pattern = pattern_config['regex_pattern']
        data_type = pattern_config['data_type']
        pattern_name = pattern_config['pattern_name']
        
        matches = []
        
        try:
            for match in re.finditer(regex_pattern, text, re.IGNORECASE):
                matched_text = match.group()
                start_pos = match.start()
                end_pos = match.end()
                
                # Extract context
                context = self._extract_context(text, start_pos, end_pos)
                
                # Basic validation
                validation_passed = self._validate_pattern_match(matched_text, data_type)
                
                # Initial confidence based on validation
                initial_confidence = 0.8 if validation_passed else 0.4
                
                # Determine risk level
                risk_level = self._determine_risk_level(data_type)
                
                pattern_match = PatternMatch(
                    text=matched_text,
                    data_type=data_type,
                    pattern_name=pattern_name,
                    confidence_score=initial_confidence,
                    start_position=start_pos,
                    end_position=end_pos,
                    context=context,
                    validation_passed=validation_passed,
                    risk_level=risk_level,
                    metadata={
                        'regex_pattern': regex_pattern,
                        'detection_method': 'regex'
                    }
                )
                
                matches.append(pattern_match)
                
        except re.error as e:
            logger.error(f"Regex error for pattern {pattern_name}: {e}")
        
        return matches
    
    async def _enhance_matches_with_ml(self, text: str, matches: List[PatternMatch]) -> List[PatternMatch]:
        """Enhance matches with ML-based confidence scoring"""
        enhanced_matches = []
        
        for match in matches:
            # Extract ML features
            ml_features = await self._extract_all_features(match, text)
            match.ml_features = ml_features
            
            # Calculate AI-enhanced confidence
            enhanced_confidence = await self.confidence_scorer.calculate_confidence(match, text)
            match.confidence_score = enhanced_confidence
            
            # Update risk level based on enhanced confidence
            if enhanced_confidence < 0.5:
                # Lower confidence reduces risk level
                match.risk_level = self._lower_risk_level(match.risk_level)
            
            enhanced_matches.append(match)
        
        return enhanced_matches
    
    async def _extract_all_features(self, match: PatternMatch, text: str) -> Dict[str, float]:
        """Extract comprehensive ML features for a match"""
        features = {}
        
        # Text-based features
        text_features = self.feature_extractors['text_features'](match.text)
        features.update(text_features)
        
        # Context-based features
        context_features = self.feature_extractors['context_features'](match.context, match.data_type)
        features.update(context_features)
        
        # Pattern-specific features
        pattern_features = self.feature_extractors['pattern_features'](match.text, match.data_type)
        features.update(pattern_features)
        
        return features
    
    def _extract_text_features(self, text: str) -> Dict[str, float]:
        """Extract text-based features for ML analysis"""
        if not text:
            return {}
        
        return {
            'length': len(text),
            'digit_ratio': sum(c.isdigit() for c in text) / len(text),
            'alpha_ratio': sum(c.isalpha() for c in text) / len(text),
            'upper_ratio': sum(c.isupper() for c in text) / len(text),
            'special_char_ratio': sum(not c.isalnum() for c in text) / len(text),
            'has_digits': float(any(c.isdigit() for c in text)),
            'has_letters': float(any(c.isalpha() for c in text)),
            'has_special_chars': float(any(not c.isalnum() for c in text)),
            'entropy': self._calculate_entropy(text),
            'unique_char_ratio': len(set(text)) / len(text)
        }
    
    def _extract_context_features(self, context: str, data_type: str) -> Dict[str, float]:
        """Extract context-based features"""
        context_keywords = {
            'phone': ['phone', 'tel', 'mobile', 'number', 'contact', 'call'],
            'email': ['email', 'mail', '@', 'contact', 'address'],
            'aadhaar': ['aadhaar', 'aadhar', 'uid', 'unique', 'identity'],
            'pan': ['pan', 'permanent', 'account', 'number', 'income', 'tax'],
            'credit_card': ['card', 'credit', 'visa', 'mastercard', 'amex', 'payment'],
            'name': ['name', 'firstname', 'lastname', 'full', 'customer'],
            'address': ['address', 'street', 'city', 'state', 'pincode', 'location']
        }
        
        keywords = context_keywords.get(data_type, [])
        context_lower = context.lower()
        
        keyword_matches = sum(1 for keyword in keywords if keyword in context_lower)
        
        return {
            'context_relevance': min(keyword_matches / max(len(keywords), 1), 1.0),
            'context_length': len(context),
            'keyword_density': keyword_matches / max(len(context.split()), 1)
        }
    
    def _extract_pattern_features(self, text: str, data_type: str) -> Dict[str, float]:
        """Extract pattern-specific features"""
        features = {}
        
        if data_type == 'email':
            features.update({
                'has_at_symbol': float('@' in text),
                'has_domain': float('.' in text.split('@')[-1] if '@' in text else False),
                'valid_tld': float(self._has_valid_tld(text))
            })
        elif data_type == 'phone':
            features.update({
                'has_country_code': float(text.startswith('+')),
                'digit_count': sum(c.isdigit() for c in text),
                'has_separators': float(any(c in text for c in ['-', ' ', '.', '(', ')']))
            })
        elif data_type == 'credit_card':
            features.update({
                'luhn_valid': float(self._validate_luhn(text)),
                'length_valid': float(13 <= len(re.sub(r'\D', '', text)) <= 19),
                'issuer_pattern': self._detect_card_issuer_score(text)
            })
        elif data_type == 'aadhaar':
            digits = re.sub(r'\D', '', text)
            features.update({
                'digit_count': len(digits),
                'has_spaces': float(' ' in text),
                'valid_format': float(len(digits) == 12)
            })
        elif data_type == 'pan':
            features.update({
                'alpha_count': sum(c.isalpha() for c in text),
                'digit_count': sum(c.isdigit() for c in text),
                'format_valid': float(len(text) == 10 and text[:5].isalpha() and text[5:9].isdigit() and text[9].isalpha())
            })
        
        return features
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text"""
        if not text:
            return 0.0
        
        counts = Counter(text)
        probabilities = [count / len(text) for count in counts.values()]
        entropy = -sum(p * np.log2(p) for p in probabilities if p > 0)
        return entropy / 8.0  # Normalize by max possible entropy for byte
    
    def _validate_pattern_match(self, text: str, data_type: str) -> bool:
        """Enhanced validation for pattern matches"""
        validators = {
            'email': self._validate_email,
            'phone': self._validate_phone,
            'credit_card': self._validate_credit_card,
            'aadhaar': self._validate_aadhaar,
            'pan': self._validate_pan,
            'ip_address': self._validate_ip_address
        }
        
        validator = validators.get(data_type)
        if validator:
            return validator(text)
        
        return True  # Default to valid for unknown types
    
    def _validate_email(self, email: str) -> bool:
        """Enhanced email validation"""
        if '@' not in email or email.count('@') != 1:
            return False
        
        local, domain = email.split('@')
        if not local or not domain or '.' not in domain:
            return False
        
        # Check for valid TLD
        return self._has_valid_tld(email)
    
    def _validate_phone(self, phone: str) -> bool:
        """Enhanced phone validation"""
        digits = re.sub(r'\D', '', phone)
        return 10 <= len(digits) <= 15
    
    def _validate_credit_card(self, card: str) -> bool:
        """Enhanced credit card validation with Luhn algorithm"""
        return self._validate_luhn(card)
    
    def _validate_luhn(self, card: str) -> bool:
        """Luhn algorithm validation"""
        digits = [int(c) for c in card if c.isdigit()]
        if len(digits) < 13:
            return False
        
        checksum = 0
        is_even = False
        
        for digit in reversed(digits):
            if is_even:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
            is_even = not is_even
        
        return checksum % 10 == 0
    
    def _validate_aadhaar(self, aadhaar: str) -> bool:
        """Enhanced Aadhaar validation"""
        digits = re.sub(r'\D', '', aadhaar)
        if len(digits) != 12:
            return False
        
        # Aadhaar should not start with 0 or 1
        return not digits.startswith(('0', '1'))
    
    def _validate_pan(self, pan: str) -> bool:
        """Enhanced PAN validation"""
        if len(pan) != 10:
            return False
        
        return (pan[:5].isalpha() and 
                pan[5:9].isdigit() and 
                pan[9].isalpha())
    
    def _validate_ip_address(self, ip: str) -> bool:
        """Enhanced IP address validation"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False
    
    def _has_valid_tld(self, email: str) -> bool:
        """Check if email has valid top-level domain"""
        if '@' not in email:
            return False
        
        domain = email.split('@')[-1]
        if '.' not in domain:
            return False
        
        tld = domain.split('.')[-1].lower()
        common_tlds = {
            'com', 'org', 'net', 'edu', 'gov', 'mil', 'int', 'co', 'in', 'uk', 'de', 'fr'
        }
        
        return tld in common_tlds or (2 <= len(tld) <= 4 and tld.isalpha())
    
    def _detect_card_issuer_score(self, card: str) -> float:
        """Detect credit card issuer pattern and return confidence score"""
        digits = re.sub(r'\D', '', card)
        if not digits:
            return 0.0
        
        issuer_patterns = {
            'visa': r'^4',
            'mastercard': r'^5[1-5]',
            'amex': r'^3[47]',
            'discover': r'^6(?:011|5)'
        }
        
        for issuer, pattern in issuer_patterns.items():
            if re.match(pattern, digits):
                return 1.0
        
        return 0.5  # Unknown issuer but could be valid
    
    def _extract_context(self, text: str, start: int, end: int) -> str:
        """Extract context around a match"""
        window_size = self.config['context_window_size']
        context_start = max(0, start - window_size // 2)
        context_end = min(len(text), end + window_size // 2)
        return text[context_start:context_end]
    
    def _determine_risk_level(self, data_type: str) -> RiskLevel:
        """Determine risk level based on data type"""
        risk_weights = self.config['risk_weights']
        
        for risk_level, types in risk_weights.items():
            if data_type in types:
                return RiskLevel(risk_level)
        
        return RiskLevel.MEDIUM  # Default risk level
    
    def _lower_risk_level(self, current_risk: RiskLevel) -> RiskLevel:
        """Lower the risk level by one step"""
        risk_order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        current_index = risk_order.index(current_risk)
        return risk_order[max(0, current_index - 1)]
    
    async def _process_unknown_patterns(self, text: str, unknown_matches: List[Dict]) -> List[PatternMatch]:
        """Process unknown patterns detected by ML"""
        processed_unknowns = []
        
        for unknown in unknown_matches:
            if unknown['confidence'] >= self.config['unknown_pattern_min_confidence']:
                pattern_match = PatternMatch(
                    text=unknown['text'],
                    data_type='unknown',
                    pattern_name='ml_detected',
                    confidence_score=unknown['confidence'],
                    start_position=unknown['start'],
                    end_position=unknown['end'],
                    context=unknown['context'],
                    validation_passed=True,
                    risk_level=RiskLevel.HIGH,  # Unknown patterns are high risk
                    ml_features=unknown.get('features', {}),
                    metadata={
                        'detection_method': 'ml_unknown',
                        'ml_type': unknown.get('predicted_type', 'unknown')
                    }
                )
                processed_unknowns.append(pattern_match)
        
        return processed_unknowns
    
    def _generate_detection_result(self, 
                                 matches: List[PatternMatch], 
                                 unknown_matches: List[PatternMatch],
                                 processing_time: float, 
                                 data_size: int) -> DetectionResult:
        """Generate comprehensive detection result"""
        
        all_matches = matches + unknown_matches
        
        # Categorize by confidence
        matches_by_confidence = {
            'very_high': [],
            'high': [],
            'medium': [],
            'low': [],
            'very_low': []
        }
        
        for match in all_matches:
            if match.confidence_score >= 0.9:
                matches_by_confidence['very_high'].append(match)
            elif match.confidence_score >= 0.7:
                matches_by_confidence['high'].append(match)
            elif match.confidence_score >= 0.5:
                matches_by_confidence['medium'].append(match)
            elif match.confidence_score >= 0.3:
                matches_by_confidence['low'].append(match)
            else:
                matches_by_confidence['very_low'].append(match)
        
        # Categorize by type
        matches_by_type = {}
        for match in all_matches:
            data_type = match.data_type
            if data_type not in matches_by_type:
                matches_by_type[data_type] = []
            matches_by_type[data_type].append(match)
        
        # Risk summary
        risk_summary = {}
        for match in all_matches:
            risk_level = match.risk_level.value
            risk_summary[risk_level] = risk_summary.get(risk_level, 0) + 1
        
        # False positive candidates (low confidence matches)
        false_positive_candidates = matches_by_confidence['very_low'] + matches_by_confidence['low']
        
        return DetectionResult(
            total_matches=len(all_matches),
            matches_by_confidence=matches_by_confidence,
            matches_by_type=matches_by_type,
            unknown_patterns=unknown_matches,
            false_positive_candidates=false_positive_candidates,
            processing_time=processing_time,
            data_analyzed_bytes=data_size,
            risk_summary=risk_summary
        )
    
    def add_custom_pattern(self, 
                          name: str, 
                          regex_pattern: str, 
                          data_type: str, 
                          description: str = "") -> bool:
        """
        Add a custom pattern for detection
        
        Args:
            name: Pattern name
            regex_pattern: Regular expression pattern
            data_type: Type of data this pattern detects
            description: Optional description
            
        Returns:
            True if pattern was added successfully
        """
        try:
            # Test the regex pattern
            re.compile(regex_pattern)
            
            custom_pattern = {
                'pattern_name': name,
                'regex_pattern': regex_pattern,
                'data_type': data_type,
                'description': description,
                'created_at': datetime.now().isoformat(),
                'custom': True
            }
            
            self.custom_patterns[name] = custom_pattern
            logger.info(f"Added custom pattern: {name}")
            return True
            
        except re.error as e:
            logger.error(f"Invalid regex pattern {name}: {e}")
            return False
    
    def remove_custom_pattern(self, name: str) -> bool:
        """Remove a custom pattern"""
        if name in self.custom_patterns:
            del self.custom_patterns[name]
            logger.info(f"Removed custom pattern: {name}")
            return True
        return False
    
    def get_custom_patterns(self) -> Dict[str, Dict]:
        """Get all custom patterns"""
        return self.custom_patterns.copy()
    
    async def learn_from_feedback(self, 
                                match: PatternMatch, 
                                is_correct: bool, 
                                actual_type: Optional[str] = None):
        """
        Learn from user feedback to improve detection accuracy
        
        Args:
            match: Pattern match that received feedback
            is_correct: Whether the match was correctly identified
            actual_type: Actual data type if different from detected
        """
        feedback_data = {
            'match': {
                'text': match.text,
                'data_type': match.data_type,
                'confidence_score': match.confidence_score,
                'ml_features': match.ml_features
            },
            'is_correct': is_correct,
            'actual_type': actual_type,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store feedback for model improvement
        if not hasattr(self, 'feedback_history'):
            self.feedback_history = []
        
        self.feedback_history.append(feedback_data)
        
        # Update pattern statistics
        pattern_key = f"{match.data_type}_{match.pattern_name}"
        if pattern_key not in self.pattern_stats:
            self.pattern_stats[pattern_key] = {
                'total_detections': 0,
                'correct_detections': 0,
                'accuracy': 0.0
            }
        
        stats = self.pattern_stats[pattern_key]
        stats['total_detections'] += 1
        if is_correct:
            stats['correct_detections'] += 1
        stats['accuracy'] = stats['correct_detections'] / stats['total_detections']
        
        # If it's a false positive, add to history for FP reduction
        if not is_correct:
            self.false_positive_history.append(feedback_data)
        
        logger.info(f"Received feedback for {match.data_type}: correct={is_correct}")
    
    def get_pattern_statistics(self) -> Dict[str, Dict]:
        """Get accuracy statistics for all patterns"""
        return self.pattern_stats.copy()
    
    def export_detection_report(self, result: DetectionResult, output_path: str):
        """Export detection result to JSON report"""
        report = {
            'summary': {
                'total_matches': result.total_matches,
                'processing_time': result.processing_time,
                'data_analyzed_bytes': result.data_analyzed_bytes,
                'risk_summary': result.risk_summary
            },
            'matches_by_confidence': {
                level: [self._match_to_dict(match) for match in matches]
                for level, matches in result.matches_by_confidence.items()
            },
            'matches_by_type': {
                data_type: [self._match_to_dict(match) for match in matches]
                for data_type, matches in result.matches_by_type.items()
            },
            'unknown_patterns': [self._match_to_dict(match) for match in result.unknown_patterns],
            'false_positive_candidates': [self._match_to_dict(match) for match in result.false_positive_candidates],
            'generated_at': datetime.now().isoformat()
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Detection report exported to {output_path}")
    
    def _match_to_dict(self, match: PatternMatch) -> Dict:
        """Convert PatternMatch to dictionary for export"""
        return {
            'text': match.text,
            'data_type': match.data_type,
            'pattern_name': match.pattern_name,
            'confidence_score': match.confidence_score,
            'start_position': match.start_position,
            'end_position': match.end_position,
            'context': match.context,
            'validation_passed': match.validation_passed,
            'risk_level': match.risk_level.value,
            'ml_features': match.ml_features,
            'metadata': match.metadata,
            'false_positive_score': match.false_positive_score
        }


class MLConfidenceScorer:
    """ML-based confidence scoring system"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.feature_weights = {
            'validation_score': 0.3,
            'context_relevance': 0.25,
            'pattern_quality': 0.2,
            'historical_accuracy': 0.15,
            'ml_features': 0.1
        }
    
    async def calculate_confidence(self, match: PatternMatch, full_text: str) -> float:
        """Calculate ML-enhanced confidence score"""
        
        # Base validation score
        validation_score = 1.0 if match.validation_passed else 0.3
        
        # Context relevance score
        context_relevance = match.ml_features.get('context_relevance', 0.5)
        
        # Pattern quality score based on features
        pattern_quality = self._calculate_pattern_quality(match)
        
        # Historical accuracy (if available)
        historical_accuracy = self._get_historical_accuracy(match)
        
        # ML features score
        ml_score = self._calculate_ml_score(match.ml_features)
        
        # Weighted combination
        confidence = (
            validation_score * self.feature_weights['validation_score'] +
            context_relevance * self.feature_weights['context_relevance'] +
            pattern_quality * self.feature_weights['pattern_quality'] +
            historical_accuracy * self.feature_weights['historical_accuracy'] +
            ml_score * self.feature_weights['ml_features']
        )
        
        return min(1.0, max(0.0, confidence))
    
    def _calculate_pattern_quality(self, match: PatternMatch) -> float:
        """Calculate pattern quality score based on match characteristics"""
        quality_score = 0.5  # Base score
        
        # Length appropriateness
        length = len(match.text)
        if match.data_type == 'email' and 5 <= length <= 100:
            quality_score += 0.2
        elif match.data_type == 'phone' and 10 <= length <= 15:
            quality_score += 0.2
        elif match.data_type in ['aadhaar', 'pan'] and length <= 15:
            quality_score += 0.2
        
        # Character composition
        if 'entropy' in match.ml_features:
            entropy = match.ml_features['entropy']
            if 0.3 <= entropy <= 0.8:  # Good entropy range
                quality_score += 0.3
        
        return min(1.0, quality_score)
    
    def _get_historical_accuracy(self, match: PatternMatch) -> float:
        """Get historical accuracy for this pattern type"""
        # This would access stored statistics in a real implementation
        return 0.8  # Default accuracy
    
    def _calculate_ml_score(self, ml_features: Dict[str, float]) -> float:
        """Calculate score based on ML features"""
        if not ml_features:
            return 0.5
        
        # Normalize and combine key features
        feature_scores = []
        
        # Text quality features
        if 'entropy' in ml_features:
            entropy_score = min(ml_features['entropy'] / 0.8, 1.0)
            feature_scores.append(entropy_score)
        
        if 'unique_char_ratio' in ml_features:
            uniqueness_score = ml_features['unique_char_ratio']
            feature_scores.append(uniqueness_score)
        
        # Pattern-specific features
        if 'luhn_valid' in ml_features:
            feature_scores.append(ml_features['luhn_valid'])
        
        if 'has_at_symbol' in ml_features and 'has_domain' in ml_features:
            email_score = (ml_features['has_at_symbol'] + ml_features['has_domain']) / 2
            feature_scores.append(email_score)
        
        return sum(feature_scores) / max(len(feature_scores), 1) if feature_scores else 0.5


class UnknownPatternDetector:
    """ML-based unknown pattern detection"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.min_pattern_length = 3
        self.max_pattern_length = 100
    
    async def detect_unknown_patterns(self, text: str) -> List[Dict[str, Any]]:
        """Detect unknown patterns using ML techniques"""
        
        # Extract potential unknown pattern candidates
        candidates = self._extract_candidates(text)
        
        # Score candidates using ML
        scored_candidates = self._score_candidates(candidates)
        
        # Filter by confidence threshold
        filtered_candidates = [
            candidate for candidate in scored_candidates
            if candidate['confidence'] >= self.config['unknown_pattern_min_confidence']
        ]
        
        return filtered_candidates
    
    def _extract_candidates(self, text: str) -> List[Dict[str, Any]]:
        """Extract potential unknown pattern candidates"""
        candidates = []
        
        # Look for structured patterns that might be PII
        import re
        
        # Patterns that suggest structured data
        potential_patterns = [
            r'\b[A-Z]{2,4}\d{4,12}\b',  # Mixed alphanumeric IDs
            r'\b\d{6,20}\b',            # Long numeric sequences
            r'\b[A-Z0-9]{8,16}\b',      # Alphanumeric codes
            r'\b\d{2,4}[-/]\d{2,4}[-/]\d{2,4}\b',  # Date-like patterns
        ]
        
        for pattern in potential_patterns:
            for match in re.finditer(pattern, text):
                start_pos = match.start()
                end_pos = match.end()
                matched_text = match.group()
                
                # Extract context
                context_start = max(0, start_pos - 50)
                context_end = min(len(text), end_pos + 50)
                context = text[context_start:context_end]
                
                candidate = {
                    'text': matched_text,
                    'start': start_pos,
                    'end': end_pos,
                    'context': context,
                    'pattern': pattern
                }
                candidates.append(candidate)
        
        return candidates
    
    def _score_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score unknown pattern candidates"""
        scored_candidates = []
        
        for candidate in candidates:
            # Calculate various scoring factors
            text = candidate['text']
            context = candidate['context']
            
            # Structural complexity
            complexity_score = self._calculate_complexity(text)
            
            # Context suggests PII
            context_score = self._assess_context_for_pii(context)
            
            # Uniqueness (not common words)
            uniqueness_score = self._assess_uniqueness(text)
            
            # Combined confidence
            confidence = (complexity_score * 0.4 + context_score * 0.4 + uniqueness_score * 0.2)
            
            candidate['confidence'] = confidence
            candidate['features'] = {
                'complexity_score': complexity_score,
                'context_score': context_score,
                'uniqueness_score': uniqueness_score
            }
            
            scored_candidates.append(candidate)
        
        return scored_candidates
    
    def _calculate_complexity(self, text: str) -> float:
        """Calculate structural complexity of text"""
        if not text:
            return 0.0
        
        # Factors that suggest structured data
        has_mixed_case = any(c.isupper() for c in text) and any(c.islower() for c in text)
        has_digits = any(c.isdigit() for c in text)
        has_letters = any(c.isalpha() for c in text)
        has_special = any(not c.isalnum() for c in text)
        
        complexity = 0.0
        if has_mixed_case:
            complexity += 0.2
        if has_digits and has_letters:
            complexity += 0.4
        if has_special:
            complexity += 0.2
        if 6 <= len(text) <= 20:  # Good length for IDs
            complexity += 0.2
        
        return min(complexity, 1.0)
    
    def _assess_context_for_pii(self, context: str) -> float:
        """Assess if context suggests PII-related content"""
        pii_indicators = [
            'id', 'number', 'code', 'account', 'customer', 'user', 'employee',
            'personal', 'private', 'confidential', 'unique', 'identifier',
            'serial', 'reference', 'registration', 'membership', 'policy'
        ]
        
        context_lower = context.lower()
        matches = sum(1 for indicator in pii_indicators if indicator in context_lower)
        
        return min(matches / 3, 1.0)  # Normalize
    
    def _assess_uniqueness(self, text: str) -> float:
        """Assess if text appears to be unique/not common words"""
        common_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'
        }
        
        if text.lower() in common_words:
            return 0.0
        
        # Check if it looks like a structured identifier
        has_structure = bool(re.search(r'\d', text)) and bool(re.search(r'[A-Za-z]', text))
        
        return 0.8 if has_structure else 0.6


class FalsePositiveReducer:
    """ML-based false positive reduction"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.false_positive_patterns = set()
        self.learned_patterns = {}
    
    async def filter_false_positives(self, matches: List[PatternMatch]) -> List[PatternMatch]:
        """Filter out likely false positives"""
        filtered_matches = []
        
        for match in matches:
            fp_score = self._calculate_false_positive_score(match)
            match.false_positive_score = fp_score
            
            # Keep matches with low false positive scores
            if fp_score < self.config['false_positive_threshold']:
                filtered_matches.append(match)
        
        return filtered_matches
    
    def _calculate_false_positive_score(self, match: PatternMatch) -> float:
        """Calculate probability that this match is a false positive"""
        fp_score = 0.0
        
        # Check against known false positive patterns
        if match.text.lower() in self.false_positive_patterns:
            fp_score += 0.8
        
        # Context-based false positive detection
        context_fp = self._assess_context_false_positive(match.context, match.data_type)
        fp_score += context_fp * 0.5
        
        # Pattern-specific false positive checks
        pattern_fp = self._pattern_specific_fp_check(match)
        fp_score += pattern_fp * 0.3
        
        return min(fp_score, 1.0)
    
    def _assess_context_false_positive(self, context: str, data_type: str) -> float:
        """Assess false positive likelihood based on context"""
        # Contexts that suggest false positives
        fp_indicators = {
            'email': ['example.com', 'test@', 'sample@', 'dummy@'],
            'phone': ['555-1234', '000-000', '123-456'],
            'credit_card': ['1234-5678', '0000-0000', 'xxxx-xxxx'],
            'name': ['john doe', 'jane doe', 'test user', 'sample name']
        }
        
        indicators = fp_indicators.get(data_type, [])
        context_lower = context.lower()
        
        matches = sum(1 for indicator in indicators if indicator in context_lower)
        return min(matches / 2, 1.0)
    
    def _pattern_specific_fp_check(self, match: PatternMatch) -> float:
        """Pattern-specific false positive checks"""
        fp_score = 0.0
        text = match.text.lower()
        
        if match.data_type == 'email':
            # Check for obvious test emails
            if any(term in text for term in ['test', 'example', 'sample', 'dummy']):
                fp_score += 0.7
        
        elif match.data_type == 'phone':
            # Check for repeated digits or obvious test numbers
            digits = re.sub(r'\D', '', match.text)
            if len(set(digits)) <= 2:  # Too few unique digits
                fp_score += 0.8
        
        elif match.data_type == 'name':
            # Check for very common test names
            if text in ['test user', 'john doe', 'jane doe', 'sample name']:
                fp_score += 0.9
        
        return fp_score
    
    def add_false_positive_pattern(self, pattern: str):
        """Add a known false positive pattern"""
        self.false_positive_patterns.add(pattern.lower())
    
    def learn_from_feedback(self, match: PatternMatch, is_false_positive: bool):
        """Learn from false positive feedback"""
        pattern_key = f"{match.data_type}_{match.text.lower()}"
        
        if pattern_key not in self.learned_patterns:
            self.learned_patterns[pattern_key] = {
                'total_occurrences': 0,
                'false_positive_count': 0,
                'fp_rate': 0.0
            }
        
        self.learned_patterns[pattern_key]['total_occurrences'] += 1
        if is_false_positive:
            self.learned_patterns[pattern_key]['false_positive_count'] += 1
        
        # Update false positive rate
        pattern_data = self.learned_patterns[pattern_key]
        pattern_data['fp_rate'] = pattern_data['false_positive_count'] / pattern_data['total_occurrences']
        
        # If FP rate is high, add to false positive patterns
        if pattern_data['fp_rate'] > 0.7 and pattern_data['total_occurrences'] >= 3:
            self.add_false_positive_pattern(match.text)
