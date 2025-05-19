import logging
import time
import threading
import schedule
from typing import Dict, Any, List, Optional
import context_manager as cm
import datetime
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FocusMonitorAgent:
    """Agent that monitors user focus and activity"""
    
    def __init__(self, agent_id: str = "focus_monitor_agent"):
        self.agent_id = agent_id
        self.initialize_context()
    
    def initialize_context(self):
        """Initialize agent's section in the shared context"""
        initial_state = {
            self.agent_id: {
                "state": {
                    "active": True,
                    "focus_level": "unknown",
                    "focus_mode": "normal",
                    "active_apps": [],
                    "idle_time": 0
                },
                "metrics": {
                    "cpu_usage": 0,
                    "memory_usage": 0,
                    "system_load": 0
                }
            }
        }
        cm.update_context(initial_state, self.agent_id)
    
    def run(self):
        """Run one cycle of the focus monitoring agent"""
        logger.info(f"Running {self.agent_id}")
        
        # Simulate detecting focus and activity metrics
        focus_level = "active"  # Could be: deep-focus, focused, active, light, minimal
        focus_mode = "coding"   # Could be: coding, writing, browsing, meeting, etc.
        active_apps = ["vscode", "terminal", "browser"]
        idle_time = 45  # seconds
        
        # Simulate system metrics
        cpu_usage = 35  # percent
        memory_usage = 65  # percent
        system_load = 2.1  # load average
        
        # Update the context with activity information
        update = {
            self.agent_id: {
                "state": {
                    "active": True,
                    "last_update": time.time(),
                    "focus_level": focus_level,
                    "focus_mode": focus_mode,
                    "active_apps": active_apps,
                    "idle_time": idle_time
                },
                "metrics": {
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage,
                    "system_load": system_load
                }
            }
        }
        
        cm.update_context(update, self.agent_id)
        logger.info(f"{self.agent_id} updated focus data: level={focus_level}, mode={focus_mode}")
        return True


class ContextAgent:
    """Agent that provides time, calendar, and environmental context"""
    
    def __init__(self, agent_id: str = "context_agent"):
        self.agent_id = agent_id
        self.initialize_context()
    
    def initialize_context(self):
        """Initialize agent's section in the shared context"""
        initial_state = {
            self.agent_id: {
                "time": {
                    "hour": 0,
                    "minute": 0,
                    "day_of_week": 0,
                    "is_working_hours": False
                },
                "calendar": {
                    "upcoming_meetings": [],
                    "next_meeting_in_minutes": None
                },
                "environment": {
                    "location": "unknown",
                    "noise_level": "normal"
                }
            }
        }
        cm.update_context(initial_state, self.agent_id)
    
    def run(self):
        """Run one cycle of the context agent"""
        logger.info(f"Running {self.agent_id}")
        
        # Get current time info
        current_time = time.localtime()
        hour = current_time.tm_hour
        minute = current_time.tm_min
        day_of_week = current_time.tm_wday  # 0-6, 0 is Monday
        is_working_hours = (day_of_week < 5 and 9 <= hour < 18)  # Weekdays 9am-6pm
        
        # Simulate calendar info
        upcoming_meetings = []
        next_meeting_in_minutes = None
        
        # If it's a weekday and morning, simulate having a meeting soon
        if day_of_week < 5 and 9 <= hour < 12:
            upcoming_meetings.append({
                "title": "Team Standup",
                "start_time": f"{hour+1}:00",
                "duration_minutes": 30
            })
            next_meeting_in_minutes = 60 - minute
        
        # Update the context with time and calendar information
        update = {
            self.agent_id: {
                "time": {
                    "hour": hour,
                    "minute": minute,
                    "day_of_week": day_of_week,
                    "is_working_hours": is_working_hours,
                    "last_update": time.time()
                },
                "calendar": {
                    "upcoming_meetings": upcoming_meetings,
                    "next_meeting_in_minutes": next_meeting_in_minutes
                }
            }
        }
        
        cm.update_context(update, self.agent_id)
        logger.info(f"{self.agent_id} updated time and calendar data")
        return True


