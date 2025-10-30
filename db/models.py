"""
Database models for Business Acquisition PDF Generator
Unified Form model with FormType enum
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from .database import Base
from datetime import datetime
from typing import Optional
from enum import Enum as PyEnum


class FormType(str, PyEnum):
    """Form type enumeration"""
    LOI = "LOI"
    CIM = "CIM"


class Form(Base):
    """
    Unified Form model for both LOI and CIM submissions
    """
    __tablename__ = 'forms'
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Form Type
    form_type = Column(SQLEnum(FormType), nullable=False, index=True, comment="Type of form: LOI or CIM")
    
    # Required Text Fields
    full_name = Column(String(100), nullable=False, comment="Full name of the submitter")
    email = Column(String(120), nullable=False, index=True, comment="Email address for communication")
    
    # Optional Text Fields
    industry = Column(String(100), nullable=True, comment="Industry sector of the business")
    location = Column(String(200), nullable=True, comment="Geographic location of the business")
    seller_role = Column(String(100), nullable=True, comment="Role of the seller in the business")
    
    # Financial Fields
    purchase_price = Column(Float, nullable=False, comment="Proposed purchase price")
    revenue = Column(Float, nullable=False, comment="Annual revenue of the business")
    avg_sde = Column(Float, nullable=True, comment="Average Seller's Discretionary Earnings")
    total_adjustments = Column(Float, nullable=True, comment="Total dollar adjustments (CIM only)")
    
    # Text Area Fields (Long text)
    reason_for_selling = Column(Text, nullable=True, comment="Detailed reason for selling the business")
    owner_involvement = Column(Text, nullable=True, comment="Owner's role, hours per week, etc.")
    
    # LOI-specific fields
    customer_concentration_risk = Column(Text, nullable=True, comment="Analysis of customer concentration risks (LOI only)")
    deal_competitiveness = Column(Text, nullable=True, comment="How competitive is this deal (LOI only)")
    seller_note_openness = Column(Text, nullable=True, comment="Seller's openness to seller financing (LOI only)")
    
    # CIM-specific fields
    gm_in_place = Column(String(10), nullable=True, comment="Is there a GM in place? (CIM only)")
    tenure_of_gm = Column(String(100), nullable=True, comment="Tenure of the GM if applicable (CIM only)")
    number_of_employees = Column(Integer, nullable=True, comment="Number of employees (CIM only)")
    
    # Search Narrative Fields (Common to both)
    cim_search_narrative_fit = Column(Text, nullable=True, comment="Does the CIM fit your Search Narrative?")
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
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Submission timestamp")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="Last update timestamp")
    
    # Status and Processing
    is_processed = Column(Boolean, default=False, comment="Whether the submission has been processed")
    pdf_generated = Column(Boolean, default=False, comment="Whether PDF has been generated")
    email_sent = Column(Boolean, default=False, comment="Whether confirmation email has been sent")
    
    def __repr__(self):
        return f'<Form {self.form_type.value} - {self.full_name} - ${self.purchase_price:,.0f}>'
    
    def to_dict(self) -> dict:
        """Convert model instance to dictionary"""
        return {
            'id': self.id,
            'form_type': self.form_type.value if self.form_type else None,
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
            'customer_concentration_risk': self.customer_concentration_risk,
            'deal_competitiveness': self.deal_competitiveness,
            'seller_note_openness': self.seller_note_openness,
            'gm_in_place': self.gm_in_place,
            'tenure_of_gm': self.tenure_of_gm,
            'number_of_employees': self.number_of_employees,
            'cim_search_narrative_fit': self.cim_search_narrative_fit,
            'search_narrative_relation': self.search_narrative_relation,
            'deal_likes_dislikes': self.deal_likes_dislikes,
            'deal_questions_concerns': self.deal_questions_concerns,
            'file_urls': self.file_urls,
            'uploaded_file_url': self.uploaded_file_url,
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


# Keep old models for backward compatibility (optional)
class LOIQuestion(Base):
    """Legacy LOI Questions model - kept for backward compatibility"""
    __tablename__ = 'loi_question'
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(120), nullable=False)
    industry = Column(String(100), nullable=True)
    location = Column(String(200), nullable=True)
    seller_role = Column(String(100), nullable=True)
    purchase_price = Column(Float, nullable=False)
    revenue = Column(Float, nullable=False)
    avg_sde = Column(Float, nullable=True)
    reason_for_selling = Column(Text, nullable=True)
    owner_involvement = Column(Text, nullable=True)
    customer_concentration_risk = Column(Text, nullable=True)
    deal_competitiveness = Column(Text, nullable=True)
    seller_note_openness = Column(Text, nullable=True)
    cim_search_narrative_fit = Column(Text, nullable=True)
    search_narrative_relation = Column(Text, nullable=True)
    deal_likes_dislikes = Column(Text, nullable=True)
    deal_questions_concerns = Column(Text, nullable=True)
    file_urls = Column(Text, nullable=True)
    uploaded_file_url = Column(Text, nullable=True)
    attachment_count = Column(Integer, default=0)
    terms_accepted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_processed = Column(Boolean, default=False)
    pdf_generated = Column(Boolean, default=False)
    email_sent = Column(Boolean, default=False)
    
    @property
    def formatted_purchase_price(self) -> str:
        if self.purchase_price:
            return f"${self.purchase_price:,.0f}"
        return "Not specified"
    
    @property
    def formatted_revenue(self) -> str:
        if self.revenue:
            return f"${self.revenue:,.0f}"
        return "Not specified"
    
    @property
    def formatted_avg_sde(self) -> str:
        if self.avg_sde:
            return f"${self.avg_sde:,.0f}"
        return "Not specified"


class CIMQuestion(Base):
    """Legacy CIM Questions model - kept for backward compatibility"""
    __tablename__ = 'cim_question'
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(120), nullable=False)
    industry = Column(String(100), nullable=True)
    location = Column(String(200), nullable=True)
    seller_role = Column(String(100), nullable=True)
    purchase_price = Column(Float, nullable=False)
    revenue = Column(Float, nullable=False)
    avg_sde = Column(Float, nullable=True)
    total_adjustments = Column(Float, nullable=True)
    reason_for_selling = Column(Text, nullable=True)
    owner_involvement = Column(Text, nullable=True)
    gm_in_place = Column(String(10), nullable=True)
    tenure_of_gm = Column(String(100), nullable=True)
    number_of_employees = Column(Integer, nullable=True)
    cim_search_narrative_fit = Column(Text, nullable=True)
    search_narrative_relation = Column(Text, nullable=True)
    deal_likes_dislikes = Column(Text, nullable=True)
    deal_questions_concerns = Column(Text, nullable=True)
    file_urls = Column(Text, nullable=True)
    uploaded_file_url = Column(Text, nullable=True)
    attachment_count = Column(Integer, default=0)
    terms_accepted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_processed = Column(Boolean, default=False)
    pdf_generated = Column(Boolean, default=False)
    email_sent = Column(Boolean, default=False)
    
    @property
    def formatted_purchase_price(self) -> str:
        if self.purchase_price:
            return f"${self.purchase_price:,.0f}"
        return "Not specified"
    
    @property
    def formatted_revenue(self) -> str:
        if self.revenue:
            return f"${self.revenue:,.0f}"
        return "Not specified"
    
    @property
    def formatted_avg_sde(self) -> str:
        if self.avg_sde:
            return f"${self.avg_sde:,.0f}"
        return "Not specified"
    
    @property
    def formatted_total_adjustments(self) -> str:
        if self.total_adjustments:
            return f"${self.total_adjustments:,.0f}"
        return "Not specified"


# Alias for backward compatibility
BusinessAcquisition = LOIQuestion


class User(Base):
    """
    User model for authentication and user management
    """
    __tablename__ = 'users'
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # User Information
    name = Column(String(100), nullable=False, comment="Full name of the user")
    email = Column(String(120), unique=True, nullable=False, index=True, comment="Email address (unique)")
    password = Column(String(255), nullable=False, comment="Hashed password")
    user_type = Column(String(20), nullable=False, default='user', comment="User type: 'user' or 'admin'")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Record creation timestamp")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="Last update timestamp")
    
    # Status
    is_active = Column(Boolean, default=True, comment="Whether the user account is active")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', type='{self.user_type}')>"
    
    def is_admin(self):
        """Check if user is an admin"""
        return self.user_type == 'admin'
