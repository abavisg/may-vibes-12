from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class WellnessScore:
    def __init__(self):
        self.score_weights = {
            'break_compliance': 0.3,  # Taking breaks when suggested
            'work_duration': 0.2,     # Not working excessively long periods
            'activity_balance': 0.2,  # Good balance of active and rest periods
            'schedule_adherence': 0.2, # Following calendar schedule
            'system_usage': 0.1       # Healthy system resource usage
        }
        
        self.score_history = []
        self.current_score = 100  # Start with a perfect score
        
    def calculate_break_compliance_score(self, breaks_taken: int, breaks_suggested: int) -> float:
        """Calculate score based on break compliance"""
        if breaks_suggested == 0:
            return 100
        compliance_rate = min(breaks_taken / breaks_suggested, 1)
        return compliance_rate * 100
    
    def calculate_work_duration_score(self, active_duration: timedelta) -> float:
        """Calculate score based on continuous work duration"""
        optimal_work_duration = timedelta(minutes=45)
        max_work_duration = timedelta(hours=2)
        
        if active_duration <= optimal_work_duration:
            return 100
        elif active_duration >= max_work_duration:
            return 50
        else:
            # Linear decrease between optimal and max duration
            score_reduction = ((active_duration - optimal_work_duration) / 
                             (max_work_duration - optimal_work_duration)) * 50
            return 100 - score_reduction
    
    def calculate_activity_balance_score(self, active_minutes: float, rest_minutes: float) -> float:
        """Calculate score based on activity balance"""
        total_time = active_minutes + rest_minutes
        if total_time == 0:
            return 100
            
        active_ratio = active_minutes / total_time
        optimal_ratio = 0.75  # 75% active time is considered optimal
        
        if active_ratio > optimal_ratio:
            # Penalize overwork
            penalty = (active_ratio - optimal_ratio) * 100
            return max(100 - penalty, 50)
        else:
            # Slight penalty for underwork
            penalty = (optimal_ratio - active_ratio) * 50
            return max(100 - penalty, 50)
    
    def calculate_schedule_adherence_score(self, meetings_attended: int, total_meetings: int) -> float:
        """Calculate score based on calendar schedule adherence"""
        if total_meetings == 0:
            return 100
        adherence_rate = min(meetings_attended / total_meetings, 1)
        return adherence_rate * 100
    
    def calculate_system_usage_score(self, cpu_percent: float, memory_percent: float) -> float:
        """Calculate score based on system resource usage"""
        # High resource usage might indicate inefficient work patterns
        cpu_score = 100 - (max(0, cpu_percent - 70) * 2)  # Penalty above 70% CPU
        memory_score = 100 - (max(0, memory_percent - 80) * 2)  # Penalty above 80% Memory
        return (cpu_score + memory_score) / 2
    
    def update_score(self, metrics: Dict) -> float:
        """
        Update the wellness score based on current metrics
        
        Args:
            metrics: Dictionary containing:
                - breaks_taken: int
                - breaks_suggested: int
                - active_duration: timedelta
                - active_minutes: float
                - rest_minutes: float
                - meetings_attended: int
                - total_meetings: int
                - cpu_percent: float
                - memory_percent: float
        """
        scores = {
            'break_compliance': self.calculate_break_compliance_score(
                metrics['breaks_taken'], metrics['breaks_suggested']
            ),
            'work_duration': self.calculate_work_duration_score(
                metrics['active_duration']
            ),
            'activity_balance': self.calculate_activity_balance_score(
                metrics['active_minutes'], metrics['rest_minutes']
            ),
            'schedule_adherence': self.calculate_schedule_adherence_score(
                metrics['meetings_attended'], metrics['total_meetings']
            ),
            'system_usage': self.calculate_system_usage_score(
                metrics['cpu_percent'], metrics['memory_percent']
            )
        }
        
        # Calculate weighted average
        new_score = sum(scores[metric] * weight 
                       for metric, weight in self.score_weights.items())
        
        # Record history
        self.score_history.append({
            'timestamp': datetime.now().isoformat(),
            'score': new_score,
            'component_scores': scores
        })
        
        # Keep only last 24 hours of history
        cutoff = datetime.now() - timedelta(hours=24)
        self.score_history = [
            entry for entry in self.score_history
            if datetime.fromisoformat(entry['timestamp']) > cutoff
        ]
        
        self.current_score = new_score
        return new_score
    
    def get_score_breakdown(self) -> Dict:
        """Get detailed breakdown of current wellness score"""
        if not self.score_history:
            return {
                'current_score': self.current_score,
                'trend': 'stable',
                'components': {},
                'suggestions': []
            }
            
        latest = self.score_history[-1]
        
        # Calculate trend
        if len(self.score_history) > 1:
            prev_score = self.score_history[-2]['score']
            if latest['score'] > prev_score + 5:
                trend = 'improving'
            elif latest['score'] < prev_score - 5:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        # Generate suggestions based on component scores
        suggestions = []
        components = latest['component_scores']
        
        if components['break_compliance'] < 70:
            suggestions.append("Try to take more regular breaks when suggested")
        if components['work_duration'] < 70:
            suggestions.append("Consider shorter work sessions between breaks")
        if components['activity_balance'] < 70:
            suggestions.append("Aim for a better balance between active work and rest periods")
        if components['schedule_adherence'] < 70:
            suggestions.append("Try to better adhere to your scheduled meetings and breaks")
        if components['system_usage'] < 70:
            suggestions.append("High system resource usage detected - consider closing unused applications")
        
        return {
            'current_score': latest['score'],
            'trend': trend,
            'components': components,
            'suggestions': suggestions
        } 