import requests
import json
import csv
from typing import Dict, List

class OktaManager:
    def __init__(self, org_url: str, api_token: str):
        self.org_url = org_url.rstrip('/')
        self.api_token = api_token
        self.headers = {
            'Authorization': f'SSWS {api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def get_users(self, limit: int = 100) -> List[Dict]:
        """Get all users from Okta"""
        url = f'{self.org_url}/api/v1/users'
        params = {'limit': limit}
        
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching users: {response.status_code}")
            return []
    
    def get_user_by_email(self, email: str) -> Dict:
        """Get specific user by email"""
        url = f'{self.org_url}/api/v1/users/{email}'
        
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching user {email}: {response.status_code}")
            return {}
    
    def create_user(self, user_data: Dict) -> Dict:
        """Create a new user"""
        url = f'{self.org_url}/api/v1/users'
        
        response = requests.post(url, headers=self.headers, 
                               data=json.dumps(user_data))
        if response.status_code == 200:
            print(f"User created successfully: {user_data['profile']['email']}")
            return response.json()
        else:
            print(f"Error creating user: {response.status_code} - {response.text}")
            return {}
    
    def update_user(self, user_id: str, updates: Dict) -> Dict:
        """Update user profile"""
        url = f'{self.org_url}/api/v1/users/{user_id}'
        
        response = requests.post(url, headers=self.headers, 
                               data=json.dumps(updates))
        if response.status_code == 200:
            print(f"User updated successfully: {user_id}")
            return response.json()
        else:
            print(f"Error updating user: {response.status_code}")
            return {}
    
    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user account"""
        url = f'{self.org_url}/api/v1/users/{user_id}/lifecycle/deactivate'
        
        response = requests.post(url, headers=self.headers)
        if response.status_code == 200:
            print(f"User deactivated: {user_id}")
            return True
        else:
            print(f"Error deactivating user: {response.status_code}")
            return False
    
    def get_groups(self) -> List[Dict]:
        """Get all groups"""
        url = f'{self.org_url}/api/v1/groups'
        
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching groups: {response.status_code}")
            return []
    
    def add_user_to_group(self, user_id: str, group_id: str) -> bool:
        """Add user to a group"""
        url = f'{self.org_url}/api/v1/groups/{group_id}/users/{user_id}'
        
        response = requests.put(url, headers=self.headers)
        if response.status_code == 204:
            print(f"User {user_id} added to group {group_id}")
            return True
        else:
            print(f"Error adding user to group: {response.status_code}")
            return False
    
    def generate_access_report(self) -> None:
        """Generate a basic access report"""
        print("=== IAM ACCESS REPORT ===")
        print()
        
        # Get users
        users = self.get_users()
        print(f"Total Users: {len(users)}")
        
        # Count by account type
        regular_count = privileged_count = service_count = 0
        departments = {}
        
        for user in users:
            profile = user.get('profile', {})
            account_type = profile.get('accountType', 'regular')
            department = profile.get('department', 'Unknown')
            
            if account_type == 'regular':
                regular_count += 1
            elif account_type == 'privileged':
                privileged_count += 1
            elif account_type == 'service':
                service_count += 1
                
            departments[department] = departments.get(department, 0) + 1
        
        print(f"Regular Users: {regular_count}")
        print(f"Privileged Users: {privileged_count}")
        print(f"Service Accounts: {service_count}")
        print()
        
        print("Users by Department:")
        for dept, count in departments.items():
            print(f"  {dept}: {count}")
        print()
        
        # Get groups
        groups = self.get_groups()
        print(f"Total Groups: {len(groups)}")
        print()

# Usage example
if __name__ == "__main__":
    # Use your actual Okta domain and API token
    ORG_URL = "https://integrator-4203250-admin.okta.com"
    API_TOKEN = "00RpWzcuyAd2gNl1pevZ9wrwapTJlAop9qx57viXS1"

    okta = OktaManager(ORG_URL, API_TOKEN)

    # Generate access report
    okta.generate_access_report()