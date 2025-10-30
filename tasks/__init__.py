"""
Tasks package - Celery background jobs
"""
from .pdf_tasks import process_submission_complete

__all__ = ['process_submission_complete']
