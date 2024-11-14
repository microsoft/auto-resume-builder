# Standard library imports
import os

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

EMPLOYEE_ID = "99999"

@app.route('/get_pending_updates', methods=['GET'])
def get_pending_updates():
    pending_updates = processor.get_pending_updates(EMPLOYEE_ID)
    
    formatted_updates = []
    for update in pending_updates:
        formatted_updates.append({
            'id': update['id'],
            'name': update.get('subject_area', 'Unknown Project'),
            'code': update['project_number'],
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
        project_id = data.get('projectId')
        
        if not project_id:
            return jsonify({
                'status': 'error',
                'message': 'Project ID is required'
            }), 400

        result = processor.discard_update(project_id)
        
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
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True, threaded=True)