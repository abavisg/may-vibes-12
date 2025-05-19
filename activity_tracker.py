import psutil
import time
from datetime import datetime, timedelta
import logging
from threading import Thread, Event

logger = logging.getLogger(__name__)

class ActivityTracker:
    def __init__(self, idle_threshold_seconds=300):  # 5 minutes default
        self.idle_threshold = idle_threshold_seconds
        self.last_activity = datetime.now()
        self.is_running = False
        self.stop_event = Event()
        self.tracking_thread = None
        
    def start(self):
        """Start the activity tracking."""
        if self.is_running:
            return
            
        self.is_running = True
        self.stop_event.clear()
        self.tracking_thread = Thread(target=self._track_activity, daemon=True)
        self.tracking_thread.start()
        logger.info("Activity tracking started")
    
    def stop(self):
        """Stop the activity tracking."""
        self.is_running = False
        self.stop_event.set()
        if self.tracking_thread:
            self.tracking_thread.join()
        logger.info("Activity tracking stopped")
    
    def _track_activity(self):
        """Background thread to track system activity."""
        while not self.stop_event.is_set():
            try:
                # Get CPU usage as a percentage
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # Get memory usage
                memory = psutil.virtual_memory()
                
                # Get disk IO counters
                disk_io = psutil.disk_io_counters()
                
                # If there's significant activity, update the last activity time
                if (cpu_percent > 10 or  # CPU activity above 10%
                    memory.percent > 75 or  # High memory usage
                    disk_io.read_bytes + disk_io.write_bytes > 1024 * 1024):  # At least 1MB IO
                    self.last_activity = datetime.now()
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error tracking activity: {e}")
                time.sleep(5)  # Wait a bit longer if there's an error
    
    def is_active(self) -> bool:
        """Check if the system is currently active."""
        time_since_activity = datetime.now() - self.last_activity
        return time_since_activity.total_seconds() < self.idle_threshold
    
    def get_idle_duration(self) -> timedelta:
        """Get how long the system has been idle."""
        return datetime.now() - self.last_activity
    
    def get_activity_stats(self) -> dict:
        """Get current activity statistics."""
        return {
            'is_active': self.is_active(),
            'idle_duration': self.get_idle_duration().total_seconds(),
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'last_activity': self.last_activity.isoformat()
        } 