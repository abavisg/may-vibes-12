# Work/Life Balance Coach

A smart application that helps you maintain a healthy work-life balance by tracking your work patterns, suggesting breaks, and providing personalized wellness advice.

## Features

- Real-time activity tracking (CPU, memory, idle time)
- AI-powered break suggestions using Ollama
- Calendar integration with timezone support
- Wellness score tracking with personalized advice
- Modern web interface with real-time updates

## Requirements

- Python 3.8+
- Ollama (for AI-powered suggestions)
- Modern web browser
- Google Calendar API credentials (optional)

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install and start Ollama:
   ```bash
   # Follow instructions at https://ollama.ai to install Ollama
   ollama pull tinyllama:latest  # Pull the TinyLlama model (faster for prototyping)
   ollama serve         # Start the Ollama server
   ```

## Configuration

1. Copy `credentials.json.example` to `credentials.json` and add your Google Calendar API credentials (optional)
2. Adjust settings in `config.py` as needed
3. The application uses port 5002 by default

## Usage

1. Start the application:
   ```bash
   python app.py
   ```
2. Open your browser and navigate to `http://localhost:5002`
3. Allow notifications when prompted for break reminders

## Features in Detail

### Activity Tracking
- Monitors system resource usage
- Tracks idle time and work patterns
- Provides real-time activity statistics

### AI-Powered Break Management
- Intelligent break suggestions using Ollama's TinyLlama model
- Fast response times for quick prototyping
- Context-aware recommendations based on:
  - Time of day
  - Work duration
  - Activity levels
  - System usage
  - Calendar events
- Break types include:
  - Eye breaks
  - Stretch breaks
  - Walk breaks
  - Hydration breaks
- Fallback suggestions when AI is unavailable
- Break effectiveness tracking

### Wellness Score
- Overall wellness score calculation
- Component-based scoring:
  - Break compliance
  - Work duration
  - Activity balance
  - Schedule adherence
  - System usage
- AI-generated improvement suggestions

### Calendar Integration
- Local or Google Calendar support
- Timezone-aware scheduling
- Meeting status tracking
- Break scheduling around meetings

## Project Structure

```
.
├── app.py                  # Main Flask application
├── calendar_integration.py # Calendar service integration
├── config.py              # Configuration management
├── wellness_suggestions.py # Break suggestion engine
├── ollama_client.py       # AI integration with Ollama
├── user_preferences.py    # User preference learning
├── activity_tracker.py    # System activity monitoring
├── wellness_score.py      # Wellness metrics calculation
├── requirements.txt       # Python dependencies
├── static/               # Static web assets
│   ├── css/
│   │   └── style.css    # Modern, responsive styling
│   ├── js/
│   │   └── app.js       # Frontend functionality
│   └── img/
├── templates/            # HTML templates
│   └── index.html       # Main application interface
├── mock-data/           # Mock data for development
└── secrets/             # Secure credentials storage
```

## Development

The application is built with modularity in mind:

- `app.py` - Main Flask application and route handlers
- `calendar_integration.py` - Handles calendar operations (Google/Local)
- `config.py` - Centralizes configuration management
- `wellness_suggestions.py` - Break suggestion engine
- `ollama_client.py` - AI integration for personalized suggestions
- `user_preferences.py` - User preference management and learning
- `activity_tracker.py` - System activity monitoring
- `wellness_score.py` - Wellness metrics calculation
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

## Calendar Integration

The application supports both local and Google Calendar integration:
- Google Calendar integration requires OAuth2 credentials
- Local calendar support for offline usage
- All calendar operations are timezone-aware
- Events are used to optimize break scheduling

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

