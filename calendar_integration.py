from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytz
from config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class CalendarService:
    def __init__(self, use_google_calendar: Optional[bool] = None, mock_time: Optional[datetime] = None):
        """
        Initialize the calendar service.
        Args:
            use_google_calendar: Override the config setting. If None, uses the config value.
            mock_time: Optional mock time to use instead of real time
        """
        self.use_google_calendar = use_google_calendar if use_google_calendar is not None else Config.USE_CALENDAR_INTEGRATION
        self.google_calendar_service = None
        self.local_calendar_file = Config.get_local_calendar_path()
        self.calendar_id = Config.GOOGLE_CALENDAR_ID
        self.user_email = None
        self.timezone = Config.get_timezone()
        
        # Set up mock time
        self.mock_current_time = mock_time
        if not self.use_google_calendar and not self.mock_current_time:
            self.mock_current_time = datetime.now(self.timezone).replace(
                hour=9, minute=0, second=0, microsecond=0
            )
        
        logger.debug(f"Calendar Service initialized with: use_google_calendar={self.use_google_calendar}, mock_time={self.mock_current_time}")
        
        if self.use_google_calendar and Config.is_google_calendar_configured():
            self._setup_google_calendar()
    
    def _setup_google_calendar(self) -> bool:
        """
        Set up Google Calendar API client.
        Returns True if setup was successful, False otherwise.
        """
        creds = None
        
        try:
            token_path = Config.get_token_path()
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, Config.GOOGLE_API_SCOPES)
                
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    client_secret_path = Config.get_client_secret_path()
                    if not os.path.exists(client_secret_path):
                        print(f"Error: {Config.GOOGLE_CLIENT_SECRET_FILE} not found. Please download it from Google Cloud Console.")
                        return False
                        
                    flow = InstalledAppFlow.from_client_secrets_file(
                        client_secret_path, Config.GOOGLE_API_SCOPES)
                    creds = flow.run_local_server(port=0)
                    
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
                    
            self.google_calendar_service = build('calendar', 'v3', credentials=creds)
            
            # Fetch user email
            user_info_service = build('oauth2', 'v2', credentials=creds)
            user_info = user_info_service.userinfo().get().execute()
            self.user_email = user_info.get('email')
            
            return True
            
        except Exception as e:
            print(f"Error setting up Google Calendar: {str(e)}")
            return False
    
    def get_calendar_email(self) -> Optional[str]:
        """Get the email address associated with the calendar."""
        return self.user_email if self.use_google_calendar else None
    
    def get_current_time(self) -> datetime:
        """Get the current time, using mock time if available."""
        if self.mock_current_time:
            # When in mock mode, return the fixed mock time without progression
            mock_now = self.mock_current_time
            
            # Ensure the datetime is timezone-aware
            if mock_now.tzinfo is None:
                mock_now = self.timezone.localize(mock_now)
                
            return mock_now
            
        return datetime.now(self.timezone)
    
    def get_day_events(self, target_date: Optional[datetime] = None) -> List[Dict]:
        """Get all events for a specific day."""
        if not target_date:
            target_date = self.get_current_time()
            
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        if self.use_google_calendar:
            return self._get_google_calendar_events_for_range(start_of_day, end_of_day)
        return self._get_local_calendar_events_for_range(start_of_day, end_of_day)
    
    def _get_google_calendar_events_for_range(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Fetch events from Google Calendar for a specific time range."""
        if not self.google_calendar_service:
            return []
            
        try:
            # Convert to UTC for Google Calendar API
            start_time_utc = start_time.astimezone(pytz.UTC)
            end_time_utc = end_time.astimezone(pytz.UTC)
            
            events_result = self.google_calendar_service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_time_utc.isoformat(),
                timeMax=end_time_utc.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            formatted_events = []
            
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                # Convert to datetime objects in local timezone
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00')).astimezone(self.timezone)
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00')).astimezone(self.timezone)
                
                formatted_events.append({
                    'summary': event.get('summary', 'Untitled Event'),
                    'start': start_dt.isoformat(),
                    'end': end_dt.isoformat(),
                    'id': event['id'],
                    'description': event.get('description', ''),
                    'location': event.get('location', ''),
                    'attendees': [
                        attendee.get('email') 
                        for attendee in event.get('attendees', [])
                        if attendee.get('email')
                    ],
                    'organizer': event.get('organizer', {}).get('email'),
                    'status': event.get('status', 'confirmed')
                })
            
            return formatted_events
            
        except HttpError as error:
            print(f"Error fetching Google Calendar events: {str(error)}")
            return []
    
    def _get_local_calendar_events_for_range(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Fetch events from local JSON calendar file for a specific time range."""
        logger.debug(f"Checking local calendar file: {self.local_calendar_file}")
        if not os.path.exists(self.local_calendar_file):
            logger.error(f"Local calendar file not found: {self.local_calendar_file}")
            return []
            
        try:
            with open(self.local_calendar_file, 'r') as f:
                calendar_data = json.load(f)
            
            events = calendar_data.get('events', [])
            logger.debug(f"Loaded {len(events)} events from local calendar")
            upcoming_events = []
            
            # Ensure start_time and end_time are timezone-aware
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=self.timezone)
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=self.timezone)
            
            # Convert search range to London time for comparison
            london_tz = pytz.timezone('Europe/London')
            start_time_london = start_time.astimezone(london_tz)
            end_time_london = end_time.astimezone(london_tz)
            
            logger.debug(f"Looking for events between {start_time_london} and {end_time_london} (London time)")
            
            for event in events:
                try:
                    # Parse event times (they're already in London time)
                    event_start = datetime.fromisoformat(event['start_time'])
                    event_end = datetime.fromisoformat(event['end_time'])
                    
                    # Add London timezone if not present
                    if event_start.tzinfo is None:
                        event_start = london_tz.localize(event_start)
                    if event_end.tzinfo is None:
                        event_end = london_tz.localize(event_end)
                    
                    logger.debug(f"Checking event: {event['summary']} at {event_start} (London time)")
                    logger.debug(f"Time window check: {event_end} >= {start_time_london} and {event_start} <= {end_time_london}")
                    
                    # Compare times in London timezone - show events that:
                    # 1. End after our start time (event hasn't finished yet)
                    # 2. Start before our end time (event starts within our window)
                    if event_end >= start_time_london and event_start <= end_time_london:
                        # Convert to standard format (in local timezone for display)
                        event_start_local = event_start.astimezone(self.timezone)
                        event_end_local = event_end.astimezone(self.timezone)
                        
                        formatted_event = {
                            'summary': event['summary'],
                            'start': event_start_local.isoformat(),
                            'end': event_end_local.isoformat(),
                            'id': event['id'],
                            'description': event.get('description', ''),
                            'location': event.get('location', ''),
                            'attendees': event.get('attendees', []),
                            'status': event.get('status', 'confirmed')
                        }
                        upcoming_events.append(formatted_event)
                        logger.debug(f"Added event: {event['summary']} at {event_start_local} (local time)")
                except (ValueError, KeyError) as e:
                    logger.error(f"Error processing event: {e}")
                    continue
            
            logger.info(f"Found {len(upcoming_events)} upcoming events")
            return upcoming_events
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Error reading local calendar: {str(e)}")
            return []
    
    def get_upcoming_events(self, minutes_ahead: int = 120) -> List[Dict]:
        """Get upcoming calendar events within the specified time window."""
        now = self.get_current_time()
        
        # Get all events for today
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day.replace(hour=23, minute=59, second=59)
        
        logger.debug(f"Looking for events between {start_of_day} and {end_of_day} (local timezone)")
        
        if self.use_google_calendar:
            return self._get_google_calendar_events_for_range(start_of_day, end_of_day)
        return self._get_local_calendar_events_for_range(start_of_day, end_of_day)
    
    def get_next_event(self) -> Optional[Dict]:
        """Get the next calendar event."""
        events = self.get_upcoming_events(minutes_ahead=240)  # Look ahead 4 hours
        return events[0] if events else None
    
    def is_free_for_next(self, minutes: int) -> bool:
        """Check if there are any events in the next X minutes."""
        now = self.get_current_time()
        end_time = now + timedelta(minutes=minutes)
        events = self._get_local_calendar_events_for_range(now, end_time)
        return len(events) == 0
    
    def get_next_free_slot(self, min_duration: int = 15) -> Optional[datetime]:
        """Find the next free time slot with at least min_duration minutes."""
        events = self.get_upcoming_events(240)  # Look ahead 4 hours
        if not events:
            return datetime.now(self.timezone)
            
        now = datetime.now(self.timezone)
        for i in range(len(events)):
            current_event_end = datetime.fromisoformat(events[i]['end']).astimezone(self.timezone)
            next_event_start = (datetime.fromisoformat(events[i + 1]['start']).astimezone(self.timezone) 
                              if i + 1 < len(events) else None)
            
            if next_event_start is None:
                return current_event_end
            
            gap = (next_event_start - current_event_end).total_seconds() / 60
            if gap >= min_duration:
                return current_event_end
        
        return None
    
    def get_busy_times(self, start_date: datetime, end_date: datetime) -> List[Tuple[datetime, datetime]]:
        """Get busy time slots between start_date and end_date."""
        events = self._get_google_calendar_events_for_range(start_date, end_date) if self.use_google_calendar \
                else self._get_local_calendar_events_for_range(start_date, end_date)
        
        busy_times = []
        for event in events:
            start = datetime.fromisoformat(event['start']).astimezone(self.timezone)
            end = datetime.fromisoformat(event['end']).astimezone(self.timezone)
            busy_times.append((start, end))
            
        return sorted(busy_times, key=lambda x: x[0]) 