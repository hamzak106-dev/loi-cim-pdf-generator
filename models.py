"""
Database models for Business Acquisition PDF Generator
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Optional

Base = declarative_base()

class LOIQuestion(Base):
    """
    Model for LOI Questions submissions
    """
    __tablename__ = 'loi_question'
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Required Text Fields
    full_name = Column(String(100), nullable=False, comment="Full name of the submitter")
    email = Column(String(120), nullable=False, comment="Email address for communication")
    
    # Optional Text Fields
    industry = Column(String(100), nullable=True, comment="Industry sector of the business")
    location = Column(String(200), nullable=True, comment="Geographic location of the business")
    seller_role = Column(String(100), nullable=True, comment="Role of the seller in the business")
    
    # Financial Fields
    purchase_price = Column(Float, nullable=False, comment="Proposed purchase price")
    revenue = Column(Float, nullable=False, comment="Annual revenue of the business")
    avg_sde = Column(Float, nullable=True, comment="Average Seller's Discretionary Earnings")
    
    # Text Area Fields (Long text)
    reason_for_selling = Column(Text, nullable=True, comment="Detailed reason for selling the business")
    owner_involvement = Column(Text, nullable=True, comment="Owner's role, hours per week, etc.")
    customer_concentration_risk = Column(Text, nullable=True, comment="Analysis of customer concentration risks")
    deal_competitiveness = Column(Text, nullable=True, comment="How competitive is this deal")
    seller_note_openness = Column(Text, nullable=True, comment="Seller's openness to seller financing")
    
    # New Search Narrative Fields
    cim_search_narrative_fit = Column(Text, nullable=True, comment="Does the CIM fit your Search Narrative & your Search Narrative Question Guide?")
    search_narrative_relation = Column(Text, nullable=True, comment="How does this relate to your search narrative?")
    deal_likes_dislikes = Column(Text, nullable=True, comment="What do you like/don't like about the deal?")
    deal_questions_concerns = Column(Text, nullable=True, comment="What questions/concerns do you have about the deal?")
    
    # File Upload Fields
    file_urls = Column(Text, nullable=True, comment="Google Drive URL for generated PDF")
    uploaded_file_url = Column(Text, nullable=True, comment="Google Drive URL for user-uploaded attachment")
    attachment_count = Column(Integer, default=0, comment="Number of files attached")
    
    # Terms and Conditions
    terms_accepted = Column(Boolean, default=False, nullable=False, comment="User accepted terms and conditions")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, comment="Submission timestamp")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Last update timestamp")
    
    # Status and Processing
    is_processed = Column(Boolean, default=False, comment="Whether the submission has been processed")
    pdf_generated = Column(Boolean, default=False, comment="Whether PDF has been generated")
    email_sent = Column(Boolean, default=False, comment="Whether confirmation email has been sent")
    
    def __repr__(self):
        return f'<LOIQuestion {self.full_name} - ${self.purchase_price:,.0f}>'
    
    def to_dict(self) -> dict:
        """Convert model instance to dictionary"""
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'industry': self.industry,
            'location': self.location,
            'seller_role': self.seller_role,
            'purchase_price': self.purchase_price,
            'revenue': self.revenue,
            'avg_sde': self.avg_sde,
            'reason_for_selling': self.reason_for_selling,
            'owner_involvement': self.owner_involvement,
            'customer_concentration_risk': self.customer_concentration_risk,
            'deal_competitiveness': self.deal_competitiveness,
            'seller_note_openness': self.seller_note_openness,
            'cim_search_narrative_fit': self.cim_search_narrative_fit,
            'search_narrative_relation': self.search_narrative_relation,
            'deal_likes_dislikes': self.deal_likes_dislikes,
            'deal_questions_concerns': self.deal_questions_concerns,
            'file_urls': self.file_urls,
            'attachment_count': self.attachment_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_processed': self.is_processed,
            'pdf_generated': self.pdf_generated,
            'email_sent': self.email_sent,
            'terms_accepted': self.terms_accepted
        }
    
    @property
    def formatted_purchase_price(self) -> str:
        """Format purchase price as currency"""
        if self.purchase_price:
            return f"${self.purchase_price:,.0f}"
        return "Not specified"
    
    @property
    def formatted_revenue(self) -> str:
        """Format revenue as currency"""
        if self.revenue:
            return f"${self.revenue:,.0f}"
        return "Not specified"
    
    @property
    def formatted_avg_sde(self) -> str:
        """Format average SDE as currency"""
        if self.avg_sde:
            return f"${self.avg_sde:,.0f}"
        return "Not specified"

class CIMQuestion(Base):
    """
    Model for CIM Questions submissions
    """
    __tablename__ = 'cim_question'
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Required Text Fields
    full_name = Column(String(100), nullable=False, comment="Full name of the submitter")
    email = Column(String(120), nullable=False, comment="Email address for communication")
    
    # Optional Text Fields
    industry = Column(String(100), nullable=True, comment="Industry sector of the business")
    location = Column(String(200), nullable=True, comment="Geographic location of the business")
    seller_role = Column(String(100), nullable=True, comment="Role of the seller in the business")
    
    # Financial Fields
    purchase_price = Column(Float, nullable=False, comment="Proposed purchase price")
    revenue = Column(Float, nullable=False, comment="Annual revenue of the business")
    avg_sde = Column(Float, nullable=True, comment="Average Seller's Discretionary Earnings")
    total_adjustments = Column(Float, nullable=True, comment="Total dollar adjustments")
    
    # Text Area Fields (Long text)
    reason_for_selling = Column(Text, nullable=True, comment="Detailed reason for selling the business")
    owner_involvement = Column(Text, nullable=True, comment="Owner's role, hours per week, etc.")
    
    # CIM-specific fields
    gm_in_place = Column(String(10), nullable=True, comment="Is there a GM in place? (Yes/No)")
    tenure_of_gm = Column(String(100), nullable=True, comment="Tenure of the GM if applicable")
    number_of_employees = Column(Integer, nullable=True, comment="Number of employees")
    
    # Search Narrative Fields
    cim_search_narrative_fit = Column(Text, nullable=True, comment="Does the CIM fit your Search Narrative & your Search Narrative Question Guide?")
    search_narrative_relation = Column(Text, nullable=True, comment="How does this relate to your search narrative?")
    deal_likes_dislikes = Column(Text, nullable=True, comment="What do you like/don't like about the deal?")
    deal_questions_concerns = Column(Text, nullable=True, comment="What questions/concerns do you have about the deal?")
    
    # File Upload Fields
    file_urls = Column(Text, nullable=True, comment="Google Drive URL for generated PDF")
    uploaded_file_url = Column(Text, nullable=True, comment="Google Drive URL for user-uploaded attachment")
    attachment_count = Column(Integer, default=0, comment="Number of files attached")
    
    # Terms and Conditions
    terms_accepted = Column(Boolean, default=False, nullable=False, comment="User accepted terms and conditions")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, comment="Submission timestamp")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Last update timestamp")
    
    # Status and Processing
    is_processed = Column(Boolean, default=False, comment="Whether the submission has been processed")
    pdf_generated = Column(Boolean, default=False, comment="Whether PDF has been generated")
    email_sent = Column(Boolean, default=False, comment="Whether confirmation email has been sent")
    
    def __repr__(self):
        return f'<CIMQuestion {self.full_name} - ${self.purchase_price:,.0f}>'
    
    def to_dict(self) -> dict:
        """Convert model instance to dictionary"""
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'industry': self.industry,
            'location': self.location,
            'seller_role': self.seller_role,
            'purchase_price': self.purchase_price,
            'revenue': self.revenue,
            'avg_sde': self.avg_sde,
            'total_adjustments': self.total_adjustments,
            'reason_for_selling': self.reason_for_selling,
            'owner_involvement': self.owner_involvement,
            'gm_in_place': self.gm_in_place,
            'tenure_of_gm': self.tenure_of_gm,
            'number_of_employees': self.number_of_employees,
            'cim_search_narrative_fit': self.cim_search_narrative_fit,
            'search_narrative_relation': self.search_narrative_relation,
            'deal_likes_dislikes': self.deal_likes_dislikes,
            'deal_questions_concerns': self.deal_questions_concerns,
            'file_urls': self.file_urls,
            'attachment_count': self.attachment_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_processed': self.is_processed,
            'pdf_generated': self.pdf_generated,
            'email_sent': self.email_sent,
            'terms_accepted': self.terms_accepted
        }
    
    @property
    def formatted_purchase_price(self) -> str:
        """Format purchase price as currency"""
        if self.purchase_price:
            return f"${self.purchase_price:,.0f}"
        return "Not specified"
    
    @property
    def formatted_revenue(self) -> str:
        """Format revenue as currency"""
        if self.revenue:
            return f"${self.revenue:,.0f}"
        return "Not specified"
    
    @property
    def formatted_avg_sde(self) -> str:
        """Format average SDE as currency"""
        if self.avg_sde:
            return f"${self.avg_sde:,.0f}"
        return "Not specified"
    
    @property
    def formatted_total_adjustments(self) -> str:
        """Format total adjustments as currency"""
        if self.total_adjustments:
            return f"${self.total_adjustments:,.0f}"
        return "Not specified"

# Backward compatibility alias
BusinessAcquisition = LOIQuestion

# Model validation functions
def validate_business_acquisition_data(data: dict) -> tuple[bool, list]:
    """
    Validate business acquisition form data
    Returns: (is_valid, error_messages)
    """
    errors = []
    
    # Required field validation
    required_fields = ['full_name', 'email', 'purchase_price', 'revenue']
    for field in required_fields:
        if not data.get(field) or str(data.get(field)).strip() == '':
            errors.append(f"{field.replace('_', ' ').title()} is required")
    
    # Email validation (basic)
    email = data.get('email', '').strip()
    if email and '@' not in email:
        errors.append("Please enter a valid email address")
    
    # Numeric field validation
    try:
        purchase_price = float(data.get('purchase_price', 0))
        if purchase_price <= 0:
            errors.append("Purchase price must be greater than 0")
    except (ValueError, TypeError):
        errors.append("Purchase price must be a valid number")
    
    try:
        revenue = float(data.get('revenue', 0))
        if revenue <= 0:
            errors.append("Revenue must be greater than 0")
    except (ValueError, TypeError):
        errors.append("Revenue must be a valid number")
    
    # Optional SDE validation
    avg_sde = data.get('avg_sde')
    if avg_sde:
        try:
            avg_sde_float = float(avg_sde)
            if avg_sde_float < 0:
                errors.append("Average SDE cannot be negative")
        except (ValueError, TypeError):
            errors.append("Average SDE must be a valid number")
    
    return len(errors) == 0, errors
