from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import pytz
from activity_tracker import ActivityTracker
from calendar_integration import CalendarService
from config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
scheduler = BackgroundScheduler()
activity_tracker = ActivityTracker(idle_threshold_seconds=300)  # 5 minutes threshold
calendar_service = CalendarService()

# Global variables for tracking state
last_break_time = datetime.now()
current_work_session_start = datetime.now()
break_duration = timedelta(minutes=5)
work_session_threshold = timedelta(minutes=45)

def check_work_patterns():
    """
    Periodically checks work patterns and triggers notifications if needed
    """
    global last_break_time, current_work_session_start
    
    current_time = datetime.now()
    active_duration = current_time - current_work_session_start
    
    # Only suggest breaks if the system is active
    if activity_tracker.is_active():
        if active_duration > work_session_threshold:
            # Check calendar for availability
            next_meeting = calendar_service.get_next_event()
            if not next_meeting or (next_meeting['start'] - current_time).total_seconds() > 900:  # 15 minutes buffer
                return {
                    "type": "break_needed",
                    "message": "Time for a short break! You've been working for a while.",
                    "duration": break_duration.total_seconds()
                }
    else:
        # If system is idle, consider it a break
        last_break_time = current_time
        current_work_session_start = current_time
    
    return None

@app.route('/')
def index():
    """Render the main application interface"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get current work/break status and statistics"""
    current_time = datetime.now()
    active_duration = current_time - current_work_session_start
    
    # Get detailed activity stats
    activity_stats = activity_tracker.get_activity_stats()
    
    return jsonify({
        "active_duration": active_duration.total_seconds(),
        "last_break": last_break_time.isoformat(),
        "is_active": activity_stats['is_active'],
        "idle_duration": activity_stats['idle_duration'],
        "system_stats": {
            "cpu_percent": activity_stats['cpu_percent'],
            "memory_percent": activity_stats['memory_percent']
        }
    })

@app.route('/api/calendar')
def get_calendar():
    """Get upcoming calendar events"""
    try:
        events = calendar_service.get_upcoming_events()
        return jsonify({"events": events})
    except Exception as e:
        logger.error(f"Error fetching calendar events: {e}")
        return jsonify({"error": "Failed to fetch calendar events"}), 500

@app.route('/api/take-break', methods=['POST'])
def take_break():
    """Record when user takes a break"""
    global last_break_time, current_work_session_start
    
    last_break_time = datetime.now()
    current_work_session_start = last_break_time + break_duration
    
    return jsonify({"status": "success"})

def start_monitoring():
    """Initialize and start the monitoring systems"""
    activity_tracker.start()
    scheduler.add_job(check_work_patterns, 'interval', minutes=5)
    scheduler.start()

if __name__ == '__main__':
    try:
        start_monitoring()
        app.run(debug=True, use_reloader=False)  # use_reloader=False to prevent duplicate schedulers
    except KeyboardInterrupt:
        scheduler.shutdown()
        activity_tracker.stop() 