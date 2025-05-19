import logging
import time
from typing import List
import context_manager as cm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FocusAgent:
    """Example agent that monitors and reports on user focus"""
    
    def __init__(self, agent_id: str = "focus_agent"):
        self.agent_id = agent_id
        self.initialize_context()
        
        # Subscribe to changes in other parts of the context
        cm.subscribe(self.on_context_change, self.agent_id, 
                     ["wellness_agent", "calendar_agent"])
    
    def initialize_context(self):
        """Initialize agent's section in the shared context"""
        initial_state = {
            self.agent_id: {
                "state": {
                    "active": False,
                    "last_update": None,
                    "focus_level": "unknown",
                    "focus_mode": "normal",
                    "active_apps": []
                },
                "config": {
                    "update_interval": 60,  # seconds
                    "idle_threshold": 300   # seconds
                }
            }
        }
        cm.update_context(initial_state, self.agent_id)
    
    def update_focus_state(self, focus_level: str, focus_mode: str, active_apps: List[str]):
        """Update the agent's focus state in the shared context"""
        update = {
            self.agent_id: {
                "state": {
                    "active": True,
                    "last_update": time.time(),
                    "focus_level": focus_level,
                    "focus_mode": focus_mode,
                    "active_apps": active_apps
                }
            }
        }
        cm.update_context(update, self.agent_id)
        logger.info(f"Updated focus state: {focus_level}, {focus_mode}")
    
    def on_context_change(self, changed_keys: List[str], source_agent_id: str):
        """React to changes in the shared context from other agents"""
        logger.info(f"Context change detected from {source_agent_id}: {changed_keys}")
        
        # Example: React to calendar events
        if source_agent_id == "calendar_agent" and any("upcoming_meeting" in key for key in changed_keys):
            calendar_info = cm.get_context("calendar_agent.upcoming_meetings")
            if calendar_info and len(calendar_info) > 0:
                logger.info(f"Adjusting focus monitoring due to upcoming meeting in {calendar_info[0].get('minutes_until', 'unknown')} minutes")
                
                # Update our own state based on the calendar information
                self.update_focus_state("preparing", "meeting-prep", ["calendar", "email"])
    
    def run_cycle(self):
        """Run one update cycle of the agent"""
        # Get current configuration
        config = cm.get_context(f"{self.agent_id}.config")
        
        # Simulate detecting user's focus
        focus_level = "active"
        focus_mode = "coding"
        active_apps = ["vscode", "terminal", "browser"]
        
        # Update the shared context
        self.update_focus_state(focus_level, focus_mode, active_apps)
        
        # Read state from other agents
        wellness_state = cm.get_context("wellness_agent.state")
        if wellness_state:
            logger.info(f"Current wellness state: {wellness_state}")
        
        # Save the current context to file periodically
        cm.save_context_to_file()


class WellnessAgent:
    """Example agent that manages user wellness and break suggestions"""
    
    def __init__(self, agent_id: str = "wellness_agent"):
        self.agent_id = agent_id
        self.initialize_context()
        
        # Subscribe to focus agent changes
        cm.subscribe(self.on_context_change, self.agent_id, ["focus_agent"])
    
    def initialize_context(self):
        """Initialize agent's section in the shared context"""
        initial_state = {
            self.agent_id: {
                "state": {
                    "active": False,
                    "last_update": None,
                    "wellness_score": 100,
                    "break_due": False,
                    "last_break": None
                },
                "config": {
                    "break_interval_minutes": 45,
                    "min_break_duration": 5
                },
                "current_suggestion": None
            }
        }
        cm.update_context(initial_state, self.agent_id)
    
    def suggest_break(self, break_type: str, duration: int, reason: str):
        """Create a break suggestion in the shared context"""
        suggestion = {
            "type": break_type,
            "duration": duration,
            "reason": reason,
            "suggested_at": time.time(),
            "completed": False
        }
        
        update = {
            self.agent_id: {
                "state": {
                    "break_due": True,
                    "last_update": time.time()
                },
                "current_suggestion": suggestion
            }
        }
        
        cm.update_context(update, self.agent_id)
        logger.info(f"Break suggested: {break_type} for {duration} minutes")
    
    def on_context_change(self, changed_keys: List[str], source_agent_id: str):
        """React to changes in the shared context from other agents"""
        if source_agent_id == "focus_agent" and "focus_agent.state.focus_level" in changed_keys:
            focus_info = cm.get_context("focus_agent.state")
            
            if focus_info.get("focus_level") == "deep-focus" and focus_info.get("focus_mode") == "coding":
                # User is in deep focus, adjust our behavior
                logger.info("User in deep focus coding. Will delay break suggestions.")
                
                update = {
                    self.agent_id: {
                        "config": {
                            "break_interval_minutes": 60  # Extend break interval
                        }
                    }
                }
                cm.update_context(update, self.agent_id)
    
    def run_cycle(self):
        """Run one update cycle of the agent"""
        # Check focus state from the context
        focus_state = cm.get_context("focus_agent.state")
        
        if not focus_state or not focus_state.get("active", False):
            logger.info("Focus agent not active or no data available")
            return
        
        # Get our current state
        wellness_state = cm.get_context(f"{self.agent_id}.state")
        config = cm.get_context(f"{self.agent_id}.config")
        
        # Check if it's time for a break
        last_break = wellness_state.get("last_break", 0)
        if last_break is None:
            last_break = 0
            
        break_interval = config.get("break_interval_minutes", 45) * 60  # convert to seconds
        
        if time.time() - last_break > break_interval:
            # Determine appropriate break type based on focus info
            if focus_state.get("focus_mode") == "coding":
                self.suggest_break("eye_break", 5, "Long coding session")
            else:
                self.suggest_break("stretch_break", 3, "Regular break interval")


def main():
    """Example of using multiple agents with the context manager"""
    logger.info("Starting agent example...")
    
    # Clear any existing context
    cm.clear_context()
    
    # Create agents
    focus_agent = FocusAgent()
    wellness_agent = WellnessAgent()
    
    # Run a few cycles
    for i in range(3):
        logger.info(f"\n--- Cycle {i+1} ---")
        focus_agent.run_cycle()
        wellness_agent.run_cycle()
        
        # Show full context after each cycle
        logger.info(f"Current context: {cm.get_context()}")
        
        # Wait between cycles
        if i < 2:  # Don't wait after the last cycle
            logger.info("Waiting 2 seconds before next cycle...")
            time.sleep(2)
    
    # Save final context
    file_path = cm.save_context_to_file()
    logger.info(f"Final context saved to {file_path}")


if __name__ == "__main__":
    main() 