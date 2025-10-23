"""
URL routes and endpoints for Business Acquisition PDF Generator
"""
import json
from typing import List, Optional
from fastapi import APIRouter, Request, Form, File, UploadFile, Depends, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models import BusinessAcquisition, validate_business_acquisition_data
from services import google_drive_service, email_service, slack_service, pdf_service
from database import get_db

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Create router
router = APIRouter()

# ============================================================================
# MAIN PAGES
# ============================================================================

@router.get("/", response_class=HTMLResponse, tags=["Pages"])
async def home_page(request: Request):
    """
    Display the main landing page
    """
    return templates.TemplateResponse("index.html", {
        "request": request,
        "page_title": "Business Acquisition Services"
    })

@router.get("/business-form", response_class=HTMLResponse, tags=["Pages"])
async def business_form_page(request: Request):
    """
    Display the business acquisition form page
    """
    return templates.TemplateResponse("business_form.html", {
        "request": request,
        "page_title": "Business Acquisition Form"
    })

# ============================================================================
# FORM SUBMISSION ENDPOINTS
# ============================================================================

@router.post("/submit-business", tags=["Submissions"])
async def submit_business_acquisition(
    request: Request,
    # Required fields
    full_name: str = Form(..., description="Full name of the submitter"),
    email: str = Form(..., description="Email address for communication"),
    purchase_price: float = Form(..., description="Proposed purchase price"),
    revenue: float = Form(..., description="Annual revenue of the business"),
    
    # Optional text fields
    industry: Optional[str] = Form(None, description="Industry sector"),
    location: Optional[str] = Form(None, description="Business location"),
    seller_role: Optional[str] = Form(None, description="Seller's role in business"),
    avg_sde: Optional[float] = Form(None, description="Average Seller's Discretionary Earnings"),
    
    # Text area fields
    reason_for_selling: Optional[str] = Form(None, description="Reason for selling the business"),
    owner_involvement: Optional[str] = Form(None, description="Owner involvement details"),
    customer_concentration_risk: Optional[str] = Form(None, description="Customer concentration analysis"),
    deal_competitiveness: Optional[str] = Form(None, description="Deal competitiveness assessment"),
    seller_note_openness: Optional[str] = Form(None, description="Seller financing considerations"),
    
    # New search narrative fields
    cim_search_narrative_fit: Optional[str] = Form(None, description="CIM fit with search narrative"),
    search_narrative_relation: Optional[str] = Form(None, description="Relation to search narrative"),
    deal_likes_dislikes: Optional[str] = Form(None, description="Deal likes and dislikes"),
    deal_questions_concerns: Optional[str] = Form(None, description="Questions and concerns about deal"),
    
    # Terms and conditions
    terms_accepted: bool = Form(..., description="Terms and conditions acceptance"),
    
    # File uploads
    files: List[UploadFile] = File(default=[], description="Supporting documents"),
    
    # Database session
    db: Session = Depends(get_db)
):
    """
    Handle business acquisition form submission
    
    This endpoint:
    1. Validates the submitted data
    2. Saves the submission to the database
    3. Uploads files to Google Drive
    4. Generates a PDF report
    5. Sends confirmation email
    6. Sends Slack notification
    """
    try:
        # Prepare data for validation
        form_data = {
            'full_name': full_name,
            'email': email,
            'purchase_price': purchase_price,
            'revenue': revenue,
            'industry': industry,
            'location': location,
            'seller_role': seller_role,
            'avg_sde': avg_sde,
            'reason_for_selling': reason_for_selling,
            'owner_involvement': owner_involvement,
            'customer_concentration_risk': customer_concentration_risk,
            'deal_competitiveness': deal_competitiveness,
            'seller_note_openness': seller_note_openness,
            'cim_search_narrative_fit': cim_search_narrative_fit,
            'search_narrative_relation': search_narrative_relation,
            'deal_likes_dislikes': deal_likes_dislikes,
            'deal_questions_concerns': deal_questions_concerns,
            'terms_accepted': terms_accepted
        }
        
        # Check terms acceptance
        if not terms_accepted:
            return templates.TemplateResponse("business_form.html", {
                "request": request,
                "error": "You must accept the terms and conditions to proceed.",
                "form_data": form_data
            })
        
        # Validate form data
        is_valid, validation_errors = validate_business_acquisition_data(form_data)
        if not is_valid:
            return templates.TemplateResponse("business_form.html", {
                "request": request,
                "error": "Please correct the following errors: " + "; ".join(validation_errors),
                "form_data": form_data
            })
        
        # Create database entry
        submission = BusinessAcquisition(
            full_name=full_name.strip(),
            email=email.strip().lower(),
            industry=industry.strip() if industry else None,
            location=location.strip() if location else None,
            seller_role=seller_role.strip() if seller_role else None,
            purchase_price=purchase_price,
            revenue=revenue,
            avg_sde=avg_sde,
            reason_for_selling=reason_for_selling.strip() if reason_for_selling else None,
            owner_involvement=owner_involvement.strip() if owner_involvement else None,
            customer_concentration_risk=customer_concentration_risk.strip() if customer_concentration_risk else None,
            deal_competitiveness=deal_competitiveness.strip() if deal_competitiveness else None,
            seller_note_openness=seller_note_openness.strip() if seller_note_openness else None,
            cim_search_narrative_fit=cim_search_narrative_fit.strip() if cim_search_narrative_fit else None,
            search_narrative_relation=search_narrative_relation.strip() if search_narrative_relation else None,
            deal_likes_dislikes=deal_likes_dislikes.strip() if deal_likes_dislikes else None,
            deal_questions_concerns=deal_questions_concerns.strip() if deal_questions_concerns else None,
            terms_accepted=terms_accepted,
            attachment_count=len([f for f in files if f.filename])
        )
        
        # Save to database
        db.add(submission)
        db.commit()
        db.refresh(submission)
        
        # Handle file uploads
        file_urls = []
        if files and any(f.filename for f in files):
            # Validate files
            for file in files:
                if file.filename:  # Skip empty files
                    is_valid_file, file_error = google_drive_service.validate_file(file)
                    if not is_valid_file:
                        db.rollback()
                        return templates.TemplateResponse("business_form.html", {
                            "request": request,
                            "error": f"File validation error: {file_error}",
                            "form_data": form_data
                        })
            
            # Upload files to Google Drive
            file_urls = await google_drive_service.upload_multiple_files(files, submission.id)
            
            # Update submission with file URLs
            submission.file_urls = json.dumps(file_urls)
            db.commit()
        
        # Generate PDF
        pdf_path = pdf_service.generate_business_acquisition_pdf(submission)
        submission.pdf_generated = True
        
        # Send confirmation email
        email_sent = await email_service.send_confirmation_email(submission)
        submission.email_sent = email_sent
        
        # Send admin notification
        await email_service.send_admin_notification(submission)
        
        # Send Slack notification
        await slack_service.send_notification(submission)
        
        # Mark as processed
        submission.is_processed = True
        db.commit()
        
        # Return the generated PDF
        return FileResponse(
            pdf_path,
            media_type='application/pdf',
            filename=f'business_acquisition_{submission.full_name.replace(" ", "_")}_{submission.id}.pdf'
        )
        
    except Exception as e:
        db.rollback()
        print(f"Error processing submission: {str(e)}")
        return templates.TemplateResponse("business_form.html", {
            "request": request,
            "error": f"An error occurred while processing your submission: {str(e)}",
            "form_data": form_data if 'form_data' in locals() else {}
        })

