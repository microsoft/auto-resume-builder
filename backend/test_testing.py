import pytest
from unittest.mock import patch, MagicMock
from testing import create_employee_metadata, processor

@pytest.fixture
def mock_processor():
    with patch('..testing.processor', autospec=True) as mock_processor:
        yield mock_processor

@patch('..testing.load_json_file')
def test_create_employee_metadata_success(mock_load_json_file, mock_processor):
    # Arrange
    sample_metadata = {
        "id": "metadata-99999",
        "employee_display_name": "Test Employee",
        "project_number": "12345",
        "total_hours": 0
    }
    mock_load_json_file.return_value = sample_metadata
    mock_processor.employee_metadata_container.create_item.return_value = None

    # Act
    create_employee_metadata()

    # Assert
    mock_load_json_file.assert_called_once_with('employee_metadata', 'metadata_1.json')
    mock_processor.employee_metadata_container.create_item.assert_called_once_with(sample_metadata)
    print("Test passed: create_item called with correct metadata")

@patch('..testing.load_json_file')
def test_create_employee_metadata_already_exists(mock_load_json_file, mock_processor):
    # Arrange
    sample_metadata = {
        "id": "metadata-99999",
        "employee_display_name": "Test Employee",
        "project_number": "12345",
        "total_hours": 0
    }
    mock_load_json_file.return_value = sample_metadata
    mock_processor.employee_metadata_container.create_item.side_effect = Exception("Employee metadata already exists")

    # Act
    create_employee_metadata()

    # Assert
    mock_load_json_file.assert_called_once_with('employee_metadata', 'metadata_1.json')
    mock_processor.employee_metadata_container.create_item.assert_called_once_with(sample_metadata)
    print("Test passed: handled existing metadata exception")