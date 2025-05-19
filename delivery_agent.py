import logging
import time
from typing import Dict, Any

import context_manager as cm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
        if total_notifications is None or not isinstance(total_notifications, int):
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