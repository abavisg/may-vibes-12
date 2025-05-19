import unittest
from datetime import datetime
import pytz
from user_preferences import UserPreferences
from config import Config

class TestBreakSuggestions(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        self.preferences = UserPreferences()
        self.london_tz = Config.get_timezone()
    
    def tearDown(self):
        """Clean up after each test."""
        UserPreferences.clear_mocked_time()
    
    def test_morning_break_suggestions(self):
        """Test break suggestions during morning hours (8-11)."""
        # Mock time to 9:30 AM
        mock_time = datetime.now(self.london_tz).replace(hour=9, minute=30)
        UserPreferences.set_mocked_time(mock_time)
        
        # Test multiple suggestions to ensure eye breaks are favored
        eye_break_count = 0
        total_tests = 100
        
        for _ in range(total_tests):
            break_type = self.preferences.get_optimal_break_type()
            if break_type == 'eye_break':
                eye_break_count += 1
        
        # Eye breaks should be suggested more often in the morning
        self.assertGreater(eye_break_count / total_tests, 0.3)  # At least 30% eye breaks
    
    def test_afternoon_break_suggestions(self):
        """Test break suggestions during afternoon hours (14-17)."""
        # Mock time to 3:30 PM
        mock_time = datetime.now(self.london_tz).replace(hour=15, minute=30)
        UserPreferences.set_mocked_time(mock_time)
        
        # Test multiple suggestions to ensure walk breaks are favored
        walk_break_count = 0
        total_tests = 100
        
        for _ in range(total_tests):
            break_type = self.preferences.get_optimal_break_type()
            if break_type == 'walk_break':
                walk_break_count += 1
        
        # Walk breaks should be suggested more often in the afternoon
        self.assertGreater(walk_break_count / total_tests, 0.3)  # At least 30% walk breaks
    
    def test_high_activity_break_suggestions(self):
        """Test break suggestions during high activity periods."""
        mock_time = datetime.now(self.london_tz).replace(hour=14, minute=0)
        UserPreferences.set_mocked_time(mock_time)
        
        # Test with high activity level
        active_breaks = set()
        total_tests = 100
        
        for _ in range(total_tests):
            break_type = self.preferences.get_optimal_break_type(activity_level=0.8)
            active_breaks.add(break_type)
        
        # Should see both walk and stretch breaks frequently
        self.assertIn('walk_break', active_breaks)
        self.assertIn('stretch_break', active_breaks)
    
    def test_low_activity_break_suggestions(self):
        """Test break suggestions during low activity periods."""
        mock_time = datetime.now(self.london_tz).replace(hour=11, minute=0)
        UserPreferences.set_mocked_time(mock_time)
        
        # Test with low activity level
        sedentary_breaks = set()
        total_tests = 100
        
        for _ in range(total_tests):
            break_type = self.preferences.get_optimal_break_type(activity_level=0.2)
            sedentary_breaks.add(break_type)
        
        # Should see both eye and hydration breaks frequently
        self.assertIn('eye_break', sedentary_breaks)
        self.assertIn('hydration_break', sedentary_breaks)

if __name__ == '__main__':
    unittest.main() 