import requests
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        """Initialize Ollama client with base URL"""
        self.base_url = base_url
        self.model = "tinyllama:latest"  # Using TinyLlama for faster prototyping
        self.model_name = self.model.split(':')[0]  # Extract base model name
        self.model_size = '1B'  # Default size for TinyLlama
        
    def check_availability(self) -> bool:
        """Check if Ollama is available and the model is loaded"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            response.raise_for_status()
            
            # Check if our model is in the list of models
            models_data = response.json().get('models', [])
            model_info = next((m for m in models_data if m.get('name') == self.model), None)
            
            return model_info is not None
        except Exception as e:
            logger.error(f"Error checking Ollama availability: {e}")
            return False
            
    def generate_break_suggestion(self, context: Dict) -> Dict:
        """
        Generate personalized break suggestions based on user context
        
        Args:
            context: Dictionary containing:
                - time_of_day: str
                - active_duration: int (minutes)
                - break_history: List[Dict]
                - activity_level: float
                - wellness_score: float
                - system_stats: Dict
                - selected_break_type: str (optional)
                - break_title: str (optional)
                - break_suggestion: str (optional)
                - break_duration: int (optional)
        """
        prompt = self._create_break_prompt(context)
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            
            result = response.json()
            suggestion = self._parse_break_suggestion(result['response'])
            
            return suggestion
            
        except Exception as e:
            logger.error(f"Failed to generate break suggestion: {str(e)}")
            return self._get_fallback_suggestion(context)
    
    def generate_wellness_advice(self, metrics: Dict) -> List[str]:
        """
        Generate personalized wellness advice based on metrics
        
        Args:
            metrics: Dictionary containing wellness metrics and scores
        """
        prompt = self._create_wellness_prompt(metrics)
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            
            result = response.json()
            advice = self._parse_wellness_advice(result['response'])
            
            return advice
            
        except Exception as e:
            logger.error(f"Failed to generate wellness advice: {str(e)}")
            return self._get_fallback_advice(metrics)
    
    def _create_break_prompt(self, context: Dict) -> str:
        """Create prompt for break suggestion"""
        time_of_day = context['time_of_day']
        active_duration = context['active_duration']
        activity_level = context['activity_level']
        wellness_score = context['wellness_score']
        
        # Check if we have a pre-selected break type
        if 'selected_break_type' in context:
            selected_type = context['selected_break_type']
            break_title = context.get('break_title', 'Break')
            suggested_activity = context.get('break_suggestion', '')
            duration = context.get('break_duration', 5)
            
            # Enhanced prompt with pre-selected break type
            prompt = f"""As a wellness coach, enhance this {selected_type} break suggestion. Context:
Time: {time_of_day}
Work duration: {active_duration} min
Activity level: {activity_level:.2f}/1.0
Current wellness: {wellness_score:.1f}

Break suggestion details:
- Type: {selected_type}
- Title: {break_title}
- Suggested activity: {suggested_activity}
- Recommended duration: {duration} minutes

Enhance this suggestion by adding personalization for the time of day and current activity level.
Keep the same break type but make the suggestion more engaging and specific.

Return JSON:
{{
    "title": "Brief descriptive title",
    "activity": "Clear, actionable instructions",
    "duration": {duration},
    "benefits": ["health benefit 1", "health benefit 2"],
    "type": "{selected_type}"
}}
"""
        else:
            # Original prompt format for open-ended suggestions
            valid_types = "eye_break, stretch_break, posture_break, deep_breathing, mindfulness, walk_break, hydration_break, nature_break, creative_break"
            
            prompt = f"""As a wellness coach, suggest a break activity. Context:
Time: {time_of_day}
Work duration: {active_duration} min
Activity: {activity_level:.2f}/1.0
Wellness: {wellness_score:.1f}

Return JSON:
{{
    "title": "Brief title",
    "activity": "Short description",
    "duration": minutes,
    "benefits": ["benefit1", "benefit2"],
    "type": "break_type"
}}

