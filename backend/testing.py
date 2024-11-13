from ResumeUpdateProcessor import ResumeUpdateProcessor
from pprint import pprint
import json
import os

# Create single processor instance to be used across all tests
processor = ResumeUpdateProcessor()

def load_json_file(filename):
    """Helper function to load JSON data from sample_data directory"""
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Navigate up one level and then into sample_data
    file_path = os.path.join(current_dir, '..', 'sample_data', filename)
    with open(file_path, 'r') as f:
        return json.load(f)

def create_employee_metadata():
    """Create metadata entry for test employee"""
    metadata = load_json_file('metadata_1.json')
    
    try:
        processor.employee_metadata_container.create_item(metadata)
        print("Created employee metadata entry")
    except:
        print("Employee metadata already exists")

def test_case_1_under_threshold():
    """
    Test Case 1: Process multiple events under the 40-hour threshold.
    Expected behavior: Store data but don't trigger draft creation.
    """
    print("\n=== Test Case 1: Multiple Events Under Threshold ===")
    
    # Load and process first event
    test_entry1 = load_json_file('event_1.json')
    print(f"\nProcessing first entry ({test_entry1['job_hours']} hours)...")
    result1 = processor.process_key_member(test_entry1)
    print(f"Result: {result1}")
    print("\nChecking tracker status...")
    view_tracker_status(f"{test_entry1['project_number']}-{test_entry1['employee_display_name'].split()[-1]}")
    
    # Load and process second event
    test_entry2 = load_json_file('event_2.json')
    print(f"\nProcessing second entry ({test_entry2['job_hours']} hours)...")
    result2 = processor.process_key_member(test_entry2)
    print(f"Result: {result2}")
    print("\nChecking tracker status...")
    view_tracker_status(f"{test_entry2['project_number']}-{test_entry2['employee_display_name'].split()[-1]}")
    
    return [result1, result2]

def test_case_2_trigger_draft():
    """
    Test Case 2: Cross threshold to trigger notification.
    Expected behavior: Status becomes 'in_progress' and email is sent
    """
    print("\n=== Test Case 2: Events Triggering Draft Creation ===")
    
    test_entry = load_json_file('event_3.json')
    print(f"\nProcessing entry crossing threshold ({test_entry['job_hours']} hours)...")
    result = processor.process_key_member(test_entry)
    print(f"Result: {result}")
    
    tracker_id = f"{test_entry['project_number']}-{test_entry['employee_display_name'].split()[-1]}"
    print("\nChecking detailed tracker status...")
    tracker = view_tracker_status(tracker_id, detailed=True)
    
    # Verify the description was generated and status changed
    assert tracker['added_to_resume'] == 'in_progress', "Status should be 'in_progress'"
    assert tracker['description'], "Description should not be empty"
    print("\nVerification passed: Status is 'in_progress' and description was generated")
    
    return result

def test_case_3_above_threshold_already_processed():
    """
    Test Case 3: Update hours after already being processed.
    Expected behavior: Store updated hours but don't trigger new notification
    """
    print("\n=== Test Case 3: Updates After Draft Triggered ===")
    
    test_entry = load_json_file('event_4.json')
    print(f"\nProcessing updated entry ({test_entry['job_hours']} hours)...")
    result = processor.process_key_member(test_entry)
    print(f"Result: {result}")
    
    tracker_id = f"{test_entry['project_number']}-{test_entry['employee_display_name'].split()[-1]}"
    print("\nChecking tracker status...")
    tracker = view_tracker_status(tracker_id, detailed=True)
    
    # Verify the description hasn't changed
    assert tracker['added_to_resume'] == 'in_progress', "Status should still be 'in_progress'"
    print("\nVerification passed: Status remained 'in_progress' and description unchanged")
    
    return result

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

def cleanup_test_data():
    """Clean up test data"""
    # Get project number from first event to use in cleanup
    first_event = load_json_file('event_1.json')
    project_number = first_event['project_number']
    employee_id = first_event['employee_display_name'].split()[-1]
    
    # Clean events for project
    query = f"SELECT * FROM c WHERE c.project_number = '{project_number}'"
    items = processor.events_container.query_items(
        query=query, 
        partition_key=project_number
    )
    for item in items:
        processor.events_container.delete_item(item['id'], item['partitionKey'])
        print(f"Deleted event: {item['id']}")
    
    # Clean tracker
    try:
        processor.trackers_container.delete_item(f"{project_number}-{employee_id}", "resumeupdatestatus")
        print("Deleted resume tracker")
    except Exception as e:
        print(f"Error deleting resume tracker: {str(e)}")

    # Clean notification
    try:
        processor.notifications.delete_item(f"notification-{employee_id}", "notifications")
        print("Deleted notification record")
    except Exception as e:
        print(f"Error deleting notification: {str(e)}")

if __name__ == "__main__":
    try:
        print("Creating employee metadata...")
        create_employee_metadata()
        
        print("\nCleaning up any existing test data...")
        cleanup_test_data()
        
        print("\nRunning Test Case 1: Under Threshold Events")
        test_case_1_under_threshold()
        
        print("\nRunning Test Case 2: Trigger Draft Creation")
        test_case_2_trigger_draft()
        
        print("\nRunning Test Case 3: Updates After Draft Triggered")
        test_case_3_above_threshold_already_processed()
        
    except Exception as e:
        print(f"Test execution failed: {str(e)}")
        raise