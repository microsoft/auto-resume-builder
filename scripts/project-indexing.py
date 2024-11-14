from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SimpleField,
    SearchFieldDataType,
    SearchableField,
    SearchIndex
)
from datetime import datetime, timezone
import hashlib
from typing import List
import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
import glob
import tiktoken

load_dotenv()

# Azure AI Search settings
ai_search_endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
ai_search_key = os.environ["AZURE_SEARCH_KEY"]
ai_search_index = "projects"

# Initialize clients
search_index_client = SearchIndexClient(
    ai_search_endpoint, 
    AzureKeyCredential(ai_search_key)
)

search_client = SearchClient(
    ai_search_endpoint, 
    ai_search_index, 
    AzureKeyCredential(ai_search_key)
)

def read_text_file(file_path):
    """Read content from a local text file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def create_index():
    try:
        search_index_client.get_index(ai_search_index)
        print("Index already exists")
        return
    except:
        pass

    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
        SimpleField(name="project_id", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="date", type=SearchFieldDataType.DateTimeOffset, filterable=True, facetable=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SearchableField(name="sourcefilename", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="sourcepage", type=SearchFieldDataType.Int32, filterable=True)
    ]

    index = SearchIndex(
        name=ai_search_index, 
        fields=fields
    )
    
    result = search_index_client.create_or_update_index(index)
    print("Index has been created")

def chunk_text(text: str, chunk_size: int = 250) -> List[str]:
    """Split text into chunks of approximately chunk_size tokens."""
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    chunks = []
    
    # Process chunks of approximately chunk_size tokens
    for i in range(0, len(tokens), chunk_size):
        chunk_tokens = tokens[i:i + chunk_size]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)
    
    return chunks

def generate_project_id(file_path):
    """Generate a unique, deterministic ID for a project."""
    unique_string = f"{file_path}"
    return hashlib.md5(unique_string.encode()).hexdigest()

def generate_page_id(project_id: str, page_number: int):
    """Generate a unique ID for each page."""
    return f"{project_id}-page-{page_number}"

def populate_index():
    print("Populating index...")
    file_pattern = "../sample_data/projects/*.txt"
    files = glob.glob(file_pattern)
    print(f"Found {len(files)} text files in the directory")
    
    for file_path in files:
        print(f"Processing {file_path}")
        
        try:
            # Read the full text and generate project ID
            full_text = read_text_file(file_path)
            project_id = generate_project_id(file_path)
            fileName = os.path.basename(file_path)
            current_date = datetime.now(timezone.utc).isoformat()
            
            # Split text into chunks (pages)
            chunks = chunk_text(full_text)
            print(f"Split into {len(chunks)} pages")
            
            # Process each chunk as a page
            documents = []
            for page_number, page_content in enumerate(chunks, start=1):  # Start page numbers at 1
                page_id = generate_page_id(project_id, page_number)
                
                document = {
                    "id": page_id,
                    "project_id": project_id,
                    "date": current_date,
                    "content": page_content,
                    "sourcefilename": fileName,
                    "sourcepage": page_number
                }
                documents.append(document)
            
            # Upload pages in batches
            batch_size = 50
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                search_client.upload_documents(documents=batch)
                print(f"Uploaded pages {i + 1} to {i + len(batch)}")
            
            print(f"Successfully processed {file_path}")
        
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")

if __name__ == "__main__":
    create_index()
    populate_index()