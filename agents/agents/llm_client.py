"""
LLM Client - Unified interface for different LLM providers
Supports OpenAI, Ollama, Google Gemini, and mock implementations
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMClient:
    """Unified LLM client supporting multiple providers"""
    
    def __init__(self, provider: str = "auto", **kwargs):
        """
        Initialize LLM client
        
        Args:
            provider: "openai", "ollama", "gemini", "mock", or "auto"
            **kwargs: Provider-specific configuration
        """
        self.provider = provider
        self.client = None
        self.available = False
        
        if provider == "auto":
            self.provider = self._detect_best_provider()
        
        self._initialize_client(**kwargs)
    
    def _detect_best_provider(self) -> str:
        """Detect the best available LLM provider"""    
        # Check for Google Gemini
        if os.getenv('GOOGLE_API_KEY'):
            logger.info("Google API key found")
            return "gemini"
        
        # Fallback to mock
        logger.info("No LLM provider available, using mock")
        return "mock"
    
    def _initialize_client(self, **kwargs):
        """Initialize the specific LLM client""" 
        try:
            if self.provider == "gemini":
                self._init_gemini(**kwargs)
            else:
                self._init_mock(**kwargs)
        except Exception as e:
            logger.error(f"Failed to initialize {self.provider}: {e}")
            logger.info("Falling back to mock LLM")
            self.provider = "mock"
            self._init_mock(**kwargs)
    
    def _init_gemini(self, **kwargs):
        """Initialize Google Gemini client"""
        try:
            import google.generativeai as genai
            api_key = kwargs.get('api_key') or os.getenv('GOOGLE_API_KEY')
            if not api_key:
                raise ValueError("Google API key not found")
            
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel('gemini-1.5-flash')
            self.available = True
            logger.info("Google Gemini client initialized")
        except Exception as e:
            raise Exception(f"Gemini initialization failed: {e}")
    
    def _init_mock(self, **kwargs):
        """Initialize mock client"""
        self.client = "mock"
        self.available = True
        logger.info("Mock LLM client initialized")
    
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate chat completion
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Provider-specific parameters
            
        Returns:
            Generated response text
        """
        if not self.available:
            return "LLM not available"
        
        try:
            if self.provider == "gemini":
                return self._gemini_completion(messages, **kwargs)
            else:
                return self._mock_completion(messages, **kwargs)
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            return self._mock_completion(messages, **kwargs)
    
    def _gemini_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Google Gemini chat completion"""
        prompt = self._messages_to_prompt(messages)
        response = self.client.generate_content(prompt)
        return response.text
    
    def _mock_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Mock chat completion"""
        # Extract the user query from messages
        user_message = ""
        for msg in messages:
            if msg.get('role') == 'user':
                user_message = msg.get('content', '')
                break
        
        # Generate contextual mock responses
        if 'risk' in user_message.lower():
            return json.dumps({
                "risk_assessment": "Medium",
                "risk_implications": ["Sensitive data detected", "Compliance review required"],
                "immediate_actions": ["Review findings", "Apply data protection measures"],
                "recommendations": ["Implement data masking", "Regular monitoring"]
            })
        elif 'source' in user_message.lower():
            return json.dumps({
                "source_analysis": "Multiple data sources identified",
                "priority_sources": ["Database systems", "Cloud storage"],
                "recommendations": ["Prioritize high-risk sources", "Implement scanning schedule"]
            })
        elif 'report' in user_message.lower():
            return json.dumps({
                "detailed_analysis": "Comprehensive analysis completed",
                "business_impact": ["Moderate compliance risk"],
                "technical_remediation": ["Implement access controls", "Data encryption"],
                "timeline": "Standard remediation recommended"
            })
        else:
            return json.dumps({
                "analysis": "Analysis completed using mock LLM",
                "status": "Mock response generated",
                "recommendations": ["Configure real LLM for enhanced analysis"]
            })
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to a single prompt string"""
        prompt_parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'system':
                prompt_parts.append(f"System: {content}")
            elif role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts) + "\n\nAssistant:"
    
    def get_status(self) -> Dict[str, Any]:
        """Get client status information"""
        return {
            "provider": self.provider,
            "available": self.available,
            "model": getattr(self, 'ollama_model', None) if self.provider == "ollama" else None,
            "timestamp": datetime.now().isoformat()
        }


# Convenience function for easy usage
def get_llm_client(**kwargs) -> LLMClient:
    """Get an LLM client with automatic provider detection"""
    return LLMClient(provider="auto", **kwargs)


# Test function
def test_llm_client():
    """Test the LLM client"""
    print("🧪 Testing LLM Client...")
    
    client = get_llm_client()
    status = client.get_status()
    
    print(f"✅ LLM Client Status:")
    print(f"   Provider: {status['provider']}")
    print(f"   Available: {status['available']}")
    if status['model']:
        print(f"   Model: {status['model']}")
    
    # Test chat completion
    test_messages = [
        {"role": "system", "content": "You are a cybersecurity expert."},
        {"role": "user", "content": "Analyze this scan finding: email detected in database"}
    ]
    
    response = client.chat_completion(test_messages, max_tokens=200)
    print(f"✅ Test Response: {response[:100]}...")
    
    return client


if __name__ == "__main__":
    test_llm_client()
