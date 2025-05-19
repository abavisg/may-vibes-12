from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os.path
from pathlib import Path
import pytz
from config import Config

class GoogleCalendarClient:
    def __init__(self):
        self.SCOPES = Config.GOOGLE_API_SCOPES
        self.service = None
        self.creds = None
        
    def authenticate(self):
        """Handle Google Calendar authentication using OAuth 2.0."""
        creds = None
        token_path = Config.get_token_path()
        
        try:
            # Check if token.json exists with valid credentials
            if token_path.exists():
                try:
                    creds = Credentials.from_authorized_user_file(str(token_path), self.SCOPES)
                except Exception as e:
                    print(f"\nError reading token file: {e}")
                    print("Removing invalid token file and starting fresh...")
                    token_path.unlink()  # Delete the invalid token file
                    creds = None
            
            # If no valid credentials available, let user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                    except Exception as e:
                        print(f"\nError refreshing token: {e}")
                        print("Starting fresh OAuth flow...")
                        creds = None
                
                if not creds:
                    client_secret_path = Config.get_client_secret_path()
                    if not client_secret_path.exists():
                        raise FileNotFoundError(
                            f'{Config.GOOGLE_CLIENT_SECRET_FILE} not found in {Config.SECRETS_DIR}. '
                            'Please download it from Google Cloud Console.'
                        )
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(client_secret_path), 
                        self.SCOPES,
                        redirect_uri=Config.get_oauth_redirect_uri()
                    )
                    
                    # Print helpful message about the redirect URI
                    print(f"\nUsing redirect URI: {Config.get_oauth_redirect_uri()}")
                    print("Make sure this URI is configured in your Google Cloud Console OAuth 2.0 Client ID settings.")
                    
                    try:
                        # Force consent to ensure we get a refresh token
                        creds = flow.run_local_server(
                            host=Config.GOOGLE_OAUTH_HOST,
                            port=Config.GOOGLE_OAUTH_PORT,
                            authorization_prompt_message="Please authorize the application again to ensure proper access.",
                            prompt='consent'  # Force consent screen to appear
                        )
                    except Exception as e:
                        print(f"\nError during OAuth flow: {str(e)}")
                        print("\nPlease ensure the following redirect URI is configured in Google Cloud Console:")
                        print(f"    {Config.get_oauth_redirect_uri()}")
                        print("\nSteps to fix this:")
                        print("1. Go to Google Cloud Console > APIs & Services > Credentials")
                        print("2. Find your OAuth 2.0 Client ID")
                        print("3. Click Edit (pencil icon)")
                        print("4. Add the above URI to 'Authorized redirect URIs'")
                        print("5. Click Save and try again")
                        raise
                
                # Verify we have a refresh token before saving
                if not creds.refresh_token:
                    print("\nWarning: No refresh token received. Please try revoking access and authenticating again:")
                    print("1. Go to https://myaccount.google.com/permissions")
                    print("2. Find this application and click 'Remove Access'")
                    print("3. Run this script again")
                    raise Exception("No refresh token received during authentication")
                
                # Save the credentials for future use
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            
            self.creds = creds
            self.service = build('calendar', 'v3', credentials=creds)
            return True
            
        except Exception as e:
            error_msg = str(e)
            if "Scope has changed" in error_msg:
                print("\nDetected scope change. Removing old token and retrying authentication...")
                if token_path.exists():
                    token_path.unlink()  # Delete the token file
                return self.authenticate()  # Retry authentication
            raise
    
    def get_today_events(self):
        """Get all calendar events scheduled for today."""
        if not self.service:
            self.authenticate()
        
        # Get timezone-aware timestamps for start and end of today
        local_tz = pytz.timezone(Config.TIMEZONE)
        now = datetime.now(local_tz)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        try:
            events_result = self.service.events().list(
                calendarId=Config.GOOGLE_CALENDAR_ID,
                timeMin=start_of_day.isoformat(),
                timeMax=end_of_day.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                return "No events found for today."
            
            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                # Convert to datetime object for consistent formatting
                if 'T' in start:  # This is a datetime
                    start_time = datetime.fromisoformat(start).strftime('%I:%M %p')
                else:  # This is a date
                    start_time = 'All day'
                
                formatted_events.append({
                    'time': start_time,
                    'summary': event['summary']
                })
            
            return formatted_events
            
        except Exception as e:
            print(f"An error occurred: {e}")
            return []

def main():
    """Example usage of the GoogleCalendarClient."""
    try:
        if not Config.GOOGLE_CALENDAR_ENABLED:
            print("\nGoogle Calendar is not enabled. Please set GOOGLE_CALENDAR_ENABLED=true in your .env file.")
            return
            
        # Initialize and authenticate
        calendar = GoogleCalendarClient()
        calendar.authenticate()
        
        # Get today's events
        print("\nFetching today's events...")
        events = calendar.get_today_events()
        
        # Display events
        if isinstance(events, str):
            print(events)
        else:
            print("\nToday's Schedule:")
            print("================")
            for event in events:
                print(f"{event['time']} - {event['summary']}")
        
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print(f"Please ensure your OAuth 2.0 Client ID credentials are in {Config.SECRETS_DIR}")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == '__main__':
    main() 