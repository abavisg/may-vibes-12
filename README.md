# May AI Vibes – Work/Life Balance Coach
A context-aware wellness companion that helps maintain a healthy work/life balance by monitoring your working activity and providing timely micro-interventions.

## Features

- **Activity Monitoring** – Tracks computer usage patterns and idle time
- **Smart Notifications** – Provides contextual wellness nudges based on work patterns
- **Calendar Integration** – Considers your schedule when suggesting breaks
- **Local Privacy** – Runs completely locally with no data transmission
- **Customizable Routines** – Adapts to your preferred work hours and break patterns

## Tech Stack

- Python 3.9+
- Flask (Web Server)
- APScheduler (Task Scheduling)
- pynput (Activity Tracking)
- Local LLM (Qwen2.5/Phi3) for context-aware suggestions
- Google Calendar API (Optional)
- Browser notifications for alerts

## Architecture

The application consists of several key components:
- Background service for activity monitoring
- Scheduler for periodic checks
- Local LLM integration for personalized nudges
- Web interface for notifications
- Activity tracking system
- Calendar integration module

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

3. Configure the application:
- Copy `.env.example` to `.env`
- Update settings in `.env` if needed
- Set up Google Calendar credentials (optional)

4. Set up Local LLM:
- Install LM Studio or Ollama
- Start the local LLM server

## Running the Application

1. Start the main service:
```bash
python app.py
```

2. Access the web interface:
- Open `http://localhost:5000` in your browser
- Allow notifications when prompted

## Development

- Main application code is in `app.py`
- Activity tracking logic in `activity_tracker.py`
- Calendar integration in `calendar_integration.py`
- LLM integration in `llm_service.py`
- Web interface in `templates/` and `static/`

## License
MIT

