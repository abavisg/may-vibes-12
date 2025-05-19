from pynput import mouse, keyboard
from datetime import datetime
import threading
import time

class ActivityTracker:
    def __init__(self):
        self.last_activity = datetime.now()
        self._lock = threading.Lock()
        
        # Start listeners
        self.mouse_listener = mouse.Listener(
            on_move=self._on_activity,
            on_click=self._on_activity,
            on_scroll=self._on_activity
        )
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_activity,
            on_release=self._on_activity
        )
        
        # Start monitoring
        self.start()
    
    def _on_activity(self, *args):
        """Update the last activity timestamp when any input is detected."""
        with self._lock:
            self.last_activity = datetime.now()
    
    def get_idle_minutes(self):
        """Return the number of minutes since last activity."""
        with self._lock:
            delta = datetime.now() - self.last_activity
            return delta.total_seconds() / 60
    
    def start(self):
        """Start monitoring user activity."""
        if not self.mouse_listener.is_alive():
            self.mouse_listener.start()
        if not self.keyboard_listener.is_alive():
            self.keyboard_listener.start()
    
    def stop(self):
        """Stop monitoring user activity."""
        self.mouse_listener.stop()
        self.keyboard_listener.stop()
        
    def is_active(self, idle_threshold_minutes=5):
        """Check if the user is currently active based on the idle threshold."""
        return self.get_idle_minutes() < idle_threshold_minutes 