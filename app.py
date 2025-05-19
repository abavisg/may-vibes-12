import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, jsonify, request, current_app
from flask_socketio import SocketIO, emit
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import pytz
from activity_tracker import ActivityTracker
from calendar_integration import CalendarService
from wellness_suggestions import WellnessSuggestions
from wellness_score import WellnessScore
from config import Config
import logging
import random
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in production
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*", logger=True, engineio_logger=True)

# Initialize scheduler with proper timezone
scheduler = BackgroundScheduler(timezone=Config.get_timezone())

# Set up mock time based on configuration
mock_mode_enabled = Config.MOCKING_ENABLED
if mock_mode_enabled:
    mock_time = Config.get_mock_time()
    logger.info(f"Mock mode enabled. Using mock time: {mock_time}")
else:
    mock_time = datetime.now(Config.get_timezone())
    logger.info("Mock mode disabled. Using real time.")

# Initialize services with mock time
activity_tracker = ActivityTracker(idle_threshold_seconds=300, mock_time=mock_time if mock_mode_enabled else None)
calendar_service = CalendarService(use_google_calendar=Config.USE_CALENDAR_INTEGRATION,
                                  mock_time=mock_time if mock_mode_enabled else None)
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
    """Periodically checks work patterns and triggers notifications if needed"""
    with app.app_context():
        global last_break_time, current_work_session_start, breaks_suggested
        
        current_time = calendar_service.get_current_time()
        active_duration = current_time - current_work_session_start
        
        # Only suggest breaks if the system is active
        if activity_tracker.is_active():
            if active_duration > work_session_threshold:
                # Check calendar for availability
                next_meeting = calendar_service.get_next_event()
                if not next_meeting or (next_meeting['start'] - current_time).total_seconds() > 900:
                    # Get enhanced activity stats with focus information
                    activity_stats = activity_tracker.get_activity_stats()
                    
                    # Get additional focus data from the agent
                    agent_state = activity_tracker.act("update")
                    
                    # Combine standard stats with focus information from the agent
                    enhanced_stats = {**activity_stats}
                    enhanced_stats['focus_level'] = agent_state.get('focus_level', 'unknown')
                    enhanced_stats['focus_mode'] = activity_tracker.get_focus_mode()
                    enhanced_stats['active_processes'] = activity_tracker.perceptions.get('active_apps', [])[:3]
                    
                    break_suggestion = wellness_suggestions.get_break_suggestion(enhanced_stats)
                    breaks_suggested += 1
                    
                    # Emit break suggestion via WebSocket
                    socketio.emit('break_suggestion', {
                        'type': 'break_suggestion',
                        'suggestion': break_suggestion
                    })
                    
                    return break_suggestion
        else:
            # If system is idle, consider it a break
            last_break_time = current_time
            current_work_session_start = current_time
        
        return None

def update_wellness_metrics():
    """Update wellness score and emit updates via WebSocket"""
    with app.app_context():
        current_time = calendar_service.get_current_time()
        activity_stats = activity_tracker.get_activity_stats()
        
        # Get enhanced focus data from the agent
        agent_state = activity_tracker.act("update")
        focus_level = agent_state.get('focus_level', 'unknown')
        focus_mode = activity_tracker.get_focus_mode()
        focus_history = activity_tracker.get_focus_history()
        
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
            'memory_percent': activity_stats['memory_percent'],
            'focus_level': focus_level,
            'focus_mode': focus_mode,
            'focus_history': {hour: patterns[-1] if patterns else 'unknown' 
                             for hour, patterns in focus_history.items()}
        }
        
        wellness_score.update_score(metrics)
        
        # Emit updates via WebSocket
        emit_dashboard_update()

def emit_dashboard_update():
    """Emit current dashboard data via Socket.IO"""
    dashboard_data = get_dashboard_data()
    socketio.emit('dashboard_update', {
        'type': 'dashboard_update',
        'data': dashboard_data
    })

def get_dashboard_data():
    """Get all data for the dashboard display"""
    current_time = calendar_service.get_current_time()
    
    # Get activity stats
    activity_stats = activity_tracker.get_activity_stats()
    
    # Get focus information
    agent_state = activity_tracker.act("update")
    focus_level = agent_state.get('focus_level', 'unknown')
    focus_mode = activity_tracker.get_focus_mode()
    
    # Calculate wellness metrics
    wellness_breakdown = wellness_score.get_score_breakdown()
    
    system_info = get_system_info()
    
    return {
        'system_info': system_info,
        'wellness_score': wellness_breakdown,
        'activity_stats': {
            'cpu_percent': activity_stats['cpu_percent'],
            'memory_percent': activity_stats['memory_percent'],
            'is_active': activity_stats['is_active'],
            'idle_duration': activity_stats['idle_duration'],
            'active_duration': (current_time - current_work_session_start).total_seconds(),
            'focus_level': focus_level,
            'focus_mode': focus_mode,
            'active_applications': activity_tracker.perceptions.get('active_apps', [])[:3]
        },
        'break_stats': {
            'taken': breaks_taken,
            'suggested': breaks_suggested,
            'last_break': last_break_time.isoformat(),
            'working_time': (current_time - current_work_session_start).total_seconds()
        },
        'calendar_events': calendar_service.get_upcoming_events(),
        'meeting_stats': {
            'attended': meetings_attended,
            'total': total_meetings
        }
    }

@app.route('/')
def index():
    """Render the main application interface"""
    current_time = calendar_service.get_current_time()
    formatted_date = current_time.strftime('%A, %B %d, %Y')
    formatted_time = current_time.strftime('%I:%M:%S %p')
    is_mock_mode = mock_mode_enabled
    
    return render_template(
        'index.html',
        formatted_date=formatted_date,
        formatted_time=formatted_time,
        is_mock_mode=is_mock_mode
    )

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    """Get all dashboard data"""
    try:
        return jsonify(get_dashboard_data())
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        return jsonify({"error": "Failed to fetch dashboard data"}), 500

