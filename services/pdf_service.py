"""
PDF Generation Service
Handles PDF creation using WeasyPrint and HTML templates
"""
import tempfile
import os
from pathlib import Path
from datetime import datetime
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
from config import settings


class PDFGenerationService:
    def __init__(self):
        self.company_name = settings.PDF_COMPANY_NAME
        
        # Setup Jinja2 environment for templates
        self.jinja_env = Environment(loader=FileSystemLoader('templates'))
        
        # Get logo path - WeasyPrint needs absolute path
        project_root = Path(__file__).parent.parent
        logo_path = project_root / "static" / "assets" / "image" / "aa-logo.png"
        if logo_path.exists():
            # Use absolute path for WeasyPrint (it handles file:// automatically)
            abs_path = logo_path.absolute()
            # Convert to file:// URL format for WeasyPrint
            self.logo_path = abs_path.as_uri()
        else:
            self.logo_path = None
            print(f"⚠️  Logo not found at: {logo_path}")
        
        # Define field configurations for different form types
        self.LOI_FIELDS = [
            ("Name", "full_name", "Not provided"),
            ("Industry", "industry", "Not specified"),
            ("Location", "location", "Not specified"),
            ("Purchase Price", "formatted_purchase_price", "Not specified"),
            ("Offer Price", "formatted_revenue", "Not specified"),
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
        
        self.LOI_NARRATIVE_SECTIONS = [
            ("Key factors that impact valuation / multiple (what makes this deal strong or weak?)", "deal_likes_dislikes"),
            ("What leverage points do you see (red flags, risks, inconsistencies) and your negotiation angle or offer strategy?", "deal_questions_concerns"),
        ]
        
        self.CIM_NARRATIVE_SECTIONS = [
            ("Search Narrative Connection", "search_narrative_relation"),
            ("Deal Interest", "deal_likes_dislikes"),
            ("Questions/Concerns", "deal_questions_concerns"),
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
        if form_type == "CIM" or form_type == "CIM_TRAINING":
            fields = self.CIM_FIELDS
            narrative_sections = self.CIM_NARRATIVE_SECTIONS
        else:
            fields = self.LOI_FIELDS
            narrative_sections = self.LOI_NARRATIVE_SECTIONS
        
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
        for section_title, attr_name in narrative_sections:
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
            narrative_sections=narrative_sections,
            company_name=self.company_name,
            timestamp=timestamp,
            logo_path=self.logo_path
        )
        
        # Generate PDF from HTML using WeasyPrint
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf_path = temp_file.name
        temp_file.close()
        
        # Generate PDF with base_url to resolve relative paths
        base_url = str(Path(__file__).parent.parent.absolute())
        HTML(string=html_content, base_url=base_url).write_pdf(pdf_path)
        
        return pdf_path
    
    # Backward compatibility aliases
    def generate_business_acquisition_pdf(self, submission) -> str:
        """Legacy method - calls generate_pdf with LOI type"""
        return self.generate_pdf(submission, "LOI")
    
    def generate_cim_pdf(self, submission) -> str:
        """Legacy method - calls generate_pdf with CIM type"""
        return self.generate_pdf(submission, "CIM")


# Singleton instance
pdf_service = PDFGenerationService()
