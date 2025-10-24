"""
Business logic services for Business Acquisition PDF Generator
"""
import json
import tempfile
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from fastapi import UploadFile
from models import BusinessAcquisition
from config import settings

class GoogleDriveService:
    """Service for handling Google Drive file uploads"""
    
    def __init__(self):
        self.folder_id = settings.GOOGLE_DRIVE_FOLDER_ID
        self.credentials_path = settings.GOOGLE_DRIVE_CREDENTIALS_PATH
    
    async def upload_file(self, file: UploadFile, submission_id: int) -> str:
        """
        Upload file to Google Drive and return the file URL
        This is a placeholder implementation
        """
        print(f"📁 GOOGLE DRIVE UPLOAD PLACEHOLDER:")
        print(f"   File: {file.filename}")
        print(f"   Size: {file.size if hasattr(file, 'size') else 'Unknown'} bytes")
        print(f"   Submission ID: {submission_id}")
        print(f"   Target Folder: {self.folder_id}")
        print("   (This is a placeholder - implement actual Google Drive API here)")
        
        # Placeholder URL - in real implementation, this would be the actual Google Drive file URL
        placeholder_url = f"https://drive.google.com/file/d/placeholder_{submission_id}_{file.filename}/view"
        
        return placeholder_url
    
    async def upload_multiple_files(self, files: List[UploadFile], submission_id: int) -> List[str]:
        """Upload multiple files and return list of URLs"""
        file_urls = []
        
        for file in files:
            if file.filename:  # Skip empty files
                url = await self.upload_file(file, submission_id)
                file_urls.append(url)
        
        return file_urls
    
    def validate_file(self, file: UploadFile) -> tuple[bool, str]:
        """Validate uploaded file"""
        if not file.filename:
            return False, "No file selected"
        
        # Check file extension
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in settings.ALLOWED_FILE_EXTENSIONS:
            return False, f"File type '{file_extension}' not allowed. Allowed types: {', '.join(settings.ALLOWED_FILE_EXTENSIONS)}"
        
        # Check file size (if available)
        if hasattr(file, 'size') and file.size > settings.MAX_FILE_SIZE:
            return False, f"File size exceeds maximum limit of {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
        
        return True, "File is valid"

class EmailService:
    """Service for handling email notifications"""
    
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.EMAIL_USERNAME
        self.password = settings.EMAIL_PASSWORD
        self.from_email = settings.FROM_EMAIL
    
    async def send_confirmation_email_with_pdf(self, submission: BusinessAcquisition, pdf_path: str) -> bool:
        """
        Send confirmation email to the user with PDF attachment
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = submission.email
            msg['Subject'] = f"Business Acquisition Analysis Report - {submission.full_name}"
            print("Email sent successfully to", submission.email)
            # Email body
            body = f"""
            Dear {submission.full_name},
            
            Thank you for submitting your business acquisition details. Please find your professional analysis report attached.
            
            Submission Details:
            • Purchase Price: {submission.formatted_purchase_price}
            • Annual Revenue: {submission.formatted_revenue}
            • Industry: {submission.industry or 'Not specified'}
            • Location: {submission.location or 'Not specified'}
            
            The attached PDF contains a comprehensive analysis of your business acquisition opportunity.
            
            Best regards,
            Business Acquisition Services Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach PDF
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
    
    async def send_admin_notification(self, submission: BusinessAcquisition) -> bool:
        """
        Send notification email to admin about new submission
        This is a placeholder implementation
        """
        admin_email = "admin@businessacquisition.com"  # Configure in settings
        
        print(f"📧 ADMIN NOTIFICATION PLACEHOLDER:")
        print(f"   To: {admin_email}")
        print(f"   From: {self.from_email}")
        print(f"   Subject: New Business Acquisition Submission - {submission.full_name}")
        print(f"   Content: New submission received from {submission.full_name}")
        print(f"   Purchase Price: {submission.formatted_purchase_price}")
        print(f"   Revenue: {submission.formatted_revenue}")
        print(f"   View Details: /admin/submissions/{submission.id}")
        print("   (This is a placeholder - implement actual email sending here)")
        
        return True

