"""
Settings configuration for Cafe Pentagon Chatbot
"""

import os
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application Configuration
    app_name: str = Field(default="Cafe Pentagon Chatbot", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=True, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    # Central chat model used across analysis/response/HITL (override via OPENAI_MODEL)
    # Use a valid default model
    openai_model: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    # Embedding model used for Pinecone vector operations
    openai_embedding_model: str = Field(default="text-embedding-3-small", env="OPENAI_EMBEDDING_MODEL")
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(default=1000, env="OPENAI_MAX_TOKENS")
    
    # Pinecone Configuration
    pinecone_api_key: str = Field(..., env="PINECONE_API_KEY")
    pinecone_environment: str = Field(..., env="PINECONE_ENVIRONMENT")
    pinecone_index_name: str = Field(default="cafe-pentagon", env="PINECONE_INDEX_NAME")
    
    # Google Sheets Configuration
    google_sheets_credentials_file: str = Field(default="data/cafechat_google_sheet.json", env="GOOGLE_SHEETS_CREDENTIALS_FILE")
    google_sheets_spreadsheet_id: str = Field(..., env="GOOGLE_SHEETS_SPREADSHEET_ID")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Language Configuration
    default_language: str = Field(default="en", env="DEFAULT_LANGUAGE")
    supported_languages: str = Field(default="en,my", env="SUPPORTED_LANGUAGES")
    
    # Conversation Configuration
    conversation_ttl: int = Field(default=86400, env="CONVERSATION_TTL")  # 24 hours
    max_conversation_length: int = Field(default=50, env="MAX_CONVERSATION_LENGTH")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="PORT")  # Railway uses PORT env var
    streamlit_port: int = Field(default=8501, env="STREAMLIT_PORT")
    
    # Security Configuration
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Monitoring Configuration
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    
    # Restaurant Configuration
    restaurant_name: str = Field(default="Cafe Pentagon", env="RESTAURANT_NAME")
    restaurant_phone: str = Field(default="+959979732781", env="RESTAURANT_PHONE")
    restaurant_email: str = Field(default="info@caferestaurant.com", env="RESTAURANT_EMAIL")
    restaurant_address: str = Field(
        default="No.285, Mahar Bandula Road, Ward 39, North Dagon Township, Yangon",
        env="RESTAURANT_ADDRESS"
    )
    
    # Facebook Messenger Configuration
    facebook_page_access_token: Optional[str] = Field(default=None, env="FACEBOOK_PAGE_ACCESS_TOKEN")
    facebook_verify_token: Optional[str] = Field(default=None, env="FACEBOOK_VERIFY_TOKEN")
    
    # Supabase Configuration
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_anon_key: str = Field(..., env="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(..., env="SUPABASE_SERVICE_ROLE_KEY")
    
    # Performance Configuration
    max_response_time: float = Field(default=5.0, env="MAX_RESPONSE_TIME")
    max_embedding_time: float = Field(default=2.0, env="MAX_EMBEDDING_TIME")
    max_llm_response_time: float = Field(default=10.0, env="MAX_LLM_RESPONSE_TIME")
    
    # Rate Limiting
    requests_per_minute: int = Field(default=60, env="REQUESTS_PER_MINUTE")
    requests_per_hour: int = Field(default=1000, env="REQUESTS_PER_HOUR")
    
    # Admin Panel Authentication Configuration
    admin_api_key: Optional[str] = Field(default=None, env="ADMIN_API_KEY")
    admin_user_id: Optional[str] = Field(default=None, env="ADMIN_USER_ID")

    # Test mode (mocks LLM calls in nodes to enable deterministic tests)
    test_mode: bool = Field(default=False, env="TEST_MODE")
    
    @property
    def supported_languages_list(self) -> List[str]:
        """Get supported languages as a list"""
        if isinstance(self.supported_languages, str):
            return [lang.strip() for lang in self.supported_languages.split(",")]
        return self.supported_languages
    
    @property
    def pinecone_namespaces(self) -> List[str]:
        """Get Pinecone namespaces as a list"""
        return ["faq", "menu", "jobs", "events"]
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    @validator("openai_temperature")
    def validate_temperature(cls, v):
        """Validate OpenAI temperature"""
        if not 0 <= v <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        return v
    
    @validator("conversation_ttl")
    def validate_conversation_ttl(cls, v):
        """Validate conversation TTL"""
        if v < 0:
            raise ValueError("Conversation TTL must be positive")
        return v
    
    class Config:
        # Load from .env file
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
_settings = None

def get_settings() -> Settings:
    """Get settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def reload_settings() -> Settings:
    """Reload settings from environment"""
    global _settings
    _settings = Settings()
    return _settings 