class NudgeAgent:
    """Agent that generates break suggestions based on context"""
    
    def __init__(self, agent_id: str = "nudge_agent"):
        self.agent_id = agent_id
        self.initialize_context()
    
    def initialize_context(self):
        """Initialize agent's section in the shared context"""
        initial_state = {
            self.agent_id: {
                "state": {
                    "active": True,
                    "last_update": None,
                    "break_due": False
                },
                "current_suggestion": None,
                "suggestion_history": []
            }
        }
        cm.update_context(initial_state, self.agent_id)
    
    def determine_break_suggestion(self) -> Dict[str, Any]:
        """Generate a break suggestion based on current context"""
        # Get focus information
        focus_info = cm.get_context("focus_monitor_agent.state")
        time_info = cm.get_context("context_agent.time")
        calendar_info = cm.get_context("context_agent.calendar")
        
        # Default suggestion
        suggestion = {
            "type": "eye_break",
            "duration": 3,
            "reason": "Regular break interval",
            "suggested_at": time.time(),
            "priority": "normal",
            "completed": False
        }
        
        # Customize based on focus context
        if focus_info and time_info:
            focus_level = focus_info.get("focus_level", "unknown")
            focus_mode = focus_info.get("focus_mode", "unknown")
            idle_time = focus_info.get("idle_time", 0)
            
            # If user is already idle, suggest a longer, more intentional break
            if idle_time > 120:  # More than 2 minutes idle
                suggestion["type"] = "stretch_break"
                suggestion["duration"] = 5
                suggestion["reason"] = "You've been idle for a while, good time for a proper break"
                
            # If user is in deep focus coding, suggest an eye break
            elif focus_level == "deep-focus" and focus_mode == "coding":
                suggestion["type"] = "eye_break"
                suggestion["duration"] = 2
                suggestion["reason"] = "You've been coding intensely"
            
            # If it's afternoon, suggest a walking break
            elif time_info.get("hour", 0) >= 14:
                suggestion["type"] = "walk_break"
                suggestion["duration"] = 7
                suggestion["reason"] = "Afternoon slump, movement will help"
            
            # If a meeting is coming up soon
            next_meeting_mins = calendar_info.get("next_meeting_in_minutes")
            if calendar_info and next_meeting_mins is not None and next_meeting_mins < 10:
                suggestion["type"] = "prepare_break"
                suggestion["duration"] = 3
                suggestion["reason"] = "Prepare for upcoming meeting"
                suggestion["priority"] = "high"
        
        return suggestion
    
    def run(self):
        """Run one cycle of the nudge agent"""
        logger.info(f"Running {self.agent_id}")
        
        # Get break suggestion based on context
        suggestion = self.determine_break_suggestion()
        
        # Add to suggestion history and update current suggestion
        update = {
            self.agent_id: {
                "state": {
                    "active": True,
                    "last_update": time.time(),
                    "break_due": True
                },
                "current_suggestion": suggestion,
            }
        }
        
        cm.update_context(update, self.agent_id)
        
        # Also add to history as a separate update to avoid overwriting
        history = cm.get_context(f"{self.agent_id}.suggestion_history") or []
        history.append(suggestion)
        
        # Keep only the last 10 suggestions
        if len(history) > 10:
            history = history[-10:]
            
        cm.update_context({
            self.agent_id: {
                "suggestion_history": history
            }
        }, self.agent_id)
        
        logger.info(f"{self.agent_id} generated break suggestion: {suggestion['type']}")
        return True


