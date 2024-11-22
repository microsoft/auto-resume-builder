# Standard library imports
import os
import io
from datetime import datetime
# Third-party imports
from dotenv import load_dotenv
from flask import Flask, jsonify, request, make_response, send_file
from flask_cors import CORS
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

# Local imports
from ResumeUpdateProcessor import ResumeUpdateProcessor

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize processor
processor = ResumeUpdateProcessor()

def get_current_user_id():
    """
    Placeholder function to get the current user's ID.
    Will be replaced with actual authentication logic later.
    """
    return "718163"

@app.route('/get_current_user', methods=['GET'])
def get_current_user():
    try:
        user_id = get_current_user_id()
        return jsonify({
            'status': 'success',
            'employeeId': user_id
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/get_pending_updates', methods=['GET'])
def get_pending_updates():
    employee_id = get_current_user_id()
    pending_updates = processor.get_pending_updates(employee_id)
    
    formatted_updates = []
    for update in pending_updates:
        formatted_updates.append({
            'id': update['id'],
            'name': update.get('project_name', 'Unknown Project'),
            'project_number': update['project_number'],  # Changed from code to project_number
            'content': update.get('description', ''),
            'total_hours': update.get('total_hours', 0),
            'role': update['role_history'][-1]['role_name'] if update.get('role_history') else 'Unknown Role'
        })
    
    return jsonify({
        'status': 'success',
        'projects': formatted_updates
    })

@app.route('/discard', methods=['POST'])
def discard_update():
    try:
        data = request.get_json()
        print("Received discard request data:", data)
        
        project_number = data.get('project_number')  # Changed from projectId
        employee_id = data.get('employee_id')  # Changed from employeeId
        
        if not project_number or not employee_id:
            print(f"Missing required fields. project_number: {project_number}, employee_id: {employee_id}")
            return jsonify({
                'status': 'error',
                'message': 'Project number and employee ID are required'
            }), 400

        result = processor.discard_update(employee_id, project_number)
        
        if result:
            return jsonify({
                'status': 'success',
                'message': 'Update discarded successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to discard update'
            }), 500

    except Exception as e:
        print(f"Error in discard_update: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/save', methods=['POST'])
def save_updates():
    try:
        data = request.get_json()
        project_numbers = data.get('project_numbers', [])  # Changed from projectIds
        employee_id = data.get('employee_id')  # Changed from employeeId
        
        if not project_numbers or not employee_id:
            return jsonify({
                'status': 'error',
                'message': 'Project numbers and employee ID are required'
            }), 400

        result = processor.save_updates(employee_id, project_numbers)
        
        if result:
            return jsonify({
                'status': 'success',
                'message': 'Updates saved successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to save updates'
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/feedback', methods=['POST'])
def submit_feedback():
    try:
        data = request.get_json()
        employee_id = get_current_user_id()
        
        # Add employee_id to feedback data
        feedback_data = {
            'type': data.get('type'),
            'content': data.get('content'),
            'employee_id': employee_id
        }
        
        # Store feedback using the processor
        stored_feedback = processor.store_feedback(feedback_data)
        
        return jsonify({
            'status': 'success',
            'message': 'Feedback stored successfully',
            'feedback_id': stored_feedback['id']
        })

    except Exception as e:
        print(f"Error processing feedback: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Add to backend/app.py
@app.route('/download', methods=['GET'])
def download_resume():
    resume_name = request.args.get('resumeName')

    content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

    storage_account_name = os.getenv("STORAGE_ACCOUNT_NAME")

    storage_account_resume_container = os.getenv("STORAGE_ACCOUNT_RESUME_CONTAINER")

    account_url = f"https://{storage_account_name}.blob.core.windows.net"
    credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(account_url=account_url, credential=credential)

    # Get container client
    container_client = blob_service_client.get_container_client(storage_account_resume_container)

    # Get blob client
    blob_client = container_client.get_blob_client(resume_name)

    try:
        download_stream = blob_client.download_blob()
        file_content = download_stream.readall()

        response = make_response(file_content)
        response.headers['Content-Type'] = content_type
        response.headers['Content-Disposition'] = f'attachment; filename="{resume_name}"'
        return response
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        return make_response('Failed to download file', 500)


@app.route('/tips-pdf', methods=['GET'])
def get_tips_pdf():
    try:
        # Retrieve environment variables once
        connection_string = os.environ.get('STORAGE_ACCOUNT_CONNECTION_STRING')
        storage_account_name = os.environ.get('STORAGE_ACCOUNT_NAME')
        print("Storage account name:", storage_account_name)
        
        if connection_string:
            try:
                blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            except Exception as e:
                print(f"Connection string auth failed, falling back to DefaultAzureCredential: {str(e)}")
                # Fall back to DefaultAzureCredential
                account_url = f"https://{storage_account_name}.blob.core.windows.net"
                credential = DefaultAzureCredential()
                blob_service_client = BlobServiceClient(account_url=account_url, credential=credential)
        else:
            # Directly use DefaultAzureCredential
            print("Using DefaultAzureCredential")
            account_url = f"https://{storage_account_name}.blob.core.windows.net"
            credential = DefaultAzureCredential()
            blob_service_client = BlobServiceClient(account_url=account_url, credential=credential)
        
        # Get container client
        container_client = blob_service_client.get_container_client("resumes")
        
        # Get blob client
        blob_client = container_client.get_blob_client("docs/Resume Guidance.pdf")
        
        # Download blob
        download_stream = blob_client.download_blob()
        file_content = download_stream.readall()
        
        # Create BytesIO object
        file_stream = io.BytesIO(file_content)
        file_stream.seek(0)
        
        return send_file(
            file_stream,
            mimetype='application/pdf',
            as_attachment=False,
            download_name='resume_tips.pdf'
        )

    except Exception as e:
        print(f"Error serving PDF: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Could not retrieve PDF'
        }), 500
if __name__ == '__main__':
    app.run(debug=True, threaded=True)