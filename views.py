"""
Views/Routes for Business Acquisition PDF Generator
Refactored with DRY principles and admin dashboard
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Form as FormField
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.status import HTTP_302_FOUND, HTTP_303_SEE_OTHER
from db import Form, FormType, LOIQuestion, CIMQuestion, User, FormReviewed, MeetScheduler, MeetingType, MeetingInstance, MeetingRegistration, get_db, SessionLocal
from services import pdf_service, process_form_submission, auth_service, create_calendar_service
from tasks.pdf_tasks import process_submission_complete
from datetime import datetime, timedelta
from typing import Optional
import os
import tempfile
import pytz
from config import settings
from googleapiclient.errors import HttpError

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
        "page_title": "LOI Questions",
        "calendar_id": settings.GOOGLE_CALENDAR_ID or 'primary'
    })


@router.get("/cim-form", response_class=HTMLResponse)
async def cim_form_page(request: Request):
    """CIM Questions form page"""
    return templates.TemplateResponse("cim_questions.html", {
        "request": request,
        "page_title": "CIM Questions",
        "calendar_id": settings.GOOGLE_CALENDAR_ID or 'primary'
    })


@router.get("/cim-training-form", response_class=HTMLResponse)
async def cim_training_form_page(request: Request):
    """CIM Training Questions form page"""
    return templates.TemplateResponse("cim_training.html", {
        "request": request,
        "page_title": "CIM Questions - Training"
    })


@router.get("/calendar", response_class=HTMLResponse)
async def calendar_page(request: Request, form_type: Optional[str] = None, host: Optional[str] = None, email: Optional[str] = None):
    """Calendar page for scheduling calls"""
    return templates.TemplateResponse("calendar.html", {
        "request": request,
        "page_title": "Schedule a Live Call",
        "form_type": form_type or "LOI Call",
        "host": host or "Evan",
        "user_email": email or "",
        "calendar_id": settings.GOOGLE_CALENDAR_ID or 'primary'
    })


@router.get("/api/calendar/events")
async def get_all_calendar_events(request: Request, calendar_id: Optional[str] = None):
    """
    API endpoint to fetch events from Google Calendar API in real-time
    Directly calls: GET https://www.googleapis.com/calendar/v3/calendars/{calendarId}/events
    
    Fetches events from now to 180 days ahead, matching the example format.
    Uses credentials from .env file (GOOGLE_* environment variables).
    
    Args:
        calendar_id: Calendar ID (uses CALENDAR_ID from .env or GOOGLE_CALENDAR_ID if not provided)
    
    Returns:
        JSON response with event details formatted like the example:
        - id (event ID)
        - summary (title)
        - description
        - location
        - start (ISO datetime string)
        - end (ISO datetime string)
        - hangoutLink (Google Meet link)
        - attendees (list of attendee objects with email, organizer, self, responseStatus)
    """
    try:
        # Use provided calendar_id or default from settings (from .env CALENDAR_ID or GOOGLE_CALENDAR_ID)
        cal_id = calendar_id or settings.GOOGLE_CALENDAR_ID or 'primary'
        
        if not cal_id:
            return JSONResponse({
                "success": False,
                "error": "calendar_id is required",
                "events": []
            }, status_code=400)
        
        # Create calendar service with specified calendar ID
        # This uses credentials from .env file (GOOGLE_* environment variables)
        calendar_service = create_calendar_service(calendar_id=cal_id)
        
        # Get events directly from Google Calendar API
        # Use UTC datetime like the example: from now to 180 days ahead
        now = datetime.utcnow()
        time_min = now.isoformat() + 'Z'  # Current time in UTC
        time_max = (now + timedelta(days=180)).isoformat() + 'Z'  # 180 days ahead
        
        # Call Google Calendar API directly using the service
        # This calls: GET https://www.googleapis.com/calendar/v3/calendars/{calendarId}/events
        # Access the Google Calendar API service directly
        google_service = calendar_service.service
        events_result = google_service.events().list(
            calendarId=cal_id,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=2500,  # Maximum allowed by Google Calendar API
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Format events exactly like the example
        formatted_events = []
        for event in events:
            # Extract start and end times as ISO strings (like the example)
            start_time = event['start'].get('dateTime', event['start'].get('date'))
            end_time = event['end'].get('dateTime', event['end'].get('date'))
            
            event_info = {
                'id': event.get('id'),
                'summary': event.get('summary'),
                'description': event.get('description'),
                'location': event.get('location'),
                'start': start_time,  # ISO datetime string
                'end': end_time,  # ISO datetime string
                'hangoutLink': event.get('hangoutLink'),
                'attendees': event.get('attendees', []),  # Full attendee objects with email, organizer, self, responseStatus
                'reminders': event.get('reminders', {}),
                'organizer': event.get('organizer', {}),
                'recurrence': event.get('recurrence', []),
                'htmlLink': event.get('htmlLink', ''),
                'status': event.get('status', ''),
                'created': event.get('created', ''),
                'updated': event.get('updated', ''),
                'iCalUID': event.get('iCalUID', '')
            }
            formatted_events.append(event_info)
        
        return JSONResponse({
            "success": True,
            "events": formatted_events,
            "count": len(formatted_events),
            "calendar_id": cal_id,
            "time_range": {
                "from": time_min,
                "to": time_max
            },
            "api_endpoint": f"GET https://www.googleapis.com/calendar/v3/calendars/{cal_id}/events"
        })
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"Error fetching calendar events from Google Calendar API: {traceback.format_exc()}")
        return JSONResponse({
            "success": False,
            "error": error_msg,
            "events": [],
            "calendar_id": calendar_id or settings.GOOGLE_CALENDAR_ID or 'primary'
        }, status_code=400)


@router.post("/api/calendar/events/add-attendee")
async def add_attendee_to_event(request: Request):
    """
    API endpoint to add a user as an attendee to an existing Google Calendar event
    Updates the existing event by adding the user's email to the attendees list
    Uses sendUpdates='none' to avoid requiring domain-wide delegation
    
    Request body should contain:
    - event_id: Google Calendar event ID (required)
    - user_email: Email address of the user to add as attendee (required)
    - calendar_id: Calendar ID where the event exists (optional, uses default from settings)
    """
    try:
        body = await request.json()
        
        event_id = body.get('event_id')
        user_email = body.get('user_email')
        calendar_id = body.get('calendar_id') or settings.GOOGLE_CALENDAR_ID or 'primary'
        
        if not event_id or not user_email:
            return JSONResponse({
                "success": False,
                "error": "event_id and user_email are required fields"
            }, status_code=400)
        
        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, user_email):
            return JSONResponse({
                "success": False,
                "error": "Invalid email format"
            }, status_code=400)
        
        # Create calendar service
        calendar_service = create_calendar_service(calendar_id=calendar_id)
        
        # Get existing event to preserve all details
        existing_event = calendar_service.get_event(event_id)
        if not existing_event:
            return JSONResponse({
                "success": False,
                "error": "Event not found"
            }, status_code=404)
        
        # Get existing attendees from raw event data
        raw_event = existing_event.get('_raw', {})
        existing_attendees = raw_event.get('attendees', [])
        existing_attendee_emails = []
        for att in existing_attendees:
            if isinstance(att, dict):
                existing_attendee_emails.append(att.get('email', '').lower())
            elif isinstance(att, str):
                existing_attendee_emails.append(att.lower())
        
        # Check if user is already an attendee
        if user_email.lower() in existing_attendee_emails:
            return JSONResponse({
                "success": False,
                "error": "User is already an attendee of this event"
            }, status_code=400)
        
        # Add new attendee to the list (preserve existing attendee objects)
        updated_attendees = list(existing_attendees)  # Keep existing attendee objects
        updated_attendees.append({'email': user_email})  # Add new attendee
        
        # Update the event with the new attendee list using sendUpdates='none'
        # This should work without domain-wide delegation since we're not sending invitations
        try:
            # Get the raw event object
            event = calendar_service.service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            # Update attendees
            event['attendees'] = updated_attendees
            
            # Update the event with sendUpdates='none' to avoid sending email invitations
            updated_event = calendar_service.service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event,
                sendUpdates='none'  # Don't send email notifications - this should bypass domain-wide delegation requirement
            ).execute()
            
            return JSONResponse({
                "success": True,
                "message": "Successfully added as attendee",
                "event": {
                    "id": updated_event.get('id'),
                    "htmlLink": updated_event.get('htmlLink'),
                    "attendees": updated_event.get('attendees', [])
                }
            })
        except HttpError as http_error:
            error_msg = str(http_error)
            # If it's still the domain-wide delegation error, provide helpful message
            if 'forbiddenForServiceAccounts' in error_msg or 'Domain-Wide Delegation' in error_msg:
                return JSONResponse({
                    "success": False,
                    "error": "Unable to add attendee: Service account requires Domain-Wide Delegation to add attendees. Please contact your administrator to set this up, or use the event link to add yourself manually.",
                    "event_html_link": raw_event.get('htmlLink', ''),
                    "alternative": "You can open the event in Google Calendar and add yourself manually"
                }, status_code=403)
            raise
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"Error adding attendee to event: {traceback.format_exc()}")
        return JSONResponse({
            "success": False,
            "error": error_msg
        }, status_code=400)
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"Error generating calendar link: {traceback.format_exc()}")
        return JSONResponse({
            "success": False,
            "error": error_msg
        }, status_code=400)


# ==================== UNIFIED SUBMISSION HANDLER ====================

async def handle_form_submission(request: Request, form_type: str, template_name: str):
    """
    Unified form submission handler for LOI, CIM, and CIM_TRAINING forms
    
    Args:
        request: FastAPI request object
        form_type: "LOI", "CIM", or "CIM_TRAINING"
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
        
        # CIM-specific fields (applies to both CIM and CIM_TRAINING)
        if form_type == "CIM" or form_type == "CIM_TRAINING":
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
        
        if form_type == "CIM" or form_type == "CIM_TRAINING":
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
        
        # Handle file uploads - encode as base64 for cross-dyno transfer
        files_data = []
        files = form.getlist('files') if hasattr(form, 'getlist') else ([form.get('files')] if form.get('files') else [])
        
        for file in files:
            if hasattr(file, 'filename') and file.filename:
                try:
                    content = await file.read()
                    # Encode file content as base64 for transfer to worker dyno
                    import base64
                    encoded_content = base64.b64encode(content).decode('utf-8')
                    
                    files_data.append({
                        'file_content': encoded_content,  # Base64 encoded content
                        'filename': file.filename,
                        'content_type': file.content_type or 'application/octet-stream'
                    })
                    print(f"📎 Prepared file for upload: {file.filename} ({len(content)} bytes)")
                except Exception as e:
                    print(f"Error reading file {file.filename}: {e}")
        
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


