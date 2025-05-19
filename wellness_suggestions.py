from datetime import datetime, time
import random
from user_preferences import UserPreferences, BreakFeedback

class WellnessSuggestions:
    def __init__(self):
        self.morning_start = time(9, 0)
        self.lunch_start = time(12, 0)
        self.lunch_end = time(14, 0)
        self.evening_start = time(17, 0)
        self.user_prefs = UserPreferences()

        # Different types of breaks with their suggestions
        self.break_types = {
            'eye_break': {
                'title': 'Eye Care Break',
                'suggestions': [
                    "Look at something 20 feet away for 20 seconds (20-20-20 rule)",
                    "Gently close your eyes and roll them in circles",
                    "Cup your hands over your eyes for 30 seconds of darkness"
                ]
            },
            'stretch_break': {
                'title': 'Quick Stretch',
                'suggestions': [
                    "Stand up and stretch your arms overhead",
                    "Gentle neck rotations - 5 each direction",
                    "Shoulder rolls - 10 forward and backward",
                    "Wrist and finger stretches for typing relief"
                ]
            },
            'walk_break': {
                'title': 'Walking Break',
                'suggestions': [
                    "Take a short walk around your space",
                    "Walk to get a glass of water",
                    "Do a lap around your office or home",
                    "Step outside for fresh air if possible"
                ]
            },
            'hydration_break': {
                'title': 'Hydration Break',
                'suggestions': [
                    "Time for a glass of water!",
                    "Refill your water bottle",
                    "Have some herbal tea",
                    "Remember to stay hydrated"
                ]
            }
        }

    def calculate_activity_level(self, activity_stats: dict) -> float:
        """Calculate normalized activity level from system stats"""
        cpu_weight = 0.4
        memory_weight = 0.3
        idle_weight = 0.3
        
        cpu_score = min(activity_stats.get('cpu_percent', 0) / 100.0, 1.0)
        memory_score = min(activity_stats.get('memory_percent', 0) / 100.0, 1.0)
        
        # Convert idle duration to a score (0 = very idle, 1 = very active)
        idle_duration = activity_stats.get('idle_duration', 0)
        idle_score = 1.0 - min(idle_duration / 3600.0, 1.0)  # Normalize to 1 hour
        
        return (cpu_score * cpu_weight + 
                memory_score * memory_weight + 
                idle_score * idle_weight)

    def get_break_suggestion(self, activity_stats: dict, last_break_type: str = None) -> dict:
        """Get a context-aware break suggestion based on activity, time, and user preferences"""
        current_time = datetime.now()
        activity_level = self.calculate_activity_level(activity_stats)
        
        # Get optimal break type based on current context and user preferences
        break_type = self.user_prefs.get_optimal_break_type(current_time, activity_level)
        
        # Get break duration from user preferences
        duration = self.user_prefs.get_optimal_break_duration(break_type)
        
        # Build suggestion
        break_info = {
            'type': break_type,
            'title': self.break_types[break_type]['title'],
            'suggestion': random.choice(self.break_types[break_type]['suggestions']),
            'duration': duration,
            'activity_level': activity_level
        }
        
        return break_info

    def record_break_feedback(self, break_type: str, accepted: bool, completed: bool,
                            effectiveness_rating: int = None, energy_level_after: int = None):
        """Record user feedback about a break suggestion"""
        feedback = BreakFeedback(
            break_type=break_type,
            timestamp=datetime.now(),
            accepted=accepted,
            completed=completed,
            effectiveness_rating=effectiveness_rating,
            energy_level_after=energy_level_after
        )
        self.user_prefs.add_break_feedback(feedback) 