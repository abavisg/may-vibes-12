import psutil
import time
from datetime import datetime, timedelta
import logging
import pytz
from config import Config

logger = logging.getLogger(__name__)

class ActivityTracker:
    def __init__(self, idle_threshold_seconds: int = 300, mock_time: datetime = None):
        """
        Initialize the activity tracker.
        Args:
            idle_threshold_seconds: Number of seconds of inactivity before considered idle
            mock_time: Optional mock current time for testing
        """
        self.idle_threshold = idle_threshold_seconds
        self.last_activity = 0
        self.running = False
        self.mock_time = mock_time
        self.timezone = Config.get_timezone()
    
    def get_current_time(self) -> datetime:
        """Get the current time, using mock time if set."""
        if self.mock_time:
            return self.mock_time
        return datetime.now(self.timezone)
    
    def start(self):
        """Start monitoring system activity."""
        self.running = True
        self.last_activity = time.time()
        logger.info("Activity tracking started")
    
    def stop(self):
        """Stop monitoring system activity."""
        self.running = False
        logger.info("Activity tracking stopped")
    
    def update_activity(self):
        """Update the last activity timestamp."""
        self.last_activity = time.time()
    
    def get_activity_stats(self) -> dict:
        """Get current activity statistics."""
        if not self.running:
            return {
                "is_active": False,
                "idle_duration": 0,
                "cpu_percent": 0,
                "memory_percent": 0
            }
        
        current_time = time.time()
        idle_duration = current_time - self.last_activity
        
        return {
            "is_active": idle_duration < self.idle_threshold,
            "idle_duration": int(idle_duration),
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent
        }
    
    def is_active(self) -> bool:
        """Check if the system is currently active."""
        return self.get_activity_stats()["is_active"] 