class DeliveryAgent:
    """Agent that handles notification delivery to the user"""
    
    def __init__(self, agent_id: str = "delivery_agent"):
        self.agent_id = agent_id
        self.initialize_context()
    
    def initialize_context(self):
        """Initialize agent's section in the shared context"""
        initial_state = {
            self.agent_id: {
                "state": {
                    "active": True,
                    "last_notification": None,
                    "total_notifications": 0,
                    "notification_enabled": True
                },
                "notification_settings": {
                    "audio_enabled": True,
                    "visual_enabled": True,
                    "do_not_disturb": False
                },
                "last_notification": None
            }
        }
        cm.update_context(initial_state, self.agent_id)
    
    def deliver_notification(self, suggestion):
        """Simulate delivering a notification to the user"""
        # Get current notification settings
        settings = cm.get_context(f"{self.agent_id}.notification_settings")
        
        # Prepare notification
        notification = {
            "title": f"Time for a {suggestion['type']}",
            "message": f"{suggestion['reason']} - Take {suggestion['duration']} minutes",
            "timestamp": time.time(),
            "priority": suggestion.get("priority", "normal"),
            "delivered": True,
            "viewed": False,
            "action_taken": None
        }
        
        # In a real implementation, this would trigger the actual notification
        logger.info(f"NOTIFICATION: {notification['title']} - {notification['message']}")
        
        return notification
    
    def run(self):
        """Run one cycle of the delivery agent"""
        logger.info(f"Running {self.agent_id}")
        
        # Get current suggestion
        suggestion = cm.get_context("nudge_agent.current_suggestion")
        
        if not suggestion:
            logger.info(f"{self.agent_id}: No suggestion to deliver")
            return False
        
        # Deliver notification
        notification = self.deliver_notification(suggestion)
        
        # Update context with notification information
        total_notifications = cm.get_context(f"{self.agent_id}.state.total_notifications")
        if total_notifications is None:
            total_notifications = 0
            
        update = {
            self.agent_id: {
                "state": {
                    "active": True,
                    "last_notification": time.time(),
                    "total_notifications": total_notifications + 1
                },
                "last_notification": notification
            }
        }
        
        cm.update_context(update, self.agent_id)
        logger.info(f"{self.agent_id} delivered notification for {suggestion['type']}")
        return True


