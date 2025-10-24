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
        doc = SimpleDocTemplate(pdf_path, pagesize=letter, topMargin=0.5*inch)
        story = []
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Light Blue Business Theme Colors
        primary_blue = colors.HexColor('#87CEEB')  # Sky Blue
        dark_blue = colors.HexColor('#4682B4')     # Steel Blue
        accent_blue = colors.HexColor('#B0E0E6')   # Powder Blue
        text_dark = colors.HexColor('#2C3E50')     # Dark Blue Gray
        text_light = colors.HexColor('#5D6D7E')    # Light Gray
        
        # Custom styles with light blue theme
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=dark_blue,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=14,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=text_light,
            fontName='Helvetica-Oblique'
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=18,
            spaceAfter=15,
            spaceBefore=20,
            textColor=dark_blue,
            fontName='Helvetica-Bold'
        )
        
        label_style = ParagraphStyle(
            'Label',
            parent=styles['Normal'],
            textColor=dark_blue,
            fontName='Helvetica-Bold',
            fontSize=11
        )
        
        value_style = ParagraphStyle(
            'Value',
            parent=styles['Normal'],
            textColor=text_dark,
            fontSize=11
        )
        
        # Header with company branding
        story.append(Paragraph("🏢 BUSINESS ACQUISITION ANALYSIS", title_style))
        story.append(Paragraph("Professional Investment Opportunity Report", subtitle_style))
        
        # Date and submission info
        if submission.created_at:
            date_style = ParagraphStyle(
                'DateStyle',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_CENTER,
                textColor=text_light
            )
            story.append(Paragraph(f"Generated on {submission.created_at.strftime('%B %d, %Y at %I:%M %p')}", date_style))
        story.append(Spacer(1, 30))

        # Helper to render key-value pairs as Paragraph
        def kv(label: str, value: str) -> Paragraph:
            safe_value = value if value not in (None, "") else 'Not provided'
            return Paragraph(f"<b>{label}:</b> {safe_value}", styles['Normal'])

        # Executive Summary Section
        story.append(Paragraph("📊 EXECUTIVE SUMMARY", header_style))
        
        # Key metrics in a styled table
        key_metrics = [
            ["Submitter", submission.full_name or 'Not provided'],
            ["Industry", submission.industry or 'Not specified'],
            ["Location", submission.location or 'Not specified'],
            ["Purchase Price", submission.formatted_purchase_price],
            ["Annual Revenue", submission.formatted_revenue],
            ["Average SDE", submission.formatted_avg_sde],
        ]
        
        metrics_table = Table(key_metrics, colWidths=[2*inch, 4*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), primary_blue),
            ('BACKGROUND', (1,0), (1,-1), accent_blue),
            ('TEXTCOLOR', (0,0), (0,-1), colors.white),
            ('TEXTCOLOR', (1,0), (1,-1), text_dark),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 12),
            ('GRID', (0,0), (-1,-1), 1, dark_blue),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 25))
        
        # Business Details Section
        story.append(Paragraph("🏢 BUSINESS DETAILS", header_style))
        
        business_details = [
            ("Role in Transaction", submission.seller_role or 'Not specified'),
            ("Reason for Selling", submission.reason_for_selling or 'Not provided'),
            ("Owner Involvement", submission.owner_involvement or 'Not provided'),
            ("Customer Risk Analysis", submission.customer_concentration_risk or 'Not provided'),
            ("Market Competition", submission.deal_competitiveness or 'Not provided'),
            ("Seller Financing", submission.seller_note_openness or 'Not provided'),
        ]
        
        for label, value in business_details:
            story.append(Paragraph(f"<b>{label}:</b>", label_style))
            story.append(Paragraph(value, value_style))
            story.append(Spacer(1, 12))
        
        story.append(Spacer(1, 15))

        # Investment Analysis Section
        story.append(Paragraph("📈 INVESTMENT ANALYSIS & SEARCH NARRATIVE", header_style))

        narrative_sections = [
            ("🎯 Search Narrative Alignment", submission.cim_search_narrative_fit or 'Not provided'),
            ("🔗 Strategic Connection", submission.search_narrative_relation or 'Not provided'),
            ("👍 Investment Highlights & Concerns", submission.deal_likes_dislikes or 'Not provided'),
            ("❓ Due Diligence Questions", submission.deal_questions_concerns or 'Not provided'),
        ]

        for label, value in narrative_sections:
            # Section header with light blue background
            section_header = ParagraphStyle(
                'SectionHeader',
                parent=styles['Normal'],
                fontSize=13,
                textColor=dark_blue,
                fontName='Helvetica-Bold',
                spaceBefore=15,
                spaceAfter=8
            )
            story.append(Paragraph(label, section_header))
            
            # Content in a light blue box
            content_style = ParagraphStyle(
                'ContentStyle',
                parent=styles['Normal'],
                fontSize=11,
                textColor=text_dark,
                leftIndent=20,
                rightIndent=20,
                spaceAfter=15
            )
            story.append(Paragraph(value, content_style))
            
            # Add a subtle separator
            story.append(Spacer(1, 5))

        # Professional Footer
        story.append(Spacer(1, 30))
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=text_light,
            spaceBefore=20
        )
        
        # Footer with light blue line
        story.append(Paragraph("_" * 80, ParagraphStyle('Line', parent=footer_style, textColor=primary_blue)))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"📊 Professional Analysis by {self.company_name}", footer_style))
        story.append(Paragraph(f"Report Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", footer_style))
        story.append(Paragraph("This report is confidential and prepared for investment analysis purposes.", footer_style))
        
        # Build PDF
        doc.build(story)
        
        return pdf_path
    
    def _get_table_style(self) -> TableStyle:
        """Get consistent table styling"""
        return TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#0d6efd')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ])

# Service instances
google_drive_service = GoogleDriveService()
email_service = EmailService()
slack_service = SlackService()
pdf_service = PDFGenerationService()
