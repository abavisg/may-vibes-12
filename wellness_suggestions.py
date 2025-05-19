from datetime import datetime, time
import random
from user_preferences import UserPreferences, BreakFeedback
from ollama_client import OllamaClient
import logging

logger = logging.getLogger(__name__)

class WellnessSuggestions:
    def __init__(self):
        self.morning_start = time(9, 0)
        self.lunch_start = time(12, 0)
        self.lunch_end = time(14, 0)
        self.evening_start = time(17, 0)
        self.user_prefs = UserPreferences()
        self.ollama = OllamaClient()

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

    def get_break_suggestion(self, activity_stats: dict) -> dict:
        """
        Get personalized break suggestion based on current context
        
        Args:
            activity_stats: Dictionary containing activity statistics
        """
        current_time = self.user_prefs.get_current_time()
        hour = current_time.hour
        
        # Determine time of day
        if 5 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 17:
            time_of_day = "afternoon"
        else:
            time_of_day = "evening"
        
        # Calculate activity level (0-1)
        activity_level = min(1.0, activity_stats['cpu_percent'] / 100)
        
        # Get recent break history
        break_history = self.user_prefs.break_history[-5:]  # Last 5 breaks
        
        context = {
            'time_of_day': time_of_day,
            'active_duration': int(activity_stats.get('active_duration', 0) / 60),  # Convert to minutes
            'break_history': [
                {
                    'type': b.break_type,
                    'effectiveness': b.effectiveness_rating
                }
                for b in break_history
                if b.effectiveness_rating is not None
            ],
            'activity_level': activity_level,
            'wellness_score': 100,  # Default score, should be updated with actual score
            'system_stats': {
                'cpu_percent': activity_stats['cpu_percent'],
                'memory_percent': activity_stats['memory_percent']
            }
        }
        
        # Get suggestion from Ollama
        suggestion = self.ollama.generate_break_suggestion(context)
        
        # Update break type weights based on suggestion
        self._update_break_weights(suggestion['type'])
        
        return suggestion

    def get_wellness_advice(self, metrics: dict) -> list:
        """
        Get personalized wellness advice based on current metrics
        
        Args:
            metrics: Dictionary containing wellness metrics and scores
        """
        return self.ollama.generate_wellness_advice(metrics)

    def record_break_feedback(self, break_type: str, accepted: bool, completed: bool,
                            effectiveness_rating: int = None, energy_level_after: int = None):
        """Record user feedback about a break suggestion"""
        feedback = BreakFeedback(
            break_type=break_type,
            timestamp=self.user_prefs.get_current_time(),
            accepted=accepted,
            completed=completed,
            effectiveness_rating=effectiveness_rating,
            energy_level_after=energy_level_after
        )
        self.user_prefs.add_break_feedback(feedback)

    def _update_break_weights(self, suggested_type: str):
        """Update break type weights based on suggestion"""
        current_weight = self.user_prefs.preferences['break_type_weights'].get(suggested_type, 1.0)
        # Slightly increase weight for suggested type
        new_weight = min(2.0, current_weight * 1.1)
        self.user_prefs.preferences['break_type_weights'][suggested_type] = new_weight
        self.user_prefs.save() 