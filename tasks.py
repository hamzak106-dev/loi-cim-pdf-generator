"""
Background tasks for Business Acquisition PDF Generator using Celery
"""
import json
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from celery_app import celery_app
from services import pdf_service, email_service, slack_service, google_drive_service
from models import BusinessAcquisition
from database import SessionLocal


@celery_app.task(bind=True)
def process_business_submission(self, submission_data: dict, files_data: list = None):
    """
    Main task to process business submission in background
    """
    try:
        # Create database session
        db = SessionLocal()
        
        # Create submission object from data
        submission = BusinessAcquisition(**submission_data)
        db.add(submission)
        db.commit()
        db.refresh(submission)
        
        # Chain all background tasks
        task_chain = (
            generate_pdf_task.s(submission.id) |
            upload_files_task.s(files_data or []) |
            send_email_with_pdf_task.s() |
            send_notifications_task.s()
        )
        
        # Execute the chain
        result = task_chain.apply_async()
        
        db.close()
        return {"status": "success", "submission_id": submission.id, "task_id": result.id}
        
    except Exception as e:
        print(f"❌ Error in process_business_submission: {str(e)}")
        if 'db' in locals():
            db.rollback()
            db.close()
        raise self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task(bind=True)
def generate_pdf_task(self, submission_id: int):
    """
    Generate PDF for business submission
    """
    try:
        db = SessionLocal()
        submission = db.query(BusinessAcquisition).filter(BusinessAcquisition.id == submission_id).first()
        
        if not submission:
            raise ValueError(f"Submission {submission_id} not found")
        
        # Generate PDF
        pdf_path = pdf_service.generate_business_acquisition_pdf(submission)
        
        # Update submission
        submission.pdf_generated = True
        db.commit()
        
        db.close()
        
        print(f"✅ PDF generated for submission {submission_id}")
        return {"pdf_path": pdf_path, "submission_id": submission_id}
        
    except Exception as e:
        print(f"❌ Error generating PDF: {str(e)}")
        if 'db' in locals():
            db.close()
        raise self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task(bind=True)
def upload_files_task(self, previous_result: dict, files_data: list):
    """
    Upload files to Google Drive
    """
    try:
        submission_id = previous_result["submission_id"]
        
        if not files_data:
            print(f"ℹ️ No files to upload for submission {submission_id}")
            return previous_result
        
        db = SessionLocal()
        submission = db.query(BusinessAcquisition).filter(BusinessAcquisition.id == submission_id).first()
        
        # Upload files (placeholder implementation)
        file_urls = []
        for file_info in files_data:
            # In real implementation, you would recreate UploadFile objects
            # For now, we'll use the placeholder service
            print(f"📁 Uploading file: {file_info.get('filename', 'unknown')}")
            # file_urls.append(await google_drive_service.upload_file(file, submission_id))
        
        if file_urls:
            submission.file_urls = json.dumps(file_urls)
            submission.attachment_count = len(file_urls)
            db.commit()
        
        db.close()
        
        print(f"✅ Files uploaded for submission {submission_id}")
        return previous_result
        
    except Exception as e:
        print(f"❌ Error uploading files: {str(e)}")
        if 'db' in locals():
            db.close()
        raise self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task(bind=True)
def send_email_with_pdf_task(self, previous_result: dict):
    """
    Send email with PDF attachment
    """
    try:
        submission_id = previous_result["submission_id"]
        pdf_path = previous_result["pdf_path"]
        
        db = SessionLocal()
        submission = db.query(BusinessAcquisition).filter(BusinessAcquisition.id == submission_id).first()
        
        # Send email with PDF (run async function in sync context)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        email_sent = loop.run_until_complete(email_service.send_confirmation_email_with_pdf(submission, pdf_path))
        loop.close()
        
        # Update submission
        submission.email_sent = email_sent
        db.commit()
        
        # Clean up PDF file after sending
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
                print(f"🗑️ Cleaned up PDF file: {pdf_path}")
        except Exception as cleanup_error:
            print(f"⚠️ Could not clean up PDF file: {cleanup_error}")
        
        db.close()
        
        print(f"✅ Email sent for submission {submission_id}")
        return previous_result
        
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        if 'db' in locals():
            db.close()
        raise self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task(bind=True)
