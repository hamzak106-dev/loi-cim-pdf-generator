"""
Business logic services for Business Acquisition PDF Generator
"""
import json
import tempfile
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
    
    async def send_confirmation_email(self, submission: BusinessAcquisition) -> bool:
        """
        Send confirmation email to the user
        This is a placeholder implementation
        """
        print(f"📧 EMAIL CONFIRMATION PLACEHOLDER:")
        print(f"   To: {submission.email}")
        print(f"   From: {self.from_email}")
        print(f"   Subject: Business Acquisition Submission Received - {submission.full_name}")
        print(f"   Content: Thank you for submitting your business acquisition details.")
        print(f"   Purchase Price: {submission.formatted_purchase_price}")
        print(f"   Revenue: {submission.formatted_revenue}")
        print(f"   Industry: {submission.industry or 'Not specified'}")
        print(f"   Submission ID: {submission.id}")
        print("   (This is a placeholder - implement actual email sending here)")
        
        return True
    
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
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#0d6efd')
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#0d6efd')
        )
        
        label_style = ParagraphStyle(
            'Label',
            parent=styles['Normal'],
            textColor=colors.HexColor('#0d6efd'),
            fontName='Helvetica-Bold'
        )
        
        value_style = ParagraphStyle(
            'Value',
            parent=styles['Normal'],
            textColor=colors.HexColor('#212529')
        )
        
        # Title
        story.append(Paragraph("🏢 Business Acquisition Report", title_style))
        story.append(Spacer(1, 10))
        if submission.created_at:
            story.append(Paragraph(submission.created_at.strftime('%B %d, %Y at %I:%M %p'), styles['Normal']))
        story.append(Spacer(1, 20))

        # Helper to render key-value pairs as Paragraph
        def kv(label: str, value: str) -> Paragraph:
            safe_value = value if value not in (None, "") else 'Not provided'
            return Paragraph(f"<b>{label}:</b> {safe_value}", styles['Normal'])

        # Two-column grid (col-6)
        story.append(Paragraph("Profile", header_style))
        grid_items = [
            ("Name", submission.full_name or ''),
            ("Industry", submission.industry or ''),
            ("Location", submission.location or ''),
            ("Seller Role", submission.seller_role or ''),
            ("Purchase Price", submission.formatted_purchase_price),
            ("Revenue", submission.formatted_revenue),
            ("Avg SDE", submission.formatted_avg_sde),
            ("Reason for selling", submission.reason_for_selling or ''),
            ("Owner Involvement", submission.owner_involvement or ''),
            ("Customer Concentration Risk", submission.customer_concentration_risk or ''),
            ("Competition", submission.deal_competitiveness or ''),
            ("Seller Note", submission.seller_note_openness or ''),
        ]

        # Pair into rows of two
        rows = []
        for i in range(0, len(grid_items), 2):
            left = kv(*grid_items[i])
            right = kv(*grid_items[i+1]) if i+1 < len(grid_items) else Paragraph("", styles['Normal'])
            rows.append([left, right])

        table = Table(rows, colWidths=[3.25*inch, 3.25*inch])
        table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#dee2e6')),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(table)
        story.append(Spacer(1, 20))

        # Full-width narrative sections (col-12)
        story.append(Paragraph("Deal Analysis & Search Narrative", header_style))

        narrative_sections = [
            ("Search Narrative Fit", submission.cim_search_narrative_fit or ''),
            ("Search Narrative Connection", submission.search_narrative_relation or ''),
            ("Deal Interest", submission.deal_likes_dislikes or ''),
            ("Questions / Concerns", submission.deal_questions_concerns or ''),
        ]

        for label, value in narrative_sections:
            story.append(Paragraph(f"<b>{label}</b>", styles['Normal']))
            story.append(Paragraph(value if value else 'Not provided', styles['Normal']))
            story.append(Spacer(1, 10))

        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#6c757d')
        )
        
        story.append(Paragraph(f"Generated by {self.company_name}", footer_style))
        story.append(Paragraph(f"Report Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", footer_style))
        
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
