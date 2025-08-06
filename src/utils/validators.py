"""
Validation utilities for Cafe Pentagon Chatbot
"""

import re
from typing import Optional, Dict, Any, List
from src.utils.logger import get_logger

logger = get_logger("validators")


def validate_email(email: str) -> bool:
    """
    Validate email address format
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    # Basic email regex pattern
    email_pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    is_valid = bool(email_pattern.match(email.strip()))
    
    if not is_valid:
        logger.debug("email_validation_failed", email=email)
    
    return is_valid


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format (Myanmar format)
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Myanmar phone number patterns
    # +959XXXXXXXXX (12 digits starting with 959)
    # 09XXXXXXXXX (11 digits starting with 09)
    # 959XXXXXXXXX (12 digits starting with 959)
    
    if len(digits_only) == 12 and digits_only.startswith('959'):
        return True
    elif len(digits_only) == 11 and digits_only.startswith('09'):
        return True
    
    logger.debug("phone_validation_failed", phone=phone)
    return False


def validate_language_code(language_code: str) -> bool:
    """
    Validate language code
    
    Args:
        language_code: Language code to validate
        
    Returns:
        True if valid, False otherwise
    """
    from src.config.constants import SUPPORTED_LANGUAGES
    
    is_valid = language_code in SUPPORTED_LANGUAGES
    
    if not is_valid:
        logger.debug("language_validation_failed", language_code=language_code)
    
    return is_valid


def validate_menu_item_id(item_id: Any) -> bool:
    """
    Validate menu item ID
    
    Args:
        item_id: Menu item ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(item_id, (int, str)):
        return False
    
    try:
        item_id_int = int(item_id)
        is_valid = item_id_int > 0
    except (ValueError, TypeError):
        is_valid = False
    
    if not is_valid:
        logger.debug("menu_item_id_validation_failed", item_id=item_id)
    
    return is_valid


def validate_price(price: Any) -> bool:
    """
    Validate price value
    
    Args:
        price: Price to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(price, (int, float, str)):
        return False
    
    try:
        price_float = float(price)
        is_valid = price_float >= 0
    except (ValueError, TypeError):
        is_valid = False
    
    if not is_valid:
        logger.debug("price_validation_failed", price=price)
    
    return is_valid


def validate_quantity(quantity: Any) -> bool:
    """
    Validate quantity value
    
    Args:
        quantity: Quantity to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(quantity, (int, str)):
        return False
    
    try:
        quantity_int = int(quantity)
        is_valid = quantity_int > 0 and quantity_int <= 100  # Reasonable limit
    except (ValueError, TypeError):
        is_valid = False
    
    if not is_valid:
        logger.debug("quantity_validation_failed", quantity=quantity)
    
    return is_valid


def validate_date_format(date_str: str, format_str: str = "%Y-%m-%d") -> bool:
    """
    Validate date format
    
    Args:
        date_str: Date string to validate
        format_str: Expected date format
        
    Returns:
        True if valid, False otherwise
    """
    if not date_str or not isinstance(date_str, str):
        return False
    
    try:
        from datetime import datetime
        datetime.strptime(date_str, format_str)
        return True
    except ValueError:
        logger.debug("date_validation_failed", date_str=date_str, format=format_str)
        return False


def validate_time_format(time_str: str, format_str: str = "%H:%M") -> bool:
    """
    Validate time format
    
    Args:
        time_str: Time string to validate
        format_str: Expected time format
        
    Returns:
        True if valid, False otherwise
    """
    if not time_str or not isinstance(time_str, str):
        return False
    
    try:
        from datetime import datetime
        datetime.strptime(time_str, format_str)
        return True
    except ValueError:
        logger.debug("time_validation_failed", time_str=time_str, format=format_str)
        return False


def validate_party_size(party_size: Any) -> bool:
    """
    Validate party size for reservations
    
    Args:
        party_size: Party size to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(party_size, (int, str)):
        return False
    
    try:
        size_int = int(party_size)
        is_valid = 1 <= size_int <= 15  # Reasonable restaurant party size
    except (ValueError, TypeError):
        is_valid = False
    
    if not is_valid:
        logger.debug("party_size_validation_failed", party_size=party_size)
    
    return is_valid


def validate_user_input(text: str, max_length: int = 1000) -> bool:
    """
    Validate user input text
    
    Args:
        text: Text to validate
        max_length: Maximum allowed length
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(text, str):
        return False
    
    # Check length
    if len(text) > max_length:
        logger.debug("user_input_too_long", length=len(text), max_length=max_length)
        return False
    
    # Check for potentially harmful content (basic)
    harmful_patterns = [
        r'<script.*?>.*?</script>',  # Script tags
        r'javascript:',  # JavaScript protocol
        r'data:text/html',  # Data URLs
    ]
    
    for pattern in harmful_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning("potentially_harmful_input_detected", pattern=pattern)
            return False
    
    return True


def validate_menu_category(category: str) -> bool:
    """
    Validate menu category
    
    Args:
        category: Category to validate
        
    Returns:
        True if valid, False otherwise
    """
    from src.config.constants import MENU_CATEGORIES
    
    is_valid = category in MENU_CATEGORIES
    
    if not is_valid:
        logger.debug("menu_category_validation_failed", category=category)
    
    return is_valid


def validate_dietary_preference(preference: str) -> bool:
    """
    Validate dietary preference
    
    Args:
        preference: Dietary preference to validate
        
    Returns:
        True if valid, False otherwise
    """
    from src.config.constants import DIETARY_TYPES
    
    is_valid = preference in DIETARY_TYPES.values()
    
    if not is_valid:
        logger.debug("dietary_preference_validation_failed", preference=preference)
    
    return is_valid


def validate_allergen(allergen: str) -> bool:
    """
    Validate allergen
    
    Args:
        allergen: Allergen to validate
        
    Returns:
        True if valid, False otherwise
    """
    from src.config.constants import ALLERGENS
    
    is_valid = allergen in ALLERGENS
    
    if not is_valid:
        logger.debug("allergen_validation_failed", allergen=allergen)
    
    return is_valid


def validate_spice_level(level: Any) -> bool:
    """
    Validate spice level
    
    Args:
        level: Spice level to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(level, (int, str)):
        return False
    
    try:
        level_int = int(level)
        is_valid = 1 <= level_int <= 4
    except (ValueError, TypeError):
        is_valid = False
    
    if not is_valid:
        logger.debug("spice_level_validation_failed", level=level)
    
    return is_valid


def sanitize_text(text: str) -> str:
    """
    Sanitize text input
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    return text


def validate_json_structure(data: Dict[str, Any], required_fields: List[str]) -> bool:
    """
    Validate JSON structure has required fields
    
    Args:
        data: Data to validate
        required_fields: List of required field names
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(data, dict):
        return False
    
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        logger.debug("json_structure_validation_failed", missing_fields=missing_fields)
        return False
    
    return True


def validate_user_id(user_id: str) -> bool:
    """
    Validate user ID format
    
    Args:
        user_id: User ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not user_id or not isinstance(user_id, str):
        return False
    
    # Basic user ID validation (alphanumeric and some special chars)
    user_id_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
    is_valid = bool(user_id_pattern.match(user_id))
    
    if not is_valid:
        logger.debug("user_id_validation_failed", user_id=user_id)
    
    return is_valid 