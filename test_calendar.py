from calendar_integration import CalendarService
from datetime import datetime, timedelta
import pytz
from config import Config

def test_calendar_integration():
    # Initialize calendar service using config
    calendar = CalendarService()  # Will use Config.USE_CALENDAR_INTEGRATION
    
    # Print configuration
    print("\nConfiguration:")
    print(f"Using Calendar Integration: {Config.USE_CALENDAR_INTEGRATION}")
    print(f"Calendar ID: {Config.GOOGLE_CALENDAR_ID}")
    print(f"Timezone: {Config.TIMEZONE}")
    
    # Get user's calendar email
    email = calendar.get_calendar_email()
    print(f"\nCalendar Email: {email}")
    
    # Get today's events
    print("\nToday's Events:")
    today_events = calendar.get_day_events()
    for event in today_events:
        print(f"- {event['summary']}")
        print(f"  Start: {event['start_time']}")
        print(f"  End: {event['end_time']}")
        if event.get('attendees'):
            print(f"  Attendees: {', '.join(event['attendees'])}")
        if event.get('location'):
            print(f"  Location: {event['location']}")
    
    # Check upcoming events
    print("\nUpcoming Events (next 2 hours):")
    upcoming = calendar.get_upcoming_events(minutes_ahead=120)
    for event in upcoming:
        print(f"- {event['summary']}")
        print(f"  Start: {event['start_time']}")
    
    # Check free slots
    print("\nFree Time Slots:")
    next_free = calendar.get_next_free_slot(min_duration=30)
    if next_free:
        print(f"Next free slot (30+ mins): {next_free}")
    
    # Get busy times for tomorrow
    local_tz = pytz.timezone(Config.TIMEZONE)
    tomorrow = datetime.now(local_tz) + timedelta(days=1)
    tomorrow_start = tomorrow.replace(
        hour=int(Config.DEFAULT_WORK_START_TIME.split(':')[0]),
        minute=int(Config.DEFAULT_WORK_START_TIME.split(':')[1]),
        second=0,
        microsecond=0
    )
    tomorrow_end = tomorrow.replace(
        hour=int(Config.DEFAULT_WORK_END_TIME.split(':')[0]),
        minute=int(Config.DEFAULT_WORK_END_TIME.split(':')[1]),
        second=0,
        microsecond=0
    )
    
    print(f"\nBusy times tomorrow ({Config.DEFAULT_WORK_START_TIME} - {Config.DEFAULT_WORK_END_TIME}):")
    busy_slots = calendar.get_busy_times(tomorrow_start, tomorrow_end)
    for start, end in busy_slots:
        print(f"- Busy from {start.strftime('%H:%M')} to {end.strftime('%H:%M')}")

if __name__ == "__main__":
    test_calendar_integration() 