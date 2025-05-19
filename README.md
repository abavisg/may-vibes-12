# May AI Vibes – Work/Life Balance Coach

A context-aware wellness companion that helps maintain a healthy work/life balance by monitoring your working activity and providing timely micro-interventions.

## Features

- **Smart Notifications** – Provides contextual wellness nudges based on work patterns
- **Calendar Integration** – Considers your schedule when suggesting breaks
- **Local Privacy** – Runs completely locally with no data transmission
- **Adaptive Learning** – Learns from your break preferences and effectiveness ratings
- **Activity-Aware** – Suggests breaks based on system usage patterns and work intensity
- **Personalized Duration** – Adjusts break durations based on your feedback
- **Modern Web Interface** – Clean, responsive design for easy interaction

## Tech Stack

- Python 3.9+
- Flask (Web Server)
- APScheduler (Task Scheduling)
- Google Calendar API (Optional)
- NumPy (Statistical Analysis)
- Modern Web Frontend (HTML5, CSS3, JavaScript)

## Setup

1. Create a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Unix/macOS
# or
.\venv\Scripts\activate  # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure Google Calendar (Optional):
   - Go to Google Cloud Console and create a project
   - Enable the Google Calendar API
   - Create OAuth 2.0 credentials
   - Download the credentials and save as `secrets/credentials.json`
   - Set up your OAuth consent screen

4. Configure the application:
   - Copy `.env.example` to `.env`
   - Update settings in `.env` with your preferences:
     ```
     # Application Settings
     TIMEZONE=Europe/London
     WORK_SESSION_THRESHOLD=45  # minutes
     NOTIFICATION_INTERVAL=30  # seconds

     # Google Calendar Settings
     GOOGLE_CALENDAR_ENABLED=true
     GOOGLE_CALENDAR_CREDENTIALS_PATH=secrets/credentials.json
     GOOGLE_CALENDAR_TOKEN_PATH=secrets/token.json

     # Development Settings
     FLASK_ENV=development
     FLASK_DEBUG=1
     SECRET_KEY=your-secret-key-here  # Change this in production!
     ```

## User Preferences & Learning

The application includes an adaptive learning system that:

1. **Break Type Selection**
   - Learns which break types are most effective for you
   - Adjusts suggestions based on time of day
   - Considers your activity level and work patterns

2. **Duration Optimization**
   - Personalizes break durations based on your feedback
   - Adapts to your schedule and work intensity
   - Maintains optimal work/break balance

3. **Effectiveness Tracking**
   - Collects feedback on break effectiveness
   - Monitors energy levels after breaks
   - Uses data to improve future suggestions

4. **Activity Context**
   - Monitors system usage patterns
   - Suggests appropriate breaks based on:
     - CPU usage
     - Memory utilization
     - Idle time
     - Work intensity

## Project Structure

```
.
├── app.py                  # Main Flask application
├── calendar_integration.py # Calendar service integration
├── config.py              # Configuration management
├── wellness_suggestions.py # Break suggestion engine
├── user_preferences.py    # User preference learning
├── activity_tracker.py    # System activity monitoring
├── requirements.txt       # Python dependencies
├── static/               # Static web assets
│   ├── css/
│   │   └── style.css    # Modern, responsive styling
│   ├── js/
│   │   └── app.js       # Frontend functionality
│   └── img/
│       ├── icon.svg     # Vector application icon
│       └── icon.png     # Raster application icon
├── templates/            # HTML templates
│   └── index.html       # Main application interface
├── data/                # User data storage
│   ├── preferences.json # User preferences
│   └── break_history.json # Break history and feedback
└── secrets/             # Secure credentials storage
    ├── credentials.json # Google OAuth credentials
    └── token.json      # OAuth refresh token
```

## Running the Application

1. Start the main service:
```bash
python app.py
```

2. Access the web interface:
   - Open `http://localhost:5000` in your browser
   - Allow notifications when prompted
   - The interface will show:
     - Current work session duration
     - Time since last break
     - Upcoming calendar events
     - Break suggestions and controls
     - Activity level indicators

## Development

The application is built with modularity in mind:

- `app.py` - Main Flask application and route handlers
- `calendar_integration.py` - Handles calendar operations (Google/Local)
- `config.py` - Centralizes configuration management
- `wellness_suggestions.py` - Break suggestion engine with machine learning
- `user_preferences.py` - User preference management and learning
- `activity_tracker.py` - System activity monitoring
- Web interface in `templates/` and `static/`

## Security Considerations

1. OAuth2 Authentication
   - Secure token storage in `secrets/` directory
   - Automatic token refresh handling
   - Proper scope management

2. Local Data
   - All data stored locally
   - No external data transmission
   - User preferences stored securely
   - Break history anonymized

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT

