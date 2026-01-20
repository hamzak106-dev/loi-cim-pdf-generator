import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:root@localhost/lol-pdf-db")
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    APP_NAME: str = "Business Acquisition PDF Generator"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    MAX_FILE_SIZE: int = 10 * 1024 * 1024
    ALLOWED_FILE_EXTENSIONS: set = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif'}
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "uploads")
    
    GOOGLE_DRIVE_FOLDER_ID: Optional[str] = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    GOOGLE_DRIVE_CREDENTIALS_PATH: str = os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH", "service_account.json")
    
    # Google Calendar
    GOOGLE_CALENDAR_ID: Optional[str] = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    
    # Google Service Account Credentials (for dynamic generation)
    GOOGLE_SERVICE_ACCOUNT_TYPE: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_TYPE", "service_account")
    GOOGLE_PROJECT_ID: Optional[str] = os.getenv("GOOGLE_PROJECT_ID")
    GOOGLE_PRIVATE_KEY_ID: Optional[str] = os.getenv("GOOGLE_PRIVATE_KEY_ID")
    GOOGLE_PRIVATE_KEY: Optional[str] = os.getenv("GOOGLE_PRIVATE_KEY")
    GOOGLE_CLIENT_EMAIL: Optional[str] = os.getenv("GOOGLE_CLIENT_EMAIL")
    GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_AUTH_URI: str = os.getenv("GOOGLE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth")
    GOOGLE_TOKEN_URI: str = os.getenv("GOOGLE_TOKEN_URI", "https://oauth2.googleapis.com/token")
    GOOGLE_AUTH_PROVIDER_CERT_URL: str = os.getenv("GOOGLE_AUTH_PROVIDER_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs")
    GOOGLE_CLIENT_CERT_URL: Optional[str] = os.getenv("GOOGLE_CLIENT_CERT_URL")
    GOOGLE_UNIVERSE_DOMAIN: str = os.getenv("GOOGLE_UNIVERSE_DOMAIN", "googleapis.com")
    
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    EMAIL_USERNAME: str = os.getenv("EMAIL_USERNAME", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "")
    CLIENT_TO_EMAIL: Optional[str] = os.getenv("CLIENT_TO_EMAIL")
    
    SLACK_WEBHOOK_URL: Optional[str] = os.getenv("SLACK_WEBHOOK_URL")
    SLACK_CHANNEL: str = os.getenv("SLACK_CHANNEL", "#business-submissions")
    
    PDF_TEMPLATE_LOGO: Optional[str] = os.getenv("PDF_TEMPLATE_LOGO")
    PDF_COMPANY_NAME: str = os.getenv("PDF_COMPANY_NAME", "Business Acquisition Services")
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    
    REQUIRED_FIELDS: list = ["full_name", "email", "purchase_price", "revenue"]

settings = Settings()
