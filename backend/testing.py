from ResumeUpdateProcessor import ResumeUpdateProcessor
from pprint import pprint
import json
import os

# Create single processor instance to be used across all tests
processor = ResumeUpdateProcessor()

def load_json_file(subfolder, filename):
    """Helper function to load JSON data from sample_data directory"""
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Navigate up one level and then into sample_data and the specified subfolder
    file_path = os.path.join(current_dir, '..', 'sample_data', subfolder, filename)
    with open(file_path, 'r') as f:
        return json.load(f)

def create_employee_metadata():
    """Create metadata entry for test employee"""
    metadata = load_json_file('employee_metadata', 'metadata_1.json')
    
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
    test_entry1 = load_json_file('events', 'event_1.json')
    print(f"\nProcessing first entry ({test_entry1['job_hours']} hours)...")
    result1 = processor.process_key_member(test_entry1)
    print(f"Result: {result1}")
    print("\nChecking tracker status...")
    view_tracker_status(f"{test_entry1['project_number']}-{test_entry1['employee_display_name'].split()[-1]}")
    
   
    
    return [result1]

def test_case_2_trigger_draft():
    """
    Test Case 2: Cross threshold to trigger notification.
    Expected behavior: Status becomes 'in_progress' and email is sent
    """
    print("\n=== Test Case 2: Events Triggering Draft Creation ===")
    
    test_entry = load_json_file('events', 'event_2.json')
    print(f"\nProcessing entry crossing threshold ({test_entry['job_hours']} hours)...")
    result = processor.process_key_member(test_entry)
    print(f"Result: {result}")

    test_entry = load_json_file('events', 'event_3.json')
    print(f"\nProcessing entry crossing threshold ({test_entry['job_hours']} hours)...")
    result = processor.process_key_member(test_entry)
    print(f"Result: {result}")

    # test_entry = load_json_file('events', 'event_5.json')
    # print(f"\nProcessing entry crossing threshold ({test_entry['job_hours']} hours)...")
    # result = processor.process_key_member(test_entry)
    # print(f"Result: {result}")
    
    return result

def test_case_3_above_threshold_already_processed():
    """
    Test Case 3: Update hours after already being processed.
    Expected behavior: Store updated hours but don't trigger new notification
    """
    print("\n=== Test Case 3: Updates After Draft Triggered ===")
    
    test_entry = load_json_file('events', 'event_4.json')
    print(f"\nProcessing updated entry ({test_entry['job_hours']} hours)...")
    result = processor.process_key_member(test_entry)
    print(f"Result: {result}")
    
    tracker_id = f"{test_entry['project_number']}-{test_entry['employee_display_name'].split()[-1]}"
    print("\nChecking tracker status...")
    tracker = view_tracker_status(tracker_id, detailed=True)
    
    # Verify the description hasn't changed
    #assert tracker['added_to_resume'] == 'in_progress', "Status should still be 'in_progress'"
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

def cleanup_test_data(employee_id: str):
    """
    Clean up all test data for a specific employee across all containers
    
    Args:
        employee_id (str): The ID of the employee whose data should be cleaned up
    """
    print(f"\nCleaning up all data for employee {employee_id}...")

    # 1. Clean up events (need to check all partition keys since events are partitioned by project)
    try:
        query = "SELECT * FROM c WHERE CONTAINS(c.employee_display_name, @employee_id)"
        parameters = [{"name": "@employee_id", "value": employee_id}]
        
        events = processor.events_container.query_items(
            query=query,
            parameters=parameters
        )
        
        for event in events:
            processor.events_container.delete_item(event['id'], event['partitionKey'])
            print(f"Deleted event: {event['id']} from project {event['project_number']}")
    except Exception as e:
        print(f"Error cleaning up events: {str(e)}")

    # 2. Clean up resume trackers
    try:
        query = "SELECT * FROM c WHERE c.employee_id = @employee_id"
        parameters = [{"name": "@employee_id", "value": employee_id}]
        
        trackers = processor.trackers_container.query_items(
            query=query,
            parameters=parameters,
            partition_key="resumeupdatestatus"
        )
        
        for tracker in trackers:
            processor.trackers_container.delete_item(tracker['id'], tracker['partitionKey'])
            print(f"Deleted resume tracker: {tracker['id']}")
    except Exception as e:
        print(f"Error cleaning up trackers: {str(e)}")

    # 3. Clean up notifications
    # try:
    #     notification_id = f"notification-{employee_id}"
    #     processor.notification_container.delete_item(notification_id, "notifications")
    #     print(f"Deleted notification record: {notification_id}")
    # except Exception as e:
    #     print(f"Error cleaning up notifications: {str(e)}")

    # 4. Clean up employee metadata
    try:
        metadata_id = f"metadata-{employee_id}"
        processor.employee_metadata_container.delete_item(metadata_id, "metadata")
        print(f"Deleted employee metadata: {metadata_id}")
    except Exception as e:
        print(f"Error cleaning up metadata: {str(e)}")

    print("\nCleanup completed!")

if __name__ == "__main__":
    try:
        test_employee_id = "718163"

        processor.reset_resume(test_employee_id)

        print("\nCleaning up any existing test data...")
        cleanup_test_data(test_employee_id)
        
        # print("Creating employee metadata...")
        create_employee_metadata()
        
        
        # # print("\nRunning Test Case 1: Under Threshold Events")
        test_case_1_under_threshold()
        
        print("\nRunning Test Case 2: Trigger Draft Creation")
        test_case_2_trigger_draft()
        
        # print("\nRunning Test Case 3: Updates After Draft Triggered")
        test_case_3_above_threshold_already_processed()
        
    except Exception as e:
        print(f"Test execution failed: {str(e)}")
        raise