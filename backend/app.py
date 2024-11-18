# Standard library imports
import os
from datetime import datetime
# Third-party imports
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

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
    return "99999"

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
            'name': update.get('subject_area', 'Unknown Project'),
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

if __name__ == '__main__':
    app.run(debug=True, threaded=True)