@router.post("/submit-cim-training")
async def submit_cim_training_form(request: Request):
    """Submit CIM Training Questions form"""
    return await handle_form_submission(request, "CIM_TRAINING", "cim_training.html")


@router.get("/submission-success", response_class=HTMLResponse)
async def submission_success(request: Request, type: str = "LOI"):
    """Success page after form submission"""
    return templates.TemplateResponse("redirect_notice.html", {
        "request": request,
        "form_type": type
    })


# ==================== ADMIN ROUTES ====================

@router.get("/admin")
async def admin_redirect():
    return RedirectResponse(url="/admin/login")


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
        # Get reviewed form IDs
        reviewed_form_ids = [fr.form_id for fr in db.query(FormReviewed.form_id).all()]
        
        # Get all forms with optional filtering (exclude reviewed forms)
        if reviewed_form_ids:
            query = db.query(Form).filter(~Form.id.in_(reviewed_form_ids)).order_by(Form.created_at.desc())
        else:
            query = db.query(Form).order_by(Form.created_at.desc())
        
        if filter_type == "loi":
            query = query.filter(Form.form_type == FormType.LOI)
        elif filter_type == "cim_ben":
            # CIM Review (Live Call) with Ben - filter by meeting_host or default CIM
            query = query.filter(
                (Form.form_type == FormType.CIM) & 
                ((Form.meeting_host == "Ben") | (Form.meeting_host == None))
            )
        elif filter_type == "cim_mitch":
            # CIM Review (Live Call) with Mitch - filter by meeting_host
            query = query.filter(
                (Form.form_type == FormType.CIM) & 
                (Form.meeting_host == "Mitch")
            )
        elif filter_type == "cim_training":
            query = query.filter(Form.form_type == FormType.CIM_TRAINING)
        elif filter_type == "cim":
            # All CIM types
            query = query.filter(Form.form_type.in_([FormType.CIM, FormType.CIM_TRAINING]))
        
        all_forms = query.all()
        
        # Get reviewed forms
        if reviewed_form_ids:
            reviewed_forms = db.query(Form).filter(Form.id.in_(reviewed_form_ids)).order_by(Form.created_at.desc()).all()
        else:
            reviewed_forms = []
        
        # Get statistics
        if reviewed_form_ids:
            loi_count = db.query(Form).filter(Form.form_type == FormType.LOI).filter(~Form.id.in_(reviewed_form_ids)).count()
            cim_count = db.query(Form).filter(Form.form_type == FormType.CIM).filter(~Form.id.in_(reviewed_form_ids)).count()
            cim_training_count = db.query(Form).filter(Form.form_type == FormType.CIM_TRAINING).filter(~Form.id.in_(reviewed_form_ids)).count()
        else:
            loi_count = db.query(Form).filter(Form.form_type == FormType.LOI).count()
            cim_count = db.query(Form).filter(Form.form_type == FormType.CIM).count()
            cim_training_count = db.query(Form).filter(Form.form_type == FormType.CIM_TRAINING).count()
        reviewed_count = len(reviewed_form_ids)
        user_count = db.query(User).count()
        
        return templates.TemplateResponse("accounts/dashboard.html", {
            "request": request,
            "admin_name": admin['name'],
            "forms": all_forms,
            "reviewed_forms": reviewed_forms,
            "loi_count": loi_count,
            "cim_count": cim_count,
            "cim_training_count": cim_training_count,
            "total_count": loi_count + cim_count + cim_training_count,
            "reviewed_count": reviewed_count,
            "user_count": user_count,
            "current_filter": filter_type
        })
    finally:
        db.close()