Types: {valid_types}
"""
        return prompt
    
    def _create_wellness_prompt(self, metrics: Dict) -> str:
        """Create prompt for wellness advice"""
        prompt = f"""As a wellness coach, give advice based on:
Score: {metrics['current_score']:.1f}
Break compliance: {metrics['components']['break_compliance']:.1f}%
Work duration: {metrics['components']['work_duration']:.1f}%
Activity balance: {metrics['components']['activity_balance']:.1f}%
Schedule: {metrics['components']['schedule_adherence']:.1f}%
System usage: {metrics['components']['system_usage']:.1f}%

Give 2-3 short, actionable work-life balance tips.
"""
        return prompt
    
    def _parse_break_suggestion(self, response: str) -> Dict:
        """Parse break suggestion from Ollama response"""
        try:
            # Clean up response to ensure valid JSON
            json_str = response.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:-3]  # Remove ```json and ``` markers
            elif json_str.startswith("```"):
                json_str = json_str[3:-3]  # Remove ``` markers
                
            suggestion = json.loads(json_str)
            
            # Validate break type
            valid_types = {
                'eye_break', 'stretch_break', 'posture_break', 'deep_breathing', 
                'mindfulness', 'walk_break', 'hydration_break', 'nature_break', 
                'creative_break'
            }
            
            if suggestion['type'] not in valid_types:
                suggestion['type'] = 'stretch_break'
            
            return suggestion
            
        except Exception as e:
            logger.error(f"Failed to parse break suggestion: {str(e)}")
            return {
                "title": "Quick Stretch Break",
                "activity": "Stand up and do some basic stretches",
                "duration": 5,
                "benefits": ["Reduce muscle tension", "Improve circulation"],
                "type": "stretch_break"
            }
    
    def _parse_wellness_advice(self, response: str) -> List[str]:
        """Parse wellness advice from Ollama response"""
        try:
            # Split response into lines and clean up
            advice = [
                line.strip()
                for line in response.split('\n')
                if line.strip() and not line.startswith('-')
            ]
            return advice[:3]  # Return up to 3 suggestions
            
        except Exception as e:
            logger.error(f"Failed to parse wellness advice: {str(e)}")
            return [
                "Take regular breaks to maintain productivity",
                "Stay hydrated throughout the day",
                "Practice good posture while working"
            ]
    
    def _get_fallback_suggestion(self, context: Dict) -> Dict:
        """Get fallback break suggestion when Ollama fails"""
        time_of_day = context['time_of_day']
        
        if time_of_day == "morning":
            return {
                "title": "Eye Rest Break",
                "activity": "Look at something 20 feet away for 20 seconds",
                "duration": 2,
                "benefits": ["Reduce eye strain", "Prevent fatigue"],
                "type": "eye_break"
            }
        elif time_of_day == "afternoon":
            return {
                "title": "Quick Walk",
                "activity": "Take a short walk around your workspace",
                "duration": 5,
                "benefits": ["Boost energy", "Improve circulation"],
                "type": "walk_break"
            }
        else:
            return {
                "title": "Stretch Break",
                "activity": "Do some basic stretches",
                "duration": 5,
                "benefits": ["Reduce muscle tension", "Improve flexibility"],
                "type": "stretch_break"
            }
    
    def _get_fallback_advice(self, metrics: Dict) -> List[str]:
        """Get fallback wellness advice when Ollama fails"""
        advice = []
        
        if metrics['components']['break_compliance'] < 70:
            advice.append("Try to take more regular breaks to maintain productivity")
        if metrics['components']['work_duration'] < 70:
            advice.append("Consider shorter work sessions with more frequent breaks")
        if metrics['components']['activity_balance'] < 70:
            advice.append("Aim for a better balance between focused work and rest periods")
        
        if not advice:
            advice = [
                "Maintain regular breaks throughout your day",
                "Stay hydrated and maintain good posture",
                "Take short walks when possible"
            ]
        
        return advice 