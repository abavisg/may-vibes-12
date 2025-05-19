import os
from pathlib import Path
from dotenv import load_dotenv
import pytz
from datetime import datetime

# Load environment variables from .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    @staticmethod
    def validate_timezone(tz_string: str) -> str:
        """Validate and return a timezone string."""
        try:
            pytz.timezone(tz_string)
            return tz_string
        except pytz.exceptions.UnknownTimeZoneError:
            print(f"Warning: Invalid timezone '{tz_string}'. Falling back to 'Europe/London'")
            return 'Europe/London'
    
    # Base Paths
    SECRETS_DIR = Path(os.getenv('SECRETS_DIR', 'secrets'))
    MOCK_DATA_DIR = Path(os.getenv('MOCK_DATA_DIR', 'mock-data'))
    
    # Mocking Settings
    MOCKING_ENABLED = os.getenv('MOCKING_ENABLED', 'true').lower() == 'true'
    MOCKED_DATE = os.getenv('MOCKED_DATE', '2025-05-19')  # Format: YYYY-MM-DD
    MOCKED_TIME = os.getenv('MOCKED_TIME', '09:00:00')    # Format: HH:MM:SS
    
    # Google Calendar Settings
    USE_CALENDAR_INTEGRATION = os.getenv('USE_CALENDAR_INTEGRATION', 'false' if MOCKING_ENABLED else 'true').lower() == 'true'
    GOOGLE_CLIENT_SECRET_FILE = os.getenv('GOOGLE_CLIENT_SECRET_FILE', 'client_secret.json')
    GOOGLE_TOKEN_FILE = os.getenv('GOOGLE_TOKEN_FILE', 'token.json')
    GOOGLE_CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
    GOOGLE_OAUTH_PORT = int(os.getenv('GOOGLE_OAUTH_PORT', '8080'))
    GOOGLE_OAUTH_HOST = os.getenv('GOOGLE_OAUTH_HOST', 'localhost')
    GOOGLE_API_SCOPES = [
        'openid',
        'https://www.googleapis.com/auth/calendar.readonly',
        'https://www.googleapis.com/auth/userinfo.email'
    ]
    
    # Application Settings
    TIMEZONE = validate_timezone(os.getenv('TIMEZONE', 'Europe/London'))
    DEFAULT_WORK_START_TIME = os.getenv('DEFAULT_WORK_START_TIME', '09:00')
    DEFAULT_WORK_END_TIME = os.getenv('DEFAULT_WORK_END_TIME', '17:00')
    DEFAULT_LUNCH_TIME = os.getenv('DEFAULT_LUNCH_TIME', '12:00')
    DEFAULT_LUNCH_DURATION = int(os.getenv('DEFAULT_LUNCH_DURATION', '60'))
    
    # Local Calendar Settings
    LOCAL_CALENDAR_FILE = os.getenv('LOCAL_CALENDAR_FILE', 'local_calendar_current.json')
    
    @classmethod
    def get_mock_time(cls) -> datetime:
        """Get a datetime object based on the configured mock date and time."""
        date_str = f"{cls.MOCKED_DATE} {cls.MOCKED_TIME}"
        try:
            # Parse the mock date and time, then localize to the configured timezone
            naive_dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            return cls.get_timezone().localize(naive_dt)
        except Exception as e:
            print(f"Error creating mock time: {e}. Using current time.")
            return datetime.now(cls.get_timezone())
    
    @classmethod
    def get_oauth_redirect_uri(cls) -> str:
        """Get the OAuth redirect URI."""
        return f'http://{cls.GOOGLE_OAUTH_HOST}:{cls.GOOGLE_OAUTH_PORT}/'
    
    @classmethod
    def get_secrets_dir(cls) -> Path:
        """Get the path to the secrets directory, creating it if it doesn't exist."""
        cls.SECRETS_DIR.mkdir(exist_ok=True)
        return cls.SECRETS_DIR
    
    @classmethod
    def get_mock_data_dir(cls) -> Path:
        """Get the path to the mock data directory, creating it if it doesn't exist."""
        cls.MOCK_DATA_DIR.mkdir(exist_ok=True)
        return cls.MOCK_DATA_DIR
    
    @classmethod
    def get_client_secret_path(cls) -> Path:
        """Get the absolute path to the client secret file."""
        return cls.get_secrets_dir() / cls.GOOGLE_CLIENT_SECRET_FILE
    
    @classmethod
    def get_token_path(cls) -> Path:
        """Get the absolute path to the token file."""
        return cls.get_secrets_dir() / cls.GOOGLE_TOKEN_FILE
    
    @classmethod
    def get_local_calendar_path(cls) -> Path:
        """Get the absolute path to the local calendar file."""
        return cls.get_mock_data_dir() / cls.LOCAL_CALENDAR_FILE
    
    @classmethod
    def is_google_calendar_configured(cls) -> bool:
        """Check if Google Calendar is properly configured."""
        client_secret_exists = cls.get_client_secret_path().exists()
        if not client_secret_exists:
            print(f"Warning: {cls.GOOGLE_CLIENT_SECRET_FILE} not found in {cls.SECRETS_DIR}")
        return cls.USE_CALENDAR_INTEGRATION and client_secret_exists
    
    @classmethod
    def get_timezone(cls) -> pytz.timezone:
        """Get the configured timezone as a pytz timezone object."""
        return pytz.timezone(cls.TIMEZONE) 