from fastapi import APIRouter, Request, Depends, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models import BusinessAcquisition
from services import pdf_service
from database import get_db
from tasks import process_submission_complete
from config import settings
import os
import tempfile

templates = Jinja2Templates(directory="templates")
router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "page_title": "Business Acquisition Services"
    })

@router.get("/business-form", response_class=HTMLResponse)
async def business_form_page(request: Request):
    return templates.TemplateResponse("business_form.html", {
        "request": request,
        "page_title": "Business Acquisition Form"
    })

@router.post("/submit-business")
async def submit_business_acquisition(request: Request, db: Session = Depends(get_db)):
    try:
        form = await request.form()
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

        def to_float(val):
            try:
                return float(val) if val not in (None, '') else None
            except Exception:
                return None

        purchase_price = to_float(form.get('purchase_price'))
        revenue = to_float(form.get('revenue'))
        avg_sde = to_float(form.get('avg_sde'))
        terms_raw = form.get('terms_accepted')
        terms_accepted = True if str(terms_raw).lower() in ['on', 'true', '1', 'yes'] else False

        if not full_name or not email:
            return templates.TemplateResponse("business_form.html", {
                "request": request,
                "error": "Please fill required fields and accept terms.",
                "form_data": {k: form.get(k) for k in form.keys()}
            })

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

        files_data = []
        files = form.getlist('files') if hasattr(form, 'getlist') else ([form.get('files')] if form.get('files') else [])
        
        for file in files:
            if hasattr(file, 'filename') and file.filename:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
                temp_path = temp_file.name
                
                try:
                    content = await file.read()
                    temp_file.write(content)
                    temp_file.close()
                    
                    files_data.append({
                        'filename': file.filename,
                        'content_type': getattr(file, 'content_type', 'application/octet-stream'),
                        'size': len(content),
                        'file_path': temp_path
                    })
                    print(f"📁 Saved uploaded file: {file.filename} to {temp_path}")
                except Exception as e:
                    print(f"❌ Error saving file {file.filename}: {e}")
                    temp_file.close()
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

        try:
            process_submission_complete.delay(submission.id, files_data)
            print(f"🚀 Started background processing for submission {submission.id}")
        except Exception as e:
            print(f"⚠️ Failed to start background tasks: {e}")

        return templates.TemplateResponse("business_form.html", {
            "request": request,
            "success": f"Thank you {submission.full_name}\! Your submission has been received. Your business acquisition analysis report will be sent to {submission.email} shortly.",
            "form_data": {}
        })

    except Exception as e:
        db.rollback()
        print(f"Error processing submission: {str(e)}")
        return templates.TemplateResponse("business_form.html", {
            "request": request,
            "error": "An error occurred while processing your submission.",
            "form_data": {}
        })

@router.get("/api/submissions")
async def get_submissions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    submissions = db.query(BusinessAcquisition).offset(skip).limit(limit).all()
    return {
        "submissions": [submission.to_dict() for submission in submissions],
        "total": db.query(BusinessAcquisition).count()
    }

@router.get("/api/submissions/{submission_id}")
async def get_submission(submission_id: int, db: Session = Depends(get_db)):
    submission = db.query(BusinessAcquisition).filter(BusinessAcquisition.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission.to_dict()

@router.get("/api/submissions/{submission_id}/pdf")
async def regenerate_pdf(submission_id: int, db: Session = Depends(get_db)):
    submission = db.query(BusinessAcquisition).filter(BusinessAcquisition.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    pdf_path = pdf_service.generate_business_acquisition_pdf(submission)
    return FileResponse(
        pdf_path,
        media_type='application/pdf',
        filename=f'business_acquisition_{submission.full_name.replace(" ", "_")}_{submission.id}.pdf'
    )

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Business Acquisition PDF Generator",
        "version": "2.0.0"
    }
