import logging
import azure.functions as func
import logging
from datetime import datetime
import azure.functions as func
from ResumeUpdateProcessor import ResumeUpdateProcessor

app = func.FunctionApp()

@app.timer_trigger(schedule="0 */5 * * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def timer_trigger(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')
    run_notifications()
    logging.info('Python timer trigger function executed.')



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