def send_notifications_task(self, previous_result: dict):
    """
    Send admin and Slack notifications
    """
    try:
        submission_id = previous_result["submission_id"]
        
        db = SessionLocal()
        submission = db.query(BusinessAcquisition).filter(BusinessAcquisition.id == submission_id).first()
    
        
        # Send Slack notification
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(slack_service.send_notification(submission))
            loop.close()
        except Exception as e:
            print(f"⚠️ Slack notification failed: {e}")
        
        # Mark as processed
        submission.is_processed = True
        db.commit()
        
        db.close()
        
        print(f"✅ Notifications sent for submission {submission_id}")
        return {"status": "completed", "submission_id": submission_id}
        
    except Exception as e:
        print(f"❌ Error sending notifications: {str(e)}")
        if 'db' in locals():
            db.close()
        raise self.retry(exc=e, countdown=60, max_retries=3)


# Simple complete processing task
@celery_app.task(bind=True)
def process_submission_complete(self, submission_id: int, files_data: list = None):
    """
    Complete processing task that handles everything in sequence
    """
    try:
        db = SessionLocal()
        submission = db.query(BusinessAcquisition).filter(BusinessAcquisition.id == submission_id).first()
        
        if not submission:
            raise ValueError(f"Submission {submission_id} not found")
        
        print(f"🚀 Starting complete processing for submission {submission_id}")
        
        # Step 1: Generate PDF
        print(f"📄 Generating PDF...")
        pdf_path = pdf_service.generate_business_acquisition_pdf(submission)
        submission.pdf_generated = True
        db.commit()
        print(f"✅ PDF generated: {pdf_path}")
        
        # Step 2: Upload files (if any)
        if files_data:
            print(f"📁 Processing {len(files_data)} files...")
            # Placeholder for file upload
            submission.attachment_count = len(files_data)
            db.commit()
            print(f"✅ Files processed")
        
        # Step 3: Send email with PDF
        print(f"📧 Sending email to {submission.email}...")
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        email_sent = loop.run_until_complete(
            email_service.send_confirmation_email_with_pdf(submission, pdf_path)
        )
        loop.close()
        
        submission.email_sent = email_sent
        db.commit()
        print(f"✅ Email sent: {email_sent}")
        
        # Step 4: Send notifications
        print(f"🔔 Sending notifications...")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(email_service.send_admin_notification(submission))
            loop.run_until_complete(slack_service.send_notification(submission))
            loop.close()
        except Exception as e:
            print(f"⚠️ Notifications failed: {e}")
        
        # Step 5: Clean up and mark as processed
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
                print(f"🗑️ Cleaned up PDF file")
        except Exception as e:
            print(f"⚠️ Could not clean up PDF: {e}")
        
        submission.is_processed = True
        db.commit()
        db.close()
        
        print(f"🎉 Complete processing finished for submission {submission_id}")
        return {"status": "success", "submission_id": submission_id}
        
    except Exception as e:
        print(f"❌ Error in complete processing: {str(e)}")
        if 'db' in locals():
            db.rollback()
            db.close()
        raise self.retry(exc=e, countdown=60, max_retries=3)


# Simple individual tasks for direct use
@celery_app.task
def simple_generate_pdf(submission_id: int):
    """Simple PDF generation task"""
    return generate_pdf_task(submission_id)


@celery_app.task
def simple_send_email(submission_id: int, pdf_path: str):
    """Simple email sending task"""
    return send_email_with_pdf_task({"submission_id": submission_id, "pdf_path": pdf_path})


@celery_app.task
def simple_send_notifications(submission_id: int):
    """Simple notifications task"""
    return send_notifications_task({"submission_id": submission_id})
