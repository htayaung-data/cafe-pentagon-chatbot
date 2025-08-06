"""
User-specific data models for Facebook Messenger integration
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime, date, time
from enum import Enum
from src.data.models import LanguageEnum, MenuCategoryEnum


class UserSourceEnum(str, Enum):
    """User registration sources"""
    FACEBOOK_MESSENGER = "facebook_messenger"
    STREAMLIT = "streamlit"
    API = "api"


class UserStatusEnum(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"


class DietaryPreferenceEnum(str, Enum):
    """Dietary preferences"""
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    NUT_FREE = "nut_free"
    HALAL = "halal"
    KOSHER = "kosher"
    NONE = "none"


class SpicePreferenceEnum(str, Enum):
    """Spice level preferences"""
    MILD = "mild"  # Level 1
    MEDIUM = "medium"  # Level 2
    HOT = "hot"  # Level 3
    EXTRA_HOT = "extra_hot"  # Level 4


class FacebookUserProfile(BaseModel):
    """Facebook user profile information"""
    facebook_id: str
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_pic: Optional[str] = None
    locale: Optional[str] = None
    timezone: Optional[int] = None
    gender: Optional[str] = None


class UserPreferences(BaseModel):
    """User preferences and settings"""
    dietary_preferences: List[DietaryPreferenceEnum] = Field(default_factory=list)
    spice_preference: SpicePreferenceEnum = SpicePreferenceEnum.MEDIUM
    allergens: List[str] = Field(default_factory=list)
    favorite_categories: List[MenuCategoryEnum] = Field(default_factory=list)
    preferred_language: LanguageEnum = LanguageEnum.ENGLISH
    notification_preferences: Dict[str, bool] = Field(default_factory=dict)
    
    @validator('spice_preference')
    def validate_spice_preference(cls, v):
        if v not in SpicePreferenceEnum:
            raise ValueError('Invalid spice preference')
        return v


class UserProfile(BaseModel):
    """Enhanced user profile for Facebook Messenger"""
    user_id: str
    facebook_profile: Optional[FacebookUserProfile] = None
    source: UserSourceEnum = UserSourceEnum.FACEBOOK_MESSENGER
    status: UserStatusEnum = UserStatusEnum.ACTIVE
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    
    # Contact information
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_active: datetime = Field(default_factory=datetime.now)
    
    # Statistics
    total_orders: int = 0
    total_spent: float = 0.0
    favorite_items: List[int] = Field(default_factory=list)  # Menu item IDs
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CartItem(BaseModel):
    """Shopping cart item"""
    menu_item_id: int
    quantity: int = Field(gt=0)
    customizations: Dict[str, Any] = Field(default_factory=dict)
    special_requests: Optional[str] = None
    added_at: datetime = Field(default_factory=datetime.now)
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        return v


class ShoppingCart(BaseModel):
    """User shopping cart"""
    user_id: str
    items: List[CartItem] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items)
    
    @property
    def total_amount(self) -> float:
        # TODO: Calculate based on menu items and customizations
        return 0.0


class OrderStatusEnum(str, Enum):
    """Order status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OrderTypeEnum(str, Enum):
    """Order types"""
    PICKUP = "pickup"
    DINE_IN = "dine_in"
    DELIVERY = "delivery"


class OrderItem(BaseModel):
    """Order item with details"""
    menu_item_id: int
    menu_item_name: str
    menu_item_name_mm: str
    quantity: int
    unit_price: float
    total_price: float
    customizations: Dict[str, Any] = Field(default_factory=dict)
    special_requests: Optional[str] = None
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        return v


class Order(BaseModel):
    """Enhanced order model for Facebook Messenger"""
    order_id: str
    user_id: str
    facebook_id: str
    
    # Order details
    items: List[OrderItem] = Field(default_factory=list)
    order_type: OrderTypeEnum = OrderTypeEnum.PICKUP
    status: OrderStatusEnum = OrderStatusEnum.PENDING
    
    # Pricing
    subtotal: float = 0.0
    tax: float = 0.0
    delivery_fee: float = 0.0
    discount: float = 0.0
    total_amount: float = 0.0
    currency: str = "MMK"
    
    # Timing
    order_time: datetime = Field(default_factory=datetime.now)
    pickup_time: Optional[datetime] = None
    estimated_ready_time: Optional[datetime] = None
    actual_ready_time: Optional[datetime] = None
    
    # Contact information
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    
    # Special requests
    special_instructions: Optional[str] = None
    
    # Payment
    payment_method: Optional[str] = None
    payment_status: str = "pending"
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConversationSession(BaseModel):
    """Enhanced conversation session for Facebook Messenger"""
    session_id: str
    user_id: str
    facebook_id: str
    
    # Session state
    current_state: str = "idle"
    context: Dict[str, Any] = Field(default_factory=dict)
    
    # Conversation data
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    intents: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Timing
    started_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    
    # Statistics
    message_count: int = 0
    user_message_count: int = 0
    bot_message_count: int = 0
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserAnalytics(BaseModel):
    """User analytics and behavior data"""
    user_id: str
    facebook_id: str
    
    # Engagement metrics
    total_sessions: int = 0
    total_messages: int = 0
    average_session_length: float = 0.0
    last_session_date: Optional[datetime] = None
    
    # Order metrics
    total_orders: int = 0
    total_spent: float = 0.0
    average_order_value: float = 0.0
    last_order_date: Optional[datetime] = None
    
    # Preference metrics
    most_ordered_items: List[int] = Field(default_factory=list)
    favorite_categories: List[str] = Field(default_factory=list)
    preferred_order_times: List[str] = Field(default_factory=list)
    
    # Language preferences
    primary_language: LanguageEnum = LanguageEnum.ENGLISH
    language_usage: Dict[str, int] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 