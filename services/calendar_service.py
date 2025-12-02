"""
Google Calendar Service
Handles calendar event creation, updates, and deletion
"""
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import settings
import pytz


class GoogleCalendarService:
    def __init__(self, credentials_dict: Optional[Dict[str, Any]] = None, calendar_id: Optional[str] = None):
        """
        Initialize Google Calendar Service
        
        Args:
            credentials_dict: Optional dict with service account credentials
            calendar_id: Optional Google Calendar ID (uses default from settings if None)
        """
        self.credentials_dict = credentials_dict
        self.calendar_id = calendar_id or settings.GOOGLE_CALENDAR_ID
        self.service = None
        self._authenticate()
        print("this API is called at 28", self.calendar_id)
    def _authenticate(self):
        """Authenticate using credentials from dictionary (env vars)"""
        try:
            # Use provided credentials dict or build from settings
            if not self.credentials_dict:
                self.credentials_dict = self._build_credentials_from_env()
            
            # Validate project ID matches
            cred_project_id = self.credentials_dict.get('project_id')
            env_project_id = settings.GOOGLE_PROJECT_ID
            if cred_project_id and env_project_id and cred_project_id != env_project_id:
                print(f"⚠️  Warning: Service account project_id ({cred_project_id}) doesn't match GOOGLE_PROJECT_ID ({env_project_id})")
                print(f"⚠️  Google will use project_id from credentials: {cred_project_id}")
            
            credentials = service_account.Credentials.from_service_account_info(
                self.credentials_dict,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            self.service = build('calendar', 'v3', credentials=credentials)
            print(f"✅ Google Calendar authentication successful")
            print(f"📋 Using project: {cred_project_id or 'unknown'}")
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Google Calendar authentication failed: {error_msg}")
            
            # Provide helpful error message for API not enabled
            if 'accessNotConfigured' in error_msg or 'API has not been used' in error_msg:
                cred_project_id = self.credentials_dict.get('project_id', 'unknown') if self.credentials_dict else 'unknown'
                
                # Try to extract actual project ID from error message
                import re
                project_match = re.search(r'project[=\s](\d+)', error_msg)
                actual_project_id = project_match.group(1) if project_match else cred_project_id
                
                print(f"\n🔧 SOLUTION:")
                print(f"   Your service account credentials belong to project: {actual_project_id}")
                print(f"   Your GOOGLE_PROJECT_ID in .env is: {cred_project_id}")
                print(f"\n   To fix:")
                print(f"   1. Update GOOGLE_PROJECT_ID in your .env file to: {actual_project_id}")
                print(f"   2. Enable Calendar API: https://console.cloud.google.com/apis/library/calendar-json.googleapis.com?project={actual_project_id}")
                print(f"   3. Click 'Enable' button")
                print(f"   4. Wait 1-2 minutes and try again")
                print(f"\n   OR if you want to use project '{cred_project_id}':")
                print(f"   - Create a new service account in that project")
                print(f"   - Update all Google credentials in .env to match the new service account")
            
            raise
    
    def _build_credentials_from_env(self) -> Dict[str, Any]:
        """Build credentials dictionary from environment variables"""
        # Validate required fields
        required_fields = {
            'GOOGLE_PROJECT_ID': settings.GOOGLE_PROJECT_ID,
            'GOOGLE_PRIVATE_KEY': settings.GOOGLE_PRIVATE_KEY,
            'GOOGLE_CLIENT_EMAIL': settings.GOOGLE_CLIENT_EMAIL,
            'GOOGLE_PRIVATE_KEY_ID': settings.GOOGLE_PRIVATE_KEY_ID,
            'GOOGLE_CLIENT_ID': settings.GOOGLE_CLIENT_ID,
        }
        
        missing_fields = [key for key, value in required_fields.items() if not value]
        if missing_fields:
            raise ValueError(
                f"Missing required Google credentials in .env file: {', '.join(missing_fields)}\n"
                f"Please ensure all Google service account credentials are set in your .env file."
            )
        
        # Handle private key formatting (replace literal \n with actual newlines)
        private_key = settings.GOOGLE_PRIVATE_KEY
        if private_key and "\\n" in private_key:
            private_key = private_key.replace("\\n", "\n")
        
        # Extract project ID from client_email if it contains project info
        # Service account emails are usually: service-account-name@project-id.iam.gserviceaccount.com
        project_id = settings.GOOGLE_PROJECT_ID
        client_email = settings.GOOGLE_CLIENT_EMAIL or ""
        
        # Try to extract project ID from email if GOOGLE_PROJECT_ID seems wrong
        if client_email and "@" in client_email:
            email_parts = client_email.split("@")
            if len(email_parts) > 1:
                domain = email_parts[1]
                # Check if domain contains project ID pattern
                if ".iam.gserviceaccount.com" in domain:
                    # Extract project ID from domain (format: project-id.iam.gserviceaccount.com)
                    potential_project = domain.replace(".iam.gserviceaccount.com", "")
                    # If current project_id doesn't match, warn but use the one from env
                    # (User should update .env to match)
                    if project_id and project_id != potential_project:
                        print(f"⚠️  Note: Service account email suggests project '{potential_project}', but GOOGLE_PROJECT_ID is '{project_id}'")
                        print(f"⚠️  If you get API errors, try setting GOOGLE_PROJECT_ID={potential_project} in your .env file")
        
        credentials = {
            "type": settings.GOOGLE_SERVICE_ACCOUNT_TYPE,
            "project_id": project_id,  # Use from .env - user should ensure it matches service account
            "private_key_id": settings.GOOGLE_PRIVATE_KEY_ID,
            "private_key": private_key,
            "client_email": settings.GOOGLE_CLIENT_EMAIL,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "auth_uri": settings.GOOGLE_AUTH_URI,
            "token_uri": settings.GOOGLE_TOKEN_URI,
            "auth_provider_x509_cert_url": settings.GOOGLE_AUTH_PROVIDER_CERT_URL,
            "client_x509_cert_url": settings.GOOGLE_CLIENT_CERT_URL,
            "universe_domain": settings.GOOGLE_UNIVERSE_DOMAIN
        }
        
        return credentials
    
    def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        meeting_link: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        recurrence: Optional[List[str]] = None,
        timezone: str = "America/New_York",
        extended_properties: Optional[Dict[str, str]] = None,
        request_google_meet: bool = False
    ) -> Dict[str, Any]:
        """
        Create a calendar event
        
        Args:
            title: Event title
            start_time: Event start time (datetime object)
            end_time: Event end time (datetime object, defaults to start_time + 1 hour)
            description: Event description
            location: Event location
            meeting_link: Meeting link (Zoom, etc.)
            attendees: List of attendee email addresses
            recurrence: List of recurrence rules (e.g., ['RRULE:FREQ=WEEKLY;BYDAY=MO;COUNT=26'])
            timezone: Timezone string (default: America/New_York)
            extended_properties: Custom properties (e.g., {'host': 'Evan', 'form_type': 'LOI Call'})
            request_google_meet: If True, requests Google Meet link creation (default: False)
        
        Returns:
            Dictionary with event details including 'id', 'htmlLink', and 'hangoutLink' (if requested)
        """
        try:
            # Ensure timezone-aware datetime
            tz = pytz.timezone(timezone)
            if start_time.tzinfo is None:
                start_time = tz.localize(start_time)
            else:
                start_time = start_time.astimezone(tz)
            
            if end_time is None:
                end_time = start_time + timedelta(hours=1)
            else:
                if end_time.tzinfo is None:
                    end_time = tz.localize(end_time)
                else:
                    end_time = end_time.astimezone(tz)
            
            # Build event body
            event = {
                'summary': title,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': timezone,
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': timezone,
                },
            }
            
            # Add description
            if description:
                event['description'] = description
            
            # Add location or meeting link
            if meeting_link:
                event['location'] = meeting_link
                # Add meeting link to description if not already there
                if description and meeting_link not in description:
                    event['description'] = f"{description}\n\nMeeting Link: {meeting_link}"
                elif not description:
                    event['description'] = f"Meeting Link: {meeting_link}"
            elif location:
                event['location'] = location
            
            # Add attendees
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            # Add recurrence
            if recurrence:
                event['recurrence'] = recurrence
            
            # Add extended properties (for storing custom data like host, form_type)
            if extended_properties:
                event['extendedProperties'] = {
                    'private': extended_properties
                }
            
            # Request Google Meet link if requested
            if request_google_meet:
                import uuid
                # Try without conferenceSolutionKey first (Google will default to hangoutsMeet)
                # This works better with service accounts
                event['conferenceData'] = {
                    'createRequest': {
                        'requestId': str(uuid.uuid4())
                    }
                }
                print(f"📞 Requesting Google Meet link (using default type)")
            
            # Validate calendar exists and is accessible
            try:
                # Try to get calendar to verify access
                self.service.calendars().get(calendarId=self.calendar_id).execute()
            except HttpError as e:
                if e.resp.status == 404:
                    raise ValueError(
                        f"Calendar not found: {self.calendar_id}\n\n"
                        f"Possible issues:\n"
                        f"1. Calendar ID is incorrect in GOOGLE_CALENDAR_ID\n"
                        f"2. Calendar doesn't exist\n"
                        f"3. Service account doesn't have access to this calendar\n\n"
                        f"To fix:\n"
                        f"1. Go to Google Calendar settings\n"
                        f"2. Find your calendar's 'Calendar ID' (usually your email or 'primary')\n"
                        f"3. Share the calendar with your service account email: {self.credentials_dict.get('client_email', 'unknown')}\n"
                        f"4. Give it 'Make changes to events' permission\n"
                        f"5. Update GOOGLE_CALENDAR_ID in .env file\n\n"
                        f"Common values:\n"
                        f"- 'primary' (for your main calendar)\n"
                        f"- Your email address (e.g., 'your-email@gmail.com')\n"
                        f"- A specific calendar ID from calendar settings"
                    )
                raise
            
            # Create the event
            # If requesting Google Meet, need to use conferenceDataVersion parameter
            if request_google_meet:
                created_event = self.service.events().insert(
                    calendarId=self.calendar_id,
                    body=event,
                    conferenceDataVersion=1
                ).execute()
            else:
                created_event = self.service.events().insert(
                    calendarId=self.calendar_id,
                    body=event
                ).execute()
            
            print(f"✅ Event created: {title} ({created_event.get('id')})")
            return {
                'id': created_event.get('id'),
                'htmlLink': created_event.get('htmlLink'),
                'iCalUID': created_event.get('iCalUID'),
                'start': created_event.get('start'),
                'end': created_event.get('end'),
                'summary': created_event.get('summary'),
                'description': created_event.get('description'),
                'location': created_event.get('location'),
                'hangoutLink': created_event.get('hangoutLink'),  # Google Meet link
                'conferenceData': created_event.get('conferenceData'),  # Conference details
                'recurrence': created_event.get('recurrence', []),
                'extendedProperties': created_event.get('extendedProperties', {}).get('private', {})
            }
        except HttpError as error:
            print(f"❌ Google Calendar event creation failed: {error}")
            raise
    
    def update_event(
        self,
        event_id: str,
        title: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        meeting_link: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        recurrence: Optional[List[str]] = None,
        timezone: str = "America/New_York",
        extended_properties: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing calendar event
        
        Args:
            event_id: Google Calendar event ID
            title: Event title (optional)
            start_time: Event start time (optional)
            end_time: Event end time (optional)
            description: Event description (optional)
            location: Event location (optional)
            meeting_link: Meeting link (optional)
            attendees: List of attendee email addresses (optional)
            recurrence: List of recurrence rules (optional)
            timezone: Timezone string (default: America/New_York)
            extended_properties: Custom properties (optional)
        
        Returns:
            Dictionary with updated event details
        """
        try:
            # Get existing event
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            # Update fields if provided
            if title:
                event['summary'] = title
            
            tz = pytz.timezone(timezone)
            if start_time:
                if start_time.tzinfo is None:
                    start_time = tz.localize(start_time)
                else:
                    start_time = start_time.astimezone(tz)
                event['start'] = {
                    'dateTime': start_time.isoformat(),
                    'timeZone': timezone,
                }
            
            if end_time:
                if end_time.tzinfo is None:
                    end_time = tz.localize(end_time)
                else:
                    end_time = end_time.astimezone(tz)
                event['end'] = {
                    'dateTime': end_time.isoformat(),
                    'timeZone': timezone,
                }
            
            if description:
                event['description'] = description
            
            if meeting_link:
                event['location'] = meeting_link
                if description and meeting_link not in description:
                    event['description'] = f"{description}\n\nMeeting Link: {meeting_link}"
                elif not event.get('description'):
                    event['description'] = f"Meeting Link: {meeting_link}"
            elif location:
                event['location'] = location
            
            if attendees is not None:
                # Merge with existing attendees if they exist
                existing_attendees = event.get('attendees', [])
                existing_emails = {att.get('email', '').lower() for att in existing_attendees if isinstance(att, dict) and att.get('email')}
                
                # Create new attendees list, preserving existing attendee objects and adding new ones
                new_attendees_list = list(existing_attendees)  # Keep existing attendee objects
                
                # Add new attendees that don't already exist
                for email in attendees:
                    if email and email.lower() not in existing_emails:
                        new_attendees_list.append({'email': email})
                        existing_emails.add(email.lower())
                
                event['attendees'] = new_attendees_list
            
            if recurrence is not None:
                event['recurrence'] = recurrence
            
            if extended_properties:
                if 'extendedProperties' not in event:
                    event['extendedProperties'] = {}
                event['extendedProperties']['private'] = extended_properties
            
            # Update the event
            # Use sendUpdates='none' to avoid sending email invitations (which requires domain-wide delegation)
            # This allows adding attendees without sending notifications
            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event,
                sendUpdates='none'  # Don't send email notifications
            ).execute()
            
            print(f"✅ Event updated: {event_id}")
            return {
                'id': updated_event.get('id'),
                'htmlLink': updated_event.get('htmlLink'),
                'iCalUID': updated_event.get('iCalUID'),
                'start': updated_event.get('start'),
                'end': updated_event.get('end'),
                'summary': updated_event.get('summary'),
                'description': updated_event.get('description'),
                'location': updated_event.get('location'),
                'recurrence': updated_event.get('recurrence', []),
                'extendedProperties': updated_event.get('extendedProperties', {}).get('private', {})
            }
        except HttpError as error:
            print(f"❌ Google Calendar event update failed: {error}")
            raise
    
    def delete_event(self, event_id: str) -> bool:
        """
        Delete a calendar event
        
        Args:
            event_id: Google Calendar event ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            print(f"✅ Event deleted: {event_id}")
            return True
        except HttpError as error:
            print(f"❌ Google Calendar event deletion failed: {error}")
            return False
    
    def add_google_meet_link(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Add Google Meet link to an existing event if it doesn't have one
        
        Args:
            event_id: Google Calendar event ID
        
        Returns:
            Updated event dictionary with hangoutLink or None if failed
        """
        try:
            # Get the current event
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            # Check if event already has a Meet link
            if event.get('hangoutLink'):
                print(f"✅ Event {event_id} already has Google Meet link")
                return {
                    'id': event.get('id'),
                    'hangoutLink': event.get('hangoutLink'),
                    'conferenceData': event.get('conferenceData')
                }
            
            # Add conference data to request Google Meet link
            import uuid
            # Try without conferenceSolutionKey first (Google will default to hangoutsMeet)
            # This works better with service accounts
            event['conferenceData'] = {
                'createRequest': {
                    'requestId': str(uuid.uuid4())
                }
            }
            print(f"📞 Adding Google Meet link (using default type)")
            
            # Update the event with conferenceDataVersion=1 to create Meet link
            try:
                updated_event = self.service.events().update(
                    calendarId=self.calendar_id,
                    eventId=event_id,
                    body=event,
                    conferenceDataVersion=1
                ).execute()
                
                hangout_link = updated_event.get('hangoutLink')
                if hangout_link:
                    print(f"✅ Google Meet link added to event {event_id}: {hangout_link}")
                else:
                    print(f"⚠️ Meet link requested but not yet available for event {event_id}")
                
                return {
                    'id': updated_event.get('id'),
                    'hangoutLink': hangout_link,
                    'conferenceData': updated_event.get('conferenceData')
                }
            except HttpError as error:
                error_msg = str(error)
                # Check if it's a conference-related error
                if 'conference' in error_msg.lower() or 'Invalid conference' in error_msg:
                    print(f"⚠️ Could not add Google Meet link to event {event_id}: {error_msg}")
                    print(f"💡 Note: Service accounts may need domain-wide delegation to create Google Meet links.")
                    print(f"💡 The event was updated but without a Meet link. You can add it manually in Google Calendar.")
                    # Return the event without Meet link (event was still updated)
                    return {
                        'id': event_id,
                        'hangoutLink': None,
                        'conferenceData': None,
                        'error': 'Could not create Meet link - may require domain-wide delegation'
                    }
                else:
                    raise
        except HttpError as error:
            print(f"❌ Failed to add Google Meet link to event {event_id}: {error}")
            return None
    
    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single event by ID directly from Google Calendar API
        Returns ALL event details from Google Calendar, not from local database
        
        Args:
            event_id: Google Calendar event ID
        
        Returns:
            Complete event dictionary with all fields from Google Calendar API or None if not found
        """
        try:
            # Fetch event directly from Google Calendar API
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            # Return the COMPLETE event data structure from Google Calendar API
            # This includes ALL fields: summary, description, location, hangoutLink, 
            # start, end, recurrence, attendees, extendedProperties, etc.
            return {
                'id': event.get('id'),
                'htmlLink': event.get('htmlLink'),
                'iCalUID': event.get('iCalUID'),
                'start': event.get('start'),  # Contains 'dateTime' and 'timeZone' keys
                'end': event.get('end'),      # Contains 'dateTime' and 'timeZone' keys
                'summary': event.get('summary'),
                'description': event.get('description'),
                'location': event.get('location'),
                'hangoutLink': event.get('hangoutLink'),  # Google Meet link
                'conferenceData': event.get('conferenceData'),  # Conference details
                'recurrence': event.get('recurrence', []),
                'extendedProperties': event.get('extendedProperties', {}).get('private', {}),
                'attendees': event.get('attendees', []),  # Full attendee objects
                'status': event.get('status'),
                'created': event.get('created'),
                'updated': event.get('updated'),
                'creator': event.get('creator'),
                'organizer': event.get('organizer'),
                # Include timezone info if available
                'start_timezone': event.get('start', {}).get('timeZone'),
                'end_timezone': event.get('end', {}).get('timeZone'),
                # Return raw event for any additional fields
                '_raw': event
            }
        except HttpError as error:      
            print(f"❌ Google Calendar event retrieval failed: {error}")
            return None
    
    def list_events(
        self,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 250,
        single_events: bool = True,
        order_by: str = 'startTime',
        q: Optional[str] = None,
        extended_properties_filter: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        List calendar events
        
        Args:
            time_min: Minimum time for events (defaults to now)
            time_max: Maximum time for events
            max_results: Maximum number of results
            single_events: If True, expand recurring events into individual instances
            order_by: Order by 'startTime' or 'updated'
            q: Free text search query
            extended_properties_filter: Filter by extended properties (e.g., {'host': 'Evan'})
        
        Returns:
            List of event dictionaries
        """
        try:
            # Validate calendar access first
            try:
                self.service.calendars().get(calendarId=self.calendar_id).execute()
            except HttpError as e:
                if e.resp.status == 404:
                    raise ValueError(
                        f"Calendar not found: {self.calendar_id}\n\n"
                        f"Please check your GOOGLE_CALENDAR_ID in .env file.\n"
                        f"Use 'primary' for your main calendar, or share the calendar with service account."
                    )
                raise
            tz = pytz.timezone("America/New_York")
            if time_min is None:
                time_min = datetime.now(tz)
            elif time_min.tzinfo is None:
                time_min = tz.localize(time_min)
            print("this API is called at 599")
            if time_max and time_max.tzinfo is None:
                time_max = tz.localize(time_max)
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat() if time_max else None,
                maxResults=max_results,
                singleEvents=single_events,
                orderBy=order_by,
                q=q
            ).execute()
            
            events = events_result.get('items', [])
            
            # Filter by extended properties if provided
            if extended_properties_filter:
                filtered_events = []
                for event in events:
                    event_props = event.get('extendedProperties', {}).get('private', {})
                    match = True
                    for key, value in extended_properties_filter.items():
                        if event_props.get(key) != value:
                            match = False
                            break
                    if match:
                        filtered_events.append(event)
                events = filtered_events
            
            # Format events
            formatted_events = []
            for event in events:
                formatted_events.append({
                    'id': event.get('id'),
                    'htmlLink': event.get('htmlLink'),
                    'iCalUID': event.get('iCalUID'),
                    'start': event.get('start'),
                    'end': event.get('end'),
                    'summary': event.get('summary'),
                    'description': event.get('description'),
                    'location': event.get('location'),
                    'recurrence': event.get('recurrence', []),
                    'extendedProperties': event.get('extendedProperties', {}).get('private', {}),
                    'attendees': [att.get('email') for att in event.get('attendees', [])]
                })
            
            return formatted_events
        except HttpError as error:
            print(f"❌ Google Calendar event listing failed: {error}")
            return []


def create_calendar_service(credentials_dict: Optional[Dict[str, Any]] = None, 
                           calendar_id: Optional[str] = None) -> GoogleCalendarService:
    """
    Factory function to create GoogleCalendarService instance
    
    Args:
        credentials_dict: Optional dict with service account credentials (uses env vars if None)
        calendar_id: Optional Google Calendar ID (uses settings if None)
        
    Returns:
        GoogleCalendarService instance
    """
    return GoogleCalendarService(credentials_dict, calendar_id)

