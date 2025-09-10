import requests
from datetime import datetime, timedelta
import json

class OktaMonitor:
    def __init__(self, org_url: str, api_token: str):
        self.org_url = org_url.rstrip('/')
        self.api_token = api_token
        self.headers = {
            'Authorization': f'SSWS {api_token}',
            'Accept': 'application/json'
        }
    
    def get_system_logs(self, hours_back=24):
        """Get system logs for the last N hours"""
        since = datetime.utcnow() - timedelta(hours=hours_back)
        since_str = since.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        url = f'{self.org_url}/api/v1/logs'
        params = {
            'since': since_str,
            'limit': 100
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching logs: {response.status_code}")
            return []
    
    def analyze_security_events(self):
        """Analyze logs for security events"""
        logs = self.get_system_logs()
        
        failed_logins = []
        mfa_events = []
        privileged_actions = []
        
        for log in logs:
            event_type = log.get('eventType', '')
            
            if 'authentication.auth_via_mfa' in event_type:
                mfa_events.append(log)
            elif 'user.authentication.auth_failure' in event_type:
                failed_logins.append(log)
            elif 'user.account.privilege' in event_type:
                privileged_actions.append(log)
        
        print("=== SECURITY ANALYSIS REPORT ===")
        print(f"Total Events Analyzed: {len(logs)}")
        print(f"Failed Login Attempts: {len(failed_logins)}")
        print(f"MFA Authentication Events: {len(mfa_events)}")
        print(f"Privileged Account Actions: {len(privileged_actions)}")
        print()
        
        # Show recent failed logins
        if failed_logins:
            print("Recent Failed Logins:")
            for event in failed_logins[:5]:
                timestamp = event.get('published', '')
                actor = event.get('actor', {}).get('displayName', 'Unknown')
                print(f"  {timestamp} - {actor}")
        
        return {
            'total_events': len(logs),
            'failed_logins': len(failed_logins),
            'mfa_events': len(mfa_events),
            'privileged_actions': len(privileged_actions)
        }

# Usage
if __name__ == "__main__":
    ORG_URL = "https://integrator-4203250-admin.okta.com"
    API_TOKEN = "00RpWzcuyAd2gNl1pevZ9wrwapTJlAop9qx57viXS1"

    monitor = OktaMonitor(ORG_URL, API_TOKEN)
    monitor.analyze_security_events()