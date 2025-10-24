"""
Configuration settings for Business Acquisition PDF Generator
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application configuration settings"""
    
    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:root@localhost/lol-pdf-db"
    )
    
    # Application Settings
    APP_NAME: str = "Business Acquisition PDF Generator"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8003"))
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_EXTENSIONS: set = {
        'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif'
    }
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "uploads")
    
    # Google Drive Configuration (Placeholders)
    GOOGLE_DRIVE_FOLDER_ID: Optional[str] = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    GOOGLE_DRIVE_CREDENTIALS_PATH: Optional[str] = os.getenv(
        "GOOGLE_DRIVE_CREDENTIALS_PATH", 
        "credentials/google_drive_credentials.json"
    )
    
    # Email Configuration
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    EMAIL_USERNAME: str = os.getenv("EMAIL_USERNAME", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "")
    
    # Slack Configuration (Placeholders)
    SLACK_WEBHOOK_URL: Optional[str] = os.getenv("SLACK_WEBHOOK_URL")
    SLACK_CHANNEL: str = os.getenv("SLACK_CHANNEL", "#business-submissions")
    
    # PDF Generation Settings
    PDF_TEMPLATE_LOGO: Optional[str] = os.getenv("PDF_TEMPLATE_LOGO")
    PDF_COMPANY_NAME: str = os.getenv("PDF_COMPANY_NAME", "Business Acquisition Services")
    
    # Security Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    
    # Validation Settings
    REQUIRED_FIELDS: list = [
        "full_name", 
        "email", 
        "purchase_price", 
        "revenue"
    ]

# Create settings instance
settings = Settings()

# Environment-specific configurations
class DevelopmentConfig(Settings):
    """Development environment configuration"""
    DEBUG = True
    DATABASE_URL = "postgresql://postgres:root@localhost/lol-pdf-db"

class ProductionConfig(Settings):
    """Production environment configuration"""
    DEBUG = False
    # Override with production database URL
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@prod-host/db")

class TestingConfig(Settings):
    """Testing environment configuration"""
    DEBUG = True
    DATABASE_URL = "postgresql://postgres:root@localhost/test_lol_pdf_db"

# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(env: str = 'default') -> Settings:
    """Get configuration based on environment"""
    return config_map.get(env, DevelopmentConfig)()
