# Work/Life Balance Coach

A smart application that helps you maintain a healthy work-life balance by tracking your work patterns, suggesting breaks, and providing personalized wellness advice using an agent-based architecture to monitor and understand your focus patterns.

## Features

- Agent-based focus monitoring with perception-reasoning-action cycle
- Focus level classification (deep-focus, focused, active, light, minimal)
- Focus mode detection (intense, focused, casual, browsing, etc.)
- Real-time activity tracking (CPU, memory, idle time, active applications)
- AI-powered break suggestions using Ollama with focus awareness
- Calendar integration with timezone support
- Wellness score tracking with personalized advice
- Modern web interface with real-time updates
- Shared context management system for agent communication

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
4. Environment variables can be set in a `.env` file:
   - `MOCKING_ENABLED`: Set to "true" to enable mock mode (default: "true")
   - `MOCKED_DATE`: Custom date for mock mode (format: YYYY-MM-DD)
   - `MOCKED_TIME`: Custom time for mock mode (format: HH:MM:SS)
   - `USE_CALENDAR_INTEGRATION`: Set to "true" to use Google Calendar (automatically set to "false" when MOCKING_ENABLED is "true")
   - `TIMEZONE`: Your local timezone (default: "Europe/London")
   - `SCHEDULER_FREQUENCY`: Agent cycle frequency in seconds (default: 300 - 5 minutes)

## Usage

1. Start the application:
   ```bash
   python app.py
   ```
2. Open your browser and navigate to `http://localhost:5002`
3. Allow notifications when prompted for break reminders

### Using the Scheduler Agent

You can run the agent system directly with the scheduler:

```bash
# Run for 1 hour with default 5-minute intervals
python run_scheduler.py --duration 3600

# Run with 1-minute intervals for testing
python run_scheduler.py --interval 1 --duration 60

# Run without the visual countdown display
python run_scheduler.py --no-countdown
```

The scheduler provides:
- Real-time countdown to the next agent cycle
- Visual status display of current focus and suggestions
- Automatic context persistence to JSON files
- Configurable intervals and run durations

## Features in Detail

### Activity Tracking
- Monitors system resource usage
- Tracks idle time and work patterns
- Provides real-time activity statistics

### AI-Powered Break Management
- Intelligent break suggestions using Ollama's TinyLlama model
- Support for Model Context Protocol (MCP)-style messaging format
- Conversational context for more natural and coherent suggestions
- Fast response times for quick prototyping
- Context-aware recommendations based on:
  - Time of day
  - Work duration
  - Activity levels
  - System usage
  - Calendar events
  - Focus state and cognitive load
- Break types include:
  - Eye breaks
  - Stretch breaks
  - Walk breaks
  - Hydration breaks
  - Posture breaks
  - Breathing exercises
  - Mindfulness moments
  - Nature connections
  - Creative pauses
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

### Context Management System
- Centralized shared context for all agents
- Thread-safe access to shared state
- Hierarchical data storage with dot-notation paths
- Subscription system for context changes
- Automatic context persistence and backup
- Support for multiple agents working collaboratively

## Project Structure

```
.
├── app.py                  # Main Flask application
├── calendar_integration.py # Calendar service integration
├── config.py              # Configuration management
├── wellness_suggestions.py # Break suggestion engine
├── ollama_client.py       # AI integration with Ollama
├── user_preferences.py    # User preference learning
├── activity_tracker.py    # Focus monitoring agent
├── wellness_score.py      # Wellness metrics calculation
├── context_manager.py     # Shared context management
├── agent_example.py       # Example of agent interaction
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
- `activity_tracker.py` - Agent-based focus monitoring (perception, reasoning, action)
- `wellness_score.py` - Wellness metrics calculation
- `context_manager.py` - Shared context management for agent communication
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
   - Context data persisted with automatic backups

## Agent-Based Architecture

The application leverages an agent-oriented architecture for its core monitoring capabilities:

- **SchedulerAgent**: Orchestrates the execution of agent pipeline
  - Runs at a configurable interval (default: 5 minutes, configurable via SCHEDULER_FREQUENCY)
  - Ensures proper sequencing of perception, reasoning, and action
  - Manages shared context passing between specialized agents
  - Logs comprehensive context data for debugging and analysis
  - Provides fault tolerance and error recovery

- **FocusMonitorAgent**: Implements perception-reasoning-action cycle
  - *Perception*: Monitors system metrics and user activity
  - *Reasoning*: Analyzes patterns and determines focus states
  - *Action*: Provides adaptable responses to changing conditions
  - Maintains internal knowledge base of activity patterns by time of day
  - Offers rich classification of focus modes based on activity patterns

- **ContextAgent**: Provides environmental awareness
  - Tracks time-based information (hour, day of week, etc.)
  - Manages calendar integration and meeting awareness
  - Detects environmental factors affecting focus

- **NudgeAgent**: Generates intelligent break suggestions
  - Analyzes current context to determine optimal breaks
  - Customizes break types based on user state and needs
  - Maintains suggestion history for improved recommendations

- **DeliveryAgent**: Handles notification delivery
  - Manages notification settings and delivery preferences
  - Formats suggestions into actionable notifications
  - Tracks user engagement with notifications

- **Context Management**:
  - Enables seamless communication between agents
  - Maintains a shared state accessible to all components
  - Provides hierarchical data structure with path-based access
  - Notifies agents of relevant changes through subscription system
  - Persists the context state for continuity between sessions

This approach enables more sophisticated pattern recognition, reasoning about user behavior, and proactive interventions through coordinated agent activities.

## Calendar Integration

The application supports both local and Google Calendar integration:
- Google Calendar integration requires OAuth2 credentials
- Local calendar support for offline usage
- All calendar operations are timezone-aware
- Events are used to optimize break scheduling
- Set `USE_CALENDAR_INTEGRATION=true` in `.env` to use Google Calendar
- When `MOCKING_ENABLED=true`, mock calendar data is used automatically

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Enhanced AI Integration

The application features improved integration with Ollama's language models:

- **MCP-Style Messaging**: Uses Ollama's chat completion API with contextual message formatting
- **Enhanced Context Passing**: Provides rich context including focus levels, active applications, and upcoming meetings
- **User Feedback Loop**: Incorporates feedback about previously suggested breaks to improve future suggestions
  - Tracks whether breaks were accepted or ignored by the user
  - Adjusts suggestion patterns based on user preferences and past responses
  - Provides personalized suggestions that adapt to user behavior over time
- **Fallback Mechanisms**: Gracefully degrades to rule-based suggestions when Ollama is unavailable
- **Adaptive Timings**: Adjusts notification timing based on cognitive load and focus state
- **Flexible LLM Selection**: Works with various Ollama models (default: tinyllama:latest)

The messaging format used with Ollama follows this pattern:

```python
messages = [
  {"role": "system", "content": "You are a kind wellness coach who gives personalised break suggestions..."},
  {"role": "user", "content": "The user has been working for X minutes during the afternoon..."},
  {"role": "assistant", "content": "The last suggestion was: {...} and the user accepted/ignored it."}
]
```

This structured approach allows the model to build on previous interactions and deliver increasingly relevant suggestions.

