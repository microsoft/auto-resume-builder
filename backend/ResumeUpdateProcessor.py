from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging
from cosmosdb import CosmosDBManager
import uuid
from dotenv import load_dotenv
import os
from prompts import generate_work_experience_system_prompt
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient
from langchain_openai import AzureChatOpenAI

load_dotenv()

# Azure OpenAI
aoai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
aoai_key = os.getenv("AZURE_OPENAI_API_KEY")
aoai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

#Azure AI Search
credential = AzureKeyCredential(os.environ.get("AZURE_SEARCH_KEY"))

primary_llm = AzureChatOpenAI(
    azure_deployment=aoai_deployment,
    api_version="2024-05-01-preview",
    temperature=0.75,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=aoai_key,
    azure_endpoint=aoai_endpoint
)

class ResumeUpdateProcessor:
    def __init__(self):
        # Constants
        self.NOTIFICATION_COOLDOWN_HOURS = 0
        self.HOURS_THRESHOLD = 40
        self.credential = credential
        
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
        self.feedback_container = CosmosDBManager(
            cosmos_database_id="ResumeAutomation",
            cosmos_container_id="feedback"
        )
        self.logger = logging.getLogger(__name__)
        self.notification_cooldown = timedelta(hours=self.NOTIFICATION_COOLDOWN_HOURS)
        load_dotenv()
        self.webapp_url = os.environ.get("WEBAPP_URL")
        
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
            select="id, date, jobTitle, experienceLevel, content, sourceFileName")
        
        for result in results: 
            return result

    def _get_project(self, project_number: str) -> Dict:
        search_client = SearchClient(os.environ.get("AZURE_SEARCH_ENDPOINT"),
                      index_name=os.environ.get("AZURE_SEARCH_INDEX_PROJECTS"),
                      credential=self.credential)

        search_results =  search_client.search(
            search_text="*" ,
            filter="project_number eq '" + project_number + "'",
            select="id, project_number, document_updated, content, sourcefile, sourcepage")
        
        sorted_results = sorted(search_results, key=lambda x: x['sourcepage'])

        return sorted_results

    def _generate_project_experience(self, project_data: Dict, role_name: str, resume: Dict) -> str:
        """
        Function for generating a project summary using the project data and resume data.
        """
        project_string = ""
        for project in project_data:
            project_string = project_string + project["content"]

        print(resume)
        #Prepare messages for LLM
        work_experience_user_message = f"<Current Resume>\n {resume["content"]}\n\n <Project Description>\n {project_string}"
        messages = [{"role": "system", "content": generate_work_experience_system_prompt}]
        messages.append({"role": "user", "content": work_experience_user_message})
        #Invoke LLM
        response = primary_llm.invoke(messages)

        return response.content

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
        try:
            employee_email = self._get_employee_email(employee_id)
            if not employee_email:
                self.logger.error(f"Could not send notification - no email found for employee {employee_id}")
                return False

            review_link = f"{self.webapp_url}/resume-review"

            message = {
                "senderAddress": "DoNotReply@5fec6054-f6e1-4926-9c37-029ca719c8ae.azurecomm.net",
                "recipients": {
                    "to": [{"address": employee_email}]
                },
                "content": {
                    "subject": "Resume Update Required",
                    "plainText": (
                        "Hello,\n\n"
                        "You have a pending resume update that requires your review. Please take a moment to review and approve these updates to keep your resume current.\n\n"
                        f"Review your updates here: {review_link}\n\n"
                        "This is an automated message. Please do not reply to this email."
                    ),
                    "html": f"""
                    <html>
                        <head>
                            <style>
                                body {{
                                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
                                    line-height: 1.6;
                                    margin: 0;
                                    padding: 0;
                                    background-color: #ffffff;
                                }}
                                .container {{
                                    max-width: 600px;
                                    margin: 0 auto;
                                    background: #ffffff;
                                }}
                                .header {{
                                    background-color: #003087;
                                    padding: 20px;
                                    text-align: left;
                                }}
                                .header h1 {{
                                    margin: 0;
                                    color: #ffffff;
                                    font-size: 20px;
                                    font-weight: 500;
                                }}
                                .content {{
                                    padding: 40px 20px;
                                    color: #333333;
                                }}
                                .button {{
                                    display: inline-block;
                                    background-color: #7AC143;
                                    color: #ffffff;
                                    padding: 10px 24px;
                                    text-decoration: none;
                                    border-radius: 4px;
                                    font-weight: 500;
                                    margin-top: 20px;
                                }}
                                .footer {{
                                    padding: 20px;
                                    color: #666666;
                                    font-size: 14px;
                                    border-top: 1px solid #eeeeee;
                                }}
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <div class="header">
                                    <h1>📄 Resume Update Review Required</h1>
                                </div>
                                <div class="content">
                                    <p>Hello,</p>
                                    <p>You have a pending resume update that requires your review. Please take a moment to review and approve these updates to keep your resume current.</p>
                                    <a href="{review_link}" class="button">Review Updates Now</a>
                                </div>
                                <div class="footer">
                                    This is an automated message. Please do not reply to this email.
                                </div>
                            </div>
                        </body>
                    </html>"""
                }
            }

            self.logger.info(f"Email sent to {employee_email}")
            return True

        except Exception as e:
            self.logger.error(f"Error sending email notification: {str(e)}")
            return False

    def _update_notification_record(self, employee_id: str) -> Dict:
        """Update notification record with latest notification time."""
        try:
            notification = {
                "id": f"notification-{employee_id}",
                "partitionKey": "notifications",
                "employee_id": employee_id,
                "last_notification": datetime.utcnow().isoformat()
            }
            return self.notification_container.update_item(notification)

        except Exception as e:
            self.logger.error(f"Error updating notification record: {str(e)}")
            raise

    def _trigger_draft_creation(self, tracker: Dict) -> Dict:
        """Process resume update for the given tracker."""
        try:
            print(tracker['employee_id'])
            # Get current resume
            resume = self._get_resume(tracker['employee_id'])
            
            print(tracker['project_number'])
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
        return (tracker['total_hours'] >= self.HOURS_THRESHOLD and 
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

    def get_pending_updates(self, employee_id: str = None) -> List[Dict]:
        """
        Get all pending resume updates for a specific employee or all employees.
        Returns updates where added_to_resume = 'in_progress'.
        
        Args:
            employee_id: Optional employee ID. If None, returns updates for all employees.
            
        Returns:
            List[Dict]: List of pending resume update trackers
        """
        base_query = """
            SELECT *
            FROM c
            WHERE c.partitionKey = 'resumeupdatestatus'
            AND c.added_to_resume = 'in_progress'
        """
        
        if employee_id:
            query = base_query + " AND c.employee_id = @employee_id"
            parameters = [{"name": "@employee_id", "value": employee_id}]
        else:
            query = base_query
            parameters = []
        
        return self.trackers_container.query_items(
            query=query,
            parameters=parameters,
            partition_key="resumeupdatestatus"
        )
    
    def save_updates(self, employee_id: str, project_numbers: List[str]) -> bool:
        """
        Save multiple resume updates, updating their status to 'yes'.
        
        Args:
            employee_id: ID of the employee
            project_numbers: List of project numbers to save
            
        Returns:
            bool: True if all updates were saved successfully, False otherwise
        """
        try:
            self.logger.info(f"Saving updates for employee {employee_id}, projects: {project_numbers}")
            
            for project_number in project_numbers:
                # Create the tracker ID using the combination
                tracker_id = f"{project_number}-{employee_id}"
                
                # Query the tracker
                results = self.trackers_container.query_items(
                    query="SELECT * FROM c WHERE c.id = @id",
                    parameters=[{"name": "@id", "value": tracker_id}],
                    partition_key="resumeupdatestatus"
                )
                
                results_list = list(results)
                if not results_list:
                    self.logger.error(f"No tracker found with ID: {tracker_id}")
                    continue
                    
                tracker = results_list[0]
                
                # For now, just update the tracker status
                tracker['added_to_resume'] = 'yes'
                tracker['last_updated'] = datetime.utcnow().isoformat()
                tracker['version'] += 1
                
                # Save the updated tracker
                self.trackers_container.update_item(tracker)
                
                self.logger.info(f"Successfully saved update for tracker: {tracker_id}")
            
            return True
                
        except Exception as e:
            self.logger.error(f"Error saving updates: {str(e)}")
            return False

    def discard_update(self, employee_id: str, project_number: str) -> bool:
        """
        Discard a pending resume update by setting its status to 'discarded'.
        
        Args:
            employee_id: ID of the employee
            project_number: Project number to discard
                
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create the tracker ID using the combination
            tracker_id = f"{project_number}-{employee_id}"
            self.logger.info(f"Discarding update for tracker ID: {tracker_id}")
            
            # Query the tracker directly by ID
            results = self.trackers_container.query_items(
                query="SELECT * FROM c WHERE c.id = @id",
                parameters=[{"name": "@id", "value": tracker_id}],
                partition_key="resumeupdatestatus"
            )
            
            results_list = list(results)
            if not results_list:
                self.logger.error(f"No tracker found with ID: {tracker_id}")
                return False
                
            tracker = results_list[0]
                    
            # Update the status to 'discarded'
            tracker['added_to_resume'] = 'discarded'
            tracker['last_updated'] = datetime.utcnow().isoformat()
            tracker['version'] += 1
            
            # Save the updated tracker
            self.trackers_container.update_item(tracker)
            
            self.logger.info(f"Successfully discarded update for tracker: {tracker_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error discarding update: {str(e)}")
            return False
    
    def recurring_notification(self) -> Dict[str, Any]:
        """
        Process recurring notifications for pending resume updates.
        Returns summary of notifications sent.
        """
        try:
            self.logger.info("Starting recurring notification process")
            summary = {
                "total_employees_processed": 0,  # Added this field
                "notifications_sent": 0,
                "skipped_cooldown": 0,
                "errors": 0
            }

            # Get all employees with pending updates
            pending_updates = self.get_pending_updates()
            
            # Get unique employee IDs
            employees_to_notify = {update['employee_id'] for update in pending_updates}
            summary["total_employees_processed"] = len(employees_to_notify)
            
            # Process each employee
            for employee_id in employees_to_notify:
                try:
                    if self._should_send_notification(employee_id):
                        if self._send_notification(employee_id):
                            self._update_notification_record(employee_id)
                            summary["notifications_sent"] += 1
                    else:
                        summary["skipped_cooldown"] += 1
                except Exception as e:
                    self.logger.error(f"Error processing notifications for employee {employee_id}: {str(e)}")
                    summary["errors"] += 1

            self.logger.info(f"Recurring notification process completed: {summary}")
            return summary

        except Exception as e:
            self.logger.error(f"Error in recurring notification process: {str(e)}")
            raise


    def _should_send_notification(self, employee_id: str) -> bool:
        """
        Check if notification should be sent based on cooldown period.
        Returns True if last notification was more than cooldown period ago.
        """
        try:
            query = """
                SELECT * FROM c 
                WHERE c.partitionKey = 'notifications'
                AND c.id = @notification_id
            """
            parameters = [
                {"name": "@notification_id", "value": f"notification-{employee_id}"}
            ]
            results = list(self.notification_container.query_items(
                query=query,
                parameters=parameters,
                partition_key="notifications"
            ))

            if not results:
                return True

            notification_record = results[0]
            last_notification = datetime.fromisoformat(notification_record['last_notification'])
            
            return datetime.utcnow() - last_notification > self.notification_cooldown

        except Exception as e:
            self.logger.error(f"Error checking notification eligibility: {str(e)}")
            return False

        except Exception as e:
            self.logger.error(f"Error checking notification eligibility: {str(e)}")
            return False

    def store_feedback(self, feedback_data: dict) -> dict:
        """
        Store feedback in the feedback container.
        
        Args:
            feedback_data (dict): Dictionary containing feedback type and content
            
        Returns:
            dict: The stored feedback document
        """
        try:
            employee_id = feedback_data.get('employee_id')
            
            feedback_doc = {
                "id": f"feedback-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{employee_id}",
                "partitionKey": "AutoResumeUpdates",  # Fixed partition key as requested
                "type": "feedback",
                "feedback_type": feedback_data.get('type'),
                "content": feedback_data.get('content'),
                "employee_id": employee_id,
                "created_timestamp": datetime.utcnow().isoformat(),
                "status": "new"
            }
            
            stored_feedback = self.feedback_container.create_item(feedback_doc)
            self.logger.info(f"Stored feedback document with id: {stored_feedback['id']}")
            
            return stored_feedback
            
        except Exception as e:
            self.logger.error(f"Error storing feedback: {str(e)}")
            raise
        