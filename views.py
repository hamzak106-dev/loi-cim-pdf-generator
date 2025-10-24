"""
URL routes and endpoints for Business Acquisition PDF Generator
"""
import json
from typing import List
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models import BusinessAcquisition
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
async def submit_business_acquisition(request: Request, db: Session = Depends(get_db)):
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
        form = await request.form()
        # Simple get for all fields
        full_name = (form.get('full_name') or '').strip()
        email = (form.get('email') or '').strip().lower()
        industry = (form.get('industry') or '').strip() or None
        location = (form.get('location') or '').strip() or None
        seller_role = (form.get('seller_role') or '').strip() or None
        reason_for_selling = (form.get('reason_for_selling') or '').strip() or None
        owner_involvement = (form.get('owner_involvement') or '').strip() or None
        customer_concentration_risk = (form.get('customer_concentration_risk') or '').strip() or None
        deal_competitiveness = (form.get('deal_competitiveness') or '').strip() or None
        seller_note_openness = (form.get('seller_note_openness') or '').strip() or None
        cim_search_narrative_fit = (form.get('cim_search_narrative_fit') or '').strip() or None
        search_narrative_relation = (form.get('search_narrative_relation') or '').strip() or None
        deal_likes_dislikes = (form.get('deal_likes_dislikes') or '').strip() or None
        deal_questions_concerns = (form.get('deal_questions_concerns') or '').strip() or None

        # Numbers (simple parsing)
        def to_float(val):
            try:
                return float(val) if val not in (None, '') else None
            except Exception:
                return None

        purchase_price = to_float(form.get('purchase_price'))
        revenue = to_float(form.get('revenue'))
        avg_sde = to_float(form.get('avg_sde'))

        # Terms
        terms_raw = form.get('terms_accepted')
        terms_accepted = True if str(terms_raw).lower() in ['on', 'true', '1', 'yes'] else False

        # Minimal validation
        if not full_name or not email or purchase_price is None or revenue is None or not terms_accepted:
            simple_form_data = {
                'full_name': full_name,
                'email': email,
                'purchase_price': form.get('purchase_price'),
                'revenue': form.get('revenue'),
                'industry': industry,
                'location': location,
                'seller_role': seller_role,
                'avg_sde': form.get('avg_sde'),
                'reason_for_selling': reason_for_selling,
                'owner_involvement': owner_involvement,
                'customer_concentration_risk': customer_concentration_risk,
                'deal_competitiveness': deal_competitiveness,
                'seller_note_openness': seller_note_openness,
                'cim_search_narrative_fit': cim_search_narrative_fit,
                'search_narrative_relation': search_narrative_relation,
                'deal_likes_dislikes': deal_likes_dislikes,
                'deal_questions_concerns': deal_questions_concerns,
            }
            return templates.TemplateResponse("business_form.html", {
                "request": request,
                "error": "Please fill required fields and accept terms.",
                "form_data": simple_form_data
            })

        # Create and save submission
        submission = BusinessAcquisition(
            full_name=full_name,
            email=email,
            industry=industry,
            location=location,
            seller_role=seller_role,
            purchase_price=purchase_price or 0.0,
            revenue=revenue or 0.0,
            avg_sde=avg_sde,
            reason_for_selling=reason_for_selling,
            owner_involvement=owner_involvement,
            customer_concentration_risk=customer_concentration_risk,
            deal_competitiveness=deal_competitiveness,
            seller_note_openness=seller_note_openness,
            cim_search_narrative_fit=cim_search_narrative_fit,
            search_narrative_relation=search_narrative_relation,
            deal_likes_dislikes=deal_likes_dislikes,
            deal_questions_concerns=deal_questions_concerns,
            terms_accepted=terms_accepted,
        )

        db.add(submission)
        db.commit()
        db.refresh(submission)

        # Files (simple handling)
        file_urls: List[str] = []
        files = []
        if hasattr(form, 'getlist'):
            files = [f for f in form.getlist('files') if getattr(f, 'filename', '')]
        else:
            one_file = form.get('files')
            if one_file and getattr(one_file, 'filename', ''):
                files = [one_file]

        if files:
            file_urls = await google_drive_service.upload_multiple_files(files, submission.id)
            submission.file_urls = json.dumps(file_urls)
            submission.attachment_count = len(file_urls)
            db.commit()

        # Generate PDF (simple)
        pdf_path = pdf_service.generate_business_acquisition_pdf(submission)
        submission.pdf_generated = True
        
        # Send email with PDF attachment
        email_sent = await email_service.send_confirmation_email_with_pdf(submission, pdf_path)
        submission.email_sent = email_sent
        submission.is_processed = True
        db.commit()

        # Optional notifications (keep simple)
        try:
            await email_service.send_admin_notification(submission)
            await slack_service.send_notification(submission)
        except Exception:
            pass

        # Clean up PDF file after sending
        try:
            import os
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
        except Exception:
            pass

        # Return success page instead of file download
        return templates.TemplateResponse("business_form.html", {
            "request": request,
            "success": f"Thank you {submission.full_name}! Your business acquisition analysis report has been sent to {submission.email}. Please check your email inbox.",
            "form_data": {}
        })

    except Exception as e:
        db.rollback()
        print(f"Error processing submission: {str(e)}")
        return templates.TemplateResponse("business_form.html", {
            "request": request,
            "error": f"An error occurred while processing your submission.",
            "form_data": {}
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
