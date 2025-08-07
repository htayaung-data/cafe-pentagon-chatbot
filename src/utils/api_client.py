"""
API Client with robust retry mechanisms and circuit breaker patterns
Handles OpenAI API failures gracefully with exponential backoff and fallbacks
"""

import asyncio
import time
from typing import Dict, Any, Optional, Callable, TypeVar, Generic
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type,
    before_sleep_log,
    after_log
)
from openai import OpenAI, RateLimitError, APIError, APIConnectionError, APITimeoutError
from src.config.settings import get_settings
from src.utils.logger import get_logger

logger = get_logger("api_client")

T = TypeVar('T')

class APIClientError(Exception):
    """Custom API client error"""
    pass

class QuotaExceededError(APIClientError):
    """Raised when API quota is exceeded"""
    pass

class CircuitBreaker:
    """Simple circuit breaker pattern implementation"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise APIClientError("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            
            raise e

class OpenAIAPIClient:
    """
    Robust OpenAI API client with retry mechanisms and circuit breakers
    """
    
    def __init__(self):
        """Initialize OpenAI API client"""
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        
        # Circuit breakers for different operations
        self.chat_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
        self.embedding_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
        
        logger.info("openai_api_client_initialized")
    
    def _should_retry_exception(self, exception: Exception) -> bool:
        """Determine if exception should trigger a retry"""
        if isinstance(exception, RateLimitError):
            # Don't retry on rate limit errors (quota exceeded)
            return False
        elif isinstance(exception, (APIConnectionError, APITimeoutError)):
            # Retry on connection and timeout errors
            return True
        elif isinstance(exception, APIError):
            # Retry on general API errors except quota issues
            error_message = str(exception).lower()
            if "quota" in error_message or "insufficient_quota" in error_message:
                return False
            return True
        return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((APIConnectionError, APITimeoutError, APIError)),
        before_sleep=before_sleep_log(logger, "INFO"),
        after=after_log(logger, "INFO")
    )
    async def chat_completion(self, messages: list, **kwargs) -> Dict[str, Any]:
        """
        Make chat completion request with retry logic
        """
        try:
            return self.chat_circuit_breaker.call(
                self.client.chat.completions.create,
                messages=messages,
                **kwargs
            )
        except RateLimitError as e:
            logger.error("openai_quota_exceeded", error=str(e))
            raise QuotaExceededError(f"OpenAI quota exceeded: {str(e)}")
        except Exception as e:
            logger.error("openai_chat_completion_failed", error=str(e))
            raise APIClientError(f"Chat completion failed: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((APIConnectionError, APITimeoutError, APIError)),
        before_sleep=before_sleep_log(logger, "INFO"),
        after=after_log(logger, "INFO")
    )
    async def create_embeddings(self, input_text: str, model: str = "text-embedding-ada-002") -> Dict[str, Any]:
        """
        Create embeddings with retry logic
        """
        try:
            return self.embedding_circuit_breaker.call(
                self.client.embeddings.create,
                input=input_text,
                model=model
            )
        except RateLimitError as e:
            logger.error("openai_embedding_quota_exceeded", error=str(e))
            raise QuotaExceededError(f"OpenAI embedding quota exceeded: {str(e)}")
        except Exception as e:
            logger.error("openai_embedding_failed", error=str(e))
            raise APIClientError(f"Embedding creation failed: {str(e)}")
    
    def is_quota_exceeded(self, exception: Exception) -> bool:
        """Check if exception indicates quota exceeded"""
        if isinstance(exception, QuotaExceededError):
            return True
        if isinstance(exception, RateLimitError):
            return True
        if isinstance(exception, APIError):
            error_message = str(exception).lower()
            return "quota" in error_message or "insufficient_quota" in error_message
        return False

class FallbackManager:
    """
    Manages fallback strategies when AI services are unavailable
    """
    
    def __init__(self):
        """Initialize fallback manager"""
        self.cache = {}
        self.logger = get_logger("fallback_manager")
    
    async def get_cached_response(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available"""
        return self.cache.get(key)
    
    async def cache_response(self, key: str, response: Dict[str, Any], ttl: int = 3600):
        """Cache response with TTL"""
        self.cache[key] = {
            "data": response,
            "timestamp": time.time(),
            "ttl": ttl
        }
    
    def is_cache_valid(self, key: str) -> bool:
        """Check if cached response is still valid"""
        if key not in self.cache:
            return False
        
        cached_data = self.cache[key]
        return time.time() - cached_data["timestamp"] < cached_data["ttl"]
    
    def get_fallback_intent(self, message: str, language: str) -> Dict[str, Any]:
        """Get fallback intent classification - NO PATTERN MATCHING"""
        # No pattern matching - return unknown intent
        return {
            "intent": "unknown",
            "confidence": 0.5,
            "entities": {},
            "reasoning": "No pattern matching - LLM should handle intent",
            "priority": 10
        }

# Global instances
_openai_client = None
_fallback_manager = None

def get_openai_client() -> OpenAIAPIClient:
    """Get OpenAI API client instance"""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAIAPIClient()
    return _openai_client

def get_fallback_manager() -> FallbackManager:
    """Get fallback manager instance"""
    global _fallback_manager
    if _fallback_manager is None:
        _fallback_manager = FallbackManager()
    return _fallback_manager 