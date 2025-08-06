"""
Simple in-memory cache management for Cafe Pentagon Chatbot
"""

import json
import time
from typing import Any, Optional, Union, Dict, List
from src.config.settings import get_settings
from src.config.constants import CACHE_TTL, CACHE_KEYS
from src.utils.logger import get_logger, log_performance, LoggerMixin


class SimpleCacheManager(LoggerMixin):
    """
    Simple in-memory cache manager for conversation persistence and data caching
    """
    
    def __init__(self):
        """Initialize cache manager with in-memory storage"""
        self.settings = get_settings()
        self._cache = {}
        self._expiry_times = {}
        self.logger.info("simple_cache_manager_initialized")
    
    @log_performance
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in cache with optional TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._cache[key] = value
            if ttl:
                self._expiry_times[key] = time.time() + ttl
            else:
                self._expiry_times[key] = None
            
            self.logger.debug("cache_set", key=key, ttl=ttl)
            return True
            
        except Exception as e:
            self.logger.error("cache_set_failed", key=key, error=str(e))
            return False
    
    @log_performance
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from cache
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        try:
            # Check if key exists and is not expired
            if key not in self._cache:
                self.logger.debug("cache_miss", key=key)
                return default
            
            # Check expiration
            expiry_time = self._expiry_times.get(key)
            if expiry_time and time.time() > expiry_time:
                # Key has expired, remove it
                del self._cache[key]
                del self._expiry_times[key]
                self.logger.debug("cache_expired", key=key)
                return default
            
            value = self._cache[key]
            self.logger.debug("cache_hit", key=key)
            return value
            
        except Exception as e:
            self.logger.error("cache_get_failed", key=key, error=str(e))
            return default
    
    @log_performance
    def delete(self, key: str) -> bool:
        """
        Delete a key from cache
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if key in self._cache:
                del self._cache[key]
                if key in self._expiry_times:
                    del self._expiry_times[key]
                self.logger.debug("cache_delete", key=key)
                return True
            return False
            
        except Exception as e:
            self.logger.error("cache_delete_failed", key=key, error=str(e))
            return False
    
    @log_performance
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            if key not in self._cache:
                return False
            
            # Check expiration
            expiry_time = self._expiry_times.get(key)
            if expiry_time and time.time() > expiry_time:
                # Key has expired, remove it
                del self._cache[key]
                del self._expiry_times[key]
                return False
            
            return True
            
        except Exception as e:
            self.logger.error("cache_exists_failed", key=key, error=str(e))
            return False
    
    @log_performance
    def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration time for a key
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if key in self._cache:
                self._expiry_times[key] = time.time() + ttl
                self.logger.debug("cache_expire", key=key, ttl=ttl)
                return True
            return False
            
        except Exception as e:
            self.logger.error("cache_expire_failed", key=key, error=str(e))
            return False
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile from cache
        
        Args:
            user_id: User ID
            
        Returns:
            User profile or None
        """
        key = CACHE_KEYS["user_profile"].format(user_id=user_id)
        return self.get(key)
    
    def set_user_profile(self, user_id: str, profile: Dict[str, Any]) -> bool:
        """
        Set user profile in cache
        
        Args:
            user_id: User ID
            profile: User profile data
            
        Returns:
            True if successful, False otherwise
        """
        key = CACHE_KEYS["user_profile"].format(user_id=user_id)
        ttl = CACHE_TTL["user_profile"]
        return self.set(key, profile, ttl)
    
    def get_conversation(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get conversation history from cache
        
        Args:
            user_id: User ID
            
        Returns:
            Conversation history or None
        """
        key = CACHE_KEYS["conversation"].format(user_id=user_id)
        return self.get(key)
    
    def set_conversation(self, user_id: str, conversation: List[Dict[str, Any]]) -> bool:
        """
        Set conversation history in cache
        
        Args:
            user_id: User ID
            conversation: Conversation history
            
        Returns:
            True if successful, False otherwise
        """
        key = CACHE_KEYS["conversation"].format(user_id=user_id)
        ttl = CACHE_TTL["conversation"]
        return self.set(key, conversation, ttl)
    
    def add_message_to_conversation(self, user_id: str, message: Dict[str, Any]) -> bool:
        """
        Add a message to conversation history
        
        Args:
            user_id: User ID
            message: Message to add
            
        Returns:
            True if successful, False otherwise
        """
        conversation = self.get_conversation(user_id) or []
        conversation.append(message)
        
        # Limit conversation length
        max_length = self.settings.max_conversation_length
        if len(conversation) > max_length:
            conversation = conversation[-max_length:]
        
        return self.set_conversation(user_id, conversation)
    
    def clear_conversation(self, user_id: str) -> bool:
        """
        Clear conversation history for a user
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        key = CACHE_KEYS["conversation"].format(user_id=user_id)
        return self.delete(key)
    
    def get_menu_cache(self) -> Optional[Dict[str, Any]]:
        """Get menu cache"""
        return self.get(CACHE_KEYS["menu_cache"])
    
    def set_menu_cache(self, menu_data: Dict[str, Any]) -> bool:
        """Set menu cache"""
        ttl = CACHE_TTL["menu_cache"]
        return self.set(CACHE_KEYS["menu_cache"], menu_data, ttl)
    
    def get_faq_cache(self) -> Optional[Dict[str, Any]]:
        """Get FAQ cache"""
        return self.get(CACHE_KEYS["faq_cache"])
    
    def set_faq_cache(self, faq_data: Dict[str, Any]) -> bool:
        """Set FAQ cache"""
        ttl = CACHE_TTL["faq_cache"]
        return self.set(CACHE_KEYS["faq_cache"], faq_data, ttl)
    
    def clear_all_caches(self) -> bool:
        """
        Clear all application caches
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self._cache.clear()
            self._expiry_times.clear()
            self.logger.info("all_caches_cleared")
            return True
            
        except Exception as e:
            self.logger.error("clear_all_caches_failed", error=str(e))
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Cache statistics
        """
        try:
            # Clean expired entries
            current_time = time.time()
            expired_keys = [
                key for key, expiry_time in self._expiry_times.items()
                if expiry_time and current_time > expiry_time
            ]
            
            for key in expired_keys:
                if key in self._cache:
                    del self._cache[key]
                if key in self._expiry_times:
                    del self._expiry_times[key]
            
            return {
                "total_keys": len(self._cache),
                "expired_keys_cleaned": len(expired_keys),
                "memory_usage": "In-memory cache"
            }
            
        except Exception as e:
            self.logger.error("get_cache_stats_failed", error=str(e))
            return {}
    
    def health_check(self) -> bool:
        """
        Perform health check on cache
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Simple health check - try to set and get a test value
            test_key = "_health_check"
            test_value = "ok"
            self.set(test_key, test_value, ttl=1)
            result = self.get(test_key) == test_value
            self.delete(test_key)
            return result
            
        except Exception as e:
            self.logger.error("cache_health_check_failed", error=str(e))
            return False
    
    def close(self):
        """Close cache manager"""
        try:
            self._cache.clear()
            self._expiry_times.clear()
            self.logger.info("cache_manager_closed")
            
        except Exception as e:
            self.logger.error("cache_close_failed", error=str(e))


# Global cache manager instance
_cache_manager: Optional[SimpleCacheManager] = None


def get_cache_manager() -> SimpleCacheManager:
    """Get or create cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = SimpleCacheManager()
    return _cache_manager


def close_cache_manager():
    """Close cache manager"""
    global _cache_manager
    if _cache_manager:
        _cache_manager.close()
        _cache_manager = None 
