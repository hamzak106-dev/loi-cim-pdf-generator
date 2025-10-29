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
    
    async def send_confirmation_email_with_pdf(self, submission, pdf_path: str, form_type: str = "LOI") -> bool:
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
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = submission.email
            subject_type = "LOI Questions" if form_type == "LOI" else "CIM Questions"
            msg['Subject'] = f"{subject_type} Analysis Report - {submission.full_name}"
            
            body = f"""
            Dear {submission.full_name},
            
            Thank you for submitting your {subject_type}. Please find your professional analysis report attached.
            
            Submission Details:
            • Purchase Price: {submission.formatted_purchase_price}
            • Annual Revenue: {submission.formatted_revenue}
            • Industry: {submission.industry or 'Not specified'}
            • Location: {submission.location or 'Not specified'}
            
            The attached PDF contains a comprehensive analysis of your business opportunity.
            
            Best regards,
            Business Acquisition Services Team
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


# Singleton instance
email_service = EmailService()
