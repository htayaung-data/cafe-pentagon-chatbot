"""
Language detection and translation utilities for Cafe Pentagon Chatbot
"""

import re
from typing import Optional, Tuple
from langdetect import detect, DetectorFactory, LangDetectException
# Removed googletrans import - will implement simple translation later
from src.config.constants import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE
from src.utils.logger import get_logger, log_performance

# Set seed for consistent language detection
DetectorFactory.seed = 0

logger = get_logger("language")


@log_performance
def detect_language(text: str) -> str:
    """
    Detect the language of the input text
    
    Args:
        text: Input text to detect language
        
    Returns:
        Detected language code (en, my, etc.)
        
    Raises:
        LangDetectException: If language detection fails
    """
    if not text or not text.strip():
        return DEFAULT_LANGUAGE
    
    # First, use reliable character-based detection for Burmese
    if is_burmese_text(text):
        logger.info(
            "language_detected",
            original_text=text[:100],
            detected_language="my",
            confidence="high"
        )
        return "my"
    
    # For non-Burmese text, use langdetect
    try:
        # Clean text for better detection
        cleaned_text = re.sub(r'[^\w\s]', '', text.strip())
        if len(cleaned_text) < 3:
            return DEFAULT_LANGUAGE
        
        detected_lang = detect(cleaned_text)
        
        # Map detected language to supported languages
        lang_mapping = {
            'en': 'en',
            'my': 'my',
            'mya': 'my',  # Alternative code for Burmese
            'bur': 'my',  # Alternative code for Burmese
        }
        
        detected_lang = lang_mapping.get(detected_lang, DEFAULT_LANGUAGE)
        
        logger.info(
            "language_detected",
            original_text=text[:100],  # Log first 100 chars
            detected_language=detected_lang,
            confidence="high"
        )
        
        return detected_lang
        
    except LangDetectException as e:
        logger.warning(
            "language_detection_failed",
            text=text[:100],
            error=str(e)
        )
        return DEFAULT_LANGUAGE
    except Exception as e:
        logger.error(
            "language_detection_error",
            text=text[:100],
            error=str(e)
        )
        return DEFAULT_LANGUAGE


@log_performance
def translate_text(
    text: str,
    target_language: str,
    source_language: Optional[str] = None
) -> str:
    """
    Translate text to target language
    Note: Currently returns original text as translation service is disabled
    
    Args:
        text: Text to translate
        target_language: Target language code
        source_language: Source language code (optional, auto-detect if not provided)
        
    Returns:
        Original text (translation disabled for now)
    """
    if not text or not text.strip():
        return text
    
    if target_language not in SUPPORTED_LANGUAGES:
        logger.warning(
            "unsupported_target_language",
            target_language=target_language,
            supported_languages=SUPPORTED_LANGUAGES
        )
        return text
    
    # For now, return original text as translation service is disabled
    # TODO: Implement translation service later
    logger.info(
        "translation_disabled",
        text=text[:100],
        target_language=target_language,
        note="Translation service temporarily disabled"
    )
    return text


def get_language_name(language_code: str) -> str:
    """
    Get human-readable language name from language code
    
    Args:
        language_code: Language code (en, my, etc.)
        
    Returns:
        Human-readable language name
    """
    language_names = {
        'en': 'English',
        'my': 'မြန်မာ',  # Burmese
        'mya': 'မြန်မာ',  # Alternative Burmese code
        'bur': 'မြန်မာ',  # Alternative Burmese code
    }
    
    return language_names.get(language_code, language_code)


def is_burmese_text(text: str) -> bool:
    """
    Check if text contains Burmese characters
    
    Args:
        text: Text to check
        
    Returns:
        True if text contains Burmese characters
    """
    # Burmese Unicode range: U+1000 to U+109F
    burmese_pattern = re.compile(r'[\u1000-\u109F]')
    return bool(burmese_pattern.search(text))


def is_english_text(text: str) -> bool:
    """
    Check if text contains English characters
    
    Args:
        text: Text to check
        
    Returns:
        True if text contains English characters
    """
    # English alphabet and common punctuation
    english_pattern = re.compile(r'[a-zA-Z]')
    return bool(english_pattern.search(text))


def get_text_language_confidence(text: str) -> Tuple[str, float]:
    """
    Get language and confidence score for text
    
    Args:
        text: Text to analyze
        
    Returns:
        Tuple of (language_code, confidence_score)
    """
    try:
        from langdetect import detect_langs
        
        if not text or not text.strip():
            return DEFAULT_LANGUAGE, 0.0
        
        # Get language probabilities
        lang_probabilities = detect_langs(text)
        
        if not lang_probabilities:
            return DEFAULT_LANGUAGE, 0.0
        
        # Get the most probable language
        best_lang = lang_probabilities[0]
        language_code = best_lang.lang
        confidence = best_lang.prob
        
        # Map to supported languages
        lang_mapping = {
            'en': 'en',
            'my': 'my',
            'mya': 'my',
            'bur': 'my',
        }
        
        mapped_lang = lang_mapping.get(language_code, DEFAULT_LANGUAGE)
        
        logger.info(
            "language_confidence",
            language=mapped_lang,
            confidence=confidence,
            text_length=len(text)
        )
        
        return mapped_lang, confidence
        
    except Exception as e:
        logger.error(
            "language_confidence_error",
            error=str(e)
        )
        return DEFAULT_LANGUAGE, 0.0


def normalize_text(text: str) -> str:
    """
    Normalize text for better language detection and processing
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove special characters that might interfere with language detection
    text = re.sub(r'[^\w\s\u1000-\u109F]', '', text)
    
    return text


def get_supported_language_codes() -> list:
    """
    Get list of supported language codes
    
    Returns:
        List of supported language codes
    """
    return SUPPORTED_LANGUAGES.copy() 
