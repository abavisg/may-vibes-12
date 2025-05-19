from datetime import datetime, time
import json
import os
from typing import Dict, List, Optional
import numpy as np
from dataclasses import dataclass, asdict
from config import Config

@dataclass
class BreakFeedback:
    break_type: str
    timestamp: datetime
    accepted: bool
    completed: bool
    effectiveness_rating: Optional[int] = None  # 1-5 rating
    energy_level_after: Optional[int] = None    # 1-5 rating
    
class UserPreferences:
    _mocked_time: Optional[datetime] = None
    
    def __init__(self):
        """Initialize user preferences with mock data directory."""
        self.mock_data_dir = Config.get_mock_data_dir()
        self.preferences_file = self.mock_data_dir / "preferences.json"
        self.break_history_file = self.mock_data_dir / "break_history.json"
        
        # Load or initialize preferences
        self.preferences = self._load_preferences()
        self.break_history: List[BreakFeedback] = self._load_break_history()
        
    @classmethod
    def set_mocked_time(cls, mocked_time: Optional[datetime]):
        """Set a mocked time for testing purposes."""
        cls._mocked_time = mocked_time
    
    @classmethod
    def get_current_time(cls) -> datetime:
        """Get the current time, using mocked time if set."""
        return cls._mocked_time if cls._mocked_time is not None else datetime.now(Config.get_timezone())
    
    @classmethod
    def clear_mocked_time(cls):
        """Clear any mocked time and return to using real time."""
        cls._mocked_time = None
    
    def _load_preferences(self) -> Dict:
        """Load user preferences from file or create default"""
        if os.path.exists(self.preferences_file):
            with open(self.preferences_file, 'r') as f:
                prefs = json.load(f)
                
                # Ensure all required fields are present
                if 'break_durations' not in prefs:
                    prefs['break_durations'] = self._get_default_break_durations()
                if 'break_type_weights' not in prefs:
                    prefs['break_type_weights'] = self._get_default_break_weights()
                
                # Add any missing break types
                for break_type in self._get_default_break_weights().keys():
                    if break_type not in prefs['break_type_weights']:
                        prefs['break_type_weights'][break_type] = 1.0
                    if break_type not in prefs['break_durations']:
                        prefs['break_durations'][break_type] = self._get_default_break_durations()[break_type]
                        
                return prefs
        
        # Default preferences
        return {
            "preferred_break_times": {
                "morning": time(10, 30).isoformat(),
                "lunch": time(12, 30).isoformat(),
                "afternoon": time(15, 30).isoformat()
            },
            "break_durations": self._get_default_break_durations(),
            "break_type_weights": self._get_default_break_weights()
        }
        
    def _get_default_break_durations(self) -> Dict[str, int]:
        """Get default durations for all break types"""
        return {
            "eye_break": 2,
            "stretch_break": 5,
            "posture_break": 3,
            "deep_breathing": 3,
            "mindfulness": 5,
            "walk_break": 10,
            "hydration_break": 3,
            "nature_break": 5,
            "creative_break": 7
        }
        
    def _get_default_break_weights(self) -> Dict[str, float]:
        """Get default weights for all break types"""
        return {
            "eye_break": 1.0,
            "stretch_break": 1.0,
            "posture_break": 1.0,
            "deep_breathing": 1.0,
            "mindfulness": 1.0,
            "walk_break": 1.0,
            "hydration_break": 1.0,
            "nature_break": 1.0,
            "creative_break": 1.0
        }
    
    def _load_break_history(self) -> List[BreakFeedback]:
        """Load break history from file"""
        if os.path.exists(self.break_history_file):
            with open(self.break_history_file, 'r') as f:
                data = json.load(f)
                return [
                    BreakFeedback(
                        break_type=item['break_type'],
                        timestamp=datetime.fromisoformat(item['timestamp']),
                        accepted=item['accepted'],
                        completed=item['completed'],
                        effectiveness_rating=item.get('effectiveness_rating'),
                        energy_level_after=item.get('energy_level_after')
                    )
                    for item in data.get('history', [])
                ]
        return []
    
    def save(self):
        """Save current preferences and history to files"""
        with open(self.preferences_file, 'w') as f:
            json.dump(self.preferences, f, indent=2)
            
        with open(self.break_history_file, 'w') as f:
            history_data = {
                'history': [
                    {
                        'break_type': item.break_type,
                        'timestamp': item.timestamp.isoformat(),
                        'accepted': item.accepted,
                        'completed': item.completed,
                        'effectiveness_rating': item.effectiveness_rating,
                        'energy_level_after': item.energy_level_after
                    }
                    for item in self.break_history
                ]
            }
            json.dump(history_data, f, indent=2)
    
    def add_break_feedback(self, feedback: BreakFeedback):
        """Add new break feedback and update preferences"""
        self.break_history.append(feedback)
        
        # Update break type weights based on effectiveness
        if feedback.effectiveness_rating:
            current_weight = self.preferences['break_type_weights'][feedback.break_type]
            # Adjust weight based on rating (1-5 scale)
            rating_factor = (feedback.effectiveness_rating - 3) * 0.1  # -0.2 to +0.2
            new_weight = max(0.1, min(2.0, current_weight * (1 + rating_factor)))
            self.preferences['break_type_weights'][feedback.break_type] = new_weight
        
        self.save()
    
    def get_optimal_break_type(self, time_of_day: Optional[datetime] = None, activity_level: float = 0.5) -> str:
        """
        Determine the optimal break type based on time, activity, and past effectiveness
        
        Args:
            time_of_day: Optional datetime to override current time (useful for testing)
            activity_level: Float between 0 and 1 indicating recent activity level
        """
        # Use provided time, mocked time, or current time
        current_time = time_of_day or self.get_current_time()
        
        weights = self.preferences['break_type_weights'].copy()
        
        # Adjust weights based on time of day
        hour = current_time.hour
        if 8 <= hour < 11:  # Morning
            weights['eye_break'] *= 1.8     # Increased from 1.5
            weights['stretch_break'] *= 1.1  # Reduced from 1.2
            weights['walk_break'] *= 0.7     # Reduced from 0.8
            weights['hydration_break'] *= 0.9  # Added reduction for hydration
        elif 14 <= hour < 17:  # Afternoon
            weights['walk_break'] *= 1.8     # Increased from 1.6
            weights['stretch_break'] *= 1.2   # Reduced from 1.3
            weights['eye_break'] *= 0.7      # Reduced from 0.8
            weights['hydration_break'] *= 0.9  # Added reduction for hydration
        
        # Adjust based on activity level
        if activity_level > 0.7:  # High activity
            weights['walk_break'] *= 1.4
            weights['stretch_break'] *= 1.2
            weights['eye_break'] *= 0.7      # Further reduce eye breaks during high activity
        elif activity_level < 0.3:  # Low activity
            weights['eye_break'] *= 1.2      # Increased from 0.8
            weights['hydration_break'] *= 1.3 # Increased from 1.2
            weights['walk_break'] *= 0.7      # Reduce walks during low activity
        
        # Convert weights to probabilities
        total_weight = sum(weights.values())
        probs = {k: v/total_weight for k, v in weights.items()}
        
        # Select break type based on weighted probabilities
        break_types = list(probs.keys())
        probabilities = list(probs.values())
        return np.random.choice(break_types, p=probabilities)
    
    def get_optimal_break_duration(self, break_type: str) -> int:
        """Get the optimal duration for a given break type"""
        return self.preferences['break_durations'].get(break_type, 5)  # Default to 5 minutes
        
    def get_recent_break_feedback(self, count: int = 1) -> List[BreakFeedback]:
        """
        Get the most recent break feedback entries
        
        Args:
            count: Number of recent feedback entries to return
        
        Returns:
            List of BreakFeedback objects, sorted with most recent first
        """
        # Sort by timestamp with most recent first
        sorted_history = sorted(
            self.break_history, 
            key=lambda x: x.timestamp, 
            reverse=True
        )
        
        # Return up to 'count' entries
        return sorted_history[:count]
        
    def get_upcoming_meetings(self, lookback_minutes: int = 15, lookahead_minutes: int = 60):
        """
        Mock method to generate upcoming meetings for the demo
        In a real implementation, this would call out to the calendar service
        """
        current_hour = self.get_current_time().hour
        
        # Simulate some meetings on weekdays during work hours 
        if self.get_current_time().weekday() < 5 and 9 <= current_hour <= 17:
            # Morning standup
            if 9 <= current_hour < 10:
                meeting_time = datetime.combine(
                    self.get_current_time().date(),
                    time(10, 0)
                ).replace(tzinfo=Config.get_timezone())
                
                if (meeting_time - self.get_current_time()).total_seconds() / 60 <= lookahead_minutes:
                    return [{
                        'title': 'Team Standup',
                        'start': meeting_time.isoformat(),
                        'end': (meeting_time + datetime.timedelta(minutes=30)).isoformat(),
                        'duration': 30
                    }]
                    
            # Afternoon sync
            elif 14 <= current_hour < 15:
                meeting_time = datetime.combine(
                    self.get_current_time().date(),
                    time(15, 0)
                ).replace(tzinfo=Config.get_timezone())
                
                if (meeting_time - self.get_current_time()).total_seconds() / 60 <= lookahead_minutes:
                    return [{
                        'title': 'Project Sync',
                        'start': meeting_time.isoformat(),
                        'end': (meeting_time + datetime.timedelta(minutes=45)).isoformat(),
                        'duration': 45
                    }]
        
        # No meetings found in the time window
        return [] 