class SchedulerAgent:
    """
    Agent that orchestrates the execution of other agents in sequence.
    Runs at a configurable interval (default: 5 minutes, configurable via SCHEDULER_FREQUENCY) 
    and ensures proper flow of context data between agents.
    """
    
    def __init__(self):
        self.agent_id = "scheduler_agent"
        self.agents = {
            "focus": FocusMonitorAgent(),
            "context": ContextAgent(),
            "nudge": NudgeAgent(),
            "delivery": DeliveryAgent()
        }
        # Get interval from config before initializing context
        self.run_interval_seconds = Config.SCHEDULER_FREQUENCY
        self.initialize_context()
        self.stop_event = threading.Event()
        self.next_run_at = None
    
    def initialize_context(self):
        """Initialize scheduler's section in the shared context"""
        # Convert from seconds to minutes for context
        run_interval_minutes = self.run_interval_seconds / 60
        
        initial_state = {
            self.agent_id: {
                "state": {
                    "active": True,
                    "last_run": None,
                    "next_run_at": None,
                    "runs_completed": 0,
                    "run_interval_minutes": run_interval_minutes,
                    "run_interval_seconds": self.run_interval_seconds
                },
                "agent_sequence": ["focus", "context", "nudge", "delivery"],
                "agent_status": {
                    "focus": False,
                    "context": False,
                    "nudge": False, 
                    "delivery": False
                }
            }
        }
        cm.update_context(initial_state, self.agent_id)
    
    def _run_agent_cycle(self):
        """Run a complete cycle with all agents in sequence"""
        logger.info("Starting agent cycle...")
        
        # Get sequence of agents to run
        agent_sequence = cm.get_context(f"{self.agent_id}.agent_sequence")
        if not agent_sequence:
            agent_sequence = ["focus", "context", "nudge", "delivery"]
        
        # Track status for each agent
        agent_status = {}
        cycle_success = True
        
        # Run each agent in sequence
        for agent_key in agent_sequence:
            if agent_key in self.agents:
                try:
                    logger.info(f"Scheduler executing agent: {agent_key}")
                    status = self.agents[agent_key].run()
                    agent_status[agent_key] = status
                    if not status:
                        logger.warning(f"Agent {agent_key} reported failure")
                        cycle_success = False
                except Exception as e:
                    logger.error(f"Error running agent {agent_key}: {e}")
                    agent_status[agent_key] = False
                    cycle_success = False
            else:
                logger.error(f"Unknown agent: {agent_key}")
                agent_status[agent_key] = False
                cycle_success = False
        
        # Update scheduler status
        runs_completed = cm.get_context(f"{self.agent_id}.state.runs_completed")
        if runs_completed is None:
            runs_completed = 0
        
        # Calculate next run time
        current_time = time.time()
        interval_seconds = cm.get_context(f"{self.agent_id}.state.run_interval_seconds")
        if interval_seconds is None:
            interval_seconds = self.run_interval_seconds
        
        # Update next run time
        self.next_run_at = current_time + interval_seconds
        
        update = {
            self.agent_id: {
                "state": {
                    "active": True,
                    "last_run": current_time,
                    "next_run_at": self.next_run_at,
                    "runs_completed": runs_completed + 1,
                    "last_run_success": cycle_success
                },
                "agent_status": agent_status
            }
        }
        cm.update_context(update, self.agent_id)
        
        # Log the entire context to a file
        filepath = cm.save_context_to_file("data/agent_context_latest.json")
        logger.info(f"Agent cycle completed. Context saved to {filepath}")
        logger.info(f"Next agent cycle scheduled at: {datetime.datetime.fromtimestamp(self.next_run_at).strftime('%Y-%m-%d %H:%M:%S')}")
    
    def scheduled_run(self):
        """Run method for the scheduler that's called by the schedule package"""
        try:
            self._run_agent_cycle()
        except Exception as e:
            logger.error(f"Error in scheduler run: {e}")
            # Even if there was an error, make sure the next run is scheduled
            current_time = time.time()
            interval_seconds = cm.get_context(f"{self.agent_id}.state.run_interval_seconds") or self.run_interval_seconds
            self.next_run_at = current_time + interval_seconds
            
            # Update context with next run time
            cm.update_context({
                self.agent_id: {
                    "state": {
                        "next_run_at": self.next_run_at,
                        "last_error": str(e),
                        "error_time": current_time
                    }
                }
            }, self.agent_id)
            
            logger.info(f"Scheduled next run despite error at: {datetime.datetime.fromtimestamp(self.next_run_at).strftime('%Y-%m-%d %H:%M:%S')}")
    
    def start(self):
        """Start the scheduler with configurable interval"""
        logger.info("Starting scheduler agent...")
        
        # Get interval in seconds from config
        interval_seconds = self.run_interval_seconds
        
        # Convert to minutes for schedule package (which works in minutes)
        interval_minutes = interval_seconds / 60
        
        # Schedule the agent to run at the configured interval
        schedule.every(interval_minutes).minutes.do(self.scheduled_run)
        
        # Calculate initial next run time
        self.next_run_at = time.time() + interval_seconds
        cm.update_context({
            self.agent_id: {
                "state": {
                    "next_run_at": self.next_run_at
                }
            }
        }, self.agent_id)
        
        # Run immediately once on startup
        self.scheduled_run()
        
        # Keep running until stopped
        while not self.stop_event.is_set():
            schedule.run_pending()
            time.sleep(1)
    
    def stop(self):
        """Stop the scheduler"""
        logger.info("Stopping scheduler agent...")
        self.stop_event.set()
    
    def get_time_until_next_run(self) -> Dict[str, int]:
        """Get time remaining until next scheduled run"""
        if not self.next_run_at:
            return {"minutes": 0, "seconds": 0}
            
        time_remaining = max(0, self.next_run_at - time.time())
        minutes = int(time_remaining // 60)
        seconds = int(time_remaining % 60)
        
        return {
            "minutes": minutes,
            "seconds": seconds
        }


def main():
    """Run the scheduler agent as a standalone process"""
    try:
        # Create and start the scheduler
        scheduler = SchedulerAgent()
        
        # Start in a separate thread
        scheduler_thread = threading.Thread(target=scheduler.start)
        scheduler_thread.start()
        
        # Keep main thread running to handle keyboard interrupts
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping scheduler...")
        scheduler.stop()
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    main() 