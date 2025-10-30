"""
Views/Routes for Business Acquisition PDF Generator
Refactored with DRY principles and admin dashboard
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Form as FormField
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.status import HTTP_302_FOUND, HTTP_303_SEE_OTHER
from db import Form, FormType, LOIQuestion, CIMQuestion, User, get_db, SessionLocal
from services import pdf_service, process_form_submission, auth_service
from tasks.pdf_tasks import process_submission_complete
import os
import tempfile

templates = Jinja2Templates(directory="templates")
router = APIRouter()

# Session management (simple in-memory for demo - use proper session management in production)
active_sessions = {}

def get_current_admin(request: Request):
    """Get current admin from session"""
    session_id = request.cookies.get("admin_session")
    if not session_id or session_id not in active_sessions:
        return None
    return active_sessions[session_id]

def require_admin(request: Request):
    """Require admin authentication"""
    admin = get_current_admin(request)
    if not admin:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return admin


# ==================== PUBLIC ROUTES ====================

@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """Homepage"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "page_title": "Business Acquisition Services"
    })


@router.get("/business-form", response_class=HTMLResponse)
async def business_form_page(request: Request):
    """LOI Questions form page"""
    return templates.TemplateResponse("business_form.html", {
        "request": request,
        "page_title": "LOI Questions"
    })


@router.get("/cim-form", response_class=HTMLResponse)
async def cim_form_page(request: Request):
    """CIM Questions form page"""
    return templates.TemplateResponse("cim_questions.html", {
        "request": request,
        "page_title": "CIM Questions"
    })


# ==================== UNIFIED SUBMISSION HANDLER ====================

async def handle_form_submission(request: Request, form_type: str, template_name: str):
    """
    Unified form submission handler for both LOI and CIM forms
    
    Args:
        request: FastAPI request object
        form_type: "LOI" or "CIM"
        template_name: Template to render on error
    """
    try:
        form = await request.form()
        
        # Extract form data
        form_data = {
            'full_name': (form.get('full_name') or '').strip(),
            'email': (form.get('email') or '').strip().lower(),
            'industry': (form.get('industry') or '').strip() or None,
            'location': (form.get('location') or '').strip() or None,
            'seller_role': (form.get('seller_role') or '').strip() or None,
            'reason_for_selling': (form.get('reason_for_selling') or '').strip() or None,
            'owner_involvement': (form.get('owner_involvement') or '').strip() or None,
            'cim_search_narrative_fit': (form.get('cim_search_narrative_fit') or '').strip() or None,
            'search_narrative_relation': (form.get('search_narrative_relation') or '').strip() or None,
            'deal_likes_dislikes': (form.get('deal_likes_dislikes') or '').strip() or None,
            'deal_questions_concerns': (form.get('deal_questions_concerns') or '').strip() or None,
        }
        
        # LOI-specific fields
        if form_type == "LOI":
            form_data.update({
                'customer_concentration_risk': (form.get('customer_concentration_risk') or '').strip() or None,
                'deal_competitiveness': (form.get('deal_competitiveness') or '').strip() or None,
                'seller_note_openness': (form.get('seller_note_openness') or '').strip() or None,
            })
        
        # CIM-specific fields
        if form_type == "CIM":
            form_data.update({
                'gm_in_place': (form.get('gm_in_place') or '').strip() or None,
                'tenure_of_gm': (form.get('tenure_of_gm') or '').strip() or None,
                'number_of_employees': (form.get('number_of_employees') or '').strip() or None,
            })
        
        # Convert numeric fields
        def to_float(val):
            try:
                return float(val) if val not in (None, '') else None
            except Exception:
                return None
        
        form_data['purchase_price'] = to_float(form.get('purchase_price')) or 0.0
        form_data['revenue'] = to_float(form.get('revenue')) or 0.0
        form_data['avg_sde'] = to_float(form.get('avg_sde'))
        
        if form_type == "CIM":
            form_data['total_adjustments'] = to_float(form.get('total_adjustments'))
        
        # Validation
        if not form_data['full_name'] or not form_data['email']:
            return templates.TemplateResponse(template_name, {
                "request": request,
                "error": "Please fill in all required fields (Name and Email).",
                "form_data": {k: form.get(k) for k in form.keys()}
            })
        
        # Process submission using helper function
        success, submission, message = process_form_submission(form_data, form_type)
        
        if not success:
            return templates.TemplateResponse(template_name, {
                "request": request,
                "error": message,
                "form_data": {k: form.get(k) for k in form.keys()}
            })
        
        # Handle file uploads
        files_data = []
        files = form.getlist('files') if hasattr(form, 'getlist') else ([form.get('files')] if form.get('files') else [])
        
        for file in files:
            if hasattr(file, 'filename') and file.filename:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
                temp_path = temp_file.name
                
                try:
                    content = await file.read()
                    with open(temp_path, 'wb') as f:
                        f.write(content)
                    
                    files_data.append({
                        'file_path': temp_path,
                        'filename': file.filename,
                        'content_type': file.content_type or 'application/octet-stream'
                    })
                except Exception as e:
                    print(f"Error saving file {file.filename}: {e}")
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
        
        # Trigger background processing
        process_submission_complete.delay(submission.id, files_data, form_type)
        
        # Return success message on same page with cleared form
        return templates.TemplateResponse(template_name, {
            "request": request,
            "success": f"✅ {form_type} form submitted successfully! Your submission is being processed and you will receive an email shortly.",
            "form_data": {}  # Clear form data on success
        })
        
        
    except Exception as e:
        print(f"Error in {form_type} submission: {e}")
        return templates.TemplateResponse(template_name, {
            "request": request,
            "error": f"An error occurred: {str(e)}",
            "form_data": {}
        })


