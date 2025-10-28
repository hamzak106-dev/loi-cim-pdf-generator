import tempfile
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
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
        
        # Define field configurations for different form types
        self.LOI_FIELDS = [
            ("Name", "full_name", "Not provided"),
            ("Industry", "industry", "Not specified"),
            ("Location", "location", "Not specified"),
            ("Purchase Price", "formatted_purchase_price", None),
            ("Revenue", "formatted_revenue", None),
            ("Avg SDE", "formatted_avg_sde", None),
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
            ("Purchase Price", "formatted_purchase_price", None),
            ("Revenue", "formatted_revenue", None),
            ("Avg SDE", "formatted_avg_sde", None),
            ("Total $ Adjustments", "formatted_total_adjustments", None),
            ("Seller Role", "seller_role", "Not specified"),
            ("Reason for Selling", "reason_for_selling", "Not provided"),
            ("Owner Involvement", "owner_involvement", "Not provided"),
            ("GM in Place", "gm_in_place", "Not specified"),
            ("Tenure of GM", "tenure_of_gm", "Not specified"),
            ("Number of Employees", "number_of_employees", "Not specified"),
        ]
        
        self.NARRATIVE_SECTIONS = [
            ("🎯 Search Narrative Fit", "cim_search_narrative_fit"),
            ("🔗 Search Narrative Connection", "search_narrative_relation"),
            ("💡 Deal Interest", "deal_likes_dislikes"),
            ("❓ Questions/Concerns", "deal_questions_concerns"),
        ]
    
    def generate_pdf(self, submission, form_type: str = "LOI") -> str:
        """
        Universal PDF generator for any form type.
        Change PDF style once here, applies to all forms.
        
        Args:
            submission: Database model instance (LOIQuestion or CIMQuestion)
            form_type: "LOI" or "CIM" to determine field configuration
        
        Returns:
            Path to generated PDF file
        """
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf_path = temp_file.name
        temp_file.close()
        
        doc = SimpleDocTemplate(pdf_path, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        styles = getSampleStyleSheet()
        
        primary_blue = colors.HexColor('#1B62CF')
        light_blue = colors.HexColor('#4A8FE7')
        accent_blue = colors.HexColor('#E8F1FC')
        text_dark = colors.HexColor('#2C3E50')
        text_medium = colors.HexColor('#5D6D7E')
        
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
        
        # Dynamic title based on form type
        title_text = f"{form_type} Overview"
        header_data = [[Paragraph(title_text, title_style)],
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

        story.append(Paragraph("📊 Business Overview", section_header_style))
        
        # Select field configuration based on form type
        fields = self.CIM_FIELDS if form_type == "CIM" else self.LOI_FIELDS
        
        # Build overview data dynamically from field configuration
        overview_data = []
        row = []
        for i, (label, attr_name, default) in enumerate(fields):
            # Get value from submission
            value = getattr(submission, attr_name, default)
            if value is None:
                value = default if default else "Not specified"
            
            # Convert to string if needed (for number_of_employees)
            if not isinstance(value, str):
                value = str(value)
            
            row.append(Paragraph(f"<b>{label}</b>", label_style))
            row.append(Paragraph(value, value_style))
            
            # Create new row every 2 fields (4 columns: label, value, label, value)
            if len(row) == 4:
                overview_data.append(row)
                row = []
        
        # Add remaining fields if odd number
        if row:
            # Pad with empty cells
            while len(row) < 4:
                row.append(Paragraph("", label_style))
            overview_data.append(row)
        
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
        
        # Build narrative sections dynamically from configuration
        for section_title, attr_name in self.NARRATIVE_SECTIONS:
            content = getattr(submission, attr_name, None) or 'Not provided'
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
        
        doc.build(story)
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

