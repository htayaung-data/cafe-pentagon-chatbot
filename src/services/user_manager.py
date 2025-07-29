"""
User Management Service for Facebook Messenger Integration
Handles user profiles, preferences, and analytics
"""

import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from src.data.user_models import (
    UserProfile, FacebookUserProfile, UserPreferences, 
    ShoppingCart, Order, ConversationSession, UserAnalytics,
    UserSourceEnum, UserStatusEnum, LanguageEnum
)
from src.utils.logger import get_logger
from src.utils.cache import get_cache_manager
from src.services.supabase_service import SupabaseService

logger = get_logger("user_manager")


class UserManager:
    """
    Manages user profiles, preferences, and analytics for Facebook Messenger
    """
    
    def __init__(self):
        """Initialize user manager"""
        self.cache_manager = get_cache_manager()
        self.supabase_service = SupabaseService()
        logger.info("user_manager_initialized")

    async def get_or_create_user(self, facebook_id: str, facebook_profile: Optional[Dict[str, Any]] = None) -> UserProfile:
        """Get existing user or create new one"""
        try:
            # Try to get existing user from cache/database
            user = await self._get_user_by_facebook_id(facebook_id)
            
            if user:
                # Update last active time
                user.last_active = datetime.now()
                await self._update_user(user)
                logger.info("existing_user_retrieved", facebook_id=facebook_id)
                return user
            
            # Create new user
            user = await self._create_new_user(facebook_id, facebook_profile)
            logger.info("new_user_created", facebook_id=facebook_id)
            return user
            
        except Exception as e:
            logger.error("user_creation_failed", facebook_id=facebook_id, error=str(e))
            # Return a basic user profile as fallback
            return UserProfile(
                user_id=str(uuid.uuid4()),
                source=UserSourceEnum.FACEBOOK_MESSENGER,
                preferences=UserPreferences()
            )

    async def _get_user_by_facebook_id(self, facebook_id: str) -> Optional[UserProfile]:
        """Get user by Facebook ID from cache/database"""
        try:
            # Try cache first
            cache_key = f"user:facebook:{facebook_id}"
            cached_user = self.cache_manager.get(cache_key)
            
            if cached_user:
                return UserProfile(**json.loads(cached_user))
            
            # Try database lookup
            db_user = await self.supabase_service.get_user_by_facebook_id(facebook_id)
            
            if db_user:
                # Convert database user to UserProfile
                user_profile = self._convert_db_user_to_profile(db_user)
                
                # Cache the user
                self.cache_manager.set(cache_key, user_profile.json(), ttl=3600)
                
                return user_profile
            
            return None
            
        except Exception as e:
            logger.error("user_retrieval_failed", facebook_id=facebook_id, error=str(e))
            return None

    async def _create_new_user(self, facebook_id: str, facebook_profile: Optional[Dict[str, Any]] = None) -> UserProfile:
        """Create new user profile"""
        try:
            # Create Facebook profile if provided
            fb_profile = None
            if facebook_profile:
                fb_profile = FacebookUserProfile(
                    facebook_id=facebook_id,
                    name=facebook_profile.get("name"),
                    first_name=facebook_profile.get("first_name"),
                    last_name=facebook_profile.get("last_name"),
                    profile_pic=facebook_profile.get("profile_pic"),
                    locale=facebook_profile.get("locale"),
                    timezone=facebook_profile.get("timezone"),
                    gender=facebook_profile.get("gender")
                )
            
            # Create user profile
            user = UserProfile(
                user_id=str(uuid.uuid4()),
                facebook_profile=fb_profile,
                source=UserSourceEnum.FACEBOOK_MESSENGER,
                status=UserStatusEnum.ACTIVE,
                preferences=UserPreferences(
                    preferred_language=self._detect_language_from_profile(fb_profile)
                ),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                last_active=datetime.now()
            )
            
            # Save to cache/database
            await self._save_user(user)
            
            # Create analytics record
            await self._create_user_analytics(user.user_id, facebook_id)
            
            return user
            
        except Exception as e:
            logger.error("new_user_creation_failed", facebook_id=facebook_id, error=str(e))
            raise

    async def _save_user(self, user: UserProfile) -> bool:
        """Save user to cache/database"""
        try:
            # Get facebook_id safely
            facebook_id = user.facebook_profile.facebook_id if user.facebook_profile else None
            
            if not facebook_id:
                logger.error("facebook_id_missing", user_id=user.user_id)
                return False
            
            # Save to database
            success = await self.supabase_service.create_user_profile(user)
            
            if success:
                # Save to cache
                cache_key = f"user:facebook:{facebook_id}"
                self.cache_manager.set(
                    cache_key, 
                    user.json(), 
                    ttl=86400  # 24 hours
                )
                
                logger.info("user_saved", user_id=user.user_id, facebook_id=facebook_id)
                return True
            else:
                logger.error("user_save_failed", user_id=user.user_id, facebook_id=facebook_id)
                return False
            
        except Exception as e:
            logger.error("user_save_failed", user_id=user.user_id, error=str(e))
            return False

    async def _update_user(self, user: UserProfile) -> bool:
        """Update user profile"""
        try:
            user.updated_at = datetime.now()
            
            # Get facebook_id safely
            facebook_id = user.facebook_profile.facebook_id if user.facebook_profile else None
            
            if not facebook_id:
                logger.error("facebook_id_missing_for_update", user_id=user.user_id)
                return False
            
            # Update in database
            updates = {
                "updated_at": user.updated_at.isoformat(),
                "last_active": user.last_active.isoformat(),
                "total_orders": user.total_orders,
                "total_spent": float(user.total_spent),
                "favorite_items": user.favorite_items
            }
            
            success = await self.supabase_service.update_user_profile(facebook_id, updates)
            
            if success:
                # Update cache
                cache_key = f"user:facebook:{facebook_id}"
                self.cache_manager.set(cache_key, user.json(), ttl=86400)
            
            return success
            
        except Exception as e:
            logger.error("user_update_failed", user_id=user.user_id, error=str(e))
            return False

    async def update_user_preferences(self, facebook_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        try:
            user = await self.get_or_create_user(facebook_id)
            
            # Update preferences
            if "dietary_preferences" in preferences:
                user.preferences.dietary_preferences = preferences["dietary_preferences"]
            if "spice_preference" in preferences:
                user.preferences.spice_preference = preferences["spice_preference"]
            if "allergens" in preferences:
                user.preferences.allergens = preferences["allergens"]
            if "preferred_language" in preferences:
                user.preferences.preferred_language = LanguageEnum(preferences["preferred_language"])
            
            return await self._update_user(user)
            
        except Exception as e:
            logger.error("preferences_update_failed", facebook_id=facebook_id, error=str(e))
            return False

    async def get_user_cart(self, facebook_id: str) -> Optional[ShoppingCart]:
        """Get user's shopping cart"""
        try:
            cache_key = f"cart:facebook:{facebook_id}"
            cached_cart = self.cache_manager.get(cache_key)
            
            if cached_cart:
                return ShoppingCart(**json.loads(cached_cart))
            
            # Create new cart
            user = await self.get_or_create_user(facebook_id)
            cart = ShoppingCart(
                user_id=user.user_id,
                items=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            await self._save_cart(cart, facebook_id)
            return cart
            
        except Exception as e:
            logger.error("cart_retrieval_failed", facebook_id=facebook_id, error=str(e))
            return None

    async def _save_cart(self, cart: ShoppingCart, facebook_id: str) -> bool:
        """Save shopping cart to cache"""
        try:
            cache_key = f"cart:facebook:{facebook_id}"
            self.cache_manager.set(
                cache_key,
                cart.json(),
                ttl=3600  # 1 hour
            )
            return True
        except Exception as e:
            logger.error("cart_save_failed", facebook_id=facebook_id, error=str(e))
            return False

    async def add_to_cart(self, facebook_id: str, menu_item_id: int, quantity: int = 1, 
                         customizations: Dict[str, Any] = None, special_requests: str = None) -> bool:
        """Add item to user's shopping cart"""
        try:
            cart = await self.get_user_cart(facebook_id)
            if not cart:
                return False
            
            # Check if item already exists in cart
            existing_item = None
            for item in cart.items:
                if (item.menu_item_id == menu_item_id and 
                    item.customizations == (customizations or {}) and
                    item.special_requests == special_requests):
                    existing_item = item
                    break
            
            if existing_item:
                # Update quantity
                existing_item.quantity += quantity
            else:
                # Add new item
                from src.data.user_models import CartItem
                new_item = CartItem(
                    menu_item_id=menu_item_id,
                    quantity=quantity,
                    customizations=customizations or {},
                    special_requests=special_requests,
                    added_at=datetime.now()
                )
                cart.items.append(new_item)
            
            cart.updated_at = datetime.now()
            return await self._save_cart(cart, facebook_id)
            
        except Exception as e:
            logger.error("add_to_cart_failed", facebook_id=facebook_id, menu_item_id=menu_item_id, error=str(e))
            return False

    async def remove_from_cart(self, facebook_id: str, menu_item_id: int, customizations: Dict[str, Any] = None) -> bool:
        """Remove item from user's shopping cart"""
        try:
            cart = await self.get_user_cart(facebook_id)
            if not cart:
                return False
            
            # Remove matching items
            cart.items = [
                item for item in cart.items
                if not (item.menu_item_id == menu_item_id and 
                       item.customizations == (customizations or {}))
            ]
            
            cart.updated_at = datetime.now()
            return await self._save_cart(cart, facebook_id)
            
        except Exception as e:
            logger.error("remove_from_cart_failed", facebook_id=facebook_id, menu_item_id=menu_item_id, error=str(e))
            return False

    async def clear_cart(self, facebook_id: str) -> bool:
        """Clear user's shopping cart"""
        try:
            cart = await self.get_user_cart(facebook_id)
            if cart:
                cart.items = []
                cart.updated_at = datetime.now()
                return await self._save_cart(cart, facebook_id)
            return True
            
        except Exception as e:
            logger.error("clear_cart_failed", facebook_id=facebook_id, error=str(e))
            return False

    async def create_order(self, facebook_id: str, cart: ShoppingCart, order_type: str = "pickup",
                          contact_name: str = None, contact_phone: str = None,
                          special_instructions: str = None) -> Optional[Order]:
        """Create order from shopping cart"""
        try:
            user = await self.get_or_create_user(facebook_id)
            
            # TODO: Calculate pricing based on menu items
            # For now, use placeholder values
            subtotal = 0.0  # Calculate from cart items
            tax = subtotal * 0.05  # 5% tax
            delivery_fee = 0.0 if order_type == "pickup" else 2000.0
            total_amount = subtotal + tax + delivery_fee
            
            order = Order(
                order_id=str(uuid.uuid4()),
                user_id=user.user_id,
                facebook_id=facebook_id,
                items=[],  # TODO: Convert cart items to order items
                order_type=order_type,
                status="pending",
                subtotal=subtotal,
                tax=tax,
                delivery_fee=delivery_fee,
                total_amount=total_amount,
                contact_name=contact_name,
                contact_phone=contact_phone,
                special_instructions=special_instructions,
                order_time=datetime.now(),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Save order
            await self._save_order(order)
            
            # Clear cart
            await self.clear_cart(facebook_id)
            
            # Update user statistics
            user.total_orders += 1
            user.total_spent += total_amount
            await self._update_user(user)
            
            logger.info("order_created", order_id=order.order_id, facebook_id=facebook_id)
            return order
            
        except Exception as e:
            logger.error("order_creation_failed", facebook_id=facebook_id, error=str(e))
            return None

    async def _save_order(self, order: Order) -> bool:
        """Save order to cache/database"""
        try:
            # Save to cache
            cache_key = f"order:{order.order_id}"
            self.cache_manager.set(
                cache_key,
                order.json(),
                ttl=86400  # 24 hours
            )
            
            # TODO: Save to database
            return True
            
        except Exception as e:
            logger.error("order_save_failed", order_id=order.order_id, error=str(e))
            return False

    async def get_user_orders(self, facebook_id: str, limit: int = 10) -> List[Order]:
        """Get user's order history"""
        try:
            # TODO: Implement database query
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error("orders_retrieval_failed", facebook_id=facebook_id, error=str(e))
            return []

    async def _create_user_analytics(self, user_id: str, facebook_id: str) -> bool:
        """Create user analytics record"""
        try:
            analytics = UserAnalytics(
                user_id=user_id,
                facebook_id=facebook_id,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Save to cache
            cache_key = f"analytics:facebook:{facebook_id}"
            self.cache_manager.set(
                cache_key,
                analytics.json(),
                ttl=86400  # 24 hours
            )
            
            return True
            
        except Exception as e:
            logger.error("analytics_creation_failed", user_id=user_id, error=str(e))
            return False

    def _detect_language_from_profile(self, fb_profile: Optional[FacebookUserProfile]) -> LanguageEnum:
        """Detect language preference from Facebook profile"""
        if not fb_profile or not fb_profile.locale:
            return LanguageEnum.ENGLISH
        
        # Map Facebook locales to our language enum
        locale = fb_profile.locale.lower()
        if locale.startswith("my") or locale.startswith("mm"):
            return LanguageEnum.BURMESE
        else:
            return LanguageEnum.ENGLISH

    def _convert_db_user_to_profile(self, db_user: Dict[str, Any]) -> UserProfile:
        """Convert database user to UserProfile"""
        try:
            # Create Facebook profile
            fb_profile = None
            if db_user.get("facebook_id"):
                fb_profile = FacebookUserProfile(
                    facebook_id=db_user["facebook_id"],
                    name=db_user.get("facebook_name"),
                    first_name=db_user.get("facebook_first_name"),
                    last_name=db_user.get("facebook_last_name"),
                    profile_pic=db_user.get("facebook_profile_pic"),
                    locale=db_user.get("facebook_locale"),
                    timezone=db_user.get("facebook_timezone"),
                    gender=db_user.get("facebook_gender")
                )
            
            # Create user preferences
            preferences_data = db_user.get("preferences", {})
            preferences = UserPreferences(
                dietary_preferences=preferences_data.get("dietary_preferences", []),
                spice_preference=preferences_data.get("spice_preference", "medium"),
                allergens=preferences_data.get("allergens", []),
                favorite_categories=preferences_data.get("favorite_categories", []),
                preferred_language=LanguageEnum(preferences_data.get("preferred_language", "en")),
                notification_preferences=preferences_data.get("notification_preferences", {})
            )
            
            # Create user profile
            user_profile = UserProfile(
                user_id=db_user["user_id"],
                facebook_profile=fb_profile,
                source=UserSourceEnum(db_user.get("source", "facebook_messenger")),
                status=UserStatusEnum(db_user.get("status", "active")),
                preferences=preferences,
                phone=db_user.get("phone"),
                email=db_user.get("email"),
                address=db_user.get("address"),
                total_orders=db_user.get("total_orders", 0),
                total_spent=float(db_user.get("total_spent", 0.0)),
                favorite_items=db_user.get("favorite_items", []),
                created_at=datetime.fromisoformat(db_user["created_at"]),
                updated_at=datetime.fromisoformat(db_user["updated_at"]),
                last_active=datetime.fromisoformat(db_user["last_active"])
            )
            
            return user_profile
            
        except Exception as e:
            logger.error("db_user_conversion_failed", error=str(e))
            # Return a basic profile as fallback
            return UserProfile(
                user_id=db_user.get("user_id", "unknown"),
                source=UserSourceEnum.FACEBOOK_MESSENGER,
                preferences=UserPreferences()
            ) 