class SlackService:
    """Service for handling Slack notifications"""
    
    def __init__(self):
        self.webhook_url = settings.SLACK_WEBHOOK_URL
        self.channel = settings.SLACK_CHANNEL
    
    async def send_notification(self, submission: BusinessAcquisition) -> bool:
        """
        Send Slack notification about new submission
        This is a placeholder implementation
        """
        print(f"💬 SLACK NOTIFICATION PLACEHOLDER:")
        print(f"   Channel: {self.channel}")
        print(f"   Webhook: {self.webhook_url}")
        print(f"   Message: 🏢 New Business Acquisition Submission")
        print(f"   Submitter: {submission.full_name} ({submission.email})")
        print(f"   Purchase Price: {submission.formatted_purchase_price}")
        print(f"   Revenue: {submission.formatted_revenue}")
        print(f"   Industry: {submission.industry or 'Not specified'}")
        print(f"   Location: {submission.location or 'Not specified'}")
        print("   (This is a placeholder - implement actual Slack webhook here)")
        
        return True

class PDFGenerationService:
    """Service for generating PDF documents"""
    
    def __init__(self):
        self.company_name = settings.PDF_COMPANY_NAME
        self.logo_path = settings.PDF_TEMPLATE_LOGO
    
    def generate_business_acquisition_pdf(self, submission: BusinessAcquisition) -> str:
        """Generate a creative PDF for business acquisition submission with specific layout"""
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf_path = temp_file.name
        temp_file.close()
        
        # Create PDF document
        doc = SimpleDocTemplate(pdf_path, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Business Blue Theme Colors
        primary_blue = colors.HexColor('#1B62CF')      # Main Brand Blue
        light_blue = colors.HexColor('#4A8FE7')        # Lighter Blue
        accent_blue = colors.HexColor('#E8F1FC')       # Very Light Blue for backgrounds
        text_dark = colors.HexColor('#2C3E50')         # Dark text
        text_medium = colors.HexColor('#5D6D7E')       # Medium Gray
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=32,
            spaceAfter=10,
            alignment=TA_CENTER,
            textColor=colors.white,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=14,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.white,
            fontName='Helvetica'
        )
        
        section_header_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=15,
            spaceBefore=25,
            textColor=primary_blue,
            fontName='Helvetica-Bold'
        )
        
        label_style = ParagraphStyle(
            'Label',
            parent=styles['Normal'],
            textColor=primary_blue,
            fontName='Helvetica-Bold',
            fontSize=10,
            spaceAfter=3
        )
        
        value_style = ParagraphStyle(
            'Value',
            parent=styles['Normal'],
            textColor=text_dark,
            fontSize=11,
            spaceAfter=15
        )
        
        # Header with gradient effect (simulated with colored table)
        header_data = [[Paragraph("BUSINESS ACQUISITION ANALYSIS", title_style)],
                    [Paragraph("Professional Investment Opportunity Report", subtitle_style)]]
        
        header_table = Table(header_data, colWidths=[7*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), primary_blue),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 20),
            ('BOTTOMPADDING', (0,0), (-1,-1), 20),
            ('LINEBELOW', (0,-1), (-1,-1), 3, light_blue),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 30))

        # Business Overview Section - 6 column layout (2 columns, 6 rows)
        story.append(Paragraph("📊 Business Overview", section_header_style))
        
        # Create data for 2x6 grid
        overview_data = [
            [Paragraph("<b>Name</b>", label_style), 
            Paragraph(submission.full_name or 'Not provided', value_style),
            Paragraph("<b>Industry</b>", label_style),
            Paragraph(submission.industry or 'Not specified', value_style)],
            
            [Paragraph("<b>Location</b>", label_style),
            Paragraph(submission.location or 'Not specified', value_style),
            Paragraph("<b>Purchase Price</b>", label_style),
            Paragraph(submission.formatted_purchase_price, value_style)],
            
            [Paragraph("<b>Revenue</b>", label_style),
            Paragraph(submission.formatted_revenue, value_style),
            Paragraph("<b>Avg SDE</b>", label_style),
            Paragraph(submission.formatted_avg_sde, value_style)],
            
            [Paragraph("<b>Seller Role</b>", label_style),
            Paragraph(submission.seller_role or 'Not specified', value_style),
            Paragraph("<b>Reason for Selling</b>", label_style),
            Paragraph(submission.reason_for_selling or 'Not provided', value_style)],
            
            [Paragraph("<b>Owner Involvement</b>", label_style),
            Paragraph(submission.owner_involvement or 'Not provided', value_style),
            Paragraph("<b>Customer Concentration Risk</b>", label_style),
            Paragraph(submission.customer_concentration_risk or 'Not provided', value_style)],
            
            [Paragraph("<b>Competition</b>", label_style),
            Paragraph(submission.deal_competitiveness or 'Not provided', value_style),
            Paragraph("<b>Seller Note</b>", label_style),
            Paragraph(submission.seller_note_openness or 'Not provided', value_style)],
        ]
        
        overview_table = Table(overview_data, colWidths=[1.2*inch, 2.2*inch, 1.2*inch, 2.2*inch])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), accent_blue),
            ('BACKGROUND', (2,0), (2,-1), accent_blue),
            ('TEXTCOLOR', (0,0), (-1,-1), text_dark),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('GRID', (0,0), (-1,-1), 0.5, light_blue),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(overview_table)
        story.append(Spacer(1, 30))
        
        # Full Width Sections
        full_width_sections = [
            ("🎯 Search Narrative Fit", submission.cim_search_narrative_fit or 'Not provided'),
            ("🔗 Search Narrative Connection", submission.search_narrative_relation or 'Not provided'),
            ("💡 Deal Interest", submission.deal_likes_dislikes or 'Not provided'),
            ("❓ Questions/Concerns", submission.deal_questions_concerns or 'Not provided'),
        ]
        
        for section_title, content in full_width_sections:
            # Section header with blue background
            header_data = [[Paragraph(section_title, 
                                    ParagraphStyle('SectionTitle',
                                                parent=styles['Normal'],
                                                fontSize=14,
                                                textColor=colors.white,
                                                fontName='Helvetica-Bold'))]]
            
            section_header_table = Table(header_data, colWidths=[7*inch])
            section_header_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), primary_blue),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,0), (-1,-1), 10),
                ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                ('LEFTPADDING', (0,0), (-1,-1), 15),
            ]))
            story.append(section_header_table)
            
            # Content box with light blue background
            content_style = ParagraphStyle(
                'ContentBox',
                parent=styles['Normal'],
                fontSize=11,
                textColor=text_dark,
                alignment=TA_LEFT,
                leading=16
            )
            
            content_data = [[Paragraph(content, content_style)]]
            content_table = Table(content_data, colWidths=[7*inch])
            content_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), accent_blue),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('TOPPADDING', (0,0), (-1,-1), 15),
                ('BOTTOMPADDING', (0,0), (-1,-1), 15),
                ('LEFTPADDING', (0,0), (-1,-1), 15),
                ('RIGHTPADDING', (0,0), (-1,-1), 15),
                ('BOX', (0,0), (-1,-1), 1, light_blue),
            ]))
            story.append(content_table)
            story.append(Spacer(1, 20))
        
        # Professional Footer
        story.append(Spacer(1, 30))
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=text_medium
        )
        
        if submission.created_at:
            footer_text = f"Report Generated: {submission.created_at.strftime('%B %d, %Y at %I:%M %p')}"
        else:
            footer_text = f"Report Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        
        footer_data = [[Paragraph("_" * 100, ParagraphStyle('Line', parent=footer_style, textColor=light_blue))],
                    [Paragraph(f"📊 Professional Analysis by {self.company_name}", footer_style)],
                    [Paragraph(footer_text, footer_style)],
                    [Paragraph("This report is confidential and prepared for investment analysis purposes.", footer_style)]]
        
        footer_table = Table(footer_data, colWidths=[7*inch])
        footer_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        story.append(footer_table)
        
        # Build PDF
        doc.build(story)
        
        return pdf_path
    

# Service instances
google_drive_service = GoogleDriveService()
email_service = EmailService()
slack_service = SlackService()
pdf_service = PDFGenerationService()