@router.post("/submit-business")
async def submit_loi_form(request: Request):
    """Submit LOI Questions form"""
    return await handle_form_submission(request, "LOI", "business_form.html")


@router.post("/submit-cim")
async def submit_cim_form(request: Request):
    """Submit CIM Questions form"""
    return await handle_form_submission(request, "CIM", "cim_questions.html")


@router.get("/submission-success", response_class=HTMLResponse)
async def submission_success(request: Request, type: str = "LOI"):
    """Success page after form submission"""
    return templates.TemplateResponse("redirect_notice.html", {
        "request": request,
        "form_type": type
    })


# ==================== ADMIN ROUTES ====================

@router.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Admin login page"""
    return templates.TemplateResponse("accounts/login.html", {
        "request": request
    })


@router.post("/admin/login")
async def admin_login(
    request: Request,
    email: str = FormField(...),
    password: str = FormField(...)
):
    """Handle admin login"""
    success, user, message = auth_service.authenticate_user(email, password)
    
    if not success or not user.is_admin():
        return templates.TemplateResponse("accounts/login.html", {
            "request": request,
            "error": "Invalid credentials or not an admin account"
        })
    
    # Create session
    import secrets
    session_id = secrets.token_urlsafe(32)
    active_sessions[session_id] = {
        'user_id': user.id,
        'email': user.email,
        'name': user.name
    }
    
    # Redirect to dashboard
    response = RedirectResponse(url="/admin/dashboard", status_code=HTTP_302_FOUND)
    response.set_cookie(key="admin_session", value=session_id, httponly=True)
    return response


@router.get("/admin/logout")
async def admin_logout(request: Request):
    """Logout admin"""
    session_id = request.cookies.get("admin_session")
    if session_id in active_sessions:
        del active_sessions[session_id]
    
    response = RedirectResponse(url="/admin/login", status_code=HTTP_302_FOUND)
    response.delete_cookie("admin_session")
    return response


@router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, filter_type: str = "all"):
    """Admin dashboard with unified Form model"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=HTTP_302_FOUND)
    
    db = SessionLocal()
    try:
        # Get all forms with optional filtering
        query = db.query(Form).order_by(Form.created_at.desc())
        
        if filter_type == "loi":
            query = query.filter(Form.form_type == FormType.LOI)
        elif filter_type == "cim":
            query = query.filter(Form.form_type == FormType.CIM)
        
        all_forms = query.all()
        
        # Get statistics
        loi_count = db.query(Form).filter(Form.form_type == FormType.LOI).count()
        cim_count = db.query(Form).filter(Form.form_type == FormType.CIM).count()
        user_count = db.query(User).count()
        
        return templates.TemplateResponse("accounts/dashboard.html", {
            "request": request,
            "admin_name": admin['name'],
            "forms": all_forms,
            "loi_count": loi_count,
            "cim_count": cim_count,
            "total_count": loi_count + cim_count,
            "user_count": user_count,
            "current_filter": filter_type
        })
    finally:
        db.close()


@router.get("/admin/record/{record_id}", response_class=HTMLResponse)
async def admin_record_detail(request: Request, record_id: int):
    """View record details using unified Form model"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=HTTP_302_FOUND)
    
    db = SessionLocal()
    try:
        record = db.query(Form).filter(Form.id == record_id).first()
        
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
        
        return templates.TemplateResponse("accounts/record_detail.html", {
            "request": request,
            "record": record,
            "form_type": record.form_type.value
        })
    finally:
        db.close()
