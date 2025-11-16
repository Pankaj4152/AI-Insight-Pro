"""
LLM Client for AI Agents
Provides LLM functionality for risk assessment and report generation
"""

import os
import logging
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class LLMClient:
    """Base LLM client class"""
    
    def __init__(self):
        self.available = False
        self.provider = "none"
    
    def chat_completion(self, messages: list, **kwargs) -> Optional[str]:
        """Generate chat completion"""
        return None

class OpenRouterLLMClient(LLMClient):
    """OpenRouter LLM client for AI analysis"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1"
        
        if self.api_key:
            self.available = True
            self.provider = "openrouter"
            logger.info("OpenRouter LLM client initialized")
        else:
            logger.warning("OpenRouter API key not found")
    
    def generate_response(self, prompt: str) -> Optional[str]:
        """Generate response using OpenRouter"""
        if not self.available:
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "openai/gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.error(f"OpenRouter API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling OpenRouter API: {e}")
            return None
    
    def chat_completion(self, messages: list, **kwargs) -> Optional[str]:
        """Generate chat completion"""
        if not self.available:
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "openai/gpt-3.5-turbo",
                "messages": messages,
                "max_tokens": kwargs.get('max_tokens', 500)
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logger.error(f"OpenRouter API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling OpenRouter API: {e}")
            return None

def get_llm_client() -> LLMClient:
    """Get LLM client instance"""
    return OpenRouterLLMClient() 