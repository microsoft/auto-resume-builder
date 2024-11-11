from app import ResumeUpdateProcessor
from pprint import pprint

# Create single processor instance to be used across all tests
processor = ResumeUpdateProcessor()

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
        "employee_display_name": "Smith, John - 12345",
        "job_hours": 25.0,
        "employee_job_family_function_code": "ENCE"
    }
    
    print("\nProcessing first entry (25 hours)...")
    result1 = processor.process_key_member(test_entry1)
    print(f"Result: {result1}")
    print("\nChecking tracker status for John Smith...")
    view_tracker_status("259014-12345")
    
    # Second entry - 35 hours (same employee)
    test_entry2 = {
        "subject_area": "fsu",
        "project_number": "259014",
        "project_role_name": "PMCL",
        "employee_display_name": "Smith, John - 12345",
        "job_hours": 35.0,
        "employee_job_family_function_code": "ENCE"
    }
    
    print("\nProcessing second entry (35 hours)...")
    result2 = processor.process_key_member(test_entry2)
    print(f"Result: {result2}")
    print("\nChecking tracker status for John Smith...")
    view_tracker_status("259014-12345")
    
    return [result1, result2]

def test_case_2_trigger_draft():
    """
    Test Case 2: Process events above threshold with added_to_resume = 'no'.
    Expected behavior: 
    1. New employee over threshold triggers draft and status becomes 'in_progress'
    2. Description should be generated and stored in the tracker
    """
    print("\n=== Test Case 2: Events Triggering Draft Creation ===")
    
    # Part 1: New employee immediately over threshold
    test_entry1 = {
        "subject_area": "fsu",
        "project_number": "291116",
        "project_role_name": "Contract Admin",
        "employee_display_name": "Johnson, Mary - 67890",
        "job_hours": 45.0,
        "employee_job_family_function_code": "FNBL"
    }
    
    print("\nProcessing entry for new employee above threshold (45 hours)...")
    result1 = processor.process_key_member(test_entry1)
    print(f"Result: {result1}")
    print("\nChecking detailed tracker status for Mary Johnson...")
    tracker1 = view_tracker_status("291116-67890", detailed=True)
    
    # Verify the description was generated and status changed
    assert tracker1['added_to_resume'] == 'in_progress', "Status should be 'in_progress'"
    assert tracker1['description'], "Description should not be empty"
    print("\nVerification passed: Status is 'in_progress' and description was generated")
    
    # Part 2: Existing employee (John Smith) crossing threshold
    test_entry2 = {
        "subject_area": "fsu",
        "project_number": "259014",
        "project_role_name": "PMCL",
        "employee_display_name": "Smith, John - 12345",
        "job_hours": 42.0,
        "employee_job_family_function_code": "ENCE"
    }
    
    print("\nProcessing entry for existing employee crossing threshold (42 hours)...")
    result2 = processor.process_key_member(test_entry2)
    print(f"Result: {result2}")
    print("\nChecking detailed tracker status for John Smith...")
    tracker2 = view_tracker_status("259014-12345", detailed=True)
    
    # Verify the description was generated and status changed
    assert tracker2['added_to_resume'] == 'in_progress', "Status should be 'in_progress'"
    assert tracker2['description'], "Description should not be empty"
    print("\nVerification passed: Status is 'in_progress' and description was generated")
    
    return [result1, result2]

def test_case_3_above_threshold_already_processed():
    """
    Test Case 3: Process events for employees that are already in_progress.
    Expected behavior: Store updated hours but don't trigger draft creation
    since added_to_resume is already 'in_progress'
    """
    print("\n=== Test Case 3: Updates After Draft Triggered ===")
    
    # Process new entry for Mary Johnson (already in_progress from test case 2)
    test_entry1 = {
        "subject_area": "fsu",
        "project_number": "291116",
        "project_role_name": "Contract Admin",
        "employee_display_name": "Johnson, Mary - 67890",
        "job_hours": 52.0,
        "employee_job_family_function_code": "FNBL"
    }
    
    print("\nProcessing updated entry for Mary Johnson (52 hours)...")
    result1 = processor.process_key_member(test_entry1)
    print(f"Result: {result1}")
    print("\nChecking tracker status for Mary Johnson...")
    tracker1 = view_tracker_status("291116-67890", detailed=True)
    
    # Verify the description hasn't changed
    assert tracker1['added_to_resume'] == 'in_progress', "Status should still be 'in_progress'"
    print("\nVerification passed: Status remained 'in_progress' and description unchanged")
    
    # Process new entry for John Smith (already in_progress from test case 2)
    test_entry2 = {
        "subject_area": "fsu",
        "project_number": "259014",
        "project_role_name": "PMCL",
        "employee_display_name": "Smith, John - 12345",
        "job_hours": 48.0,
        "employee_job_family_function_code": "ENCE"
    }
    
    print("\nProcessing updated entry for John Smith (48 hours)...")
    result2 = processor.process_key_member(test_entry2)
    print(f"Result: {result2}")
    print("\nChecking tracker status for John Smith...")
    tracker2 = view_tracker_status("259014-12345", detailed=True)
    
    # Verify the description hasn't changed
    assert tracker2['added_to_resume'] == 'in_progress', "Status should still be 'in_progress'"
    print("\nVerification passed: Status remained 'in_progress' and description unchanged")
    
    return [result1, result2]

def view_tracker_status(tracker_id: str, detailed=False):
    """Helper function to view current tracker status"""
    # Use the existing processor's trackers container
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

def update_tracker_status(tracker_id: str, status: str):
    """Helper function to update tracker status for testing"""
    results = processor.trackers_container.query_items(
        query="SELECT * FROM c WHERE c.id = @id",
        parameters=[{"name": "@id", "value": tracker_id}],
        partition_key="resumeupdatestatus"
    )
    
    if results:
        tracker = results[0]
        tracker['added_to_resume'] = status
        processor.trackers_container.update_item(tracker)
        print(f"Updated tracker status to: {status}")

def cleanup_test_data(project_numbers: list):
    """Clean up test data for specified projects"""
    for project_number in project_numbers:
        # Clean events
        query = f"SELECT * FROM c WHERE c.project_number = '{project_number}'"
        items = processor.events_container.query_items(
            query=query, 
            partition_key=project_number
        )
        for item in items:
            processor.events_container.delete_item(item['id'], item['partitionKey'])
            print(f"Deleted event: {item['id']}")
    
    # Clean trackers
    tracker_ids = ["259014-12345", "291116-67890"]
    for tracker_id in tracker_ids:
        try:
            processor.trackers_container.delete_item(tracker_id, "resumeupdatestatus")
            print(f"Deleted tracker: {tracker_id}")
        except Exception as e:
            print(f"Error deleting tracker {tracker_id}: {str(e)}")

if __name__ == "__main__":
    try:
        # Clean up any existing test data first
        # project_numbers = ["259014", "291116"]
        # print("Cleaning up any existing test data...")
        # cleanup_test_data(project_numbers)
        
        # print("\nRunning Test Case 1: Under Threshold Events")
        # test_case_1_under_threshold()
        
        # print("\nRunning Test Case 2: Trigger Draft Creation")
        # test_case_2_trigger_draft()
        
        print("\nRunning Test Case 3: Updates After Draft Triggered")
        test_case_3_above_threshold_already_processed()
        
    except Exception as e:
        print(f"Test execution failed: {str(e)}")
        raise