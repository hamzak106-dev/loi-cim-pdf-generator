"""
Submission Helper Functions
DRY helper functions for managing form submissions and users
"""
from db import User, Form, FormType, SessionLocal
from services.auth_service import auth_service
from typing import Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session


def get_or_create_user(email: str, db: Session, name: str = None) -> Tuple[User, bool]:
    """
    Get existing user or create new one
    
    Args:
        name: User's full name
        email: User's email address
        db: Database session
        
    Returns:
        Tuple of (user: User, created: bool)
    """
    # Check if user exists
    user = db.query(User).filter(User.email == email).first()
    
    if user:
        return user, False
    
    # Create new user with default password
    from werkzeug.security import generate_password_hash
    user = User(
        name=name or email.split('@')[0],  # Use email prefix if name not provided
        email=email,
        password=generate_password_hash('default_password'),  # User can reset later
        user_type='user',
        is_active=True
    )
    
    db.add(user)
    db.flush()  # Get the ID without committing
    
    return user, True


def create_submission_record(form_data: Dict[str, Any], form_type: str, db: Session) -> Form:
    """
    Create a unified submission record using Form model
    
    Args:
        form_data: Form data dictionary
        form_type: "LOI" or "CIM"
        db: Database session
        
    Returns:
        Form submission record
    """
    # Convert string form_type to FormType enum
    if form_type == "LOI":
        form_type_enum = FormType.LOI
    elif form_type == "CIM_TRAINING":
        form_type_enum = FormType.CIM_TRAINING
    else:
        form_type_enum = FormType.CIM
    
    # Create unified Form record
    submission = Form(
        form_type=form_type_enum,
        full_name=form_data.get('full_name'),
        email=form_data.get('email'),
        industry=form_data.get('industry'),
        location=form_data.get('location'),
        purchase_price=float(form_data.get('purchase_price', 0)),
        revenue=float(form_data.get('revenue', 0)),
        avg_sde=float(form_data.get('avg_sde', 0)) if form_data.get('avg_sde') else None,
        seller_role=form_data.get('seller_role'),
        reason_for_selling=form_data.get('reason_for_selling'),
        owner_involvement=form_data.get('owner_involvement'),
        cim_search_narrative_fit=form_data.get('cim_search_narrative_fit'),
        search_narrative_relation=form_data.get('search_narrative_relation'),
        deal_likes_dislikes=form_data.get('deal_likes_dislikes'),
        deal_questions_concerns=form_data.get('deal_questions_concerns'),
        # LOI-specific fields
        customer_concentration_risk=form_data.get('customer_concentration_risk'),
        deal_competitiveness=form_data.get('deal_competitiveness'),
        seller_note_openness=form_data.get('seller_note_openness'),
        # CIM-specific fields
        total_adjustments=float(form_data.get('total_adjustments', 0)) if form_data.get('total_adjustments') else None,
        gm_in_place=form_data.get('gm_in_place'),
        tenure_of_gm=form_data.get('tenure_of_gm'),
        number_of_employees=form_data.get('number_of_employees'),
        # Status fields
        pdf_generated=False,
        email_sent=False,
        is_processed=False
    )
    
    db.add(submission)
    db.flush()
    return submission


def process_form_submission(form_data: Dict[str, Any], form_type: str, files_data: list = None) -> Tuple[bool, Any, str]:
    """
    Unified function to process LOI, CIM, and CIM_TRAINING form submissions
    
    Args:
        form_data: Form data dictionary
        form_type: "LOI", "CIM", or "CIM_TRAINING"
        files_data: Optional list of uploaded files
        
    Returns:
        Tuple of (success: bool, submission: record or None, message: str)
    """
    db = SessionLocal()
    
    try:
        # Step 1: Get or create user
        user, created = get_or_create_user(
            email=form_data.get('email'),
            name=form_data.get('full_name'),
            db=db
        )
        
        if created:
            print(f"✅ Created new user: {user.email}")
        else:
            print(f"ℹ️  Using existing user: {user.email}")
        
        # Step 2: Create submission record
        submission = create_submission_record(form_data, form_type, db)
        
        # Commit the transaction
        db.commit()
        db.refresh(submission)
        
        print(f"✅ {form_type} submission created: ID {submission.id}")
        
        return True, submission, f"{form_type} submission created successfully"
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error processing {form_type} submission: {e}")
        return False, None, f"Failed to process submission: {str(e)}"
    finally:
        db.close()