@router.post("/admin/mark-reviewed/{form_id}")
async def mark_form_reviewed(request: Request, form_id: int):
    """Mark a form as reviewed"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=HTTP_302_FOUND)
    
    db = SessionLocal()
    try:
        # Check if already reviewed
        existing = db.query(FormReviewed).filter(FormReviewed.form_id == form_id).first()
        if existing:
            return RedirectResponse(url="/admin/dashboard", status_code=HTTP_302_FOUND)
        
        # Create reviewed record
        reviewed = FormReviewed(
            form_id=form_id,
            reviewed_by=admin['name']
        )
        db.add(reviewed)
        db.commit()
        
        return RedirectResponse(url="/admin/dashboard", status_code=HTTP_302_FOUND)
    except Exception as e:
        db.rollback()
        print(f"Error marking form as reviewed: {e}")
        return RedirectResponse(url="/admin/dashboard", status_code=HTTP_302_FOUND)
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
        
        # Check if reviewed
        is_reviewed = db.query(FormReviewed).filter(FormReviewed.form_id == record_id).first() is not None
        
        return templates.TemplateResponse("accounts/record_detail.html", {
            "request": request,
            "record": record,
            "form_type": record.form_type.value,
            "is_reviewed": is_reviewed
        })
    finally:
        db.close()


# ==================== MEETING SCHEDULER ROUTES ====================

@router.get("/admin/meetings", response_class=HTMLResponse)
async def meeting_scheduler_page(request: Request):
    """Meeting scheduler page with calendar"""
    admin = get_current_admin(request)
    if not admin:
        return RedirectResponse(url="/admin/login", status_code=HTTP_302_FOUND)
    
    return templates.TemplateResponse("accounts/meeting_scheduler.html", {
        "request": request
    })


@router.get("/admin/meetings/api/list")
async def get_meetings(request: Request, start: Optional[str] = None, end: Optional[str] = None):
    """API endpoint to get all meetings for calendar display from Google Calendar"""
    admin = get_current_admin(request)
    if not admin:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        calendar_service = create_calendar_service()
        
        # Parse start/end dates if provided
        time_min = None
        time_max = None
        if start:
            time_min = datetime.fromisoformat(start.replace('Z', '+00:00'))
        if end:
            time_max = datetime.fromisoformat(end.replace('Z', '+00:00'))
        
        # Get events from Google Calendar
        events = calendar_service.list_events(
            time_min=time_min,
            time_max=time_max,
            max_results=250,
            single_events=True,
            order_by='startTime'
        )
        
        # Convert to FullCalendar format
        calendar_events = []
        for event in events:
            start_time = event.get('start', {}).get('dateTime') or event.get('start', {}).get('date')
            end_time = event.get('end', {}).get('dateTime') or event.get('end', {}).get('date')
            
            extended_props = event.get('extendedProperties', {})
            is_recurring = len(event.get('recurrence', [])) > 0
            
            calendar_events.append({
                "id": event.get('id'),
                "title": event.get('summary', 'Untitled Event'),
                "start": start_time,
                "end": end_time,
                "description": event.get('description', ''),
                "meeting_link": event.get('location', ''),
                "host": extended_props.get('host', ''),
                "form_type": extended_props.get('form_type', ''),
                "recurring": is_recurring,
                "htmlLink": event.get('htmlLink', '')
            })
        
        return JSONResponse(calendar_events)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.post("/admin/meetings/api/create")
async def create_meeting(
    request: Request,
    title: str = FormField(...),
    meeting_time: str = FormField(...),
    meeting_link: str = FormField(...),
    description: Optional[str] = FormField(None),
    host: str = FormField(...),
    guest_count: Optional[int] = FormField(None),
    form_type: str = FormField(...),
    is_recurring: Optional[str] = FormField(None)
):
    """Create a new meeting schedule in Google Calendar"""
    admin = get_current_admin(request)
    if not admin:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        calendar_service = create_calendar_service()
        
        # Parse meeting time - treat as America/New_York timezone
        ny_tz = pytz.timezone("America/New_York")
        meeting_time_clean = meeting_time.replace('Z', '')
        if '+' not in meeting_time_clean and meeting_time_clean.count(':') >= 2:
            meeting_datetime = datetime.fromisoformat(meeting_time_clean)
            meeting_datetime = ny_tz.localize(meeting_datetime)
        else:
            meeting_datetime = datetime.fromisoformat(meeting_time_clean.replace('Z', '+00:00'))
            if meeting_datetime.tzinfo is None:
                meeting_datetime = ny_tz.localize(meeting_datetime)
            else:
                meeting_datetime = meeting_datetime.astimezone(ny_tz)
        
        # Calculate end time (1 hour default)
        end_datetime = meeting_datetime + timedelta(hours=1)
        
        # Build recurrence rule if recurring
        recurrence = None
        if is_recurring and (is_recurring.lower() == 'true' or is_recurring == '1'):
            # Get day of week abbreviation (MO, TU, WE, etc.)
            day_abbr = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'][meeting_datetime.weekday()]
            recurrence = [f'RRULE:FREQ=WEEKLY;BYDAY={day_abbr};COUNT=26']
        
        # Extended properties for storing custom data
        extended_properties = {
            'host': host,
            'form_type': form_type,
            'guest_count': str(guest_count or 0)
        }
        
        # Create event in Google Calendar
        event = calendar_service.create_event(
            title=title,
            start_time=meeting_datetime,
            end_time=end_datetime,
            description=description,
            meeting_link=meeting_link,
            recurrence=recurrence,
            timezone="America/New_York",
            extended_properties=extended_properties
        )
        
        return JSONResponse({
            "success": True,
            "meeting": {
                "id": event.get('id'),
                "title": title,
                "meeting_time": meeting_datetime.isoformat(),
                "meeting_link": meeting_link,
                "description": description,
                "host": host,
                "form_type": form_type,
                "htmlLink": event.get('htmlLink')
            }
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.put("/admin/meetings/api/{meeting_id}")
async def update_meeting(
    request: Request,
    meeting_id: str,  # Changed to str for Google Calendar event ID
    title: Optional[str] = FormField(None),
    meeting_time: Optional[str] = FormField(None),
    meeting_link: Optional[str] = FormField(None),
    description: Optional[str] = FormField(None),
    host: Optional[str] = FormField(None),
    guest_count: Optional[int] = FormField(None),
    form_type: Optional[str] = FormField(None),
    is_active: Optional[str] = FormField(None),
    is_recurring: Optional[str] = FormField(None)
):
    """Update a meeting schedule in Google Calendar"""
    admin = get_current_admin(request)
    if not admin:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        calendar_service = create_calendar_service()
        
        # Get existing event
        existing_event = calendar_service.get_event(meeting_id)
        if not existing_event:
            return JSONResponse({"error": "Meeting not found"}, status_code=404)
        
        # Parse meeting time if provided
        start_time = None
        end_time = None
        if meeting_time is not None:
            ny_tz = pytz.timezone("America/New_York")
            meeting_time_clean = meeting_time.replace('Z', '')
            if '+' not in meeting_time_clean and meeting_time_clean.count(':') >= 2:
                start_time = datetime.fromisoformat(meeting_time_clean)
                start_time = ny_tz.localize(start_time)
            else:
                start_time = datetime.fromisoformat(meeting_time_clean.replace('Z', '+00:00'))
                if start_time.tzinfo is None:
                    start_time = ny_tz.localize(start_time)
                else:
                    start_time = start_time.astimezone(ny_tz)
            end_time = start_time + timedelta(hours=1)
        
        # Build recurrence rule if recurring
        recurrence = None
        if is_recurring and (is_recurring.lower() == 'true' or is_recurring == '1'):
            if start_time:
                day_abbr = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'][start_time.weekday()]
                recurrence = [f'RRULE:FREQ=WEEKLY;BYDAY={day_abbr};COUNT=26']
            else:
                # Use existing event time
                existing_start = existing_event.get('start', {}).get('dateTime')
                if existing_start:
                    existing_dt = datetime.fromisoformat(existing_start.replace('Z', '+00:00'))
                    day_abbr = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'][existing_dt.weekday()]
                    recurrence = [f'RRULE:FREQ=WEEKLY;BYDAY={day_abbr};COUNT=26']
        
        # Build extended properties
        extended_properties = existing_event.get('extendedProperties', {})
        if host is not None:
            extended_properties['host'] = host
        if form_type is not None:
            extended_properties['form_type'] = form_type
        if guest_count is not None:
            extended_properties['guest_count'] = str(guest_count)
        
        # Update event
        updated_event = calendar_service.update_event(
            event_id=meeting_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            meeting_link=meeting_link,
            recurrence=recurrence,
            timezone="America/New_York",
            extended_properties=extended_properties
        )
        
        return JSONResponse({
            "success": True,
            "meeting": {
                "id": updated_event.get('id'),
                "title": updated_event.get('summary', title),
                "htmlLink": updated_event.get('htmlLink')
            }
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.get("/admin/meetings/api/{meeting_id}")
async def get_meeting(request: Request, meeting_id: str):
    """Get a single meeting by ID from Google Calendar"""
    admin = get_current_admin(request)
    if not admin:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        calendar_service = create_calendar_service()
        event = calendar_service.get_event(meeting_id)
        
        if not event:
            return JSONResponse({"error": "Meeting not found"}, status_code=404)
        
        # Format response similar to old format
        start_time = event.get('start', {}).get('dateTime') or event.get('start', {}).get('date')
        end_time = event.get('end', {}).get('dateTime') or event.get('end', {}).get('date')
        extended_props = event.get('extendedProperties', {})
        is_recurring = len(event.get('recurrence', [])) > 0
        
        return JSONResponse({
            "id": event.get('id'),
            "title": event.get('summary', ''),
            "meeting_time": start_time,
            "meeting_link": event.get('location', ''),
            "description": event.get('description', ''),
            "host": extended_props.get('host', ''),
            "form_type": extended_props.get('form_type', ''),
            "guest_count": int(extended_props.get('guest_count', 0)),
            "recurring_day": None,  # Not needed for Google Calendar
            "is_active": True,
            "htmlLink": event.get('htmlLink', '')
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.get("/api/meetings/available")
async def get_available_meetings(
    request: Request,
    form_type: str,
    host: str,
    limit: int = 3
):
    """Get available meeting instances for a specific form type and host
    Returns only google_event_id values with basic info (instance_time, guest_count, max_guests)
    Full event details should be fetched separately using /api/meetings/get-event/{event_id}
    """
    db = SessionLocal()
    try:
        # Step 1: Convert form_type string to MeetingType enum for database query
        try:
            if form_type == "LOI Call":
                meeting_type = MeetingType.LOI_CALL
            elif form_type == "CIM Call":
                meeting_type = MeetingType.CIM_CALL
            else:
                meeting_type = MeetingType(form_type)
        except ValueError:
            return JSONResponse({"error": f"Invalid form_type: {form_type}"}, status_code=400)
        
        # Step 2: Query LOCAL DATABASE to get event_id(s) matching form_type and host
        print(f"📋 Querying database for form_type={form_type}, host={host}")
        meetings = db.query(MeetScheduler).filter(
            MeetScheduler.form_type == meeting_type,
            MeetScheduler.host == host,
            MeetScheduler.is_active == True
        ).all()
        
        if not meetings:
            print(f"⚠️ No meetings found in database for form_type={form_type}, host={host}")
            return JSONResponse([])
        
        print(f"✅ Found {len(meetings)} meeting(s) in database")
        
        # Step 3: Initialize Google Calendar service
        calendar_service = create_calendar_service()
        ny_tz = pytz.timezone("America/New_York")
        current_time = datetime.now(ny_tz)
        
        available_instances = []
        
        # Step 4: For each event_id from database, get instance IDs from Google Calendar
        for meeting in meetings:
            event_id = meeting.google_event_id
            if not event_id:
                print(f"⚠️ Meeting {meeting.id} has no google_event_id, skipping")
                continue
            
            print(f"🔄 Getting instance IDs from Google Calendar for event_id: {event_id}")
            
            # Fetch event to check if it's recurring
            event = calendar_service.get_event(event_id)
            if not event:
                print(f"❌ Event {event_id} not found in Google Calendar")
                continue
            print(event, "KKKKKKKKKKKKKKKKKKKKKKKKKKKKKK")
            event_recurrence = event.get('recurrence', [])
            is_recurring = len(event_recurrence) > 0
            
            # Get instances (for recurring events) or single event
            if is_recurring:
                # For recurring events, get all future occurrences using instances API
                print(f"📅 Event is recurring, fetching future instances...")
                try:
                    service = calendar_service.service
                    events_result = service.events().instances(
                        calendarId=calendar_service.calendar_id,
                        eventId=event_id,
                        timeMin=current_time.isoformat(),
                        maxResults=limit * 2  # Get more to filter
                    ).execute()
                    
                    instances = events_result.get('items', [])
                    if not instances:
                        instances = [event]
                    print(f"✅ Found {len(instances)} future instances")
                except Exception as e:
                    print(f"⚠️ Warning: Could not get recurring event instances: {e}")
                    instances = [event]
            else:
                # Single event
                instances = [event]
            
            # Process each instance to get google_event_id and basic info
            for event_instance in instances:
                start_data = event_instance.get('start', {})
                start_time_str = start_data.get('dateTime') or start_data.get('date')
                if not start_time_str:
                    continue
                
                # Parse start time
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                if start_time.tzinfo is None:
                    start_time = ny_tz.localize(start_time)
                else:
                    start_time = start_time.astimezone(ny_tz)
                
                # Skip past events
                if start_time <= current_time:
                    continue
                
                # Get instance-specific event_id (for recurring events, each instance has its own ID)
                instance_event_id = event_instance.get('id')
                
                # Get guest count from database (MeetingInstance) - this is the only thing we track locally
                instance = db.query(MeetingInstance).filter(
                    MeetingInstance.google_event_id == instance_event_id,
                    MeetingInstance.instance_time == start_time
                ).first()
                
                max_guests = 10  # Default
                guest_count = 0
                
                if instance:
                    guest_count = instance.guest_count
                    max_guests = instance.max_guests
                else:
                    # If instance doesn't exist, create it (lazy creation)
                    instance = MeetingInstance(
                        google_event_id=instance_event_id,
                        instance_time=start_time,
                        guest_count=0,
                        max_guests=max_guests
                    )
                    db.add(instance)
                    db.commit()
                    db.refresh(instance)
                
                if guest_count < max_guests:
                    # Return only google_event_id and basic info - full details will be fetched separately
                    available_instances.append({
                        'google_event_id': instance_event_id,  # Google Calendar event ID
                        'instance_time': start_time.isoformat(),  # Instance time
                        'guest_count': guest_count,  # From local database
                        'max_guests': max_guests,
                        'available_slots': max_guests - guest_count,
                        'host': host,  # From database (filtering purpose)
                        'form_type': form_type,  # From database (filtering purpose)
                    })
        
        # Sort by time and limit
        available_instances.sort(key=lambda x: x['instance_time'])
        available_instances = available_instances[:limit]
        
        print(f"✅ Returning {len(available_instances)} available meeting instance IDs")
        
        return JSONResponse(available_instances)
    except Exception as e:
        import traceback
        print(f"❌ Error getting available meetings: {traceback.format_exc()}")
        return JSONResponse({"error": str(e)}, status_code=400)
    finally:
        db.close()


@router.get("/api/meetings/get-event/{event_id}")
async def get_event_details(
    request: Request,
    event_id: str
):
    """Get full event details from Google Calendar API using google_event_id
    This endpoint fetches complete event information from Google Calendar
    """
    db = SessionLocal()
    try:
        print(f"🔄 Fetching event details from Google Calendar for event_id: {event_id}")
        
        # Initialize Google Calendar service
        calendar_service = create_calendar_service()
        
        # Fetch complete event details from Google Calendar using event_id
        event = calendar_service.get_event(event_id)
        if not event:
            print(f"❌ Event {event_id} not found in Google Calendar")
            return JSONResponse({"error": "Event not found in Google Calendar"}, status_code=404)
        
        print(f"✅ Retrieved event from Google Calendar: {event.get('summary', 'Untitled')}")
        
        # Extract ALL details directly from Google Calendar event
        event_title = event.get('summary', 'Untitled Event')
        event_description = event.get('description', '') or ''
        event_location = event.get('location', '') or ''
        event_hangout_link = event.get('hangoutLink', '') or ''  # Google Meet link
        event_conference_data = event.get('conferenceData', {})
        
        # Determine meeting link: prefer hangoutLink (Google Meet), then location, then conference entry point
        meeting_link = ''
        if event_hangout_link:
            meeting_link = event_hangout_link
        elif event_location:
            meeting_link = event_location
        elif event_conference_data and event_conference_data.get('entryPoints'):
            # Check for video conference entry points
            for entry_point in event_conference_data.get('entryPoints', []):
                if entry_point.get('entryPointType') == 'video':
                    meeting_link = entry_point.get('uri', '')
                    break
        
        # Get start and end times
        start_data = event.get('start', {})
        end_data = event.get('end', {})
        start_time_str = start_data.get('dateTime') or start_data.get('date')
        end_time_str = end_data.get('dateTime') or end_data.get('date')
        
        # Get guest count from database (MeetingInstance)
        ny_tz = pytz.timezone("America/New_York")
        start_time = None
        if start_time_str:
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            if start_time.tzinfo is None:
                start_time = ny_tz.localize(start_time)
            else:
                start_time = start_time.astimezone(ny_tz)
        
        guest_count = 0
        max_guests = 10
        if start_time:
            instance = db.query(MeetingInstance).filter(
                MeetingInstance.google_event_id == event_id,
                MeetingInstance.instance_time == start_time
            ).first()
            
            if instance:
                guest_count = instance.guest_count
                max_guests = instance.max_guests
        
        # Return complete event details from Google Calendar
        return JSONResponse({
            'id': event_id,  # Google Calendar event ID
            'title': event_title,  # From Google Calendar API
            'description': event_description,  # From Google Calendar API
            'instance_time': start_time.isoformat() if start_time else None,  # From Google Calendar API
            'end_time': end_time_str,  # From Google Calendar API
            'meeting_link': meeting_link or 'To be added',  # From Google Calendar API
            'htmlLink': event.get('htmlLink', ''),  # From Google Calendar API
            'hangoutLink': event_hangout_link,  # From Google Calendar API
            'guest_count': guest_count,  # From local database
            'max_guests': max_guests,
            'available_slots': max_guests - guest_count,
        })
    except Exception as e:
        import traceback
        print(f"❌ Error getting event details: {traceback.format_exc()}")
        return JSONResponse({"error": str(e)}, status_code=400)
    finally:
        db.close()


@router.post("/api/meetings/register")
async def register_for_meeting(
    request: Request,
    instance_id: str = FormField(...),  # Changed to str for Google Calendar event ID
    full_name: str = FormField(...),
    email: str = FormField(...)
):
    """Register a user for a meeting instance (Google Calendar event)"""
    db = SessionLocal()
    try:
        calendar_service = create_calendar_service()
        
        # Get event from Google Calendar
        event = calendar_service.get_event(instance_id)
        if not event:
            return JSONResponse({"error": "Meeting not found"}, status_code=404)
        
        # Parse event time
        start_time_str = event.get('start', {}).get('dateTime') or event.get('start', {}).get('date')
        if not start_time_str:
            return JSONResponse({"error": "Invalid meeting time"}, status_code=400)
        
        ny_tz = pytz.timezone("America/New_York")
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        if start_time.tzinfo is None:
            start_time = ny_tz.localize(start_time)
        else:
            start_time = start_time.astimezone(ny_tz)
        
        # Check if event is in the past
        current_time = datetime.now(ny_tz)
        if start_time <= current_time:
            return JSONResponse({"error": "Cannot register for past meetings"}, status_code=400)
        
        # Get or create MeetingInstance for this event
        # Use google_event_id + instance_time to identify instances (for recurring events)
        instance = db.query(MeetingInstance).filter(
            MeetingInstance.google_event_id == instance_id,
            MeetingInstance.instance_time == start_time
        ).first()
        
        max_guests = 10  # Default
        if not instance:
            # Create new instance record
            instance = MeetingInstance(
                google_event_id=instance_id,
                scheduler_id=None,  # Optional - can link to MeetScheduler if needed
                instance_time=start_time,
                guest_count=0,
                max_guests=max_guests
            )
            db.add(instance)
            db.flush()  # Get the ID
        
        # Normalize email (lowercase, trimmed)
        normalized_email = email.lower().strip()
        
        # Get meeting link from Google Calendar event
        meeting_link = event.get('location', '') or 'To be added'
        
        # Check if email is already registered for this meeting instance
        existing_registration = db.query(MeetingRegistration).filter(
            MeetingRegistration.instance_id == instance.id,
            MeetingRegistration.email == normalized_email
        ).first()
        
        if existing_registration:
            return JSONResponse({
                "error": "This email is already registered for this meeting",
                "already_registered": True
            }, status_code=400)
        
        # Count current registrations (up to 10 unique emails)
        current_registrations = db.query(MeetingRegistration).filter(
            MeetingRegistration.instance_id == instance.id
        ).count()
        
        # Check if instance is full (10 unique emails)
        if current_registrations >= max_guests:
            return JSONResponse({
                "error": "This meeting is full. Maximum 10 registrations allowed.",
                "full": True
            }, status_code=400)
        
        # Create registration with normalized email
        registration = MeetingRegistration(
            instance_id=instance.id,
            full_name=full_name.strip(),
            email=normalized_email
        )
        db.add(registration)
        
        # Update guest count based on actual registrations
        instance.guest_count = current_registrations + 1
        
        db.commit()
        db.refresh(registration)
        
        print(f"✅ User registered: {full_name} ({normalized_email}) for meeting {instance_id} at {start_time}")
        
        return JSONResponse({
            "success": True,
            "message": "Successfully registered for the meeting",
            "registration": {
                "id": registration.id,
                "full_name": registration.full_name,
                "email": registration.email,
                "registered_at": registration.registered_at.isoformat() if registration.registered_at else None,
                "meeting_link": meeting_link
            },
            "meeting": {
                "guest_count": instance.guest_count,
                "max_guests": max_guests,
                "available_slots": max_guests - instance.guest_count
            }
        })
    except Exception as e:
        db.rollback()
        return JSONResponse({"error": str(e)}, status_code=400)
    finally:
        db.close()


@router.delete("/admin/meetings/api/{meeting_id}")
async def delete_meeting(request: Request, meeting_id: str):
    """Delete a meeting schedule from Google Calendar"""
    admin = get_current_admin(request)
    if not admin:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        calendar_service = create_calendar_service()
        
        # Check for cancel_all query parameter (for recurring events)
        cancel_all = request.query_params.get("cancel_all", "false").lower() == "true"
        
        if cancel_all:
            # For recurring events, we need to delete all future instances
            # This is handled by deleting the recurring event itself
            # Google Calendar will handle removing all instances
            pass
        
        success = calendar_service.delete_event(meeting_id)
        
        if success:
            return JSONResponse({"success": True, "message": "Meeting deleted successfully"})
        else:
            return JSONResponse({"error": "Failed to delete meeting"}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@router.post("/admin/meetings/create-draft")
async def create_draft_meeting(request: Request):
    """Create a draft event in Google Calendar and return the edit link"""
    admin = get_current_admin(request)
    if not admin:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    try:
        data = await request.json()
        form_type = data.get('form_type')
        host = data.get('host')
        
        if not form_type or not host:
            return JSONResponse({"error": "form_type and host are required"}, status_code=400)
        
        calendar_service = create_calendar_service()
        
        # Create a draft event with basic details
        ny_tz = pytz.timezone("America/New_York")
        # Default to tomorrow at 2 PM
        tomorrow = datetime.now(ny_tz) + timedelta(days=1)
        start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        title = f"{form_type} - {host}"
        dashboard_url = f"{request.base_url}admin/dashboard"
        description = f"Meeting scheduled via admin dashboard.\nForm Type: {form_type}\nHost: {host}\n\nPlease add meeting link and adjust time as needed.\n\nAfter saving this event, return to the dashboard to sync it to the database:\n{dashboard_url}"
        
        extended_properties = {
            'host': host,
            'form_type': form_type,
            'guest_count': '0',
            'source': 'admin_dashboard'
        }
        
        # Create the event with Google Meet link requested
        event = calendar_service.create_event(
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            meeting_link="",  # Admin will add this in Google Calendar
            timezone="America/New_York",
            extended_properties=extended_properties,
            request_google_meet=True  # Request Google Meet link creation
        )
        
        # Return the Google Calendar edit link
        event_id = event.get('id')
        calendar_id = settings.GOOGLE_CALENDAR_ID or 'primary'
        
        # Construct the Google Calendar edit URL
        # Google Calendar edit URL format: https://calendar.google.com/calendar/r/eventedit?eid={encoded_event_id}
        # The eid parameter needs to be base64url encoded: {event_id} {calendar_id}
        import base64
        # Format: {event_id} {calendar_id}
        event_data = f"{event_id} {calendar_id}"
        # Base64 URL-safe encode (no padding)
        encoded_event = base64.urlsafe_b64encode(event_data.encode()).decode().rstrip('=')
        edit_link = f"https://calendar.google.com/calendar/r/eventedit?eid={encoded_event}"
        
        # Alternative: Try using the htmlLink if available
        html_link = event.get('htmlLink', '')
        if html_link and 'eid=' in html_link:
            # Extract the eid parameter from htmlLink
            try:
                eid_param = html_link.split('eid=')[1].split('&')[0]
                # Use the same eid for edit link
                edit_link = f"https://calendar.google.com/calendar/r/eventedit?eid={eid_param}"
            except:
                pass  # Fall back to constructed URL
        
        return JSONResponse({
            "success": True,
            "eventId": event_id,
            "eventLink": edit_link,
            "message": "Draft event created. Redirecting to Google Calendar..."
        })
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"Error creating draft meeting: {traceback.format_exc()}")
        
        # Provide user-friendly error message
        if 'accessNotConfigured' in error_msg or 'API has not been used' in error_msg:
            # Extract project ID from error if available
            import re
            project_match = re.search(r'project=(\d+)', error_msg)
            project_id = project_match.group(1) if project_match else 'your-project-id'
            
            user_error = (
                f"Google Calendar API is not enabled in your Google Cloud project.\n\n"
                f"To fix this:\n"
                f"1. Go to: https://console.cloud.google.com/apis/library/calendar-json.googleapis.com?project={project_id}\n"
                f"2. Click 'Enable' button\n"
                f"3. Wait 1-2 minutes and try again\n\n"
                f"Note: Your service account belongs to project '{project_id}'.\n"
                f"This is the project where you need to enable the Calendar API."
            )
            return JSONResponse({"error": user_error}, status_code=400)
        elif 'Not Found' in error_msg or 'notFound' in error_msg or '404' in error_msg:
            user_error = (
                f"Calendar not found or service account doesn't have access.\n\n"
                f"To fix this:\n"
                f"1. Check your GOOGLE_CALENDAR_ID in .env file\n"
                f"2. Common values: 'primary' (for main calendar) or your email address\n"
                f"3. Go to Google Calendar → Settings → Share with specific people\n"
                f"4. Add your service account email: {settings.GOOGLE_CLIENT_EMAIL}\n"
                f"5. Give it 'Make changes to events' permission\n"
                f"6. Update GOOGLE_CALENDAR_ID in .env if needed\n\n"
                f"Current calendar ID: {settings.GOOGLE_CALENDAR_ID or 'not set'}"
            )
            return JSONResponse({"error": user_error}, status_code=400)
        
        return JSONResponse({"error": error_msg}, status_code=400)


@router.post("/admin/meetings/sync/{event_id}")
async def sync_meeting_from_calendar(request: Request, event_id: str):
    """Sync meeting event_id to database - details are fetched from Google Calendar when needed"""
    admin = get_current_admin(request)
    if not admin:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    db = SessionLocal()
    try:
        calendar_service = create_calendar_service()
        
        # Get event from Google Calendar to extract minimal info
        event = calendar_service.get_event(event_id)
        if not event:
            return JSONResponse({"error": "Event not found in Google Calendar"}, status_code=404)
        
        # Check if Google Meet link exists, if not, add it
        hangout_link = event.get('hangoutLink')
        if not hangout_link:
            print(f"📞 No Google Meet link found for event {event_id}, attempting to add one...")
            meet_result = calendar_service.add_google_meet_link(event_id)
            if meet_result and meet_result.get('hangoutLink'):
                hangout_link = meet_result.get('hangoutLink')
                print(f"✅ Google Meet link added: {hangout_link}")
                # Refresh event to get updated details
                event = calendar_service.get_event(event_id)
            else:
                print(f"⚠️ Could not add Google Meet link to event {event_id}")
        else:
            print(f"✅ Event {event_id} already has Google Meet link: {hangout_link}")
        
        # Extract only essential info for database storage
        extended_props = event.get('extendedProperties', {}) or {}
        host = (extended_props.get('host') or '').strip()
        form_type = (extended_props.get('form_type') or '').strip()
        
        # Check if event is recurring
        recurrence_list = event.get('recurrence', [])
        is_recurring = len(recurrence_list) > 0
        
        # Validate form_type
        if not form_type:
            return JSONResponse({"error": "Form type not found in event. Please ensure event was created from dashboard."}, status_code=400)
        
        try:
            meeting_type = MeetingType(form_type)
        except ValueError:
            return JSONResponse({"error": f"Invalid form_type: {form_type}"}, status_code=400)
        
        # Check if meeting already exists by google_event_id
        existing_meeting = db.query(MeetScheduler).filter(
            MeetScheduler.google_event_id == event_id
        ).first()
        
        if existing_meeting:
            # Update existing meeting (just update active status and host/form_type if changed)
            existing_meeting.host = host
            existing_meeting.form_type = meeting_type
            existing_meeting.is_active = True
            if is_recurring:
                # Get start time to determine recurring day
                start_data = event.get('start', {})
                start_time_str = start_data.get('dateTime') or start_data.get('date')
                if start_time_str and 'T' in start_time_str:
                    try:
                        ny_tz = pytz.timezone("America/New_York")
                        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                        if start_time.tzinfo is None:
                            start_time = ny_tz.localize(start_time)
                        else:
                            start_time = start_time.astimezone(ny_tz)
                        existing_meeting.recurring_day = start_time.weekday()
                    except:
                        pass
            else:
                existing_meeting.recurring_day = None
            db.commit()
            
            return JSONResponse({
                "success": True,
                "message": "Meeting updated in database",
                "meeting_id": existing_meeting.id,
                "google_event_id": event_id
            })
        else:
            # Create new meeting record with minimal info
            recurring_day = None
            if is_recurring:
                # Get start time to determine recurring day
                start_data = event.get('start', {})
                start_time_str = start_data.get('dateTime') or start_data.get('date')
                if start_time_str and 'T' in start_time_str:
                    try:
                        ny_tz = pytz.timezone("America/New_York")
                        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                        if start_time.tzinfo is None:
                            start_time = ny_tz.localize(start_time)
                        else:
                            start_time = start_time.astimezone(ny_tz)
                        recurring_day = start_time.weekday()
                    except:
                        pass
            
            new_meeting = MeetScheduler(
                google_event_id=event_id,
                host=host,
                form_type=meeting_type,
                is_active=True,
                recurring_day=recurring_day,
                guest_count=0
            )
            
            db.add(new_meeting)
            db.commit()
            db.refresh(new_meeting)
            
            print(f"✅ Saved meeting to database: event_id={event_id}, host={host}, form_type={form_type}")
            
            return JSONResponse({
                "success": True,
                "message": "Meeting synced to database",
                "meeting_id": new_meeting.id,
                "google_event_id": event_id
            })
    except Exception as e:
        db.rollback()
        import traceback
        print(f"Error syncing meeting: {traceback.format_exc()}")
        return JSONResponse({"error": str(e)}, status_code=400)
    finally:
        db.close()
