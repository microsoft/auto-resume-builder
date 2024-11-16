# notification_runner.py
import logging
from datetime import datetime
from ResumeUpdateProcessor import ResumeUpdateProcessor



def run_notifications():
    """
    Execute the recurring notification process.
    This function can be scheduled to run periodically.
    """
    try:
        print("Starting notification runner")
        processor = ResumeUpdateProcessor()
        
        # Run the recurring notification process
        result = processor.recurring_notification()
        
        # Log the results
        print("Notification process completed")
        print(f"Total employees processed: {result['total_employees_processed']}")
        print(f"Notifications sent: {result['notifications_sent']}")
        print(f"Skipped (cooldown): {result['skipped_cooldown']}")
        print(f"Errors: {result['errors']}")
        
    except Exception as e:
        print(f"Error in notification runner: {str(e)}")
        raise

if __name__ == "__main__":
    run_notifications()