#!/usr/bin/env python3
"""
Example script to run the SchedulerAgent for a specified duration
"""

import time
import argparse
import logging
import threading
import os
import sys
from scheduler_agent import SchedulerAgent
from config import Config

# Configure logging to file instead of console when countdown is active
def setup_logging(to_file=False):
    if to_file:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename='scheduler_run.log',
            filemode='w'
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    return logging.getLogger(__name__)

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_countdown(scheduler, stop_event, interval_seconds=300):
    """Display a countdown timer for the next scheduled run"""
    try:
        while not stop_event.is_set():
            clear_screen()
            
            # Get time until next run
            time_info = scheduler.get_time_until_next_run()
            minutes = time_info["minutes"]
            seconds = time_info["seconds"]
            
            # Format interval as minutes:seconds
            interval_mins = int(interval_seconds // 60)
            interval_secs = int(interval_seconds % 60)
            interval_formatted = f"{interval_mins}:{interval_secs:02d}"
            
            # Display header with interval information
            print("\n=== WORK/LIFE BALANCE COACH ===")
            print(f"=== Cycle Interval: {interval_formatted} ===")
            print("================================")
            
            # Display countdown with visual elements based on remaining time
            if minutes > 4:
                countdown_msg = f"⏱️  Next agent cycle in: {minutes:02d}:{seconds:02d}"
                bar = "█" * 10
            elif minutes > 2:
                countdown_msg = f"⏳  Next agent cycle in: {minutes:02d}:{seconds:02d}"
                bar = "█" * 15
            elif minutes > 0:
                countdown_msg = f"🔄  Next agent cycle SOON: {minutes:02d}:{seconds:02d}"
                bar = "█" * 20
            else:
                countdown_msg = f"🚀  Agent cycle imminent: {minutes:02d}:{seconds:02d}"
                bar = "█" * 25
                
            print(f"\n{countdown_msg}")
            print(f"{bar}")
            
            # Display status info from context
            status_info = get_status_from_context(scheduler)
            if status_info:
                print("\n=== CURRENT AGENT STATUS ===")
                for key, value in status_info.items():
                    print(f"{key}: {value}")
            
            # Display instructions
            print("\n=== CONTROLS ===")
            print("Press Ctrl+C to exit")
            
            # Sleep briefly
            time.sleep(0.5)
    except KeyboardInterrupt:
        return
    except Exception as e:
        logger.error(f"Error in countdown display: {e}")
    finally:
        # Clear screen when done
        clear_screen()

def get_status_from_context(scheduler):
    """Get current status information from context"""
    import context_manager as cm
    
    status = {}
    
    # Get focus information
    focus_info = cm.get_context("focus_monitor_agent.state")
    if focus_info:
        status["Focus Level"] = focus_info.get("focus_level", "unknown")
        status["Focus Mode"] = focus_info.get("focus_mode", "unknown")
    
    # Get suggestion information
    suggestion = cm.get_context("nudge_agent.current_suggestion")
    if suggestion:
        status["Current Suggestion"] = f"{suggestion.get('type', 'unknown')} ({suggestion.get('duration', 0)} min)"
        status["Suggestion Reason"] = suggestion.get("reason", "unknown")
    
    # Get run information
    scheduler_info = cm.get_context("scheduler_agent.state")
    if scheduler_info:
        status["Completed Cycles"] = scheduler_info.get("runs_completed", 0)
    
    return status

def main():
    parser = argparse.ArgumentParser(description='Run the SchedulerAgent for a specified duration')
    parser.add_argument('--duration', type=int, default=60,
                      help='Duration to run the scheduler in seconds (default: 60)')
    parser.add_argument('--interval', type=int, default=None,
                      help=f'Time between agent cycles in seconds (default: {Config.SCHEDULER_FREQUENCY} seconds)')
    parser.add_argument('--no-countdown', action='store_true',
                      help='Disable the countdown display')
    args = parser.parse_args()
    
    # Set default interval from config if not specified
    interval_seconds = args.interval if args.interval is not None else Config.SCHEDULER_FREQUENCY
    # Convert to minutes for display
    interval_minutes = interval_seconds / 60
    
    # Configure logging based on display mode
    global logger
    logger = setup_logging(not args.no_countdown)
    
    logger.info(f"Starting scheduler for {args.duration} seconds with {interval_seconds} seconds interval ({interval_minutes:.1f} minutes)")
    
    try:
        # Create the scheduler agent with specified interval
        scheduler = SchedulerAgent()
        
        # Override the default interval if requested
        if args.interval is not None:
            import schedule
            schedule.clear()
            # Convert seconds to minutes for schedule package
            schedule_interval = interval_seconds / 60
            schedule.every(schedule_interval).minutes.do(scheduler.scheduled_run)
            
            # Update the next run time in the scheduler
            scheduler.next_run_at = time.time() + interval_seconds
        
        # Start scheduler in a thread
        scheduler_thread = threading.Thread(target=scheduler.start)
        scheduler_thread.daemon = True  # Allow the main thread to exit even if scheduler is running
        scheduler_thread.start()
        
        # Create a stop event for the countdown thread
        countdown_stop = threading.Event()
        
        # If not disabled, start the countdown display in a separate thread
        countdown_thread = None
        if not args.no_countdown:
            # Give a brief moment for the scheduler to initialize
            time.sleep(0.5)
            countdown_thread = threading.Thread(target=display_countdown, 
                                               args=(scheduler, countdown_stop, interval_seconds))
            countdown_thread.daemon = True
            countdown_thread.start()
        
        # Log info about the run
        logger.info(f"Scheduler will run for {args.duration} seconds")
        
        # If duration is short, run the agent immediately once
        if args.duration < interval_seconds:
            logger.info("Duration is shorter than interval, running agent once")
            scheduler.scheduled_run()
        
        # Sleep until the duration expires
        time.sleep(args.duration)
        
        # Shut down
        logger.info("Time's up! Stopping scheduler...")
        
        # Stop the countdown display
        if countdown_thread:
            countdown_stop.set()
            countdown_thread.join(timeout=1)
        
        # Stop the scheduler
        scheduler.stop()
        
        # Wait for thread to finish
        scheduler_thread.join(timeout=2)
        logger.info("Scheduler stopped")
        
    except KeyboardInterrupt:
        logger.info("\nKeyboard interrupt received, stopping scheduler...")
        
        # Stop the countdown display if it's running
        if 'countdown_stop' in locals() and 'countdown_thread' in locals() and countdown_thread:
            countdown_stop.set()
            countdown_thread.join(timeout=1)
            
        # Stop the scheduler
        if 'scheduler' in locals():
            scheduler.stop()
            
        logger.info("Scheduler stopped")
    
    logger.info("Example completed")

if __name__ == "__main__":
    main() 