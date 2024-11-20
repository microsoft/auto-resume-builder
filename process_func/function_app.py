"""
This module is the main entry point for the Azure Function app. 
It contains the function that is triggered by a new blob being uploaded to the storage account. 
The function reads the blob content, processes it using the ResumeUpdateProcessor class, 
and prints the result. 
It also checks the status of the tracker for the employee and project mentioned in the blob data.
"""
import logging
from pprint import pprint
import json
import azure.functions as func
from ResumeUpdateProcessor import ResumeUpdateProcessor

# Create single processor instance to be used across all tests
processor = ResumeUpdateProcessor()

app = func.FunctionApp()

@app.blob_trigger(arg_name="myblob", path="cdmsmithcodewith",
                               connection="cdmsmithcodewith8e65_STORAGE")
def auto_resume_blob_trigger(myblob: func.InputStream):

    if myblob is not None:
    # Read file content from blob storage
        blob_content = myblob.read()
    # Assuming the blob content is JSON, parse it
        blob_data = json.loads(blob_content)
        result1 = processor.process_key_member(blob_data)

        # Print the result

        # You don't need to print the result in production, but it's useful for debugging
        print(f"Result: {result1}")
        print("\nChecking tracker status...")
        view_tracker_status(f"{blob_data['project_number']}-{blob_data['employee_display_name'].split()[-1]}")
    
        logging.info("Python blob trigger function processed blob Name: %s Blob Size: %d bytes", myblob.name, myblob.length)

def view_tracker_status(tracker_id: str, detailed=False):
    """Helper function to view current tracker status"""
    results = processor.trackers_container.query_items(
        query="SELECT * FROM c WHERE c.id = @id",
        parameters=[{"name": "@id", "value": tracker_id}],
        partition_key="resumeupdatestatus"
    )
    
    if results:
        tracker = results[0]
        if detailed:
            print("\nDetailed Tracker Information:")
            pprint(tracker)
        else:
            print(f"""
            Current Tracker Status:
            - Employee: {tracker['employee_display_name']}
            - Project: {tracker['project_number']}
            - Total Hours: {tracker['total_hours']}
            - Added to Resume: {tracker['added_to_resume']}
            - Description: {tracker.get('description', 'Not generated yet')}
            - Current Role: {tracker['role_history'][-1]['role_name']}
            - Version: {tracker['version']}
            """)
        return tracker
    return None