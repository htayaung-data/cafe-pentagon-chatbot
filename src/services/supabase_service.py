"""
Supabase Database Service for Cafe Pentagon Chatbot
Handles all database operations for user profiles, orders, and analytics
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from supabase import create_client, Client
from src.utils.logger import get_logger
from src.config.settings import get_settings
from src.data.user_models import (
    UserProfile, FacebookUserProfile, UserPreferences,
    ShoppingCart, Order, ConversationSession, UserAnalytics
)

logger = get_logger("supabase_service")


class SupabaseService:
    """
    Supabase database service for user management
    """
    
    def __init__(self):
        """Initialize Supabase client"""
        self.settings = get_settings()
        
        # Initialize Supabase client
        self.supabase: Client = create_client(
            self.settings.supabase_url,
            self.settings.supabase_anon_key
        )
        
        logger.info("supabase_service_initialized")

    async def get_user_by_facebook_id(self, facebook_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by Facebook ID"""
        try:
            response = self.supabase.table("user_profiles").select("*").eq("facebook_id", facebook_id).execute()
            
            if response.data and len(response.data) > 0:
                logger.info("user_retrieved", facebook_id=facebook_id)
                return response.data[0]
            else:
                logger.info("user_not_found", facebook_id=facebook_id)
                return None
                
        except Exception as e:
            logger.error("user_retrieval_failed", facebook_id=facebook_id, error=str(e))
            return None

    async def create_user_profile(self, user_profile: UserProfile) -> bool:
        """Create user profile with upsert to handle existing users"""
        try:
            # Get facebook_id safely
            facebook_id = user_profile.facebook_profile.facebook_id if user_profile.facebook_profile else None
            
            if not facebook_id:
                logger.error("facebook_id_missing_in_profile", user_id=user_profile.user_id)
                return False
            
            profile_data = {
                "facebook_id": facebook_id,
                "user_id": user_profile.user_id,
                "source": user_profile.source.value,
                "status": user_profile.status.value,
                
                # Facebook Profile Data
                "facebook_name": user_profile.facebook_profile.name if user_profile.facebook_profile else None,
                "facebook_first_name": user_profile.facebook_profile.first_name if user_profile.facebook_profile else None,
                "facebook_last_name": user_profile.facebook_profile.last_name if user_profile.facebook_profile else None,
                "facebook_profile_pic": user_profile.facebook_profile.profile_pic if user_profile.facebook_profile else None,
                "facebook_locale": user_profile.facebook_profile.locale if user_profile.facebook_profile else None,
                "facebook_timezone": user_profile.facebook_profile.timezone if user_profile.facebook_profile else None,
                "facebook_gender": user_profile.facebook_profile.gender if user_profile.facebook_profile else None,
                
                # Contact Information
                "phone": user_profile.phone,
                "email": user_profile.email,
                "address": user_profile.address,
                
                # Preferences
                "preferences": user_profile.preferences.dict(),
                
                # Statistics
                "total_orders": user_profile.total_orders,
                "total_spent": float(user_profile.total_spent),
                "favorite_items": user_profile.favorite_items,
                
                # Timestamps
                "created_at": user_profile.created_at.isoformat(),
                "updated_at": user_profile.updated_at.isoformat(),
                "last_active": user_profile.last_active.isoformat()
            }
            
            # Use upsert to handle existing users
            response = self.supabase.table("user_profiles").upsert(profile_data, on_conflict="facebook_id").execute()
            
            if response.data:
                logger.info("user_profile_upserted", user_id=user_profile.user_id)
                return True
            else:
                logger.error("user_profile_upsert_failed", user_id=user_profile.user_id)
                return False
                
        except Exception as e:
            logger.error("user_profile_upsert_exception", user_id=user_profile.user_id, error=str(e))
            return False

    async def update_user_profile(self, facebook_id: str, updates: Dict[str, Any]) -> bool:
        """Update user profile"""
        try:
            # Convert datetime objects to ISO format
            for key, value in updates.items():
                if isinstance(value, datetime):
                    updates[key] = value.isoformat()
                elif hasattr(value, 'value'):  # Handle enums
                    updates[key] = value.value
                elif hasattr(value, 'dict'):  # Handle Pydantic models
                    updates[key] = value.dict()
            
            response = self.supabase.table("user_profiles").update(updates).eq("facebook_id", facebook_id).execute()
            
            if response.data:
                logger.info("user_profile_updated", facebook_id=facebook_id)
                return True
            else:
                logger.error("user_profile_update_failed", facebook_id=facebook_id)
                return False
                
        except Exception as e:
            logger.error("user_profile_update_exception", facebook_id=facebook_id, error=str(e))
            return False

    async def get_user_cart(self, facebook_id: str) -> Optional[Dict[str, Any]]:
        """Get user's shopping cart"""
        try:
            response = self.supabase.table("shopping_carts").select("*").eq("facebook_id", facebook_id).execute()
            
            if response.data and len(response.data) > 0:
                logger.info("cart_retrieved", facebook_id=facebook_id)
                return response.data[0]
            else:
                logger.info("cart_not_found", facebook_id=facebook_id)
                return None
                
        except Exception as e:
            logger.error("cart_retrieval_failed", facebook_id=facebook_id, error=str(e))
            return None

    async def create_or_update_cart(self, facebook_id: str, user_id: str, items: List[Dict[str, Any]]) -> bool:
        """Create or update shopping cart with upsert"""
        try:
            cart_data = {
                "facebook_id": facebook_id,
                "user_id": user_id,
                "items": items,
                "updated_at": datetime.now().isoformat()
            }
            
            # Use upsert to handle existing carts
            response = self.supabase.table("shopping_carts").upsert(cart_data, on_conflict="facebook_id").execute()
            
            if response.data:
                logger.info("cart_upserted", facebook_id=facebook_id)
                return True
            else:
                logger.error("cart_upsert_failed", facebook_id=facebook_id)
                return False
                
        except Exception as e:
            logger.error("cart_upsert_exception", facebook_id=facebook_id, error=str(e))
            return False

    async def create_order(self, order: Order) -> bool:
        """Create new order"""
        try:
            order_data = {
                "order_id": order.order_id,
                "user_id": order.user_id,
                "facebook_id": order.facebook_id,
                "items": [item.dict() for item in order.items],
                "order_type": order.order_type.value,
                "status": order.status.value,
                "subtotal": float(order.subtotal),
                "tax": float(order.tax),
                "delivery_fee": float(order.delivery_fee),
                "discount": float(order.discount),
                "total_amount": float(order.total_amount),
                "currency": order.currency,
                "order_time": order.order_time.isoformat(),
                "pickup_time": order.pickup_time.isoformat() if order.pickup_time else None,
                "estimated_ready_time": order.estimated_ready_time.isoformat() if order.estimated_ready_time else None,
                "actual_ready_time": order.actual_ready_time.isoformat() if order.actual_ready_time else None,
                "contact_name": order.contact_name,
                "contact_phone": order.contact_phone,
                "special_instructions": order.special_instructions,
                "payment_method": order.payment_method,
                "payment_status": order.payment_status,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat()
            }
            
            response = self.supabase.table("orders").insert(order_data).execute()
            
            if response.data:
                logger.info("order_created", order_id=order.order_id)
                return True
            else:
                logger.error("order_creation_failed", order_id=order.order_id)
                return False
                
        except Exception as e:
            logger.error("order_creation_exception", order_id=order.order_id, error=str(e))
            return False

    async def get_user_orders(self, facebook_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's order history"""
        try:
            response = self.supabase.table("orders").select("*").eq("facebook_id", facebook_id).order("created_at", desc=True).limit(limit).execute()
            
            if response.data:
                logger.info("orders_retrieved", facebook_id=facebook_id, count=len(response.data))
                return response.data
            else:
                logger.info("no_orders_found", facebook_id=facebook_id)
                return []
                
        except Exception as e:
            logger.error("orders_retrieval_failed", facebook_id=facebook_id, error=str(e))
            return []

    async def update_order_status(self, order_id: str, status: str) -> bool:
        """Update order status"""
        try:
            response = self.supabase.table("orders").update({
                "status": status,
                "updated_at": datetime.now().isoformat()
            }).eq("order_id", order_id).execute()
            
            if response.data:
                logger.info("order_status_updated", order_id=order_id, status=status)
                return True
            else:
                logger.error("order_status_update_failed", order_id=order_id)
                return False
                
        except Exception as e:
            logger.error("order_status_update_exception", order_id=order_id, error=str(e))
            return False

    async def create_conversation_session(self, session: ConversationSession) -> bool:
        """Create conversation session"""
        try:
            session_data = {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "facebook_id": session.facebook_id,
                "current_state": session.current_state,
                "context": session.context,
                "messages": session.messages,
                "intents": session.intents,
                "started_at": session.started_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "ended_at": session.ended_at.isoformat() if session.ended_at else None,
                "message_count": session.message_count,
                "user_message_count": session.user_message_count,
                "bot_message_count": session.bot_message_count
            }
            
            response = self.supabase.table("conversation_sessions").insert(session_data).execute()
            
            if response.data:
                logger.info("conversation_session_created", session_id=session.session_id)
                return True
            else:
                logger.error("conversation_session_creation_failed", session_id=session.session_id)
                return False
                
        except Exception as e:
            logger.error("conversation_session_creation_exception", session_id=session.session_id, error=str(e))
            return False

    async def update_conversation_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update conversation session"""
        try:
            # Convert datetime objects to ISO format
            for key, value in updates.items():
                if isinstance(value, datetime):
                    updates[key] = value.isoformat()
            
            response = self.supabase.table("conversation_sessions").update(updates).eq("session_id", session_id).execute()
            
            if response.data:
                logger.info("conversation_session_updated", session_id=session_id)
                return True
            else:
                logger.error("conversation_session_update_failed", session_id=session_id)
                return False
                
        except Exception as e:
            logger.error("conversation_session_update_exception", session_id=session_id, error=str(e))
            return False

    async def create_user_analytics(self, analytics: UserAnalytics) -> bool:
        """Create user analytics record"""
        try:
            analytics_data = {
                "user_id": analytics.user_id,
                "facebook_id": analytics.facebook_id,
                "total_sessions": analytics.total_sessions,
                "total_messages": analytics.total_messages,
                "average_session_length": float(analytics.average_session_length),
                "last_session_date": analytics.last_session_date.isoformat() if analytics.last_session_date else None,
                "total_orders": analytics.total_orders,
                "total_spent": float(analytics.total_spent),
                "average_order_value": float(analytics.average_order_value),
                "last_order_date": analytics.last_order_date.isoformat() if analytics.last_order_date else None,
                "most_ordered_items": analytics.most_ordered_items,
                "favorite_categories": analytics.favorite_categories,
                "preferred_order_times": analytics.preferred_order_times,
                "primary_language": analytics.primary_language.value,
                "language_usage": analytics.language_usage,
                "created_at": analytics.created_at.isoformat(),
                "updated_at": analytics.updated_at.isoformat()
            }
            
            response = self.supabase.table("user_analytics").insert(analytics_data).execute()
            
            if response.data:
                logger.info("user_analytics_created", user_id=analytics.user_id)
                return True
            else:
                logger.error("user_analytics_creation_failed", user_id=analytics.user_id)
                return False
                
        except Exception as e:
            logger.error("user_analytics_creation_exception", user_id=analytics.user_id, error=str(e))
            return False

    async def update_user_analytics(self, facebook_id: str, updates: Dict[str, Any]) -> bool:
        """Update user analytics"""
        try:
            # Convert datetime objects to ISO format
            for key, value in updates.items():
                if isinstance(value, datetime):
                    updates[key] = value.isoformat()
            
            response = self.supabase.table("user_analytics").update(updates).eq("facebook_id", facebook_id).execute()
            
            if response.data:
                logger.info("user_analytics_updated", facebook_id=facebook_id)
                return True
            else:
                logger.error("user_analytics_update_failed", facebook_id=facebook_id)
                return False
                
        except Exception as e:
            logger.error("user_analytics_update_exception", facebook_id=facebook_id, error=str(e))
            return False

    async def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary for dashboard"""
        try:
            # Get total users
            users_response = self.supabase.table("user_profiles").select("id", count="exact").execute()
            total_users = users_response.count if users_response.count else 0
            
            # Get total orders
            orders_response = self.supabase.table("orders").select("id", count="exact").execute()
            total_orders = orders_response.count if orders_response.count else 0
            
            # Get total revenue
            revenue_response = self.supabase.table("orders").select("total_amount").execute()
            total_revenue = sum(float(order["total_amount"]) for order in revenue_response.data) if revenue_response.data else 0
            
            # Get recent orders
            recent_orders_response = self.supabase.table("orders").select("*").order("created_at", desc=True).limit(5).execute()
            recent_orders = recent_orders_response.data if recent_orders_response.data else []
            
            summary = {
                "total_users": total_users,
                "total_orders": total_orders,
                "total_revenue": total_revenue,
                "recent_orders": recent_orders
            }
            
            logger.info("analytics_summary_retrieved", summary=summary)
            return summary
            
        except Exception as e:
            logger.error("analytics_summary_retrieval_failed", error=str(e))
            return {
                "total_users": 0,
                "total_orders": 0,
                "total_revenue": 0,
                "recent_orders": []
            } 