@app.route('/api/breaks/respond', methods=['POST'])
def handle_break_response():
    """Handle user response to break suggestion"""
    global last_break_time, current_work_session_start, breaks_taken
    
    try:
        data = request.get_json()
        accepted = data.get('accepted', False)
        
        if accepted:
            # Record successful break
            last_break_time = calendar_service.get_current_time()
            current_work_session_start = last_break_time
            breaks_taken += 1
            
            wellness_suggestions.record_break_feedback(
                break_type='user_initiated',
                accepted=True,
                completed=True
            )
            
            message = "Break recorded successfully!"
        else:
            # Record skipped break
            wellness_suggestions.record_break_feedback(
                break_type='user_initiated',
                accepted=False,
                completed=False
            )
            
            message = "Break postponed."
        
        # Update metrics and emit updates
        update_wellness_metrics()
        
        return jsonify({
            "status": "success",
            "message": message
        })
        
    except Exception as e:
        logger.error(f"Error handling break response: {e}")
        return jsonify({
            "status": "error",
            "message": "Failed to process break response"
        }), 500

@socketio.on('connect')
def handle_connect(auth=None):
    """Handle Socket.IO connection"""
    logger.info("Client connected")
    emit_dashboard_update()

@socketio.on('disconnect')
def handle_disconnect():
    """Handle Socket.IO disconnection"""
    logger.info("Client disconnected")

def start_monitoring():
    """Initialize and start the monitoring systems"""
    activity_tracker.start()
    
    # Add jobs with proper error handling
    def add_job_safely(func, trigger, **trigger_args):
        try:
            scheduler.add_job(func, trigger, **trigger_args)
        except Exception as e:
            logger.error(f"Failed to add job {func.__name__}: {e}")
    
    add_job_safely(check_work_patterns, 'interval', minutes=5)
    add_job_safely(update_wellness_metrics, 'interval', minutes=15)
    
    try:
        scheduler.start()
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")

def get_system_info():
    """Get system information for the dashboard"""
    current_time = datetime.now()
    if mock_mode_enabled:
        current_time = mock_time
        
    # Now using the properly implemented get_status() method
    calendar_status = calendar_service.get_status()
    
    try:
        llm_status = wellness_suggestions.check_llm_status()
    except Exception as e:
        logger.error(f"Error checking LLM status: {e}")
        llm_status = {
            'is_available': False,
            'model': 'Unknown',
            'error': str(e)
        }
    
    # Get activity stats for display
    activity_stats = activity_tracker.get_activity_stats()
    
    # Get enhanced focus information for break recommendations
    agent_state = activity_tracker.act("update")
    focus_level = agent_state.get('focus_level', 'unknown')
    focus_mode = activity_tracker.get_focus_mode()
    
    # Enhance activity stats with focus data
    enhanced_stats = {**activity_stats}
    enhanced_stats['focus_level'] = focus_level
    enhanced_stats['focus_mode'] = focus_mode
    enhanced_stats['active_processes'] = activity_tracker.perceptions.get('active_apps', [])[:3]
    
    # Convert idle_duration from seconds to minutes for the wellness engine
    active_duration_minutes = (current_time - current_work_session_start).total_seconds() / 60
    idle_duration_minutes = activity_stats.get('idle_duration', 0) / 60
    
    # Get break recommendations with enhanced activity data
    break_rec = wellness_suggestions.check_work_patterns(
        active_duration_minutes,
        idle_duration_minutes,
        enhanced_stats
    )
    should_break, suggestion, reason = break_rec
    
    # If a break is suggested, send it to the client
    if should_break and suggestion:
        socketio.emit('break_suggestion', suggestion)
    
    # Get enhanced focus information from the agent
    focus_mode = activity_tracker.get_focus_mode()
    
    # Get agent state through perception-reasoning cycle
    agent_perception = activity_tracker.perceive()
    agent_reasoning = activity_tracker.reason()
    focus_history = activity_tracker.get_focus_history()
    
    system_info = {
        'time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
        'uptime': activity_tracker.get_uptime_seconds(),
        'focus_mode': focus_mode,
        'focus_level': agent_reasoning.get('focus_level', 'unknown'),
        'active_processes': activity_tracker.perceptions.get('active_apps', [])[:3],
        'activity_level': activity_stats.get('activity_level', 0),
        'active_duration': activity_stats.get('active_duration', 0),
        'idle_duration': activity_stats.get('idle_duration', 0),
        'calendar_status': calendar_status,
        'mock_mode': mock_mode_enabled,
        'llm_status': llm_status,
        'break_check': {
            'should_break': should_break,
            'reason': reason,
            'last_check': wellness_suggestions.last_check_time
        },
        'current_time': current_time.isoformat(),
        'is_active': activity_stats['is_active'],
        'formatted_date': current_time.strftime('%A, %B %d, %Y'),
        'formatted_time': current_time.strftime('%I:%M:%S %p')
    }
    
    return system_info

if __name__ == '__main__':
    try:
        start_monitoring()
        # Use eventlet's WSGI server
        eventlet_socket = eventlet.listen(('0.0.0.0', 5002))
        eventlet.wsgi.server(eventlet_socket, app, log_output=True)
    except KeyboardInterrupt:
        scheduler.shutdown()
        activity_tracker.stop()
    except Exception as e:
        logger.error(f"Application error: {e}")
        scheduler.shutdown()
        activity_tracker.stop() 