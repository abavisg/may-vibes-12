# simulation_tool.py
import argparse
import json
import time
import logging
import random
from datetime import datetime, timedelta
import context_manager as cm
from config import Config
from user_preferences import UserPreferences, BreakFeedback
from scheduler_agent import SchedulerAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UserStateSimulator:
    """Tool to simulate different user states for testing the agent system"""
    
    def __init__(self):
        # Ensure we're in mock mode
        if not Config.MOCKING_ENABLED:
            logger.warning("Simulator should be run with MOCKING_ENABLED=true")
        
        self.user_prefs = UserPreferences()
        self.agent = SchedulerAgent()
        
        # Define available user state profiles
        self.profiles = {
            "deep_work": self._create_deep_work_state,
            "distracted": self._create_distracted_state,
            "tired": self._create_tired_state,
            "meeting_heavy": self._create_meeting_heavy_state,
            "end_of_day": self._create_end_of_day_state,
            "morning_start": self._create_morning_start_state,
            "stressed": self._create_stressed_state,
            "eye_strain": self._create_eye_strain_state,
            "sedentary": self._create_sedentary_state,
            "dual_monitor": self._create_dual_monitor_state,
        }
    
    def list_profiles(self):
        """List available simulation profiles"""
        print("Available simulation profiles:")
        for profile, func in self.profiles.items():
            print(f"  - {profile}: {func.__doc__.strip()}")
    
    def simulate(self, profile_name, run_agent=False, add_break_history=False):
        """
        Simulate a specific user state profile
        
        Args:
            profile_name: Name of the profile to simulate
            run_agent: Whether to run the agent cycle after simulation
            add_break_history: Whether to add simulated break history
        """
        if profile_name not in self.profiles:
            logger.error(f"Unknown profile: {profile_name}")
            self.list_profiles()
            return False
        
        # Clear existing context to start fresh
        cm.clear_context()
        
        # Initialize the agent to properly set up its context
        if run_agent:
            self.agent.initialize_context()
        
        # Apply the selected profile
        logger.info(f"Simulating user state: {profile_name}")
        profile_func = self.profiles[profile_name]
        state = profile_func()
        
        # Log the state that will be applied
        logger.info(f"Applying user state: {json.dumps(state, indent=2, default=str)}")
        
        # Use context manager to update state
        cm.update_context(state, "simulation_tool")
        
        # Optionally add break history
        if add_break_history:
            self._add_simulated_break_history(profile_name)
        
        # Save updated context
        cm.save_context_to_file("data/simulated_state.json")
        logger.info(f"Simulated state saved to data/simulated_state.json")
        
        # Optionally run a single agent cycle
        if run_agent:
            logger.info("Running agent cycle with simulated state...")
            self.agent._run_agent_cycle()
            
            # Save updated context after agent run
            cm.save_context_to_file("data/post_agent_run_state.json")
            logger.info("Agent cycle completed. Results saved to data/post_agent_run_state.json")
        
        return True
    
    def _create_deep_work_state(self):
        """Simulates a user in deep focus coding for 60+ minutes"""
        # Set mock time to 11:30 AM
        mock_time = datetime.combine(
            datetime.now().date(), 
            datetime.strptime("11:30", "%H:%M").time()
        ).replace(tzinfo=Config.get_timezone())
        UserPreferences.set_mocked_time(mock_time)
        
        return {
            "focus_monitor_agent": {
                "state": {
                    "active": True,
                    "last_update": time.time(),
                    "focus_level": "deep-focus",
                    "focus_mode": "coding",
                    "active_apps": ["vscode", "terminal", "browser"],
                    "idle_time": 45
                },
                "metrics": {
                    "cpu_usage": 65,
                    "memory_usage": 70,
                    "system_load": 3.2
                },
                "focus_history": {
                    "10": ["active", "active", "deep-focus"],
                    "11": ["deep-focus", "deep-focus", "deep-focus"]
                }
            },
            "context_agent": {
                "time": {
                    "hour": 11,
                    "minute": 30,
                    "day_of_week": mock_time.weekday(),
                    "is_working_hours": True
                },
                "calendar": {
                    "upcoming_meetings": [{
                        "title": "Team Meeting",
                        "start_time": "13:00",
                        "duration_minutes": 60
                    }],
                    "next_meeting_in_minutes": 90
                }
            }
        }
        
    def _create_distracted_state(self):
        """Simulates a user rapidly switching between applications for 30+ minutes"""
        # Set mock time to 2:15 PM
        mock_time = datetime.combine(
            datetime.now().date(), 
            datetime.strptime("14:15", "%H:%M").time()
        ).replace(tzinfo=Config.get_timezone())
        UserPreferences.set_mocked_time(mock_time)
        
        return {
            "focus_monitor_agent": {
                "state": {
                    "active": True,
                    "last_update": time.time(),
                    "focus_level": "light",
                    "focus_mode": "erratic-high",
                    "active_apps": ["browser", "slack", "mail", "notes", "calendar"],
                    "idle_time": 20
                },
                "metrics": {
                    "cpu_usage": 45,
                    "memory_usage": 60,
                    "system_load": 2.1
                },
                "focus_history": {
                    "13": ["active", "active", "active"],
                    "14": ["light", "light", "erratic-high"]
                }
            },
            "context_agent": {
                "time": {
                    "hour": 14,
                    "minute": 15,
                    "day_of_week": mock_time.weekday(),
                    "is_working_hours": True
                },
                "calendar": {
                    "upcoming_meetings": [],
                    "next_meeting_in_minutes": None
                }
            }
        }
        
    def _create_tired_state(self):
        """Simulates a user showing fatigue patterns after working 3+ hours"""
        # Set mock time to 4:45 PM
        mock_time = datetime.combine(
            datetime.now().date(), 
            datetime.strptime("16:45", "%H:%M").time()
        ).replace(tzinfo=Config.get_timezone())
        UserPreferences.set_mocked_time(mock_time)
        
        return {
            "focus_monitor_agent": {
                "state": {
                    "active": True,
                    "last_update": time.time(),
                    "focus_level": "minimal",
                    "focus_mode": "low-activity",
                    "active_apps": ["browser", "mail", "chat"],
                    "idle_time": 90
                },
                "metrics": {
                    "cpu_usage": 25,
                    "memory_usage": 55,
                    "system_load": 1.2
                },
                "focus_history": {
                    "14": ["active", "active", "focused"],
                    "15": ["focused", "active", "light"],
                    "16": ["light", "minimal", "minimal"]
                }
            },
            "context_agent": {
                "time": {
                    "hour": 16,
                    "minute": 45,
                    "day_of_week": mock_time.weekday(),
                    "is_working_hours": True
                },
                "calendar": {
                    "upcoming_meetings": [],
                    "next_meeting_in_minutes": None
                }
            }
        }
        
    def _create_meeting_heavy_state(self):
        """Simulates a user with back-to-back meetings all day"""
        # Set mock time to 1:45 PM
        mock_time = datetime.combine(
            datetime.now().date(), 
            datetime.strptime("13:45", "%H:%M").time()
        ).replace(tzinfo=Config.get_timezone())
        UserPreferences.set_mocked_time(mock_time)
        
        return {
            "focus_monitor_agent": {
                "state": {
                    "active": True,
                    "last_update": time.time(),
                    "focus_level": "active",
                    "focus_mode": "meeting",
                    "active_apps": ["zoom", "browser", "presentation", "notes"],
                    "idle_time": 30
                },
                "metrics": {
                    "cpu_usage": 55,
                    "memory_usage": 75,
                    "system_load": 3.5
                },
                "focus_history": {
                    "09": ["meeting", "meeting", "meeting"],
                    "10": ["meeting", "meeting", "active"],
                    "11": ["active", "meeting", "meeting"],
                    "12": ["meeting", "active", "active"],
                    "13": ["active", "meeting", "meeting"]
                }
            },
            "context_agent": {
                "time": {
                    "hour": 13,
                    "minute": 45,
                    "day_of_week": mock_time.weekday(),
                    "is_working_hours": True
                },
                "calendar": {
                    "upcoming_meetings": [
                        {
                            "title": "Project Review",
                            "start_time": "14:00",
                            "duration_minutes": 60
                        },
                        {
                            "title": "Client Call",
                            "start_time": "15:30",
                            "duration_minutes": 45
                        }
                    ],
                    "next_meeting_in_minutes": 15
                }
            }
        }
        
    def _create_end_of_day_state(self):
        """Simulates a user wrapping up work tasks at end of day"""
        # Set mock time to 5:45 PM
        mock_time = datetime.combine(
            datetime.now().date(), 
            datetime.strptime("17:45", "%H:%M").time()
        ).replace(tzinfo=Config.get_timezone())
        UserPreferences.set_mocked_time(mock_time)
        
        return {
            "focus_monitor_agent": {
                "state": {
                    "active": True,
                    "last_update": time.time(),
                    "focus_level": "active",
                    "focus_mode": "mixed",
                    "active_apps": ["mail", "chat", "notes", "browser"],
                    "idle_time": 60
                },
                "metrics": {
                    "cpu_usage": 30,
                    "memory_usage": 45,
                    "system_load": 1.5
                },
                "focus_history": {
                    "15": ["active", "active", "active"],
                    "16": ["active", "active", "light"],
                    "17": ["light", "active", "active"]
                }
            },
            "context_agent": {
                "time": {
                    "hour": 17,
                    "minute": 45,
                    "day_of_week": mock_time.weekday(),
                    "is_working_hours": True
                },
                "calendar": {
                    "upcoming_meetings": [],
                    "next_meeting_in_minutes": None
                }
            }
        }
        
    def _create_morning_start_state(self):
        """Simulates a user just beginning their workday"""
        # Set mock time to 9:15 AM
        mock_time = datetime.combine(
            datetime.now().date(), 
            datetime.strptime("09:15", "%H:%M").time()
        ).replace(tzinfo=Config.get_timezone())
        UserPreferences.set_mocked_time(mock_time)
        
        return {
            "focus_monitor_agent": {
                "state": {
                    "active": True,
                    "last_update": time.time(),
                    "focus_level": "light",
                    "focus_mode": "mixed",
                    "active_apps": ["mail", "browser", "calendar"],
                    "idle_time": 30
                },
                "metrics": {
                    "cpu_usage": 25,
                    "memory_usage": 40,
                    "system_load": 1.2
                },
                "focus_history": {
                    "09": ["light", "light", "light"]
                }
            },
            "context_agent": {
                "time": {
                    "hour": 9,
                    "minute": 15,
                    "day_of_week": mock_time.weekday(),
                    "is_working_hours": True
                },
                "calendar": {
                    "upcoming_meetings": [{
                        "title": "Morning Standup",
                        "start_time": "10:00",
                        "duration_minutes": 30
                    }],
                    "next_meeting_in_minutes": 45
                }
            }
        }
        
    def _create_stressed_state(self):
        """Simulates a user with high system activity and approaching deadline"""
        # Set mock time to 3:45 PM
        mock_time = datetime.combine(
            datetime.now().date(), 
            datetime.strptime("15:45", "%H:%M").time()
        ).replace(tzinfo=Config.get_timezone())
        UserPreferences.set_mocked_time(mock_time)
        
        return {
            "focus_monitor_agent": {
                "state": {
                    "active": True,
                    "last_update": time.time(),
                    "focus_level": "deep-focus",
                    "focus_mode": "intense",
                    "active_apps": ["vscode", "browser", "terminal", "chat"],
                    "idle_time": 10
                },
                "metrics": {
                    "cpu_usage": 85,
                    "memory_usage": 80,
                    "system_load": 4.2
                },
                "focus_history": {
                    "13": ["active", "focused", "focused"],
                    "14": ["focused", "deep-focus", "deep-focus"],
                    "15": ["deep-focus", "deep-focus", "intense"]
                }
            },
            "context_agent": {
                "time": {
                    "hour": 15,
                    "minute": 45,
                    "day_of_week": mock_time.weekday(),
                    "is_working_hours": True
                },
                "calendar": {
                    "upcoming_meetings": [{
                        "title": "Project Deadline Review",
                        "start_time": "16:30",
                        "duration_minutes": 30
                    }],
                    "next_meeting_in_minutes": 45
                }
            }
        }
    
    def _create_eye_strain_state(self):
        """Simulates a user who has been looking at screens for hours without breaks"""
        # Set mock time to 2:30 PM
        mock_time = datetime.combine(
            datetime.now().date(), 
            datetime.strptime("14:30", "%H:%M").time()
        ).replace(tzinfo=Config.get_timezone())
        UserPreferences.set_mocked_time(mock_time)
        
        return {
            "focus_monitor_agent": {
                "state": {
                    "active": True,
                    "last_update": time.time(),
                    "focus_level": "focused",
                    "focus_mode": "reading",
                    "active_apps": ["browser", "pdf-reader", "notes"],
                    "idle_time": 15,
                    "screen_time_minutes": 180
                },
                "metrics": {
                    "cpu_usage": 40,
                    "memory_usage": 60,
                    "system_load": 2.0
                },
                "focus_history": {
                    "11": ["focused", "focused", "focused"],
                    "12": ["focused", "active", "active"],
                    "13": ["active", "focused", "focused"],
                    "14": ["focused", "reading", "reading"]
                }
            },
            "context_agent": {
                "time": {
                    "hour": 14,
                    "minute": 30,
                    "day_of_week": mock_time.weekday(),
                    "is_working_hours": True
                },
                "calendar": {
                    "upcoming_meetings": [],
                    "next_meeting_in_minutes": None
                }
            }
        }
    
    def _create_sedentary_state(self):
        """Simulates a user who has been sitting at their desk for 3+ hours"""
        # Set mock time to 11:45 AM
        mock_time = datetime.combine(
            datetime.now().date(), 
            datetime.strptime("11:45", "%H:%M").time()
        ).replace(tzinfo=Config.get_timezone())
        UserPreferences.set_mocked_time(mock_time)
        
        return {
            "focus_monitor_agent": {
                "state": {
                    "active": True,
                    "last_update": time.time(),
                    "focus_level": "active",
                    "focus_mode": "normal",
                    "active_apps": ["excel", "browser", "mail"],
                    "idle_time": 25,
                    "sedentary_minutes": 185
                },
                "metrics": {
                    "cpu_usage": 45,
                    "memory_usage": 55,
                    "system_load": 1.8
                },
                "focus_history": {
                    "08": ["light", "active", "active"],
                    "09": ["active", "active", "focused"],
                    "10": ["focused", "active", "active"],
                    "11": ["active", "active", "active"]
                }
            },
            "context_agent": {
                "time": {
                    "hour": 11,
                    "minute": 45,
                    "day_of_week": mock_time.weekday(),
                    "is_working_hours": True
                },
                "calendar": {
                    "upcoming_meetings": [{
                        "title": "Lunch Meeting",
                        "start_time": "12:30",
                        "duration_minutes": 60
                    }],
                    "next_meeting_in_minutes": 45
                }
            }
        }
    
    def _create_dual_monitor_state(self):
        """Simulates a user working with multiple monitors and applications"""
        # Set mock time to 10:30 AM
        mock_time = datetime.combine(
            datetime.now().date(), 
            datetime.strptime("10:30", "%H:%M").time()
        ).replace(tzinfo=Config.get_timezone())
        UserPreferences.set_mocked_time(mock_time)
        
        return {
            "focus_monitor_agent": {
                "state": {
                    "active": True,
                    "last_update": time.time(),
                    "focus_level": "focused",
                    "focus_mode": "multitasking",
                    "active_apps": ["design-tool", "browser", "vscode", "chat", "music"],
                    "idle_time": 15,
                    "screen_count": 2
                },
                "metrics": {
                    "cpu_usage": 60,
                    "memory_usage": 70,
                    "system_load": 2.8
                },
                "focus_history": {
                    "09": ["light", "active", "active"],
                    "10": ["active", "focused", "multitasking"]
                }
            },
            "context_agent": {
                "time": {
                    "hour": 10,
                    "minute": 30,
                    "day_of_week": mock_time.weekday(),
                    "is_working_hours": True
                },
                "calendar": {
                    "upcoming_meetings": [],
                    "next_meeting_in_minutes": None
                }
            }
        }
        
    def _add_simulated_break_history(self, profile_name):
        """Add simulated break history based on the user profile"""
        # Clear existing history
        self.user_prefs.break_history = []
        
        # Create mock break history entries
        now = self.user_prefs.get_current_time()
        
        # Different behavior patterns based on profile
        if profile_name in ["deep_work", "stressed"]:
            # This user tends to ignore breaks when deeply focused
            feedbacks = [
                BreakFeedback(
                    break_type="eye_break",
                    timestamp=now - timedelta(hours=2),
                    accepted=False,
                    completed=False
                ),
                BreakFeedback(
                    break_type="stretch_break",
                    timestamp=now - timedelta(hours=1),
                    accepted=False,
                    completed=False
                )
            ]
        elif profile_name in ["tired", "eye_strain"]:
            # This user accepts but doesn't complete breaks
            feedbacks = [
                BreakFeedback(
                    break_type="eye_break",
                    timestamp=now - timedelta(hours=2),
                    accepted=True,
                    completed=False,
                    effectiveness_rating=2
                ),
                BreakFeedback(
                    break_type="stretch_break",
                    timestamp=now - timedelta(hours=1),
                    accepted=True,
                    completed=False,
                    effectiveness_rating=2
                )
            ]
        elif profile_name in ["distracted", "sedentary"]:
            # This user takes and completes breaks consistently
            feedbacks = [
                BreakFeedback(
                    break_type="eye_break",
                    timestamp=now - timedelta(hours=3),
                    accepted=True,
                    completed=True,
                    effectiveness_rating=4
                ),
                BreakFeedback(
                    break_type="walk_break",
                    timestamp=now - timedelta(hours=2),
                    accepted=True,
                    completed=True,
                    effectiveness_rating=5
                ),
                BreakFeedback(
                    break_type="stretch_break",
                    timestamp=now - timedelta(hours=1),
                    accepted=True,
                    completed=True,
                    effectiveness_rating=4
                )
            ]
        else:
            # Default mixed pattern
            feedbacks = [
                BreakFeedback(
                    break_type="eye_break",
                    timestamp=now - timedelta(hours=3),
                    accepted=True,
                    completed=True,
                    effectiveness_rating=3
                ),
                BreakFeedback(
                    break_type="stretch_break",
                    timestamp=now - timedelta(hours=2),
                    accepted=False,
                    completed=False
                ),
                BreakFeedback(
                    break_type="walk_break",
                    timestamp=now - timedelta(hours=1),
                    accepted=True,
                    completed=False,
                    effectiveness_rating=2
                )
            ]
        
        # Add the feedback to user preferences
        for feedback in feedbacks:
            self.user_prefs.add_break_feedback(feedback)
            
        logger.info(f"Added {len(feedbacks)} simulated break history entries")

def main():
    parser = argparse.ArgumentParser(description="Tool to simulate user states for testing")
    parser.add_argument("--profile", type=str, choices=[
        "deep_work", "distracted", "tired", "meeting_heavy", 
        "end_of_day", "morning_start", "stressed", "eye_strain",
        "sedentary", "dual_monitor", "list"
    ], default="list", help="User state profile to simulate")
    parser.add_argument("--run-agent", action="store_true", help="Run agent cycle after simulation")
    parser.add_argument("--with-history", action="store_true", help="Add simulated break history")
    
    args = parser.parse_args()
    
    simulator = UserStateSimulator()
    
    if args.profile == "list":
        simulator.list_profiles()
        return
        
    result = simulator.simulate(args.profile, args.run_agent, args.with_history)
    if result:
        print(f"Successfully simulated {args.profile} user state")
        if args.run_agent:
            print("Agent cycle completed")
        print("\nYou can now run the web app to see the results:")
        print("  python app.py")

if __name__ == "__main__":
    main()