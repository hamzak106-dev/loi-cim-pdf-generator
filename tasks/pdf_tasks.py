"""
PDF Processing Tasks
Background jobs for PDF generation, email sending, and file uploads
"""
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

from celery_worker.celery_config import celery_app
from services import pdf_service, email_service, create_drive_uploader, create_slack_notifier
from db import Form, FormType, SessionLocal
from config import settings


@celery_app.task(bind=True)
def process_submission_complete(self, submission_id: int, files_data: list = None, form_type: str = "LOI"):
    """
    Complete processing workflow for form submissions
    
    Steps:
    1. Generate PDF from submission data
    2. Upload user files to Google Drive (if any)
    3. Upload generated PDF to Google Drive
    4. Send confirmation email with PDF
    5. Send Slack notification
    6. Cleanup temporary files
    
    Args:
        submission_id: Database ID of the submission
        files_data: List of uploaded file information
        form_type: "LOI" or "CIM"
        
    Returns:
        dict: Status and submission_id
    """
    try:
        db = SessionLocal()
        # Use unified Form model
        submission = db.query(Form).filter(Form.id == submission_id).first()
        
        if not submission:
            raise ValueError(f"Submission {submission_id} not found")
        
        print(f"🚀 Starting complete processing for {form_type} submission {submission_id}")
        
        # Step 1: Generate PDF
        pdf_path = pdf_service.generate_pdf(submission, form_type)
        submission.pdf_generated = True
        db.commit()
        print(f"✅ PDF generated: {pdf_path}")
        
        # Step 2: Upload user files to Google Drive
        uploaded_file_url = None
        if files_data and len(files_data) > 0:
            print(f"📁 Processing {len(files_data)} uploaded files...")
            try:
                file_info = files_data[0]
                file_path = file_info.get('file_path')
                file_name = file_info.get('filename')
                mime_type = file_info.get('content_type', 'application/octet-stream')
                
                if file_path and os.path.exists(file_path):
                    drive_uploader = create_drive_uploader(
                        folder_id=settings.GOOGLE_DRIVE_FOLDER_ID
                    )
                    
                    upload_result = drive_uploader.upload_file(file_path, file_name, mime_type)
                    uploaded_file_url = upload_result['shareable_url']
                    
                    submission.uploaded_file_url = uploaded_file_url
                    submission.attachment_count = len(files_data)
                    db.commit()
                    
                    print(f"✅ User file uploaded to Google Drive: {file_name}")
                    print(f"📎 File URL: {uploaded_file_url}")
                    
                    # Cleanup uploaded file
                    try:
                        os.remove(file_path)
                        print(f"🗑️ Cleaned up uploaded file")
                    except Exception as e:
                        print(f"⚠️ Could not clean up uploaded file: {e}")
                else:
                    print(f"⚠️ File path not found or invalid")
                    
            except Exception as e:
                print(f"❌ Failed to upload user file to Drive: {e}")
                import traceback
                traceback.print_exc()
        
        # Step 3: Upload PDF to Google Drive
        drive_url = None
        file_prefix = "cim_overview" if form_type == "CIM" else "loi_overview"
        drive_file_name = f"{file_prefix}_{submission.full_name.replace(' ', '_')}_{submission.id}.pdf"
        
        try:
            print(f"☁️ Uploading PDF to Google Drive...")
            print(f"📂 Folder ID: {settings.GOOGLE_DRIVE_FOLDER_ID or 'Root folder'}")
            
            drive_uploader = create_drive_uploader(
                folder_id=settings.GOOGLE_DRIVE_FOLDER_ID
            )
            
            upload_result = drive_uploader.upload_pdf(pdf_path, drive_file_name)
            drive_url = upload_result['shareable_url']
            
            submission.file_urls = drive_url
            db.commit()
            
            print(f"✅ PDF uploaded to Google Drive")
            print(f"📎 Drive URL: {drive_url}")
            
        except FileNotFoundError as e:
            print(f"❌ Service account file not found: {e}")
            print(f"⚠️ Skipping Google Drive upload")
        except Exception as e:
            print(f"❌ Google Drive upload failed: {e}")
            import traceback
            traceback.print_exc()
            print(f"⚠️ Continuing without Drive upload")
        
        # Step 4: Send confirmation email
        print(f"📧 Sending email to {submission.email}...")
        try:
            email_sent = asyncio.run(
                email_service.send_confirmation_email_with_pdf(submission, pdf_path, form_type)
            )
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
        else:
            print("✅ Email sent successfully!")
        
        submission.email_sent = email_sent
        db.commit()
        print(f"✅ Email sent: {email_sent}")
        
        # Step 5: Send Slack notification
        try:
            print(f"💬 Sending Slack notification...")
            
            if not settings.SLACK_WEBHOOK_URL:
                print(f"⚠️ SLACK_WEBHOOK_URL not configured, skipping Slack notification")
            else:
                slack_notifier = create_slack_notifier(
                    webhook_url=settings.SLACK_WEBHOOK_URL,
                    channel=settings.SLACK_CHANNEL
                )
                
                submission_data = {
                    'full_name': submission.full_name,
                    'email': submission.email,
                    'formatted_purchase_price': submission.formatted_purchase_price,
                    'formatted_revenue': submission.formatted_revenue,
                    'industry': submission.industry,
                    'location': submission.location
                }
                
                if drive_url:
                    print(f"📎 Including Drive URL in notification")
                    slack_sent = slack_notifier.send_pdf_notification(
                        submission_data=submission_data,
                        drive_url=drive_url,
                        file_name=drive_file_name,
                        uploaded_file_url=uploaded_file_url
                    )
                else:
                    print(f"⚠️ No Drive URL available, sending simple notification")
                    form_label = "CIM Questions" if form_type == "CIM" else "LOI Questions"
                    message = f"New {form_label} Submission from {submission.full_name} ({submission.email})"
                    slack_sent = slack_notifier.send_simple_message(message)
                
                if slack_sent:
                    print(f"✅ Slack notification sent successfully")
                else:
                    print(f"⚠️ Slack notification failed")
                    
        except Exception as e:
            print(f"❌ Slack notification error: {e}")
            import traceback
            traceback.print_exc()
        
        # Step 6: Cleanup temporary PDF file
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
                print(f"🗑️ Cleaned up PDF file")
        except Exception as e:
            print(f"⚠️ Could not clean up PDF: {e}")
        
        # Mark as processed
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