# ============================================================================
# API ENDPOINTS (for future use)
# ============================================================================

@router.get("/api/submissions", tags=["API"])
async def get_submissions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get list of business acquisition submissions (API endpoint)
    """
    submissions = db.query(BusinessAcquisition).offset(skip).limit(limit).all()
    return {
        "submissions": [submission.to_dict() for submission in submissions],
        "total": db.query(BusinessAcquisition).count()
    }

@router.get("/api/submissions/{submission_id}", tags=["API"])
async def get_submission(
    submission_id: int,
    db: Session = Depends(get_db)
):
    """
    Get specific business acquisition submission (API endpoint)
    """
    submission = db.query(BusinessAcquisition).filter(BusinessAcquisition.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    return submission.to_dict()

@router.get("/api/submissions/{submission_id}/pdf", tags=["API"])
async def regenerate_pdf(
    submission_id: int,
    db: Session = Depends(get_db)
):
    """
    Regenerate PDF for a specific submission (API endpoint)
    """
    submission = db.query(BusinessAcquisition).filter(BusinessAcquisition.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Generate new PDF
    pdf_path = pdf_service.generate_business_acquisition_pdf(submission)
    
    return FileResponse(
        pdf_path,
        media_type='application/pdf',
        filename=f'business_acquisition_{submission.full_name.replace(" ", "_")}_{submission.id}.pdf'
    )

 

# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": "Business Acquisition PDF Generator",
        "version": "2.0.0"
    }
