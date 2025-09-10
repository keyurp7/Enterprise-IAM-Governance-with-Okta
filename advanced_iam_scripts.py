
# ==========================================
# Advanced IAM Automation Scripts
# ==========================================

import requests
import json
import csv
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import hashlib
import secrets

# ==========================================
# Advanced IAM Automation Scripts
# ==========================================

import requests
import json
import csv
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import hashlib
import secrets

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AdvancedOktaManager:
    def activate_all_staged_users(self):
        """
        Activate all users with status 'STAGED' in Okta tenant, except Keyur and Vishal.
        """
        users = self.get_users(limit=1000)
        activated = []
        skip_emails = {"Keyur_7@outlook.com", "vishal@babiesmart.com.au"}
        for user in users:
            email = user['profile'].get('email')
            if user.get('status') == 'STAGED' and email not in skip_emails:
                user_id = user['id']
                url = f"{self.org_url}/api/v1/users/{user_id}/lifecycle/activate"
                response = self.session.post(url)
                if response.status_code == 200:
                    activated.append(user_id)
                    logger.info(f"Activated user {email}")
                else:
                    logger.error(f"Failed to activate user {email}: {response.text}")
        return activated
    def get_user_factors(self, user_id: str) -> list:
        """
        Get all enrolled MFA factors for a given user from Okta API.
        """
        url = f"{self.org_url}/api/v1/users/{user_id}/factors"
        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get factors for user {user_id}: {response.text}")
            return []
    def get_user_groups(self, user_id: str) -> list:
        """
        Get all groups for a given user from Okta API.
        """
        url = f"{self.org_url}/api/v1/users/{user_id}/groups"
        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get groups for user {user_id}: {response.text}")
            return []
    def bulk_update_employee_number(self, employee_numbers: list):
        """
        Bulk update employeeNumber attribute for all Okta users using the provided list, in chronological order.
        Each employeeNumber will be assigned to a user in the order returned by get_users().
        """
        users = self.get_users(limit=len(employee_numbers))
        if len(users) != len(employee_numbers):
            logger.warning(f"Number of users ({len(users)}) does not match number of employeeNumbers ({len(employee_numbers)}). Proceeding with minimum of both.")
        count = min(len(users), len(employee_numbers))
        results = []
        for i in range(count):
            user = users[i]
            user_id = user['id']
            emp_num = employee_numbers[i]
            try:
                update_result = self.update_user_profile(user_id, {"employeeNumber": emp_num})
                results.append({"user_id": user_id, "email": user['profile'].get('email'), "employeeNumber": emp_num, "status": "success"})
                logger.info(f"Updated user {user['profile'].get('email')} with employeeNumber {emp_num}")
            except Exception as e:
                results.append({"user_id": user_id, "email": user['profile'].get('email'), "employeeNumber": emp_num, "status": "failed", "error": str(e)})
                logger.error(f"Failed to update user {user['profile'].get('email')}: {str(e)}")
        return results
    def get_user_applications(self, user_id: str) -> list:
        url = f"{self.org_url}/api/v1/users/{user_id}/appLinks"
        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get user applications: {response.text}")
            return []

    def get_group_members(self, group_id: str) -> list:
        url = f"{self.org_url}/api/v1/groups/{group_id}/users"
        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get group members: {response.text}")
            return []

    def add_user_to_group(self, user_id: str, group_id: str) -> bool:
        url = f"{self.org_url}/api/v1/groups/{group_id}/users/{user_id}"
        response = self.session.put(url)
        if response.status_code == 204:
            return True
        else:
            logger.error(f"Failed to add user to group: {response.text}")
            return False

    def get_groups(self) -> list:
        url = f"{self.org_url}/api/v1/groups"
        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get groups: {response.text}")
            return []

    def get_group_by_name(self, group_name: str) -> Dict:
        groups = self.get_groups()
        for group in groups:
            if group.get("profile", {}).get("name", group.get("name")) == group_name:
                return group
        logger.error(f"Group not found: {group_name}")
        return {}

    def get_users(self, limit: int = 1000) -> list:
        url = f"{self.org_url}/api/v1/users?limit={limit}"
        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get users: {response.text}")
            return []

    def get_user(self, user_id: str) -> Dict:
        url = f"{self.org_url}/api/v1/users/{user_id}"
        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get user: {response.text}")
            return {}

    def update_user_profile(self, user_id: str, new_attributes: Dict) -> Dict:
        url = f"{self.org_url}/api/v1/users/{user_id}"
        data = {"profile": new_attributes}
        response = self.session.post(url, data=json.dumps(data))
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to update user profile: {response.text}")
            return {}

    def remove_department_groups(self, user_id: str, department: str) -> list:
        # This would require listing all groups, finding department groups, and removing user from them
        removed = []
        groups = self.get_groups()
        for group in groups:
            if group.get("profile", {}).get("name", group.get("name")) == f"{department}_Department":
                url = f"{self.org_url}/api/v1/groups/{group['id']}/users/{user_id}"
                response = self.session.delete(url)
                if response.status_code == 204:
                    removed.append(group['id'])
        return removed

    def remove_all_group_memberships(self, user_id: str) -> list:
        groups = self.get_user_groups(user_id)
        removed = []
        for group in groups:
            url = f"{self.org_url}/api/v1/groups/{group['id']}/users/{user_id}"
            response = self.session.delete(url)
            if response.status_code == 204:
                removed.append(group['id'])
        return removed

    def remove_all_application_assignments(self, user_id: str) -> list:
        # Okta does not have a direct API for removing all app assignments, must do per app
        apps = self.get_user_applications(user_id)
        removed = []
        for app in apps:
            app_id = app.get('id')
            if app_id:
                url = f"{self.org_url}/api/v1/apps/{app_id}/users/{user_id}"
                response = self.session.delete(url)
                if response.status_code == 204:
                    removed.append(app_id)
        return removed

    def get_system_logs(self, hours_back: int = 24) -> list:
        # Stub: Replace with actual Okta API call
        return [
            {
                'actor': {'alternateId': 'user@example.com', 'id': 'fake_user_id'},
                'eventType': 'user.session.start',
                'client': {'ipAddress': '127.0.0.1', 'geographicalContext': {'city': 'City', 'country': 'Country'}},
                'published': datetime.now().isoformat()
            },
            {
                'actor': {'alternateId': 'user2@example.com', 'id': 'fake_user_id2'},
                'eventType': 'auth_failure',
                'client': {'ipAddress': '127.0.0.2', 'geographicalContext': {'city': 'OtherCity', 'country': 'OtherCountry'}},
                'published': datetime.now().isoformat()
            }
        ]
    def __init__(self, org_url: str, api_token: str):
        self.org_url = org_url.rstrip('/')
        self.api_token = api_token
        self.headers = {
            'Authorization': f'SSWS {api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    # ==========================================
    # Advanced User Lifecycle Management
    # ==========================================
    
    def automated_joiner_workflow(self, user_data: Dict) -> Dict:
        """Complete automated joiner workflow"""
        logger.info(f"Starting joiner workflow for {user_data['profile']['email']}")
        
        workflow_steps = []
        
        try:
            # Step 1: Create user account
            user = self.create_user_with_activation(user_data)
            workflow_steps.append({"step": "account_creation", "status": "success", "user_id": user.get('id')})
            
            # Step 2: Assign to groups based on attributes
            group_assignments = self.auto_assign_groups(user['id'], user_data['profile'])
            workflow_steps.append({"step": "group_assignment", "status": "success", "groups": group_assignments})
            
            # Step 3: Provision applications
            app_assignments = self.auto_assign_applications(user['id'], user_data['profile'])
            workflow_steps.append({"step": "application_provisioning", "status": "success", "apps": app_assignments})
            
            # Step 4: Generate welcome email
            welcome_info = self.generate_welcome_package(user)
            workflow_steps.append({"step": "welcome_generation", "status": "success"})
            
            # Step 5: Schedule access review
            review_scheduled = self.schedule_access_review(user['id'])
            workflow_steps.append({"step": "access_review_scheduled", "status": "success"})
            
            logger.info(f"Joiner workflow completed successfully for {user_data['profile']['email']}")
            
            return {
                "status": "success",
                "user_id": user['id'],
                "workflow_steps": workflow_steps,
                "welcome_info": welcome_info
            }
            
        except Exception as e:
            logger.error(f"Joiner workflow failed: {str(e)}")
            return {"status": "failed", "error": str(e), "completed_steps": workflow_steps}
    
    def automated_mover_workflow(self, user_id: str, new_attributes: Dict) -> Dict:
        """Handle department/role changes"""
        logger.info(f"Starting mover workflow for user {user_id}")
        
        try:
            # Get current user
            current_user = self.get_user(user_id)
            old_department = current_user['profile'].get('department')
            new_department = new_attributes.get('department')
            
            workflow_steps = []
            
            # Step 1: Update user attributes
            updated_user = self.update_user_profile(user_id, new_attributes)
            workflow_steps.append({"step": "profile_update", "status": "success"})
            
            # Step 2: Remove old group memberships
            if old_department != new_department:
                old_groups_removed = self.remove_department_groups(user_id, old_department)
                workflow_steps.append({"step": "old_groups_removed", "status": "success", "groups": old_groups_removed})
            
            # Step 3: Add new group memberships
            new_groups_added = self.auto_assign_groups(user_id, new_attributes)
            workflow_steps.append({"step": "new_groups_assigned", "status": "success", "groups": new_groups_added})
            
            # Step 4: Update application access
            app_updates = self.update_application_access(user_id, new_attributes)
            workflow_steps.append({"step": "application_access_updated", "status": "success"})
            
            # Step 5: Trigger access recertification
            recert_triggered = self.trigger_access_recertification(user_id)
            workflow_steps.append({"step": "recertification_triggered", "status": "success"})
            
            return {
                "status": "success",
                "user_id": user_id,
                "old_department": old_department,
                "new_department": new_department,
                "workflow_steps": workflow_steps
            }
            
        except Exception as e:
            logger.error(f"Mover workflow failed: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def automated_leaver_workflow(self, user_id: str, last_day: datetime) -> Dict:
        """Handle employee termination"""
        logger.info(f"Starting leaver workflow for user {user_id}")
        
        try:
            user = self.get_user(user_id)
            workflow_steps = []
            
            # Step 1: Immediate access suspension if last day is today/past
            if last_day <= datetime.now():
                self.suspend_user_access(user_id)
                workflow_steps.append({"step": "immediate_suspension", "status": "success"})
            
            # Step 2: Remove from all groups
            groups_removed = self.remove_all_group_memberships(user_id)
            workflow_steps.append({"step": "groups_removed", "status": "success", "count": len(groups_removed)})
            
            # Step 3: Remove application assignments
            apps_removed = self.remove_all_application_assignments(user_id)
            workflow_steps.append({"step": "applications_removed", "status": "success", "count": len(apps_removed)})
            
            # Step 4: Generate offboarding report
            offboarding_report = self.generate_offboarding_report(user_id)
            workflow_steps.append({"step": "offboarding_report_generated", "status": "success"})
            
            # Step 5: Schedule account deactivation (after grace period)
            deactivation_scheduled = self.schedule_account_deactivation(user_id, last_day + timedelta(days=30))
            workflow_steps.append({"step": "deactivation_scheduled", "status": "success"})
            
            return {
                "status": "success",
                "user_id": user_id,
                "user_email": user['profile']['email'],
                "workflow_steps": workflow_steps,
                "offboarding_report": offboarding_report
            }
            
        except Exception as e:
            logger.error(f"Leaver workflow failed: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    # ==========================================
    # Privileged Access Management
    # ==========================================
    
    def request_privileged_access(self, user_email: str, resource: str, justification: str, duration_hours: int = 8) -> Dict:
        """Request temporary privileged access"""
        request_id = self.generate_request_id()
        
        access_request = {
            "request_id": request_id,
            "user_email": user_email,
            "resource": resource,
            "justification": justification,
            "duration_hours": duration_hours,
            "status": "pending_approval",
            "created_date": datetime.now().isoformat(),
            "approver_required": self.determine_approver(resource)
        }
        
        # Store request (in production, this would go to a database)
        self.store_access_request(access_request)
        
        # Send approval notification
        self.send_approval_notification(access_request)
        
        logger.info(f"Privileged access request created: {request_id}")
        return access_request
    
    def approve_privileged_access(self, request_id: str, approver_email: str) -> Dict:
        """Approve privileged access request"""
        request = self.get_access_request(request_id)
        
        if not request:
            return {"status": "failed", "error": "Request not found"}
        
        try:
            # Get user
            user = self.get_user_by_email(request['user_email'])
            
            # Grant temporary privileged access
            privileged_group_id = self.get_group_id_by_name("Privileged_Users")
            self.add_user_to_group(user['id'], privileged_group_id)
            
            # Schedule automatic revocation
            self.schedule_access_revocation(user['id'], privileged_group_id, 
                                          datetime.now() + timedelta(hours=request['duration_hours']))
            
            # Update request status
            request['status'] = 'approved'
            request['approved_by'] = approver_email
            request['approved_date'] = datetime.now().isoformat()
            self.update_access_request(request)
            
            # Send notification to user
            self.send_access_granted_notification(request)
            
            logger.info(f"Privileged access approved: {request_id}")
            return {"status": "success", "request": request}
            
        except Exception as e:
            logger.error(f"Failed to approve privileged access: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def revoke_privileged_access(self, user_id: str, group_id: str) -> Dict:
        """Revoke privileged access"""
        try:
            self.remove_user_from_group(user_id, group_id)
            
            # Log the revocation
            self.log_privileged_access_revocation(user_id, group_id)
            
            return {"status": "success", "revoked_at": datetime.now().isoformat()}
            
        except Exception as e:
            logger.error(f"Failed to revoke privileged access: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    # ==========================================
    # Advanced Security Monitoring
    # ==========================================
    
    def detect_anomalous_behavior(self, hours_back: int = 24) -> List[Dict]:
        """Detect potential security anomalies"""
        logger.info("Starting anomaly detection analysis")
        
        anomalies = []
        logs = self.get_system_logs(hours_back)
        
        # Analyze patterns
        user_activity = {}
        failed_attempts = {}
        
        for log in logs:
            actor_email = log.get('actor', {}).get('alternateId', '')
            event_type = log.get('eventType', '')
            client_geo = log.get('client', {}).get('geographicalContext', {})
            
            # Track user activity
            if actor_email:
                if actor_email not in user_activity:
                    user_activity[actor_email] = []
                user_activity[actor_email].append({
                    'timestamp': log.get('published'),
                    'event_type': event_type,
                    'ip': log.get('client', {}).get('ipAddress'),
                    'location': f"{client_geo.get('city', '')}, {client_geo.get('country', '')}"
                })
            
            # Track failed attempts
            if 'auth_failure' in event_type:
                if actor_email not in failed_attempts:
                    failed_attempts[actor_email] = 0
                failed_attempts[actor_email] += 1
        
        # Detect anomalies
        
        # 1. Multiple failed login attempts
        for user, count in failed_attempts.items():
            if count >= 5:
                anomalies.append({
                    'type': 'multiple_failed_logins',
                    'user': user,
                    'count': count,
                    'severity': 'high' if count >= 10 else 'medium'
                })
        
        # 2. Unusual location access
        for user, activities in user_activity.items():
            locations = set()
            for activity in activities:
                if activity['location'] != ', ':
                    locations.add(activity['location'])
            
            if len(locations) > 3:  # Multiple locations in 24 hours
                anomalies.append({
                    'type': 'multiple_locations',
                    'user': user,
                    'locations': list(locations),
                    'severity': 'medium'
                })
        
        # 3. Off-hours access by privileged users
        privileged_users = self.get_privileged_users()
        for user, activities in user_activity.items():
            if user in [pu['profile']['email'] for pu in privileged_users]:
                for activity in activities:
                    timestamp = datetime.fromisoformat(activity['timestamp'].replace('Z', '+00:00'))
                    hour = timestamp.hour
                    
                    if hour < 6 or hour > 22:  # Outside business hours
                        anomalies.append({
                            'type': 'off_hours_privileged_access',
                            'user': user,
                            'timestamp': activity['timestamp'],
                            'event_type': activity['event_type'],
                            'severity': 'high'
                        })
        
        logger.info(f"Detected {len(anomalies)} potential anomalies")
        return anomalies
    
    def generate_security_dashboard(self) -> Dict:
        """Generate comprehensive security dashboard data"""
        dashboard = {
            'timestamp': datetime.now().isoformat(),
            'metrics': {},
            'alerts': [],
            'trends': {}
        }
        
        # Basic metrics
        users = self.get_users(limit=1000)
        groups = self.get_groups()
        
        dashboard['metrics'] = {
            'total_users': len(users),
            'active_users': len([u for u in users if u['status'] == 'ACTIVE']),
            'privileged_users': len([u for u in users if u['profile'].get('accountType') == 'privileged']),
            'total_groups': len(groups),
            'mfa_enrolled': len([u for u in users if u.get('credentials', {}).get('provider', {}).get('type') == 'OKTA'])
        }
        
        # Security alerts
        anomalies = self.detect_anomalous_behavior()
        dashboard['alerts'] = [a for a in anomalies if a['severity'] == 'high']
        
        # Trends (last 7 days)
        trends = self.calculate_security_trends()
        dashboard['trends'] = trends
        
        return dashboard
    
    # ==========================================
    # Compliance and Reporting
    # ==========================================
    
    def generate_access_certification_report(self, group_name: str) -> Dict:
        """Generate access certification report for a specific group"""
        logger.info(f"Generating access certification report for group: {group_name}")
        
        group = self.get_group_by_name(group_name)
        if not group:
            return {"error": "Group not found"}
        
        group_members = self.get_group_members(group['id'])
        
        certification_data = []
        for member in group_members:
            profile = member['profile']
            
            # Get manager for approval
            manager_email = profile.get('managerEmail', 'No manager assigned')
            
            # Get last login
            last_login = self.get_user_last_login(member['id'])
            
            # Determine risk assessment
            account_type = profile.get('accountType', 'regular')
            department = profile.get('department', 'Unknown')
            
            risk_score = self.calculate_user_risk_score(member)
            
            certification_data.append({
                'user_id': member['id'],
                'email': profile['email'],
                'first_name': profile['firstName'],
                'last_name': profile['lastName'],
                'department': department,
                'account_type': account_type,
                'manager_email': manager_email,
                'last_login': last_login,
                'risk_score': risk_score,
                'requires_review': risk_score > 7 or account_type == 'privileged',
                'applications': self.get_user_applications(member['id'])
            })
        
        report = {
            'group_name': group_name,
            'group_id': group['id'],
            'total_members': len(group_members),
            'high_risk_users': len([u for u in certification_data if u['requires_review']]),
            'generated_date': datetime.now().isoformat(),
            'certification_data': certification_data
        }
        
        # Save report
        self.save_certification_report(report)
        
        return report
    
    def generate_sod_violation_report(self) -> Dict:
        """Generate Segregation of Duties violation report"""
        logger.info("Generating SOD violation report")
        
        # Define conflicting roles/groups
        sod_conflicts = [
            {'group1': 'Finance_Department', 'group2': 'System_Administrators'},
            {'group1': 'HR_Department', 'group2': 'System_Administrators'},
            {'group1': 'Privileged_Users', 'group2': 'External_Auditors'}
        ]
        
        violations = []
        users = self.get_users(limit=1000)
        
        for user in users:
            user_groups = self.get_user_groups(user['id'])
            user_group_names = [g['profile']['name'] for g in user_groups]
            
            # Check for conflicts
            for conflict in sod_conflicts:
                if conflict['group1'] in user_group_names and conflict['group2'] in user_group_names:
                    violations.append({
                        'user_id': user['id'],
                        'user_email': user['profile']['email'],
                        'conflicting_groups': [conflict['group1'], conflict['group2']],
                        'risk_level': 'high',
                        'detected_date': datetime.now().isoformat()
                    })
        
        report = {
            'total_violations': len(violations),
            'violations': violations,
            'generated_date': datetime.now().isoformat()
        }
        
        return report
    
    # ==========================================
    # Webhook Event Handler
    # ==========================================
    
    def process_webhook_event(self, event_data: Dict) -> Dict:
        """Process incoming webhook events from Okta"""
        event_type = event_data.get('eventType', '')
        
        logger.info(f"Processing webhook event: {event_type}")
        
        response = {"status": "processed", "actions_taken": []}
        
        try:
            if event_type == 'user.lifecycle.create':
                # Auto-assign groups based on user attributes
                user_id = event_data['target'][0]['id']
                user_data = self.get_user(user_id)
                
                assignments = self.auto_assign_groups(user_id, user_data['profile'])
                response['actions_taken'].append(f"Auto-assigned to {len(assignments)} groups")
                
            elif event_type == 'user.lifecycle.deactivate':
                # Clean up user resources
                user_id = event_data['target'][0]['id']
                cleanup_result = self.cleanup_deactivated_user(user_id)
                response['actions_taken'].append("User resources cleaned up")
                
            elif event_type == 'user.authentication.auth_via_mfa':
                # Log successful MFA for compliance
                self.log_mfa_compliance_event(event_data)
                response['actions_taken'].append("MFA compliance logged")
                
            elif 'user.account.privilege' in event_type:
                # Monitor privileged account changes
                self.monitor_privileged_account_change(event_data)
                response['actions_taken'].append("Privileged account change monitored")
                
            elif event_type == 'policy.evaluate_sign_on':
                # Analyze policy evaluation for tuning
                self.analyze_policy_evaluation(event_data)
                response['actions_taken'].append("Policy evaluation analyzed")
                
        except Exception as e:
            logger.error(f"Error processing webhook event: {str(e)}")
            response['status'] = 'error'
            response['error'] = str(e)
        
        return response
    
    # ==========================================
    # Helper Methods
    # ==========================================
    
    def create_user_with_activation(self, user_data: Dict) -> Dict:
        """Create user and send activation email"""
        url = f'{self.org_url}/api/v1/users'
        user_data['activate'] = True
        
        response = self.session.post(url, data=json.dumps(user_data))
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to create user: {response.text}")
    
    def auto_assign_groups(self, user_id: str, profile: Dict) -> List[str]:
        """Automatically assign user to groups based on attributes"""
        assignments = []
        
        # Department group
        department = profile.get('department')
        if department:
            dept_group = self.get_group_by_name(f"{department}_Department")
            if dept_group:
                self.add_user_to_group(user_id, dept_group['id'])
                assignments.append(dept_group['profile']['name'])
        
        # Account type group
        account_type = profile.get('accountType', 'regular')
        if account_type == 'privileged':
            priv_group = self.get_group_by_name("Privileged_Users")
            if priv_group:
                self.add_user_to_group(user_id, priv_group['id'])
                assignments.append(priv_group['profile']['name'])
        else:
            regular_group = self.get_group_by_name("Regular_Users")
            if regular_group:
                self.add_user_to_group(user_id, regular_group['id'])
                assignments.append(regular_group['profile']['name'])
        
        return assignments
    
    def generate_request_id(self) -> str:
        """Generate unique request ID"""
        return f"REQ-{datetime.now().strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"
    
    def calculate_user_risk_score(self, user: Dict) -> int:
        """Calculate risk score for a user (1-10 scale)"""
        score = 1
        profile = user['profile']
        
        # Account type factor
        if profile.get('accountType') == 'privileged':
            score += 5
        elif profile.get('accountType') == 'service':
            score += 3
        
        # Department factor
        high_risk_depts = ['IT', 'Finance', 'HR']
        if profile.get('department') in high_risk_depts:
            score += 2
        
        # Last login factor
        last_login = self.get_user_last_login(user['id'])
        if last_login:
            days_since = (datetime.now() - datetime.fromisoformat(last_login.replace('Z', ''))).days
            if days_since > 90:
                score += 2
        
        return min(score, 10)
    
    def get_user_last_login(self, user_id: str) -> Optional[str]:
        """Get user's last login timestamp"""
        # This would query the system logs for the last successful login
        logs = self.get_system_logs(hours_back=720)  # Last 30 days
        
        for log in logs:
            if (log.get('actor', {}).get('id') == user_id and 
                'user.session.start' in log.get('eventType', '')):
                return log.get('published')
        
        return None
    
    # Placeholder methods that would be implemented based on specific requirements
    def store_access_request(self, request: Dict):
        """Store access request in a local JSON file."""
        try:
            filename = "access_requests.json"
            try:
                with open(filename, "r") as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                data = []
            data.append(request)
            with open(filename, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to store access request: {str(e)}")

    def get_access_request(self, request_id: str):
        """Retrieve access request from local JSON file."""
        try:
            filename = "access_requests.json"
            with open(filename, "r") as f:
                data = json.load(f)
            for req in data:
                if req.get("request_id") == request_id:
                    return req
        except Exception as e:
            logger.error(f"Failed to get access request: {str(e)}")
        return None

    def update_access_request(self, request: Dict):
        """Update access request in local JSON file."""
        try:
            filename = "access_requests.json"
            with open(filename, "r") as f:
                data = json.load(f)
            for i, req in enumerate(data):
                if req.get("request_id") == request.get("request_id"):
                    data[i] = request
                    break
            with open(filename, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to update access request: {str(e)}")

    def send_approval_notification(self, request: Dict):
        """Send approval notification email."""
        try:
            sender = "noreply@company.com"
            receiver = request.get("approver_required", "security@company.com")
            subject = f"Privileged Access Request: {request['request_id']}"
            body = f"A privileged access request has been submitted for {request['user_email']} to resource {request['resource']}. Justification: {request['justification']}"
            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = receiver
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            # SMTP server config required for real email
            # smtp = smtplib.SMTP('localhost')
            # smtp.sendmail(sender, receiver, msg.as_string())
            # smtp.quit()
            logger.info(f"Approval notification prepared for {receiver}")
        except Exception as e:
            logger.error(f"Failed to send approval notification: {str(e)}")

    def send_access_granted_notification(self, request: Dict):
        """Send access granted notification email."""
        try:
            sender = "noreply@company.com"
            receiver = request.get("user_email")
            subject = f"Privileged Access Granted: {request['request_id']}"
            body = f"Your privileged access request for resource {request['resource']} has been approved. Duration: {request['duration_hours']} hours."
            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = receiver
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            # SMTP server config required for real email
            # smtp = smtplib.SMTP('localhost')
            # smtp.sendmail(sender, receiver, msg.as_string())
            # smtp.quit()
            logger.info(f"Access granted notification prepared for {receiver}")
        except Exception as e:
            logger.error(f"Failed to send access granted notification: {str(e)}")

    def determine_approver(self, resource: str):
        """Determine approver for a resource."""
        # This could be dynamic based on resource type
        return "security@company.com"

    def schedule_access_revocation(self, user_id: str, group_id: str, revoke_time: datetime):
        """Schedule access revocation (placeholder)."""
        logger.info(f"Access revocation for user {user_id} from group {group_id} scheduled at {revoke_time}")

    def log_privileged_access_revocation(self, user_id: str, group_id: str):
        """Log privileged access revocation."""
        logger.info(f"Privileged access revoked for user {user_id} from group {group_id}")

    def get_privileged_users(self):
        """Return list of privileged users from Okta."""
        users = self.get_users(limit=1000)
        return [u for u in users if u['profile'].get('accountType') == 'privileged']

    def calculate_security_trends(self):
        """Calculate security trends (placeholder)."""
        # Implement trend analysis as needed
        return {}

    def save_certification_report(self, report: Dict):
        """Save certification report to a local file."""
        try:
            filename = f"certification_report_{report.get('group_name', 'unknown')}.json"
            with open(filename, "w") as f:
                json.dump(report, f, indent=2)
            logger.info(f"Certification report saved: {filename}")
        except Exception as e:
            logger.error(f"Failed to save certification report: {str(e)}")

    def cleanup_deactivated_user(self, user_id: str):
        """Cleanup resources for deactivated user (placeholder)."""
        logger.info(f"Cleanup for deactivated user {user_id} completed.")

    def log_mfa_compliance_event(self, event_data: Dict):
        """Log MFA compliance event (placeholder)."""
        logger.info(f"MFA compliance event logged: {event_data}")

    def monitor_privileged_account_change(self, event_data: Dict):
        """Monitor privileged account change (placeholder)."""
        logger.info(f"Privileged account change monitored: {event_data}")

    def analyze_policy_evaluation(self, event_data: Dict):
        """Analyze policy evaluation event (placeholder)."""
        logger.info(f"Policy evaluation analyzed: {event_data}")

# ==========================================
# Usage Example
# ==========================================

if __name__ == "__main__":
    # Replace with your actual values
        ORG_URL = "https://integrator-4203250-admin.okta.com"
        API_TOKEN = "00RpWzcuyAd2gNl1pevZ9wrwapTJlAop9qx57viXS1"
        okta_mgr = AdvancedOktaManager(ORG_URL, API_TOKEN)

        # --- Usage examples for lifecycle workflows ---
        # Example: Automated Joiner Workflow
        joiner_data = {
            "profile": {
                "email": "newuser@example.com",
                "firstName": "New",
                "lastName": "User",
                "department": "IT"
            }
        }
        joiner_result = okta_mgr.automated_joiner_workflow(joiner_data)
        print("Joiner Workflow Result:", joiner_result)

        # Example: Automated Mover Workflow
        mover_result = okta_mgr.automated_mover_workflow("fake_user_id", {"department": "HR"})
        print("Mover Workflow Result:", mover_result)

        # Example: Automated Leaver Workflow
        leaver_result = okta_mgr.automated_leaver_workflow("fake_user_id", datetime.now())
        print("Leaver Workflow Result:", leaver_result)

        # Example: Generate security dashboard
        dashboard = okta_mgr.generate_security_dashboard()
        print(json.dumps(dashboard, indent=2))

        # Example: Detect anomalies
        anomalies = okta_mgr.detect_anomalous_behavior()
        print(f"Found {len(anomalies)} anomalies")

        # Example: Generate access certification report
        cert_report = okta_mgr.generate_access_certification_report("Privileged_Users")
        print(f"Certification report generated for {cert_report.get('total_members', 0)} users")
