import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from ResumeUpdateProcessor import ResumeUpdateProcessor

# FILE: backend/test_ResumeUpdateProcessor.py

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def processor():
    return ResumeUpdateProcessor()

@patch('backend.ResumeUpdateProcessor.SearchClient')
def test_get_project(MockSearchClient, processor):
    # Arrange
    mock_search_client = MockSearchClient.return_value
    mock_search_client.search.return_value = [
        {'id': '1', 'project_number': '123', 'document_updated': '2023-01-01', 'content': 'Project 1', 'sourcefile': 'file1', 'sourcepage': 1},
        {'id': '2', 'project_number': '123', 'document_updated': '2023-01-02', 'content': 'Project 2', 'sourcefile': 'file2', 'sourcepage': 2}
    ]
    os.environ['AZURE_SEARCH_ENDPOINT'] = 'https://example.search.windows.net'
    os.environ['AZURE_SEARCH_INDEX_PROJECTS'] = 'projects'
    os.environ['AZURE_SEARCH_KEY'] = 'fake_key'

    # Act
    result = processor._get_project('123')

    # Assert
    assert len(result) == 2
    assert result[0]['sourcepage'] == 1
    assert result[1]['sourcepage'] == 2
    mock_search_client.search.assert_called_once_with(
        search_text="*",
        filter="project_number eq '123'",
        select="id, project_number, document_updated, content, sourcefile, sourcepage"
    )