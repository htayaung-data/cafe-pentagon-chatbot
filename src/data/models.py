"""
Data models for Cafe Pentagon Chatbot
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime, date, time
from enum import Enum


class LanguageEnum(str, Enum):
    """Supported languages"""
    ENGLISH = "en"
    BURMESE = "my"


class IntentCategoryEnum(str, Enum):
    """Intent categories"""
    GREETING = "greeting"
    MENU_BROWSE = "menu_browse"
    ORDER_PLACE = "order_place"
    RESERVATION = "reservation"
    FAQ = "faq"
    COMPLAINT = "complaint"
    EVENTS = "events"
    JOBS = "jobs"
    GOODBYE = "goodbye"
    UNKNOWN = "unknown"


class ConversationStateEnum(str, Enum):
    """Conversation states"""
    IDLE = "idle"
    MENU_BROWSING = "menu_browsing"
    ORDERING = "ordering"
    RESERVATION_FLOW = "reservation_flow"
    COMPLAINT_HANDLING = "complaint_handling"
    EVENT_BOOKING = "event_booking"
    JOB_APPLICATION = "job_application"
    HUMAN_HANDOFF = "human_handoff"


class MenuCategoryEnum(str, Enum):
    """Menu categories"""
    BREAKFAST = "breakfast"
    MAIN_COURSE = "main_course"
    APPETIZERS_SIDES = "appetizers_sides"
    SOUPS = "soups"
    NOODLES = "noodles"
    SANDWICHES_BURGERS = "sandwiches_burgers"
    SALADS = "salads"
    PASTA = "pasta"
    RICE_DISHES = "rice_dishes"


class DietaryInfo(BaseModel):
    """Dietary information for menu items"""
    vegetarian: bool = False
    vegan: bool = False
    gluten_free: bool = False
    contains_dairy: bool = False
    contains_eggs: bool = False


class MenuItem(BaseModel):
    """Menu item model"""
    id: int
    category: MenuCategoryEnum
    english_name: str
    myanmar_name: str
    price: float
    currency: str = "MMK"
    image_url: Optional[str] = None
    ingredients: List[str] = Field(default_factory=list)
    dietary_info: DietaryInfo
    allergens: List[str] = Field(default_factory=list)
    description_en: str
    description_mm: str
    spice_level: int = Field(ge=1, le=4)
    preparation_time: str = "15-20 minutes"
    
    @validator('spice_level')
    def validate_spice_level(cls, v):
        if not 1 <= v <= 4:
            raise ValueError('Spice level must be between 1 and 4')
        return v


class FAQItem(BaseModel):
    """FAQ item model"""
    id: int
    category: str
    question_en: str
    answer_en: str
    question_mm: str
    answer_mm: str
    tags: List[str] = Field(default_factory=list)
    priority: int = 1


class ReservationStatusEnum(str, Enum):
    """Reservation status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class TableConfiguration(BaseModel):
    """Table configuration model"""
    table_id: str
    name: str
    name_mm: str
    capacity: int
    location: str
    area: str
    reserved_for: Optional[str] = None
    status: str = "available"
    special_features: List[str] = Field(default_factory=list)
    price_category: str = "standard"


class OpeningHours(BaseModel):
    """Opening hours model"""
    open: str
    close: str
    status: str = "open"
    notes_en: str = "Regular hours"
    notes_mm: str = "ပုံမှန်ဖွင့်ချိန်"


class RestaurantInfo(BaseModel):
    """Restaurant information model"""
    name: str
    name_mm: str
    address: str
    address_mm: str
    phone: str
    email: str
    total_tables: int
    max_party_size: int
    seating_capacity: int


class ReservationConfig(BaseModel):
    """Reservation configuration model"""
    restaurant_info: RestaurantInfo
    opening_hours: Dict[str, OpeningHours]
    table_configuration: List[TableConfiguration]


class EventTypeEnum(str, Enum):
    """Event types"""
    LIVE_MUSIC = "live_music"
    SPECIAL_OCCASION = "special_occasion"
    CELEBRATION = "celebration"
    PROMOTION = "promotion"
    BUSINESS = "business"


class EventPrice(BaseModel):
    """Event price model"""
    entry_fee: float
    dinner_set: float
    currency: str = "MMK"


