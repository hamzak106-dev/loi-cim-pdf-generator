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


class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.EMAIL_USERNAME
        self.password = settings.EMAIL_PASSWORD
        self.from_email = settings.FROM_EMAIL
    
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
            subject_type = "LOI Review"
            if form_type == "CIM":
                subject_type = "CIM Review"
            elif form_type == "CIM_TRAINING":
                subject_type = "CIM Training Review"
            else:
                subject_type = "LOI Questions"
            msg['Subject'] = f"{subject_type} Analysis Report - {submission.full_name}"
            title_message = "Thank you for filling this out. Your live call will be reviewed at scheduled_time."
            if form_type == "CIM_TRAINING":
                title_message = "Thank you for filling this out. Your review will may take 3 to 5 business days."
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
            server.sendmail(self.from_email, submission.email, text)
            server.quit()
            
            print(f"✅ Email sent successfully to {submission.email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {str(e)}")
            return False
    
    def send_invitation_email(self, email: str, password: str, name: str = None) -> bool:
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
            
            # Get base URL from settings or use default
            base_url = getattr(settings, 'BASE_URL', None) or f"http://{settings.HOST}:{settings.PORT}"
            
            body = f"""
{greeting}

You have been invited to access the Business Acquisition Services platform.

Your login credentials are:
Email: {email}
Password: {password}

Please log in at: {base_url}/login

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
