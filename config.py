import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:root@localhost/lol-pdf-db")
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
    
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    EMAIL_USERNAME: str = os.getenv("EMAIL_USERNAME", "")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "")
    
    SLACK_WEBHOOK_URL: Optional[str] = os.getenv("SLACK_WEBHOOK_URL")
    SLACK_CHANNEL: str = os.getenv("SLACK_CHANNEL", "#business-submissions")
    
    PDF_TEMPLATE_LOGO: Optional[str] = os.getenv("PDF_TEMPLATE_LOGO")
    PDF_COMPANY_NAME: str = os.getenv("PDF_COMPANY_NAME", "Business Acquisition Services")
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    
    REQUIRED_FIELDS: list = ["full_name", "email", "purchase_price", "revenue"]

settings = Settings()
