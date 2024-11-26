import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from ResumeUpdateProcessor import ResumeUpdateProcessor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def processor():
    return ResumeUpdateProcessor()

@patch('backend.ResumeUpdateProcessor.SearchClient')
def test_get_project(MockSearchClient, processor):
    mock_search_client = MockSearchClient.return_value
    mock_search_client.search.return_value = [
        {'id': '1', 'project_number': '123', 'document_updated': '2023-01-01', 'content': 'Project 1', 'sourcefile': 'file1', 'sourcepage': 1},
        {'id': '2', 'project_number': '123', 'document_updated': '2023-01-02', 'content': 'Project 2', 'sourcefile': 'file2', 'sourcepage': 2}
    ]
    os.environ['AZURE_SEARCH_ENDPOINT'] = 'https://example.search.windows.net'
    os.environ['AZURE_SEARCH_INDEX_PROJECTS'] = 'projects'
    os.environ['AZURE_SEARCH_KEY'] = 'fake_key'

    result = processor._get_project('123')

    assert len(result) == 2
    assert result[0]['sourcepage'] == 1
    assert result[1]['sourcepage'] == 2
    mock_search_client.search.assert_called_once_with(
        search_text="*",
        filter="project_number eq '123'",
        select="id, project_number, document_updated, content, sourcefile, sourcepage"
    )

@patch('backend.ResumeUpdateProcessor.CosmosDBManager')
def test_store_event(MockCosmosDBManager, processor):
    mock_events_container = MockCosmosDBManager.return_value
    member_entry = {
        'employee_display_name': 'Doe, John - 12345',
        'project_number': '123',
        'subject_area': 'Engineering',
        'project_role_name': 'Developer',
        'job_hours': 10,
        'employee_job_family_function_code': 'ENG'
    }
    mock_events_container.create_item.return_value = {'id': 'event123'}

    result = processor._store_event(member_entry)

    assert result['id'] == 'event123'
    mock_events_container.create_item.assert_called_once()

@patch('backend.ResumeUpdateProcessor.CosmosDBManager')
def test_get_or_create_tracker(MockCosmosDBManager, processor):
    mock_trackers_container = MockCosmosDBManager.return_value
    member_entry = {
        'employee_display_name': 'Doe, John - 12345',
        'project_number': '123',
        'subject_area': 'Engineering',
        'project_role_name': 'Developer',
        'job_hours': 10,
        'employee_job_family_function_code': 'ENG'
    }
    mock_trackers_container.query_items.return_value = []
    mock_trackers_container.create_item.return_value = {'id': 'tracker123'}

    result = processor._get_or_create_tracker(member_entry)

    assert result['id'] == 'tracker123'
    mock_trackers_container.query_items.assert_called_once()
    mock_trackers_container.create_item.assert_called_once()

@patch('backend.ResumeUpdateProcessor.CosmosDBManager')
def test_get_employee_email(MockCosmosDBManager, processor):
    mock_employee_metadata_container = MockCosmosDBManager.return_value
    mock_employee_metadata_container.query_items.return_value = [{'email': 'john.doe@example.com'}]

    result = processor._get_employee_email('12345')

    assert result == 'john.doe@example.com'
    mock_employee_metadata_container.query_items.assert_called_once()

@patch('backend.ResumeUpdateProcessor.CosmosDBManager')
def test_send_notification(MockCosmosDBManager, processor):
    mock_employee_metadata_container = MockCosmosDBManager.return_value
    mock_employee_metadata_container.query_items.return_value = [{'email': 'john.doe@example.com'}]
    processor.webapp_url = 'https://example.com'

    result = processor._send_notification('12345')

    assert result is True

@patch('backend.ResumeUpdateProcessor.CosmosDBManager')
def test_update_notification_record(MockCosmosDBManager, processor):
    mock_notification_container = MockCosmosDBManager.return_value
    mock_notification_container.update_item.return_value = {'id': 'notification-12345'}

    result = processor._update_notification_record('12345')

    assert result['id'] == 'notification-12345'
    mock_notification_container.update_item.assert_called_once()

@patch('backend.ResumeUpdateProcessor.CosmosDBManager')
def test_should_send_notification(MockCosmosDBManager, processor):
    mock_notification_container = MockCosmosDBManager.return_value
    mock_notification_container.query_items.return_value = [{'last_notification': (datetime.utcnow() - timedelta(hours=1)).isoformat()}]
    processor.notification_cooldown = timedelta(hours=2)

    result = processor._should_send_notification('12345')

    assert result is False
    mock_notification_container.query_items.assert_called_once()

@patch('backend.ResumeUpdateProcessor.CosmosDBManager')
def test_store_feedback(MockCosmosDBManager, processor):
    mock_feedback_container = MockCosmosDBManager.return_value
    feedback_data = {
        'employee_id': '12345',
        'type': 'positive',
        'content': 'Great job!'
    }
    mock_feedback_container.create_item.return_value = {'id': 'feedback-20230101-12345'}

    result = processor.store_feedback(feedback_data)

    assert result['id'] == 'feedback-20230101-12345'
    mock_feedback_container.create_item.assert_called_once()