class Event(BaseModel):
    """Event model"""
    event_id: str
    type: EventTypeEnum
    title_en: str
    title_mm: str
    date: str
    time: str
    day_of_week: str
    description_en: str
    description_mm: str
    artist_en: str
    artist_mm: str
    special_menu: List[str] = Field(default_factory=list)
    menu_description_en: str
    menu_description_mm: str
    reservation_required: bool = False
    promotion_code: Optional[str] = None
    discount_percentage: int = 0
    max_capacity: int
    current_bookings: int = 0
    price: EventPrice
    features: List[str] = Field(default_factory=list)
    status: str = "upcoming"


class JobDepartmentEnum(str, Enum):
    """Job departments"""
    SERVICE = "service"
    KITCHEN = "kitchen"
    BEVERAGE = "beverage"
    MANAGEMENT = "management"


class EmploymentTypeEnum(str, Enum):
    """Employment types"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"


class SalaryRange(BaseModel):
    """Salary range model"""
    min: int
    max: int
    currency: str = "MMK"
    period: str = "monthly"


class JobRequirements(BaseModel):
    """Job requirements model"""
    experience: str
    languages: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    education: Optional[str] = None


class JobPosition(BaseModel):
    """Job position model"""
    position_id: str
    title_en: str
    title_mm: str
    department: JobDepartmentEnum
    employment_type: EmploymentTypeEnum
    vacancies: int
    urgent: bool = False
    salary_range: SalaryRange
    requirements: JobRequirements
    responsibilities: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)
    application_deadline: str
    status: str = "open"


class CompanyInfo(BaseModel):
    """Company information model"""
    name: str
    name_mm: str
    industry: str
    location: str
    contact_email: str
    contact_phone: str


class JobsConfig(BaseModel):
    """Jobs configuration model"""
    company_info: CompanyInfo
    positions: List[JobPosition]


class UserProfile(BaseModel):
    """User profile model"""
    user_id: str
    language: LanguageEnum = LanguageEnum.ENGLISH
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    dietary_preferences: List[str] = Field(default_factory=list)
    allergens: List[str] = Field(default_factory=list)
    spice_preference: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @validator('spice_preference')
    def validate_spice_preference(cls, v):
        if v is not None and not 1 <= v <= 4:
            raise ValueError('Spice preference must be between 1 and 4')
        return v


class MessageRoleEnum(str, Enum):
    """Message roles"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Message model"""
    role: MessageRoleEnum
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    language: LanguageEnum = LanguageEnum.ENGLISH
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Conversation(BaseModel):
    """Conversation model"""
    user_id: str
    messages: List[Message] = Field(default_factory=list)
    current_state: ConversationStateEnum = ConversationStateEnum.IDLE
    context: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Intent(BaseModel):
    """Intent model"""
    category: IntentCategoryEnum
    confidence: float = Field(ge=0.0, le=1.0)
    entities: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OrderItem(BaseModel):
    """Order item model"""
    menu_item_id: int
    quantity: int = Field(gt=0)
    customizations: Dict[str, Any] = Field(default_factory=dict)
    special_requests: Optional[str] = None
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        return v


class Order(BaseModel):
    """Order model"""
    order_id: str
    user_id: str
    items: List[OrderItem] = Field(default_factory=list)
    total_amount: float = 0.0
    currency: str = "MMK"
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items)


class Reservation(BaseModel):
    """Reservation model"""
    reservation_id: str
    user_id: str
    date: date
    time: time
    party_size: int = Field(gt=0, le=15)
    table_id: Optional[str] = None
    status: ReservationStatusEnum = ReservationStatusEnum.PENDING
    special_requests: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @validator('party_size')
    def validate_party_size(cls, v):
        if not 1 <= v <= 15:
            raise ValueError('Party size must be between 1 and 15')
        return v


class ComplaintSeverityEnum(str, Enum):
    """Complaint severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Complaint(BaseModel):
    """Complaint model"""
    complaint_id: str
    user_id: str
    category: str
    description: str
    severity: ComplaintSeverityEnum = ComplaintSeverityEnum.MEDIUM
    status: str = "open"
    assigned_to: Optional[str] = None
    resolution: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None


class ChatbotResponse(BaseModel):
    """Chatbot response model"""
    message: str
    language: LanguageEnum
    intent: Optional[Intent] = None
    suggested_actions: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatbotRequest(BaseModel):
    """Chatbot request model"""
    user_id: str
    message: str
    language: Optional[LanguageEnum] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now) 