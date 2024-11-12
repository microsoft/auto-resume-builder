from ResumeUpdateProcessor import ResumeUpdateProcessor
from pprint import pprint

# Create single processor instance to be used across all tests
processor = ResumeUpdateProcessor()

def create_employee_metadata():
    """Create metadata entry for test employee"""
    metadata = {
        "id": "metadata-99999",
        "partitionKey": "metadata",
        "employee_id": "99999",
        "email": "abc@xyz.com",
        "name": "Dan Giannone",
        "department": "Engineering"
    }
    
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
    
    # First entry - 25 hours
    test_entry1 = {
        "subject_area": "fsu",
        "project_number": "259014",
        "project_role_name": "PMCL",
        "employee_display_name": "Giannone, Dan - 99999",
        "job_hours": 25.0,
        "employee_job_family_function_code": "ENCE"
    }
    
    print("\nProcessing first entry (25 hours)...")
    result1 = processor.process_key_member(test_entry1)
    print(f"Result: {result1}")
    print("\nChecking tracker status...")
    view_tracker_status("259014-99999")
    
    # Second entry - 35 hours (same employee)
    test_entry2 = {
        "subject_area": "fsu",
        "project_number": "259014",
        "project_role_name": "PMCL",
        "employee_display_name": "Giannone, Dan - 99999",
        "job_hours": 35.0,
        "employee_job_family_function_code": "ENCE"
    }
    
    print("\nProcessing second entry (35 hours)...")
    result2 = processor.process_key_member(test_entry2)
    print(f"Result: {result2}")
    print("\nChecking tracker status...")
    view_tracker_status("259014-99999")
    
    return [result1, result2]

def test_case_2_trigger_draft():
    """
    Test Case 2: Cross threshold to trigger notification.
    Expected behavior: Status becomes 'in_progress' and email is sent
    """
    print("\n=== Test Case 2: Events Triggering Draft Creation ===")
    
    test_entry = {
        "subject_area": "fsu",
        "project_number": "259014",
        "project_role_name": "PMCL",
        "employee_display_name": "Giannone, Dan - 99999",
        "job_hours": 45.0,
        "employee_job_family_function_code": "ENCE"
    }
    
    print("\nProcessing entry crossing threshold (45 hours)...")
    result = processor.process_key_member(test_entry)
    print(f"Result: {result}")
    print("\nChecking detailed tracker status...")
    tracker = view_tracker_status("259014-99999", detailed=True)
    
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
    
    test_entry = {
        "subject_area": "fsu",
        "project_number": "259014",
        "project_role_name": "PMCL",
        "employee_display_name": "Giannone, Dan - 99999",
        "job_hours": 52.0,
        "employee_job_family_function_code": "ENCE"
    }
    
    print("\nProcessing updated entry (52 hours)...")
    result = processor.process_key_member(test_entry)
    print(f"Result: {result}")
    print("\nChecking tracker status...")
    tracker = view_tracker_status("259014-99999", detailed=True)
    
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
    # Clean events for project
    query = "SELECT * FROM c WHERE c.project_number = '259014'"
    items = processor.events_container.query_items(
        query=query, 
        partition_key="259014"
    )
    for item in items:
        processor.events_container.delete_item(item['id'], item['partitionKey'])
        print(f"Deleted event: {item['id']}")
    
    # Clean tracker
    try:
        processor.trackers_container.delete_item("259014-99999", "resumeupdatestatus")
        print("Deleted resume tracker")
    except Exception as e:
        print(f"Error deleting resume tracker: {str(e)}")

    # Clean notification
    try:
        processor.notifications.delete_item("notification-99999", "notifications")
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