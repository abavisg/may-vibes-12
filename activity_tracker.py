import psutil
import time
from datetime import datetime, timedelta
import logging
import pytz
from config import Config

logger = logging.getLogger(__name__)

class FocusMonitorAgent:
    """
    An agent responsible for monitoring user focus, activity levels, and system resource usage.
    Follows an agent-oriented design pattern with perception, reasoning, and action components.
    """
    
    def __init__(self, idle_threshold_seconds: int = 300, mock_time: datetime = None):
        """
        Initialize the focus monitoring agent.
        
        Args:
            idle_threshold_seconds: Number of seconds of inactivity before considered idle
            mock_time: Optional mock current time for testing
        """
        # Perception state
        self.perceptions = {
            "last_activity_time": time.time(),
            "cpu_usage_history": [],
            "memory_usage_history": [],
            "active_apps": [],
            "system_events": []
        }
        
        # Knowledge state
        self.knowledge = {
            "idle_threshold": idle_threshold_seconds,
            "focus_patterns": {},
            "activity_baseline": None,
            "environment": {
                "mock_time": mock_time,
                "timezone": Config.get_timezone()
            }
        }
        
        # Action state
        self.actions = {
            "is_monitoring": False,
            "last_update": time.time(),
            "metrics_calculated": False
        }
        
        # Internal state tracking
        self._init_time = time.time()
    
    def perceive(self):
        """
        Update agent's perceptions of the environment.
        This is the sensing component of the agent.
        """
        # Update system metrics
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        
        # Store in perception history (keep last 10 readings)
        self.perceptions["cpu_usage_history"].append(cpu_percent)
        if len(self.perceptions["cpu_usage_history"]) > 10:
            self.perceptions["cpu_usage_history"].pop(0)
            
        self.perceptions["memory_usage_history"].append(memory_percent)
        if len(self.perceptions["memory_usage_history"]) > 10:
            self.perceptions["memory_usage_history"].pop(0)
        
        # Update active applications (simplified example)
        try:
            active_processes = [p.info["name"] for p in psutil.process_iter(["name"]) 
                               if p.info["name"] not in ["System", "Idle"]][:5]  # Just top 5 for efficiency
            self.perceptions["active_apps"] = active_processes
        except Exception as e:
            logger.warning(f"Failed to update active applications: {e}")
            
        # Update action state
        self.actions["last_update"] = time.time()
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent
        }
    
    def reason(self):
        """
        Process perceptions and determine current state.
        This is the reasoning component of the agent.
        """
        if not self.actions["is_monitoring"]:
            return {"status": "inactive", "recommendation": "Agent not monitoring"}
        
        current_time = time.time()
        idle_duration = current_time - self.perceptions["last_activity_time"]
        is_active = idle_duration < self.knowledge["idle_threshold"]
        
        # Calculate average system metrics
        avg_cpu = sum(self.perceptions["cpu_usage_history"]) / max(1, len(self.perceptions["cpu_usage_history"]))
        avg_memory = sum(self.perceptions["memory_usage_history"]) / max(1, len(self.perceptions["memory_usage_history"]))
        
        # Determine focus level based on CPU activity and idle time
        focus_level = self._determine_focus_level(avg_cpu, idle_duration)
        
        # Update knowledge about focus patterns
        hour_of_day = self.get_current_time().hour
        if hour_of_day not in self.knowledge["focus_patterns"]:
            self.knowledge["focus_patterns"][hour_of_day] = []
        
        # Keep up to 10 focus level records per hour
        self.knowledge["focus_patterns"][hour_of_day].append(focus_level)
        if len(self.knowledge["focus_patterns"][hour_of_day]) > 10:
            self.knowledge["focus_patterns"][hour_of_day].pop(0)
        
        return {
            "is_active": is_active,
            "idle_duration": idle_duration,
            "focus_level": focus_level,
            "system_load": {
                "cpu": avg_cpu,
                "memory": avg_memory
            }
        }
    
    def act(self, action_type: str = "update"):
        """
        Take action based on current state and reasoning.
        This is the action component of the agent.
        
        Args:
            action_type: Type of action to perform ("update", "reset", etc.)
        """
        if action_type == "update":
            # Update perceptions and process them
            self.perceive()
            state = self.reason()
            self.actions["metrics_calculated"] = True
            return state
            
        elif action_type == "reset":
            # Reset activity tracking
            self.perceptions["last_activity_time"] = time.time()
            logger.info("Focus monitor reset activity tracking")
            return {"status": "reset", "timestamp": time.time()}
            
        else:
            logger.warning(f"Unknown action type: {action_type}")
            return {"status": "error", "message": f"Unknown action type: {action_type}"}
    
    def start(self):
        """Start the focus monitoring agent."""
        self.actions["is_monitoring"] = True
        self.perceptions["last_activity_time"] = time.time()
        logger.info("Focus monitoring started")
    
    def stop(self):
        """Stop the focus monitoring agent."""
        self.actions["is_monitoring"] = False
        logger.info("Focus monitoring stopped")
    
    def update_activity(self):
        """Update the last activity timestamp."""
        self.perceptions["last_activity_time"] = time.time()
    
    def get_activity_stats(self) -> dict:
        """Get current activity statistics."""
        if not self.actions["is_monitoring"]:
            return {
                "is_active": False,
                "idle_duration": 0,
                "cpu_percent": 0,
                "memory_percent": 0
            }
        
        # If we haven't calculated metrics recently, do so now
        if not self.actions["metrics_calculated"]:
            self.perceive()
        
        current_time = time.time()
        idle_duration = current_time - self.perceptions["last_activity_time"]
        
        # Get latest CPU and memory values
        cpu_percent = self.perceptions["cpu_usage_history"][-1] if self.perceptions["cpu_usage_history"] else 0
        memory_percent = self.perceptions["memory_usage_history"][-1] if self.perceptions["memory_usage_history"] else 0
        
        return {
            "is_active": idle_duration < self.knowledge["idle_threshold"],
            "idle_duration": int(idle_duration),
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent
        }
    
    def is_active(self) -> bool:
        """Check if the system is currently active."""
        return self.get_activity_stats()["is_active"]
    
    def get_focus_mode(self) -> str:
        """Get the current focus mode based on activity patterns."""
        # Process perceptions to determine focus mode
        stats = self.get_activity_stats()
        if not stats["is_active"]:
            return "idle"
        
        # More sophisticated focus determination based on CPU and activity patterns
        cpu = stats["cpu_percent"]
        
        if not self.perceptions["cpu_usage_history"]:
            # Default if no history
            if cpu > 80:
                return "intense"
            elif cpu > 50:
                return "focused"
            else:
                return "casual"
        
        # Check for consistent CPU usage patterns
        cpu_variance = self._calculate_variance(self.perceptions["cpu_usage_history"])
        
        if cpu > 80:
            return "intense" if cpu_variance < 15 else "erratic-high"
        elif cpu > 50:
            return "focused" if cpu_variance < 10 else "mixed-work"
        elif cpu > 30:
            return "casual" if cpu_variance < 5 else "browsing"
        else:
            return "low-activity"
    
    def get_uptime_seconds(self) -> int:
        """Get the number of seconds the agent has been running."""
        return int(time.time() - self._init_time)
    
    def get_current_time(self) -> datetime:
        """Get the current time, using mock time if set."""
        if self.knowledge["environment"]["mock_time"]:
            return self.knowledge["environment"]["mock_time"]
        return datetime.now(self.knowledge["environment"]["timezone"])
    
    def get_focus_history(self) -> dict:
        """Get historical focus patterns by hour."""
        return self.knowledge["focus_patterns"]
    
    def _determine_focus_level(self, cpu_usage: float, idle_time: float) -> str:
        """
        Determine focus level based on CPU usage and idle time.
        
        Args:
            cpu_usage: Current CPU usage percentage
            idle_time: Time since last activity in seconds
            
        Returns:
            Focus level classification
        """
        if idle_time > self.knowledge["idle_threshold"]:
            return "idle"
            
        if cpu_usage > 80:
            return "deep-focus"
        elif cpu_usage > 60:
            return "focused"
        elif cpu_usage > 40:
            return "active"
        elif cpu_usage > 20:
            return "light"
        else:
            return "minimal"
    
    def _calculate_variance(self, values: list) -> float:
        """Calculate statistical variance of a list of values."""
        if not values or len(values) < 2:
            return 0
            
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)

# For backward compatibility
ActivityTracker = FocusMonitorAgent 