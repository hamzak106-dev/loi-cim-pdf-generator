import tempfile
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
from models import LOIQuestion, CIMQuestion, BusinessAcquisition
from config import settings

class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.EMAIL_USERNAME
        self.password = settings.EMAIL_PASSWORD
        self.from_email = settings.FROM_EMAIL
    
    async def send_confirmation_email_with_pdf(self, submission, pdf_path: str, form_type: str = "LOI") -> bool:
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

class PDFGenerationService:
    def __init__(self):
        self.company_name = settings.PDF_COMPANY_NAME
        
        # Setup Jinja2 environment for templates
        self.jinja_env = Environment(loader=FileSystemLoader('templates'))
        
        # Define field configurations for different form types
        self.LOI_FIELDS = [
            ("Name", "full_name", "Not provided"),
            ("Industry", "industry", "Not specified"),
            ("Location", "location", "Not specified"),
            ("Purchase Price", "formatted_purchase_price", "Not specified"),
            ("Revenue", "formatted_revenue", "Not specified"),
            ("Avg SDE", "formatted_avg_sde", "Not specified"),
            ("Seller Role", "seller_role", "Not specified"),
            ("Reason for Selling", "reason_for_selling", "Not provided"),
            ("Owner Involvement", "owner_involvement", "Not provided"),
            ("Customer Concentration Risk", "customer_concentration_risk", "Not provided"),
            ("Competition", "deal_competitiveness", "Not provided"),
            ("Seller Note", "seller_note_openness", "Not provided"),
        ]
        
        self.CIM_FIELDS = [
            ("Name", "full_name", "Not provided"),
            ("Industry", "industry", "Not specified"),
            ("Location", "location", "Not specified"),
            ("Purchase Price", "formatted_purchase_price", "Not specified"),
            ("Revenue", "formatted_revenue", "Not specified"),
            ("Avg SDE", "formatted_avg_sde", "Not specified"),
            ("Total $ Adjustments", "formatted_total_adjustments", "Not specified"),
            ("Seller Role", "seller_role", "Not specified"),
            ("Reason for Selling", "reason_for_selling", "Not provided"),
            ("Owner Involvement", "owner_involvement", "Not provided"),
            ("GM in Place", "gm_in_place", "Not specified"),
            ("Tenure of GM", "tenure_of_gm", "Not specified"),
            ("Number of Employees", "number_of_employees", "Not specified"),
        ]
        
        self.NARRATIVE_SECTIONS = [
            ("Search Narrative Connection", "search_narrative_relation"),
            ("Deal Interest", "deal_likes_dislikes"),
            (" Questions/Concerns", "deal_questions_concerns"),
        ]
    
    def generate_pdf(self, submission, form_type: str = "LOI") -> str:
        """
        Universal PDF generator using HTML templates.
        Edit templates/pdf_template.html and templates/pdf_styles.css to customize.
        
        Args:
            submission: Database model instance (LOIQuestion or CIMQuestion)
            form_type: "LOI" or "CIM" to determine field configuration
        
        Returns:
            Path to generated PDF file
        """
        # Select field configuration based on form type
        fields = self.CIM_FIELDS if form_type == "CIM" else self.LOI_FIELDS
        
        # Prepare submission data as dictionary for template
        submission_dict = {}
        for label, attr_name, default in fields:
            value = getattr(submission, attr_name, None)
            if value is None:
                value = default if default else "Not specified"
            # Convert to string if needed
            if not isinstance(value, str):
                value = str(value)
            submission_dict[attr_name] = value
        
        # Add narrative sections
        for section_title, attr_name in self.NARRATIVE_SECTIONS:
            value = getattr(submission, attr_name, None)
            submission_dict[attr_name] = value if value else "Not provided"
        
        # Format timestamp
        if submission.created_at:
            timestamp = submission.created_at.strftime('%B %d, %Y at %I:%M %p')
        else:
            timestamp = datetime.now().strftime('%B %d, %Y at %I:%M %p')
        
        # Render HTML template
        template = self.jinja_env.get_template('pdf_template.html')
        html_content = template.render(
            form_type=form_type,
            submission=submission_dict,
            fields=fields,
            narrative_sections=self.NARRATIVE_SECTIONS,
            company_name=self.company_name,
            timestamp=timestamp
        )
        
        # Generate PDF from HTML using WeasyPrint
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf_path = temp_file.name
        temp_file.close()
        
        HTML(string=html_content).write_pdf(pdf_path)
        
        return pdf_path
    
    # Backward compatibility aliases
    def generate_business_acquisition_pdf(self, submission) -> str:
        """Legacy method - calls generate_pdf with LOI type"""
        return self.generate_pdf(submission, "LOI")
    
    def generate_cim_pdf(self, submission) -> str:
        """Legacy method - calls generate_pdf with CIM type"""
        return self.generate_pdf(submission, "CIM")

email_service = EmailService()
pdf_service = PDFGenerationService()
