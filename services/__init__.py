"""
Services package - Core business logic organized by feature
"""
from .pdf_service import PDFGenerationService, pdf_service
from .email_service import EmailService, email_service
from .drive_service import create_drive_uploader
from .slack_service import create_slack_notifier
from .auth_service import AuthService, auth_service
from .submission_helpers import get_or_create_user, create_submission_record, process_form_submission

__all__ = [
    'PDFGenerationService',
    'pdf_service',
    'EmailService',
    'email_service',
    'create_drive_uploader',
    'create_slack_notifier',
    'AuthService',
    'auth_service',
    'get_or_create_user',
    'create_submission_record',
    'process_form_submission',
]
