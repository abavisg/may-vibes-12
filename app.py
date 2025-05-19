from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import pytz
from activity_tracker import ActivityTracker
from calendar_integration import CalendarService
from wellness_suggestions import WellnessSuggestions
from wellness_score import WellnessScore
from config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
scheduler = BackgroundScheduler()

# Set up mock time for testing (9 AM)
mock_time = datetime.now(Config.get_timezone()).replace(
    hour=9, minute=0, second=0, microsecond=0
)

# Initialize services with mock time
activity_tracker = ActivityTracker(idle_threshold_seconds=300, mock_time=mock_time)  # 5 minutes threshold
calendar_service = CalendarService(use_google_calendar=False)  # Explicitly use local calendar
wellness_suggestions = WellnessSuggestions()
wellness_score = WellnessScore()

# Global variables for tracking state
last_break_time = mock_time
current_work_session_start = mock_time
work_session_threshold = timedelta(minutes=45)
breaks_taken = 0
breaks_suggested = 0
meetings_attended = 0
total_meetings = 0

def check_work_patterns():
    """
    Periodically checks work patterns and triggers notifications if needed
    """
    global last_break_time, current_work_session_start, breaks_suggested
    
    current_time = calendar_service.get_current_time()
    active_duration = current_time - current_work_session_start
    
    # Only suggest breaks if the system is active
    if activity_tracker.is_active():
        if active_duration > work_session_threshold:
            # Check calendar for availability
            next_meeting = calendar_service.get_next_event()
            if not next_meeting or (next_meeting['start'] - current_time).total_seconds() > 900:  # 15 minutes buffer
                activity_stats = activity_tracker.get_activity_stats()
                break_suggestion = wellness_suggestions.get_break_suggestion(activity_stats)
                breaks_suggested += 1
                return {
                    "type": "break_needed",
                    "message": f"Time for a {break_suggestion['title']}! {break_suggestion['suggestion']}",
                    "duration": break_suggestion['duration'] * 60,  # Convert to seconds
                    "break_type": break_suggestion['type']
                }
    else:
        # If system is idle, consider it a break
        last_break_time = current_time
        current_work_session_start = current_time
    
    return None

def update_wellness_metrics():
    """Update wellness score based on current metrics"""
    current_time = calendar_service.get_current_time()
    activity_stats = activity_tracker.get_activity_stats()
    
    # Calculate active duration from idle duration
    active_minutes = max(0, (current_time - current_work_session_start).total_seconds() - activity_stats['idle_duration']) / 60
    rest_minutes = activity_stats['idle_duration'] / 60
    
    metrics = {
        'breaks_taken': breaks_taken,
        'breaks_suggested': breaks_suggested,
        'active_duration': current_time - current_work_session_start,
        'active_minutes': active_minutes,
        'rest_minutes': rest_minutes,
        'meetings_attended': meetings_attended,
        'total_meetings': total_meetings,
        'cpu_percent': activity_stats['cpu_percent'],
        'memory_percent': activity_stats['memory_percent']
    }
    
    wellness_score.update_score(metrics)

@app.route('/')
def index():
    """Render the main application interface"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get current work/break status and statistics"""
    current_time = calendar_service.get_current_time()
    active_duration = current_time - current_work_session_start
    
    # Get detailed activity stats
    activity_stats = activity_tracker.get_activity_stats()
    
    # Calculate active and idle durations
    total_session_seconds = active_duration.total_seconds()
    idle_duration = activity_stats['idle_duration']
    active_duration_seconds = max(0, total_session_seconds - idle_duration)
    
    # Get break suggestion if needed
    break_suggestion = None
    if active_duration > work_session_threshold:
        break_suggestion = wellness_suggestions.get_break_suggestion(activity_stats)
    
    # Update wellness metrics
    update_wellness_metrics()
    wellness_breakdown = wellness_score.get_score_breakdown()
    
    return jsonify({
        "active_duration": active_duration_seconds,
        "last_break": last_break_time.isoformat(),
        "is_active": activity_stats['is_active'],
        "idle_duration": idle_duration,
        "system_stats": {
            "cpu_percent": activity_stats['cpu_percent'],
            "memory_percent": activity_stats['memory_percent']
        },
        "break_suggestion": break_suggestion,
        "wellness_score": wellness_breakdown,
        "break_stats": {
            "taken": breaks_taken,
            "suggested": breaks_suggested
        },
        "meeting_stats": {
            "attended": meetings_attended,
            "total": total_meetings
        }
    })

@app.route('/api/calendar')
def get_calendar():
    """Get upcoming calendar events"""
    try:
        logger.info("Fetching calendar events...")
        events = calendar_service.get_upcoming_events()
        logger.info(f"Found {len(events)} upcoming events")
        logger.debug(f"Events: {events}")
        return jsonify({"events": events})
    except Exception as e:
        logger.error(f"Error fetching calendar events: {e}")
        return jsonify({"error": "Failed to fetch calendar events"}), 500

@app.route('/api/take-break', methods=['POST'])
def take_break():
    """Record when user takes a break and collect feedback"""
    global last_break_time, current_work_session_start, breaks_taken
    
    data = request.get_json()
    break_type = data.get('break_type', 'stretch_break')  # Default to stretch break if not specified
    accepted = data.get('accepted', True)
    completed = data.get('completed', True)
    effectiveness_rating = data.get('effectiveness_rating')
    energy_level_after = data.get('energy_level_after')
    
    # Record break feedback
    wellness_suggestions.record_break_feedback(
        break_type=break_type,
        accepted=accepted,
        completed=completed,
        effectiveness_rating=effectiveness_rating,
        energy_level_after=energy_level_after
    )
    
    # Update timing and counters
    last_break_time = calendar_service.get_current_time()
    current_work_session_start = last_break_time + timedelta(
        minutes=wellness_suggestions.user_prefs.get_optimal_break_duration(break_type)
    )
    breaks_taken += 1
    
    # Update wellness metrics
    update_wellness_metrics()
    
    return jsonify({"status": "success"})

@app.route('/api/skip-break', methods=['POST'])
def skip_break():
    """Record when user skips a break"""
    data = request.get_json()
    break_type = data.get('break_type', 'stretch_break')  # Default to stretch break if not specified
    
    # Record skipped break
    wellness_suggestions.record_break_feedback(
        break_type=break_type,
        accepted=False,
        completed=False
    )
    
    # Update wellness metrics
    update_wellness_metrics()
    
    return jsonify({"status": "success"})

@app.route('/api/meeting-status', methods=['POST'])
def update_meeting_status():
    """Update meeting attendance status"""
    global meetings_attended, total_meetings
    
    data = request.get_json()
    attended = data.get('attended', True)
    
    total_meetings += 1
    if attended:
        meetings_attended += 1
    
    # Update wellness metrics
    update_wellness_metrics()
    
    return jsonify({"status": "success"})

def start_monitoring():
    """Initialize and start the monitoring systems"""
    activity_tracker.start()
    scheduler.add_job(check_work_patterns, 'interval', minutes=5)
    scheduler.add_job(update_wellness_metrics, 'interval', minutes=15)
    scheduler.start()

if __name__ == '__main__':
    try:
        start_monitoring()
        app.run(debug=True, use_reloader=False, port=5002)  # Changed port to 5002
    except KeyboardInterrupt:
        scheduler.shutdown()
        activity_tracker.stop() 