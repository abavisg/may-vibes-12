import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    # Base Paths
    SECRETS_DIR = Path(os.getenv('SECRETS_DIR', 'secrets'))
    
    # Google Calendar Settings
    GOOGLE_CALENDAR_ENABLED = os.getenv('GOOGLE_CALENDAR_ENABLED', 'false').lower() == 'true'
    GOOGLE_CLIENT_SECRET_FILE = os.getenv('GOOGLE_CLIENT_SECRET_FILE', 'client_secret.json')
    GOOGLE_TOKEN_FILE = os.getenv('GOOGLE_TOKEN_FILE', 'token.json')
    GOOGLE_CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
    GOOGLE_OAUTH_PORT = int(os.getenv('GOOGLE_OAUTH_PORT', '8080'))
    GOOGLE_OAUTH_HOST = os.getenv('GOOGLE_OAUTH_HOST', 'localhost')
    GOOGLE_API_SCOPES = [
        'https://www.googleapis.com/auth/calendar.readonly',
        'https://www.googleapis.com/auth/userinfo.email'
    ]
    
    # Application Settings
    TIMEZONE = os.getenv('TIMEZONE', 'UTC')
    DEFAULT_WORK_START_TIME = os.getenv('DEFAULT_WORK_START_TIME', '09:00')
    DEFAULT_WORK_END_TIME = os.getenv('DEFAULT_WORK_END_TIME', '17:00')
    DEFAULT_LUNCH_TIME = os.getenv('DEFAULT_LUNCH_TIME', '12:00')
    DEFAULT_LUNCH_DURATION = int(os.getenv('DEFAULT_LUNCH_DURATION', '60'))
    
    # Local Calendar Settings
    LOCAL_CALENDAR_FILE = os.getenv('LOCAL_CALENDAR_FILE', 'local_calendar.json')
    
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
        return cls.get_secrets_dir() / cls.LOCAL_CALENDAR_FILE
    
    @classmethod
    def is_google_calendar_configured(cls) -> bool:
        """Check if Google Calendar is properly configured."""
        client_secret_exists = cls.get_client_secret_path().exists()
        if not client_secret_exists:
            print(f"Warning: {cls.GOOGLE_CLIENT_SECRET_FILE} not found in {cls.SECRETS_DIR}")
        return cls.GOOGLE_CALENDAR_ENABLED and client_secret_exists 