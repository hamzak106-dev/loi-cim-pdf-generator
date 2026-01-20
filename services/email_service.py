"""
Email Service
Handles sending confirmation emails with PDF attachments
"""
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from config import settings
from db import MeetingRegistration, MeetingInstance, SessionLocal
from datetime import datetime
import pytz


class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.EMAIL_USERNAME
        self.password = settings.EMAIL_PASSWORD
        self.from_email = settings.FROM_EMAIL
    
    def _get_scheduled_time(self, submission_email: str, form_type: str) -> str:
        """
        Get the scheduled meeting time for a submission
        
        Args:
            submission_email: Email address of the submitter
            form_type: "LOI", "CIM", or "CIM_TRAINING"
            
        Returns:
            Formatted scheduled time string or empty string if not found
        """
        try:
            db = SessionLocal()
            try:
                # Find the most recent MeetingRegistration for this email
                registration = db.query(MeetingRegistration).filter(
                    MeetingRegistration.email == submission_email.lower().strip()
                ).order_by(MeetingRegistration.registered_at.desc()).first()
                
                if not registration:
                    return ""
                
                # Get the MeetingInstance
                instance = db.query(MeetingInstance).filter(
                    MeetingInstance.id == registration.instance_id
                ).first()
                
                if not instance or not instance.instance_time:
                    return ""
                
                # Format the time nicely
                scheduled_time = instance.instance_time
                
                # Convert to Eastern Time if needed
                if scheduled_time.tzinfo is None:
                    ny_tz = pytz.timezone("America/New_York")
                    scheduled_time = ny_tz.localize(scheduled_time)
                else:
                    ny_tz = pytz.timezone("America/New_York")
                    scheduled_time = scheduled_time.astimezone(ny_tz)
                
                # Format: "Monday, January 15th @ 2:00 PM EST"
                day_name = scheduled_time.strftime("%A")
                month_name = scheduled_time.strftime("%B")
                day = scheduled_time.day
                
                # Add ordinal suffix
                if 10 <= day % 100 <= 20:
                    suffix = "th"
                else:
                    suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
                
                # Format time (use # instead of - for cross-platform compatibility)
                hour = scheduled_time.hour
                minute = scheduled_time.minute
                am_pm = "AM" if hour < 12 else "PM"
                hour_12 = hour if hour <= 12 else hour - 12
                if hour_12 == 0:
                    hour_12 = 12
                time_str = f"{hour_12}:{minute:02d} {am_pm}"
                timezone_str = scheduled_time.strftime("%Z")
                
                formatted_time = f"{day_name}, {month_name} {day}{suffix} @ {time_str} {timezone_str}"
                
                return formatted_time
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"⚠️ Error fetching scheduled time: {e}")
            return ""
    
    def send_confirmation_email_with_pdf(self, submission, pdf_path: str, form_type: str = "LOI") -> bool:
        """
        Send confirmation email with PDF attachment
        
        Args:
            submission: Database model instance with email and submission details
            pdf_path: Path to the generated PDF file
            form_type: "LOI" or "CIM" for email subject customization
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            print("email services, :::::::::::::::::")
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = submission.email
            
            # Recipients for user email
            recipients = [submission.email]
            
            subject_type = "LOI Review"
            if form_type == "CIM":
                subject_type = "CIM Review"
            elif form_type == "CIM_TRAINING":
                subject_type = "CIM Training Review"
            else:
                subject_type = "LOI Questions"
            msg['Subject'] = f"{subject_type} Analysis Report - {submission.full_name}"
            
            # Get scheduled time for LOI and CIM forms (not CIM_TRAINING)
            scheduled_time_str = ""
            if form_type in ["LOI", "CIM"]:
                scheduled_time_str = self._get_scheduled_time(submission.email, form_type)
            
            # Build the message based on form type
            if form_type == "CIM_TRAINING":
                title_message = "Thank you for filling this out. Your review will may take 3 to 5 business days."
            elif scheduled_time_str:
                title_message = f"Thank you for filling this out. Your live call will be reviewed at {scheduled_time_str}."
            else:
                title_message = "Thank you for filling this out. Your live call will be reviewed at the scheduled time."
            
            body = f"""
            Dear {submission.full_name},
            
            {title_message}
            
            Best regards,
            Your Ace Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach PDF if it exists
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= business_acquisition_report_{submission.id}.pdf'
                )
                msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            text = msg.as_string()
            server.sendmail(self.from_email, recipients, text)
            server.quit()
            
            print(f"✅ Email sent successfully to {submission.email}")
            
            # Send separate email to CLIENT_TO_EMAIL if configured
            if settings.CLIENT_TO_EMAIL:
                try:
                    print(f"📧 Sending separate email to CLIENT_TO_EMAIL ({settings.CLIENT_TO_EMAIL})...")
                    client_msg = MIMEMultipart()
                    client_msg['From'] = self.from_email
                    client_msg['To'] = settings.CLIENT_TO_EMAIL
                    client_msg['Subject'] = f"[Client Copy] {msg['Subject']}"
                    
                    # Use the same body as the user email
                    client_msg.attach(MIMEText(body, 'plain'))
                    
                    # Attach PDF if it exists
                    if os.path.exists(pdf_path):
                        with open(pdf_path, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= business_acquisition_report_{submission.id}.pdf'
                        )
                        client_msg.attach(part)
                    
                    # Send email to client
                    server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                    server.starttls()
                    server.login(self.username, self.password)
                    client_text = client_msg.as_string()
                    server.sendmail(self.from_email, [settings.CLIENT_TO_EMAIL], client_text)
                    server.quit()
                    
                    print(f"✅ Separate email sent successfully to CLIENT_TO_EMAIL ({settings.CLIENT_TO_EMAIL})")
                except Exception as e:
                    print(f"⚠️ Failed to send email to CLIENT_TO_EMAIL: {str(e)}")
                    # Don't fail the whole operation if client email fails
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {str(e)}")
            return False
    
    def send_invitation_email(self, email: str, password: str, name: str = None, base_url: str = None) -> bool:
        """
        Send invitation email with login credentials
        
        Args:
            email: User's email address
            password: Generated password for the user
            name: User's name (optional)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = email
            msg['Subject'] = "Your Business Acquisition Services Account"
            
            greeting = f"Dear {name}," if name else "Hello,"
            
            # Build a robust base URL for the login link
            # Prefer caller-provided base_url (e.g., from request.base_url)
            base_url = (base_url)
            print("base url >>>>>>>>>>>>>>>>>>>>>>>", base_url)
            if not base_url:
                # Fallback to HOST and PORT. If HOST is 0.0.0.0, present localhost for email link
                host = getattr(settings, 'HOST', '127.0.0.1')
                port = getattr(settings, 'PORT', 8000)
                host_for_url = 'localhost' if host in ('0.0.0.0', '127.0.0.1') else host
                base_url = f"http://{host_for_url}:{port}"
            base_url = base_url.rstrip('/')
            login_url = f"{base_url}/login"

            body = f"""
{greeting}

You have been invited to access the Business Acquisition Services platform.

Your login credentials are:
Email: {email}
Password: {password}

Please log in at: {login_url}

After logging in, you can access the forms to submit LOI and CIM reviews.

Best regards,
Business Acquisition Services Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            text = msg.as_string()
            server.sendmail(self.from_email, email, text)
            server.quit()
            
            print(f"✅ Invitation email sent successfully to {email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send invitation email: {str(e)}")
            return False


# Singleton instance
email_service = EmailService()
