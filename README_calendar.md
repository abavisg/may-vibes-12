# Google Calendar Integration

This script provides a simple way to access your Google Calendar events using Python.

## Setup Instructions

1. **Set up Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Calendar API for your project

2. **Create OAuth 2.0 Credentials**:
   - Go to APIs & Services > Credentials
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as the application type
   - Give it a name (e.g., "Calendar Client")
   - Download the client configuration file
   - Rename it to `credentials.json` and place it in the script directory

3. **Install Required Packages**:
```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client pytz
```

## Usage

1. **First Run**:
```bash
python google_calendar_client.py
```
- On first run, it will open your browser for OAuth authentication
- Grant the requested permissions
- The script will save the token in `token.json` for future use

2. **Subsequent Runs**:
- The script will use the stored `token.json`
- No browser authentication needed
- If the token expires, it will refresh automatically

## Features

- Authenticates with Google Calendar API using OAuth 2.0
- Retrieves all events scheduled for today
- Displays events in a readable format with start times
- Handles both timed events and all-day events
- Stores authentication token for future use

## File Structure

- `google_calendar_client.py`: Main script file
- `credentials.json`: OAuth 2.0 client configuration (you need to download this)
- `token.json`: Generated after first authentication (do not share this file)

## Error Handling

The script includes error handling for common issues:
- Missing credentials file
- Authentication failures
- API errors

## Security Notes

- Keep your `credentials.json` and `token.json` files secure
- Never commit these files to version control
- Add them to your `.gitignore` file

## Customization

You can modify the timezone in the script by changing:
```python
local_tz = pytz.timezone('UTC')  # Change to your timezone, e.g., 'America/New_York'
``` 