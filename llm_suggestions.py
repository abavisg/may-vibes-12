from datetime import datetime
import json
from typing import Dict, Optional
from config import Config

class LLMSuggestions:
    def __init__(self):
        """Initialize LLM suggestions handler"""
        self.system_prompt = """You are a mindful wellness assistant that helps maintain work/life balance.
Your role is to provide gentle, contextual suggestions for taking breaks during work.
Keep responses brief, friendly, and focused on the immediate context.
Use a supportive but not pushy tone."""

    def generate_break_message(self, 
                             break_type: str,
                             activity_stats: Dict,
                             calendar_context: Optional[Dict] = None,
                             work_duration: int = 0) -> str:
        """
        Generate a contextual break suggestion message using LLM.
        
        Args:
            break_type: Type of break (eye_break, stretch_break, etc.)
            activity_stats: Current system activity statistics
            calendar_context: Optional upcoming calendar events
            work_duration: Minutes worked since last break
        """
        # Build context for LLM
        current_time = datetime.now(Config.get_timezone())
        hour = current_time.hour
        
        context = {
            "time_of_day": "morning" if 5 <= hour < 12 else "afternoon" if hour < 17 else "evening",
            "break_type": break_type,
            "work_duration": work_duration,
            "activity_level": "high" if activity_stats.get('cpu_percent', 0) > 70 else "moderate",
            "has_meetings": bool(calendar_context and calendar_context.get('next_event')),
        }
        
        user_prompt = self._build_prompt(context)
        
        # TODO: Integrate with actual LLM service
        # For now, return template-based messages
        return self._get_template_message(context)
    
    def _build_prompt(self, context: Dict) -> str:
        """Build a prompt for the LLM based on context"""
        prompt = f"""Given the current context:
- Time of day: {context['time_of_day']}
- Suggested break: {context['break_type']}
- Working for: {context['work_duration']} minutes
- Activity level: {context['activity_level']}
- Upcoming meetings: {'Yes' if context['has_meetings'] else 'No'}

Generate a brief, friendly message suggesting a {context['break_type']}.
Consider the time of day and current work context.
Keep the message under 100 characters.
Focus on the immediate benefit of taking the break."""
        
        return prompt
    
    def _get_template_message(self, context: Dict) -> str:
        """Temporary template-based messages until LLM integration"""
        templates = {
            'eye_break': {
                'morning': "Your eyes could use a quick rest. Look at something distant for 20 seconds?",
                'afternoon': "Been focusing on the screen a while. Time for a 20-second eye break?",
                'evening': "As the day winds down, let's give your eyes a quick rest."
            },
            'stretch_break': {
                'morning': "Start the day right with some energizing stretches!",
                'afternoon': "A quick stretch could help maintain your momentum.",
                'evening': "Some gentle stretches to release the day's tension?"
            },
            'walk_break': {
                'morning': "A brief morning walk could energize your day!",
                'afternoon': "Perfect time for a short walk to refresh your mind.",
                'evening': "A walk could help transition from work mode."
            },
            'hydration_break': {
                'morning': "Start fresh with some water!",
                'afternoon': "Stay hydrated through the afternoon!",
                'evening': "One last hydration break before wrapping up?"
            }
        }
        
        return templates[context['break_type']][context['time_of_day']]
    
    def generate_break_explanation(self, 
                                 break_type: str,
                                 work_duration: int,
                                 activity_stats: Dict) -> str:
        """
        Generate an explanation for why a break is suggested now.
        
        Args:
            break_type: Type of break suggested
            work_duration: Minutes worked since last break
            activity_stats: Current system activity statistics
        """
        # TODO: Integrate with actual LLM service
        # For now, return template-based explanation
        if work_duration > 60:
            return f"You've been working for over an hour. A {break_type.replace('_', ' ')} could help you stay fresh."
        elif activity_stats.get('cpu_percent', 0) > 70:
            return "I notice high system activity. A quick break might help maintain your productivity."
        else:
            return f"Regular {break_type.replace('_', ' ')}s help maintain your wellbeing."
    
    def generate_alternative_suggestion(self, 
                                     original_break: str,
                                     activity_stats: Dict) -> str:
        """
        Generate an alternative break suggestion if the original is postponed.
        
        Args:
            original_break: The originally suggested break type
            activity_stats: Current system activity statistics
        """
        # TODO: Integrate with actual LLM service
        # For now, return template-based alternative
        alternatives = {
            'walk_break': "How about some desk stretches instead?",
            'stretch_break': "Even a 30-second posture check can help!",
            'eye_break': "Could you at least look away from the screen briefly?",
            'hydration_break': "Even a small sip of water would be good!"
        }
        
        return alternatives.get(original_break, "Consider a micro-break if you can't take a full break.") 