from datetime import datetime, time, timezone
import random
from user_preferences import UserPreferences, BreakFeedback
from ollama_client import OllamaClient
import logging
import requests
import numpy as np
from typing import Dict, List, Optional, Tuple
import math
import os
import urllib3

from config import Config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class WellnessSuggestions:
    def __init__(self):
        self.morning_start = time(9, 0)
        self.lunch_start = time(12, 0)
        self.lunch_end = time(14, 0)
        self.evening_start = time(17, 0)
        self.user_prefs = UserPreferences()
        self.ollama = OllamaClient()
        self.last_break_check = datetime.now()
        self.last_suggestion_time = None
        self.last_check_time = None
        
        # Time-based weights for different break types
        self.time_weights = {
            "morning": {
                "eye_break": 1.8,
                "stretch_break": 1.2,
                "posture_break": 1.5,
                "deep_breathing": 1.4,
                "mindfulness": 1.7,
                "walk_break": 0.7,
                "hydration_break": 1.2,
                "nature_break": 0.8,
                "creative_break": 0.8
            },
            "midday": {
                "eye_break": 1.3,
                "stretch_break": 1.4,
                "posture_break": 1.3,
                "deep_breathing": 1.2,
                "mindfulness": 1.0,
                "walk_break": 1.5,
                "hydration_break": 1.4,
                "nature_break": 1.3,
                "creative_break": 1.0
            },
            "afternoon": {
                "eye_break": 1.5,
                "stretch_break": 1.3,
                "posture_break": 1.2,
                "deep_breathing": 1.0,
                "mindfulness": 1.2,
                "walk_break": 1.8,
                "hydration_break": 1.3,
                "nature_break": 1.2,
                "creative_break": 1.6
            },
            "evening": {
                "eye_break": 1.8,
                "stretch_break": 1.0,
                "posture_break": 1.0,
                "deep_breathing": 1.5,
                "mindfulness": 1.5,
                "walk_break": 0.8,
                "hydration_break": 0.9,
                "nature_break": 1.0,
                "creative_break": 1.2
            }
        }
        
        # Activity level weights
        self.activity_weights = {
            "high": {  # CPU/memory usage high, user very active
                "eye_break": 1.8,
                "stretch_break": 1.6,
                "posture_break": 1.5,
                "deep_breathing": 1.3,
                "mindfulness": 0.8,
                "walk_break": 1.0,
                "hydration_break": 1.4,
                "nature_break": 0.7,
                "creative_break": 0.6
            },
            "medium": {  # Normal activity
                "eye_break": 1.3,
                "stretch_break": 1.3,
                "posture_break": 1.3,
                "deep_breathing": 1.3,
                "mindfulness": 1.3,
                "walk_break": 1.3,
                "hydration_break": 1.3,
                "nature_break": 1.3,
                "creative_break": 1.3
            },
            "low": {  # User not very active, idle periods
                "eye_break": 0.8,
                "stretch_break": 0.9,
                "posture_break": 0.8,
                "deep_breathing": 1.5,
                "mindfulness": 1.8,
                "walk_break": 1.7,
                "hydration_break": 1.2,
                "nature_break": 1.5,
                "creative_break": 1.7
            }
        }

        # Different types of breaks with their suggestions
        self.break_types = {
            'eye_break': {
                'title': 'Eye Care Break',
                'suggestions': [
                    "Look at something 20 feet away for 20 seconds (20-20-20 rule)",
                    "Gently close your eyes and roll them in circles",
                    "Cup your hands over your eyes for 30 seconds of darkness",
                    "Focus on an object far away, then one up close, alternating 5 times",
                    "Blink rapidly for 15 seconds to refresh your eyes"
                ]
            },
            'stretch_break': {
                'title': 'Quick Stretch',
                'suggestions': [
                    "Stand up and stretch your arms overhead",
                    "Gentle neck rotations - 5 each direction",
                    "Shoulder rolls - 10 forward and backward",
                    "Wrist and finger stretches for typing relief",
                    "Touch your toes or reach as far down as comfortable",
                    "Side stretches - reach arm overhead and lean to each side",
                    "Desk pushups - hands on desk edge, step back and do 5-10 pushups"
                ]
            },
            'posture_break': {
                'title': 'Posture Reset',
                'suggestions': [
                    "Stand up straight against a wall to realign your spine",
                    "Roll your shoulders back and down to correct hunching",
                    "Tuck your chin slightly to align your neck properly",
                    "Check that your screen is at eye level and adjust if needed",
                    "Sit with both feet flat on floor, back supported, for proper alignment"
                ]
            },
            'deep_breathing': {
                'title': 'Breathing Exercise',
                'suggestions': [
                    "4-7-8 breath: Inhale for 4, hold for 7, exhale for 8 counts",
                    "Take 5 deep belly breaths, focusing on full exhales",
                    "Box breathing: Equal counts of inhale, hold, exhale, hold",
                    "Alternate nostril breathing for 1 minute",
                    "Lion's breath: Inhale through nose, exhale with open mouth and tongue out"
                ]
            },
            'mindfulness': {
                'title': 'Mindfulness Moment',
                'suggestions': [
                    "Focus on physical sensations for 1 minute without judgment",
                    "Notice 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell, 1 you can taste",
                    "Perform a quick body scan from head to toe, noticing sensations",
                    "Practice mindful eating with a small snack, focusing on all sensory aspects",
                    "Close your eyes and focus on your breath for 2 minutes, returning whenever mind wanders"
                ]
            },
            'walk_break': {
                'title': 'Walking Break',
                'suggestions': [
                    "Take a short walk around your space",
                    "Walk to get a glass of water",
                    "Do a lap around your office or home",
                    "Step outside for fresh air if possible",
                    "Walk up and down stairs for 2 minutes",
                    "Walk to a window and enjoy the view for a moment",
                    "Walk in place with high knees for 1 minute"
                ]
            },
            'hydration_break': {
                'title': 'Hydration Break',
                'suggestions': [
                    "Time for a glass of water!",
                    "Refill your water bottle",
                    "Have some herbal tea",
                    "Remember to stay hydrated",
                    "Try water with a slice of lemon or cucumber",
                    "Check your water intake for the day and adjust if needed",
                    "Prepare a warm cup of caffeine-free tea"
                ]
            },
            'nature_break': {
                'title': 'Nature Connection',
                'suggestions': [
                    "Look out a window at natural elements for 2 minutes",
                    "If possible, step outside and feel the sun or breeze",
                    "Water or check on a houseplant",
                    "Take a moment to listen to nature sounds, even from an app",
                    "Look at images of natural scenes for a mental refresh"
                ]
            },
            'creative_break': {
                'title': 'Creative Pause',
                'suggestions': [
                    "Doodle or sketch for 3 minutes",
                    "Write a haiku about your current mood",
                    "List 3 ideas for something unrelated to work",
                    "Play a quick word association game with yourself",
                    "Listen to a favorite song and focus just on the music"
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

    def get_activity_category(self, activity_level: float) -> str:
        """Categorize activity level as high, medium, or low"""
        if activity_level > 0.7:
            return "high"
        elif activity_level < 0.3:
            return "low"
        else:
            return "medium"
            
    def get_time_category(self, current_time: datetime) -> str:
        """Categorize time of day"""
        hour = current_time.hour
        
        if 5 <= hour < 11:
            return "morning"
        elif 11 <= hour < 14:
            return "midday"
        elif 14 <= hour < 18:
            return "afternoon"
        else:
            return "evening"
            
    def get_break_weights(self, time_category: str, activity_category: str, work_duration_minutes: int) -> Dict[str, float]:
        """Calculate weighted scores for each break type based on context"""
        # Start with base weights from user preferences
        base_weights = self.user_prefs.preferences.get('break_type_weights', {
            "eye_break": 1.0,
            "stretch_break": 1.0,
            "posture_break": 1.0,
            "deep_breathing": 1.0,
            "mindfulness": 1.0,
            "walk_break": 1.0,
            "hydration_break": 1.0,
            "nature_break": 1.0,
            "creative_break": 1.0
        })
        
        # Apply time of day and activity level modifiers
        time_modifiers = self.time_weights.get(time_category, self.time_weights["afternoon"])
        activity_modifiers = self.activity_weights.get(activity_category, self.activity_weights["medium"])
        
        # Calculate combined weights
        combined_weights = {}
        for break_type in base_weights:
            # If break type isn't in modifiers, default to 1.0
            time_mod = time_modifiers.get(break_type, 1.0)
            activity_mod = activity_modifiers.get(break_type, 1.0)
            
            # Duration factor: longer work = more need for physical breaks
            duration_factor = 1.0
            if work_duration_minutes > 90:
                # For long work sessions, prioritize physical breaks
                if break_type in ["walk_break", "stretch_break", "posture_break"]:
                    duration_factor = 1.5
                elif break_type == "eye_break":
                    duration_factor = 1.3
            
            # Combine all factors
            combined_weights[break_type] = base_weights.get(break_type, 1.0) * time_mod * activity_mod * duration_factor
        
        # Check if we have feedback history to adjust weights
        if self.user_prefs.break_history:
            self._adjust_weights_from_history(combined_weights)
            
        return combined_weights
    
    def _adjust_weights_from_history(self, weights: Dict[str, float]) -> None:
        """Adjust weights based on break history and effectiveness ratings"""
        # Use only the last 20 breaks with ratings
        recent_breaks = [b for b in self.user_prefs.break_history[-20:] 
                         if b.effectiveness_rating is not None]
        
        if not recent_breaks:
            return
            
        # Calculate average effectiveness per break type
        type_ratings = {}
        for b in recent_breaks:
            if b.break_type not in type_ratings:
                type_ratings[b.break_type] = []
            type_ratings[b.break_type].append(b.effectiveness_rating)
        
        # Average ratings
        avg_ratings = {}
        for break_type, ratings in type_ratings.items():
            if ratings:
                avg_ratings[break_type] = sum(ratings) / len(ratings)
        
        # Adjust weights based on ratings (1-5 scale)
        for break_type, rating in avg_ratings.items():
            if break_type in weights:
                # Convert 1-5 scale to multiplier (0.7-1.3)
                multiplier = 0.7 + (rating - 1) * 0.15
                weights[break_type] *= multiplier
    
    def select_break_type(self, weights: Dict[str, float]) -> str:
        """Select a break type based on weighted probabilities"""
        break_types = list(weights.keys())
        weights_list = [weights[bt] for bt in break_types]
        
        # Convert to probabilities
        total = sum(weights_list)
        if total == 0:  # Safety check
            return random.choice(list(self.break_types.keys()))
            
        probabilities = [w/total for w in weights_list]
        
        return np.random.choice(break_types, p=probabilities)

    def check_llm_status(self) -> dict:
        """Check if the LLM is available and return status info"""
        try:
            # Check if Ollama is responding
            ollama_host = 'localhost' if not hasattr(self.ollama, 'host') or not self.ollama.host else self.ollama.host
            ollama_port = '11434'  # Standard Ollama port
            
            # Log attempt
            logger.info(f"Checking Ollama availability at http://{ollama_host}:{ollama_port}/api/tags")
            
            # Set a timeout for the request to avoid hanging
            response = requests.get(f'http://{ollama_host}:{ollama_port}/api/tags', timeout=3)
            
            # Log response status
            logger.info(f"Ollama API response status: {response.status_code}")
            
            # Attempt to parse the response
            response_data = response.json()
            logger.info(f"Found {len(response_data.get('models', []))} models from Ollama API")
            
            # Find our model in the response
            models_data = response_data.get('models', [])
            model_info = next((m for m in models_data if m.get('name') == self.ollama.model), None)
            
            if model_info:
                # Get frequency in minutes for display
                frequency_seconds = Config.SCHEDULER_FREQUENCY
                frequency_minutes = frequency_seconds / 60
                
                return {
                    'is_available': True,
                    'model': self.ollama.model,
                    'model_size': model_info.get('details', {}).get('parameter_size', 'Unknown'),
                    'last_check': datetime.now().isoformat(),
                    'last_suggestion': self.last_suggestion_time.isoformat() if self.last_suggestion_time else None,
                    'check_interval': f'{int(frequency_minutes)} minutes',
                    'suggestion_threshold': '45 minutes of activity'
                }
            else:
                # Model not found but API is available
                logger.warning(f"Ollama is running but model '{self.ollama.model}' not found. Available models: {[m.get('name') for m in models_data]}")
                return {
                    'is_available': False,
                    'model': self.ollama.model,
                    'model_size': 'Unknown',
                    'last_check': datetime.now().isoformat(),
                    'note': f"Model '{self.ollama.model}' not found in Ollama. Try 'ollama pull {self.ollama.model}'"
                }
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error reaching Ollama: {e}")
            return {
                'is_available': False,
                'error': f"Cannot connect to Ollama at http://{ollama_host}:{ollama_port}. Is Ollama running?",
                'last_check': datetime.now().isoformat(),
                'model': self.ollama.model if hasattr(self, 'ollama') and hasattr(self.ollama, 'model') else 'unknown'
            }
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout reaching Ollama: {e}")
            return {
                'is_available': False,
                'error': f"Timeout connecting to Ollama. Service may be overloaded.",
                'last_check': datetime.now().isoformat(),
                'model': self.ollama.model if hasattr(self, 'ollama') and hasattr(self.ollama, 'model') else 'unknown'
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error reaching Ollama: {e}")
            return {
                'is_available': False,
                'error': f"Error connecting to Ollama: {str(e)}",
                'last_check': datetime.now().isoformat(),
                'model': self.ollama.model if hasattr(self, 'ollama') and hasattr(self.ollama, 'model') else 'unknown'
            }
        except Exception as e:
            logger.error(f"Unexpected error checking Ollama status: {e}")
            return {
                'is_available': False,
                'error': f"Unexpected error: {str(e)}",
                'last_check': datetime.now().isoformat(),
                'model': self.ollama.model if hasattr(self, 'ollama') and hasattr(self.ollama, 'model') else 'unknown'
            }

    def get_break_suggestion(self, activity_stats: dict) -> dict:
        """
        Get personalized break suggestion based on current context
        
        Args:
            activity_stats: Dictionary containing activity statistics
            
        Note:
            If activity_stats contains focus_level and focus_mode from the FocusMonitorAgent,
            those will be used to provide more personalized suggestions.
        """
        self.last_break_check = datetime.now()
        current_time = self.user_prefs.get_current_time()
        
        # Calculate activity level (0-1)
        activity_level = self.calculate_activity_level(activity_stats)
        
        # Determine time and activity categories
        time_category = self.get_time_category(current_time)
        activity_category = self.get_activity_category(activity_level)
        
        # Use focus information from the agent if available
        focus_level = activity_stats.get('focus_level', None)
        focus_mode = activity_stats.get('focus_mode', None)
        
        # Calculate work duration in minutes
        active_duration_minutes = int(activity_stats.get('active_duration', 0) / 60)
        
        # Prepare context for LLM using MCP format
        context = {
            'time_of_day': time_category,
            'active_duration': active_duration_minutes,
            'activity_level': activity_level
        }
        
        # Add focus data if available
        if focus_level and focus_mode:
            context['focus_data'] = {
                'focus_level': focus_level,
                'focus_mode': focus_mode,
                'active_apps': activity_stats.get('active_processes', [])
            }
        
        # Get upcoming meetings if available
        upcoming_meetings = self.user_prefs.get_upcoming_meetings(
            lookback_minutes=0, 
            lookahead_minutes=60
        )
        
        if upcoming_meetings:
            next_meeting = upcoming_meetings[0]
            next_meeting_time = next_meeting.get('start')
            
            if next_meeting_time:
                # Calculate minutes until next meeting
                try:
                    if isinstance(next_meeting_time, str):
                        next_meeting_time = datetime.fromisoformat(next_meeting_time)
                    
                    time_diff = (next_meeting_time - current_time).total_seconds() / 60
                    context['next_meeting_in_minutes'] = int(time_diff)
                except Exception as e:
                    logger.error(f"Error calculating next meeting time: {e}")
        
        # Add feedback about the last break suggestion if available
        recent_feedback = self.user_prefs.get_recent_break_feedback(1)
        if recent_feedback:
            last_feedback = recent_feedback[0]
            context['last_break_accepted'] = last_feedback.accepted
            logger.info(f"Including feedback from last break: accepted={last_feedback.accepted}")
        
        try:
            # Use the new MCP-style message format
            suggestion = self.ollama.get_suggestion(context)
            self.last_suggestion_time = datetime.now()
            
            # Update break type weights based on suggestion
            self._update_break_weights(suggestion.get('type', 'stretch_break'))
            
            return suggestion
            
        except Exception as e:
            # Fallback to previous method if the new one fails
            logger.error(f"Error using MCP message format, falling back: {e}")
            try:
                # Get personalized break weights
                break_weights = self.get_break_weights(
                    time_category, 
                    activity_category, 
                    active_duration_minutes
                )
                
                # Select break type based on weights
                selected_break_type = self.select_break_type(break_weights)
                
                # Get break details
                break_info = self.break_types.get(selected_break_type)
                if not break_info:
                    # Fallback if somehow we selected an invalid break type
                    selected_break_type = random.choice(list(self.break_types.keys()))
                    break_info = self.break_types[selected_break_type]
                
                # Select a random suggestion for this break type
                suggestion_text = random.choice(break_info['suggestions'])
                
                # Get optimal duration based on user preferences
                duration = self.user_prefs.get_optimal_break_duration(selected_break_type)
                
                # Create fallback suggestion
                fallback_suggestion = {
                    'title': break_info['title'],
                    'activity': suggestion_text,
                    'duration': duration,
                    'benefits': ["Reduces fatigue", "Improves focus"],
                    'type': selected_break_type
                }
                
                # Update break type weights
                self._update_break_weights(selected_break_type)
                self.last_suggestion_time = datetime.now()
                
                return fallback_suggestion
                
            except Exception as nested_e:
                logger.error(f"Both suggestion methods failed: {nested_e}")
                # Ultimate fallback
                self.last_suggestion_time = datetime.now()
                return {
                    'title': "Quick Break",
                    'activity': "Stand up and stretch for a minute",
                    'duration': 2,
                    'benefits': ["Reduces fatigue", "Improves circulation"],
                    'type': "stretch_break"
                }

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

    def check_work_patterns(self, active_time_minutes, idle_time_minutes, activity_history):
        """
        Check work patterns and suggest breaks if needed.
        Returns a tuple of (should_take_break, suggestion, reason)
        
        If the activity_history contains focus information from FocusMonitorAgent,
        it will be used to make more intelligent break decisions.
        """
        # Record the current check time
        self.last_check_time = datetime.now(timezone.utc).isoformat()
        
        # Log current status for debugging
        current_time = self.user_prefs.get_current_time()
        logger.info(f"Checking work patterns at {current_time}")
        logger.info(f"Active time: {active_time_minutes} minutes, Idle time: {idle_time_minutes} minutes")
        
        # Get focus information if available
        focus_level = activity_history.get('focus_level', None)
        focus_mode = activity_history.get('focus_mode', None)
        
        # Make more intelligent break decisions if focus data is available
        if focus_level and focus_mode:
            logger.info(f"Focus level: {focus_level}, Focus mode: {focus_mode}")
            
            # Don't interrupt deep focus unless it's been going on too long
            if focus_level == "deep-focus" and active_time_minutes < 60:
                return False, None, "User in deep focus state"
                
            # Suggest breaks more aggressively for high cognitive load activities
            if focus_mode in ["intense", "erratic-high"] and active_time_minutes > 30:
                logger.info("User in high cognitive load activity. Break suggested.")
                suggestion = self.get_break_suggestion(activity_history)
                if suggestion:
                    self.last_suggestion_time = datetime.now(timezone.utc).isoformat()
                    return True, suggestion, "High cognitive load detected"
        
        # Standard idle checks
        if idle_time_minutes > 10:
            logger.info("User has been idle for more than 10 minutes. No break suggested.")
            return False, None, "User is already idle"

        # Standard active time checks - adjust based on focus mode if available
        minimum_active_time = 45  # default
        if focus_mode in ["intense", "erratic-high"]:
            minimum_active_time = 30  # suggest breaks sooner for high-intensity work
        elif focus_mode in ["casual", "browsing", "low-activity"]:
            minimum_active_time = 60  # suggest breaks later for low-intensity work
            
        if active_time_minutes < minimum_active_time:
            logger.info(f"User has only been active for {active_time_minutes} minutes. No break suggested.")
            return False, None, "Not enough active time"

        # Check if there's an upcoming meeting in the next 15 minutes
        upcoming_meetings = self.user_prefs.get_upcoming_meetings(
            lookback_minutes=0, 
            lookahead_minutes=15
        )
        
        if upcoming_meetings:
            next_meeting = upcoming_meetings[0]
            logger.info(f"Upcoming meeting at {next_meeting['start']}. No break suggested.")
            return False, None, f"Meeting soon at {next_meeting['start']}"
        
        # Get a break suggestion from the LLM
        suggestion = self.get_break_suggestion(activity_history)
        if suggestion:
            self.last_suggestion_time = datetime.now(timezone.utc).isoformat()
            return True, suggestion, "Time for a break"
        
        return False, None, "No suggestion generated"

    def get_llm_status(self):
        """Get the status of the LLM service."""
        is_available = self.ollama.check_availability()
        
        status = {
            "is_available": is_available,
            "model": self.ollama.model_name if is_available else None,
            "model_size": self.ollama.model_size,
            "last_suggestion": self.last_suggestion_time,
            "last_check": self.last_check_time
        }
        
        return status 