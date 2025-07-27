"""
Cache management for Cafe Pentagon Chatbot using Redis
"""

import json
import pickle
from typing import Any, Optional, Union, Dict, List
import redis
from src.config.settings import get_settings
from src.config.constants import CACHE_TTL, CACHE_KEYS
from src.utils.logger import get_logger, log_performance, LoggerMixin


class CacheManager(LoggerMixin):
    """
    Redis cache manager for conversation persistence and data caching
    """
    
    def __init__(self):
        """Initialize cache manager with Redis connection"""
        self.settings = get_settings()
        self.redis_client = self._create_redis_connection()
        self._fallback_cache = {} if self.redis_client is None else None
        self.logger.info("cache_manager_initialized", redis_available=self.redis_client is not None)
    
    def _create_redis_connection(self) -> redis.Redis:
        """Create Redis connection"""
        try:
            # Parse Redis URL
            redis_url = self.settings.redis_url
            if redis_url.startswith('redis://'):
                # Extract components from URL
                url_parts = redis_url.replace('redis://', '').split('@')
                if len(url_parts) > 1:
                    # URL with password
                    auth, host_port = url_parts
                    password = auth.split(':')[1] if ':' in auth else None
                    host, port = host_port.split(':')
                else:
                    # URL without password
                    host_port = url_parts[0]
                    password = None
                    host, port = host_port.split(':')
                
                port = int(port) if port else 6379
            else:
                # Fallback to default values
                host = 'localhost'
                port = 6379
                password = None
            
            # Create Redis client
            client = redis.Redis(
                host=host,
                port=port,
                password=password or self.settings.redis_password,
                db=self.settings.redis_db,
                decode_responses=False,  # Keep as bytes for pickle compatibility
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            client.ping()
            self.logger.info("redis_connection_established", host=host, port=port)
            return client
            
        except Exception as e:
            self.logger.error("redis_connection_failed", error=str(e))
            self.logger.warning("redis_fallback_to_memory", message="Using in-memory fallback")
            return None
    
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
        # Use fallback cache if Redis is not available
        if self.redis_client is None:
            if self._fallback_cache is not None:
                self._fallback_cache[key] = value
                self.logger.debug("cache_set_fallback", key=key, ttl=ttl)
                return True
            return False
        
        try:
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, ensure_ascii=False)
            else:
                serialized_value = pickle.dumps(value)
            
            # Set in Redis
            result = self.redis_client.set(key, serialized_value, ex=ttl)
            
            self.logger.debug(
                "cache_set",
                key=key,
                ttl=ttl,
                success=bool(result)
            )
            
            return bool(result)
            
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
        # Use fallback cache if Redis is not available
        if self.redis_client is None:
            if self._fallback_cache is not None:
                value = self._fallback_cache.get(key, default)
                if value is not default:
                    self.logger.debug("cache_hit_fallback", key=key)
                else:
                    self.logger.debug("cache_miss_fallback", key=key)
                return value
            return default
        
        try:
            value = self.redis_client.get(key)
            
            if value is None:
                self.logger.debug("cache_miss", key=key)
                return default
            
            # Try to deserialize as JSON first, then pickle
            try:
                deserialized_value = json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                try:
                    deserialized_value = pickle.loads(value)
                except pickle.UnpicklingError:
                    self.logger.warning("cache_deserialization_failed", key=key)
                    return default
            
            self.logger.debug("cache_hit", key=key)
            return deserialized_value
            
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
            result = self.redis_client.delete(key)
            self.logger.debug("cache_delete", key=key, success=bool(result))
            return bool(result)
            
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
            result = self.redis_client.exists(key)
            return bool(result)
            
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
            result = self.redis_client.expire(key, ttl)
            self.logger.debug("cache_expire", key=key, ttl=ttl, success=bool(result))
            return bool(result)
            
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
            # Clear specific cache keys
            cache_keys = [
                CACHE_KEYS["menu_cache"],
                CACHE_KEYS["faq_cache"],
                CACHE_KEYS["reservation_cache"],
                CACHE_KEYS["event_cache"],
                CACHE_KEYS["job_cache"]
            ]
            
            for key in cache_keys:
                self.delete(key)
            
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
            info = self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
            
        except Exception as e:
            self.logger.error("get_cache_stats_failed", error=str(e))
            return {}
    
    def health_check(self) -> bool:
        """
        Perform health check on Redis connection
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            self.redis_client.ping()
            return True
            
        except Exception as e:
            self.logger.error("redis_health_check_failed", error=str(e))
            return False
    
    def close(self):
        """Close Redis connection"""
        try:
            self.redis_client.close()
            self.logger.info("redis_connection_closed")
            
        except Exception as e:
            self.logger.error("redis_close_failed", error=str(e))


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def close_cache_manager():
    """Close cache manager"""
    global _cache_manager
    if _cache_manager:
        _cache_manager.close()
        _cache_manager = None 