import requests
import json
import logging
import socket
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, host: str = "localhost", port: int = 11434, model: str = "tinyllama:latest"):
        """Initialize Ollama client with host, port and model"""
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.model = model  # Using TinyLlama for faster prototyping
        self.model_name = self.model.split(':')[0]  # Extract base model name
        self.model_size = '1B'  # Default size for TinyLlama
        self.last_suggestion = None  # Store the last suggestion for continuity
        
        # Log initialization
        logger.info(f"Initializing OllamaClient with host={host}, port={port}, model={model}")
        
        # Check availability at startup
        available, status = self.check_availability_with_status()
        if available:
            logger.info(f"Successfully connected to Ollama. Model {model} is available.")
        else:
            logger.warning(f"Could not connect to Ollama: {status}")
        
    def check_availability(self) -> bool:
        """Check if Ollama is available and the model is loaded"""
        available, _ = self.check_availability_with_status()
        return available
        
    def check_availability_with_status(self) -> Tuple[bool, str]:
        """Check if Ollama is available and the model is loaded, returns status reason"""
        try:
            # First check if the port is open
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            
            if result != 0:
                return False, f"Port {self.port} is not open on {self.host}. Is Ollama running?"
                
            # Then check the API
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            
            if response.status_code != 200:
                return False, f"Ollama API returned status code {response.status_code}"
            
            # Check if our model is in the list of models
            models_data = response.json().get('models', [])
            if not models_data:
                return False, "No models found in Ollama"
                
            model_info = next((m for m in models_data if m.get('name') == self.model), None)
            
            if model_info is None:
                available_models = ", ".join([m.get('name', 'unknown') for m in models_data])
                return False, f"Model {self.model} not found. Available models: {available_models}"
            
            # Extract model size if available
            if 'details' in model_info and 'parameter_size' in model_info['details']:
                self.model_size = model_info['details']['parameter_size']
                
            return True, f"Model {self.model} is available"
            
        except requests.exceptions.ConnectionError as e:
            return False, f"Connection error: {str(e)}"
        except requests.exceptions.Timeout as e:
            return False, f"Connection timeout: {str(e)}"
        except requests.exceptions.RequestException as e:
            return False, f"Request error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def get_suggestion(self, context: Dict) -> Dict:
        """
        Generate personalized break suggestion using Model Context Protocol (MCP)-style messages
        
        Args:
            context: Dictionary containing:
                - time_of_day: str
                - active_duration: int (minutes)
                - break_history: List[Dict]
                - activity_level: float
                - focus_data: Dict (optional)
                - calendar_data: Dict (optional)
                - next_meeting_in_minutes: int (optional)
                - last_break_accepted: bool (optional)
        
        Returns:
            Dict containing the suggested break
        """
        # Check if Ollama is available first
        if not self.check_availability():
            logger.warning("Ollama not available, using fallback suggestion")
            fallback = self._get_fallback_suggestion(context)
            return fallback
        
        # Extract key information from context
        time_of_day = context.get('time_of_day', 'afternoon')
        active_duration = context.get('active_duration', 45)
        activity_level = context.get('activity_level', 0.5)
        
        # Format meeting information
        meeting_info = "No upcoming meetings"
        if 'next_meeting_in_minutes' in context:
            next_meeting = context['next_meeting_in_minutes']
            if next_meeting > 0:
                meeting_info = f"Meeting in {next_meeting} minutes"
        
        # Format focus information
        focus_info = ""
        if 'focus_data' in context:
            focus_level = context['focus_data'].get('focus_level', 'unknown')
            focus_mode = context['focus_data'].get('focus_mode', 'normal')
            focus_info = f" Focus level: {focus_level} ({focus_mode})"
        
        # Create messages with improved human-readable format
        messages = [
            {
                "role": "system", 
                "content": "You are a kind wellness coach who gives personalised break suggestions to help the user maintain work-life balance."
            },
            {
                "role": "user", 
                "content": f"The user has been working for {active_duration} minutes. It's currently {time_of_day}. Their activity level is {activity_level:.1f}/1.0.{focus_info} Upcoming meeting: {meeting_info}. Please suggest a suitable micro-break in JSON format with title, activity, duration, benefits, and type fields."
            }
        ]
        
        # Add previous suggestion with user feedback if available
        if self.last_suggestion:
            last_accepted = context.get('last_break_accepted', None)
            feedback = ""
            if last_accepted is not None:
                feedback = f" and the user {'accepted' if last_accepted else 'ignored'} it."
            
            messages.append({
                "role": "assistant",
                "content": f"The last suggestion was: '{json.dumps(self.last_suggestion)}'{feedback}"
            })
        
        try:
            # Using Ollama's chat completions API with messages array
            logger.info(f"Sending request to Ollama for break suggestion")
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                },
                timeout=10  # Add timeout to avoid hanging
            )
            response.raise_for_status()
            
            result = response.json()
            suggestion = self._parse_break_suggestion(result['message']['content'])
            
            # Store this suggestion for future context
            self.last_suggestion = suggestion
            logger.info(f"Successfully generated break suggestion: {suggestion['type']}")
            
            return suggestion
            
        except Exception as e:
            logger.error(f"Failed to generate break suggestion: {str(e)}")
            fallback = self._get_fallback_suggestion(context)
            self.last_suggestion = fallback
            return fallback
    
    def _create_context_description(self, context: Dict) -> str:
        """Create a concise context description for the user message"""
        time_of_day = context.get('time_of_day', 'afternoon')
        active_duration = context.get('active_duration', 45)
        activity_level = context.get('activity_level', 0.5)
        
        # Check if we have focus information
        focus_info = ""
        if 'focus_data' in context:
            focus_level = context['focus_data'].get('focus_level', 'unknown')
            focus_mode = context['focus_data'].get('focus_mode', 'normal')
            focus_info = f" Their focus level is {focus_level} in {focus_mode} mode."
        
        # Check if we have calendar information
        meeting_info = ""
        if 'next_meeting_in_minutes' in context:
            next_meeting = context['next_meeting_in_minutes']
            if next_meeting > 0:
                meeting_info = f" They have a meeting in {next_meeting} minutes."
        
        # Create concise description
        return f"The user has worked for {active_duration} minutes during the {time_of_day} with activity level {activity_level:.1f}/1.0.{focus_info}{meeting_info} Please suggest a suitable micro-break in JSON format: {{\"title\": \"...\", \"activity\": \"...\", \"duration\": X, \"benefits\": [...], \"type\": \"...\"}}"
            
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
        time_of_day = context.get('time_of_day', 'afternoon')
        
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