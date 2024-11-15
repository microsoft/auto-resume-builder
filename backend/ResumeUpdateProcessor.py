from datetime import datetime, timedelta
from typing import Dict, List
import logging
from cosmosdb import CosmosDBManager
import uuid
from dotenv import load_dotenv
import os
from azure.communication.email import EmailClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient

class ResumeUpdateProcessor:
    def __init__(self):
        self.events_container = CosmosDBManager(
            cosmos_database_id="ResumeAutomation",
            cosmos_container_id="project_key_members"
        )
        self.trackers_container = CosmosDBManager(
            cosmos_database_id="ResumeAutomation",
            cosmos_container_id="resume_trackers"
        )
        self.notification_container = CosmosDBManager(
            cosmos_database_id="ResumeAutomation",
            cosmos_container_id="notifications"
        )
        self.employee_metadata_container = CosmosDBManager(
            cosmos_database_id="ResumeAutomation",
            cosmos_container_id="employee_metadata"
        )
        self.logger = logging.getLogger(__name__)
        load_dotenv()
        connection_string = os.environ.get("COMMUNICATION_SERVICES_CONNECTION_STRING")
        self.email_client = EmailClient.from_connection_string(connection_string)
        self.credential = AzureKeyCredential(os.environ.get("AZURE_SEARCH_KEY"))
        
    def process_key_member(self, member_entry: Dict) -> Dict:
        """Process an incoming key member entry."""
        try:
            # 1. Store the event
            stored_event = self._store_event(member_entry)
            
            # 2. Get or create resume tracker
            tracker = self._get_or_create_tracker(member_entry)
            
            # 3. Check if we need to trigger resume update
            if self._should_trigger_update(tracker):
                # Update tracker status to in_progress first
                tracker['added_to_resume'] = 'in_progress'
                tracker['last_updated'] = datetime.utcnow().isoformat()
                tracker['version'] += 1
                updated_tracker = self.trackers_container.update_item(tracker)
                
                # Then trigger the draft creation
                final_tracker = self._trigger_draft_creation(updated_tracker)
                
                return {
                    'status': 'triggered',
                    'message': f"Resume update triggered. Total hours: {final_tracker['total_hours']}",
                    'event_id': stored_event['id'],
                    'tracker_id': final_tracker['id']
                }
            
            return {
                'status': 'stored',
                'message': f"Event stored, total hours: {tracker['total_hours']}",
                'event_id': stored_event['id'],
                'tracker_id': tracker['id']
            }

        except Exception as e:
            self.logger.error(f"Error processing key member entry: {str(e)}")
            raise

    def _get_resume(self, employee_id: str) -> Dict:
        search_client = SearchClient(os.environ.get("AZURE_SEARCH_ENDPOINT"),
                      index_name=os.environ.get("AZURE_SEARCH_INDEX_RESUMES"),
                      credential=self.credential)

        results =  search_client.search(
            search_text=employee_id ,
            search_fields=['sourceFileName'],
            select="id,employee_first_name,employee_last_name, date, jobTitle, experienceLevel, content, sourceFileName")
        
        for result in results: 
            return result

    def _get_project(self, project_number: str) -> Dict:
        search_client = SearchClient(os.environ.get("AZURE_SEARCH_ENDPOINT"),
                      index_name=os.environ.get("AZURE_SEARCH_INDEX_PROJECTS"),
                      credential=self.credential)

        search_results =  search_client.search(
            search_text="*" ,
            filter="project_id eq '" + project_number + "'",
            select="id, project_id, date, content, sourcefilename, sourcepage")
        
        sorted_results = sorted(search_results, key=lambda x: x['sourcepage'])

        return sorted_results

    def _generate_project_experience(self, project_data: Dict, role_name: str, resume: Dict) -> str:
        """
        Temporary implementation that returns a placeholder project experience description.
        Will be replaced with LLM-based generation later.
        """
        return f"Served as {role_name} on {project_data['name']}, a {project_data['industry']} project. "\
               f"Led initiatives in {', '.join(project_data['technologies'])} while driving "\
               f"digital transformation efforts."


    def _get_employee_email(self, employee_id: str) -> str:
        """Get employee email from metadata container."""
        try:
            results = self.employee_metadata_container.query_items(
                query="SELECT * FROM c WHERE c.employee_id = @employee_id",
                parameters=[{"name": "@employee_id", "value": employee_id}],
                partition_key="metadata"
            )
            
            if results:
                return results[0].get('email')
            else:
                # For testing - return default email if no record exists
                self.logger.warning(f"No email found for employee {employee_id}, using default")
                return "NA"
                
        except Exception as e:
            self.logger.error(f"Error getting employee email: {str(e)}")
            return None

    def _send_notification(self, employee_id: str) -> bool:
        """Send email notification to employee."""
        try:
            # Get employee email
            employee_email = self._get_employee_email(employee_id)
            if not employee_email:
                self.logger.error(f"Could not send notification - no email found for employee {employee_id}")
                return False

            message = {
                "senderAddress": "DoNotReply@5fec6054-f6e1-4926-9c37-029ca719c8ae.azurecomm.net",
                "recipients": {
                    "to": [{"address": employee_email}]
                },
                "content": {
                    "subject": "Resume Update Required",
                    "plainText": "You have a pending resume update to review.",
                    "html": """
                    <html>
                        <body>
                            <h1>Resume Update Review Required</h1>
                            <p>You have a pending resume update that needs your review.</p>
                            <p>Please log in to review and approve the updates.</p>
                        </body>
                    </html>"""
                }
            }

            poller = self.email_client.begin_send(message)
            result = poller.result()
            self.logger.info(f"Email sent to {employee_email}: {result}")
            return True

        except Exception as e:
            self.logger.error(f"Error sending email notification: {str(e)}")
            return False

    def _update_notification_record(self, employee_id: str) -> Dict:
        """Create or update notification record for an employee."""
        try:
            notification = {
                "id": f"notification-{employee_id}",
                "partitionKey": "notifications",
                "employee_id": employee_id,
                "last_notification": datetime.utcnow().isoformat()
            }

            # Try to create new document
            try:
                return self.notification_container.create_item(notification)
            except:
                # If creation fails (document exists), update the existing one
                return self.notification_container.update_item(notification)

        except Exception as e:
            self.logger.error(f"Error updating notification record: {str(e)}")
            raise

    def _trigger_draft_creation(self, tracker: Dict) -> Dict:
        """Process resume update for the given tracker."""
        try:
            # Get current resume
            resume = self._get_resume(tracker['employee_id'])
            
            # Get project details
            project = self._get_project(tracker['project_number'])
            
            # Get current role from tracker's role history
            current_role = tracker['role_history'][-1]['role_name']
            
            # Generate project experience description
            description = self._generate_project_experience(
                project_data=project,
                role_name=current_role,
                resume=resume
            )
            
            # Update tracker with the generated description
            tracker['description'] = description
            tracker['last_updated'] = datetime.utcnow().isoformat()
            tracker['version'] += 1
            
            # Save the updated tracker
            updated_tracker = self.trackers_container.update_item(tracker)

            # Send notification and update notification record
            if self._send_notification(tracker['employee_id']):
                print("Notification sent successfully")
                self._update_notification_record(tracker['employee_id'])
            
            return updated_tracker
            
        except Exception as e:
            self.logger.error(f"Error in trigger_draft_creation: {str(e)}")
            raise

    def _should_trigger_update(self, tracker: Dict) -> bool:
        """
        Determine if we should trigger a resume update.
        Returns True if hours >= 40 and status is 'no'
        """
        return (tracker['total_hours'] >= 40 and 
                tracker['added_to_resume'] == 'no')

    def _store_event(self, member_entry: Dict) -> Dict:
        """Store the key member entry in the events container."""
        # Extract employee ID from display name (e.g., "Diaz, John - 18117" -> "18117")
        employee_id = member_entry['employee_display_name'].split(' - ')[1]
        
        event_doc = {
            "id": str(uuid.uuid4()),
            "partitionKey": member_entry['project_number'],  # Use project number as partition key
            "type": "project_key_member",
            "subject_area": member_entry['subject_area'],
            "project_number": member_entry['project_number'],
            "project_role_name": member_entry['project_role_name'],
            "employee_display_name": member_entry['employee_display_name'],
            "employee_id": employee_id,
            "job_hours": member_entry['job_hours'],
            "employee_job_family_function_code": member_entry['employee_job_family_function_code'],
            "timestamp": datetime.utcnow().isoformat()
        }
        return self.events_container.create_item(event_doc)

    def _get_or_create_tracker(self, member_entry: Dict) -> Dict:
        """Get or create tracker in the trackers container."""
        # Extract employee ID from display name
        employee_id = member_entry['employee_display_name'].split(' - ')[1]
        
        # Create compound ID from project and employee
        tracker_id = f"{member_entry['project_number']}-{employee_id}"
        
        try:
            # Try to get existing tracker directly by ID
            tracker = self.trackers_container.query_items(
                query="SELECT * FROM c WHERE c.id = @id",
                parameters=[{"name": "@id", "value": tracker_id}],
                partition_key="resumeupdatestatus"
            )
            
            if tracker:
                existing_tracker = tracker[0]
                # Update with latest hours - no need to sum up events anymore
                existing_tracker['total_hours'] = member_entry['job_hours']
                existing_tracker['last_updated'] = datetime.utcnow().isoformat()
                existing_tracker['version'] += 1
                
                # Update role history if needed
                self._update_role_history(existing_tracker, member_entry)
                
                return self.trackers_container.update_item(existing_tracker)
            
            # Create new tracker if not found
            new_tracker = {
                "id": tracker_id,
                "partitionKey": "resumeupdatestatus",
                "type": "resume_update_tracker",
                "employee_id": employee_id,
                "employee_display_name": member_entry['employee_display_name'],
                "project_number": member_entry['project_number'],
                "subject_area": member_entry['subject_area'],
                "total_hours": member_entry['job_hours'],
                "added_to_resume": "no",
                "description": "",
                "created_timestamp": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
                "version": 1,
                "role_history": [
                    {
                        "role_name": member_entry['project_role_name'],
                        "job_family_code": member_entry['employee_job_family_function_code'],
                        "start_date": datetime.utcnow().isoformat(),
                        "end_date": None
                    }
                ],
                "review_date": (datetime.utcnow() + timedelta(days=30)).isoformat()
            }
            return self.trackers_container.create_item(new_tracker)
            
        except Exception as e:
            self.logger.error(f"Error in get_or_create_tracker: {str(e)}")
            raise

    def _update_role_history(self, tracker: Dict, member_entry: Dict):
        """Update role history if role has changed."""
        current_role = tracker['role_history'][-1]
        if (current_role['role_name'] != member_entry['project_role_name'] or 
            current_role['job_family_code'] != member_entry['employee_job_family_function_code']):
            # Close current role
            current_role['end_date'] = datetime.utcnow().isoformat()
            # Add new role
            tracker['role_history'].append({
                "role_name": member_entry['project_role_name'],
                "job_family_code": member_entry['employee_job_family_function_code'],
                "start_date": datetime.utcnow().isoformat(),
                "end_date": None
            })

    def get_pending_updates(self, employee_id: str) -> List[Dict]:
        """
        Get all pending resume updates for a specific employee.
        Returns updates where added_to_resume = 'in_progress'.
        """
        query = """
            SELECT *
            FROM c
            WHERE c.partitionKey = 'resumeupdatestatus'
            AND c.employee_id = @employee_id
            AND c.added_to_resume = 'in_progress'
        """
        
        parameters = [
            {"name": "@employee_id", "value": employee_id}
        ]
        
        # Query Cosmos DB for pending updates
        pending_updates = self.trackers_container.query_items(
            query=query,
            parameters=parameters,
            partition_key="resumeupdatestatus"
        )
        
        return pending_updates
    
    def discard_update(self, project_id: str) -> bool:
        """
        Discard a pending resume update by setting its status to 'discarded'.
        
        Args:
            project_id: The ID of the resume tracker to discard
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Query the tracker directly by ID
            results = self.trackers_container.query_items(
                query="SELECT * FROM c WHERE c.id = @id",
                parameters=[{"name": "@id", "value": project_id}],
                partition_key="resumeupdatestatus"
            )
            
            for result in results:
                print(result)

            # Convert results to list and get first item if it exists
            results_list = list(results)
            if not results_list:
                self.logger.error(f"No tracker found with ID: {project_id}")
                return False
                
            tracker = results_list[0]
                    
            # Update the status to 'discarded'
            tracker['added_to_resume'] = 'discarded'
            tracker['last_updated'] = datetime.utcnow().isoformat()
            tracker['version'] += 1
            
            # Save the updated tracker
            self.trackers_container.update_item(tracker)
            
            self.logger.info(f"Successfully discarded update for tracker: {project_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error discarding update: {str(e)}")
            return False