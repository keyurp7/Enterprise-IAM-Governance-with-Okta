#!/usr/bin/env python3

# ==========================================
# IAM Project Interactive Demo Script
# ==========================================

import time
import json
import random
from datetime import datetime, timedelta
from advanced_iam_scripts import AdvancedOktaManager
import os
from dotenv import load_dotenv

load_dotenv()

class IAMProjectDemo:
    def __init__(self):
        # Use your real Okta tenant values if .env is not set
        self.org_url = os.getenv('OKTA_ORG_URL', 'https://integrator-4203250-admin.okta.com')
        self.api_token = os.getenv('OKTA_API_TOKEN', '00RpWzcuyAd2gNl1pevZ9wrwapTJlAop9qx57viXS1')
        self.okta = AdvancedOktaManager(self.org_url, self.api_token)
        
    def print_banner(self, title):
        """Print formatted banner for sections"""
        print("\n" + "=" * 60)
        print(f"🎯 {title}")
        print("=" * 60)
    
    def print_step(self, step_num, description):
        """Print formatted step"""
        print(f"\n📍 Step {step_num}: {description}")
        print("-" * 40)
    
    def wait_for_user(self, message="Press Enter to continue..."):
        """Wait for user input"""
        input(f"\n⏸️  {message}")
    
    def simulate_typing(self, text, delay=0.03):
        """Simulate typing effect"""
        for char in text:
            print(char, end='', flush=True)
            time.sleep(delay)
        print()
    
    def demo_user_lifecycle(self):
        """Demonstrate automated user lifecycle management"""
        self.print_banner("USER LIFECYCLE MANAGEMENT DEMO")
        
        # Step 1: New Employee Onboarding
        self.print_step(1, "New Employee Onboarding")
        
        new_employee = {
            "profile": {
                "firstName": "Sarah",
                "lastName": "Johnson",
                "email": "sarah.johnson@company.com",
                "login": "sarah.johnson@company.com",
                "employeeId": "EMP2024",
                "department": "IT",
                "costCenter": "CC-IT-001",
                "managerEmail": "manager@company.com",
                "accountType": "regular",
                "riskLevel": "low",
                "jobTitle": "Software Engineer",
                "location": "US_East"
            }
        }
        
        print("👤 Creating new employee profile...")
        self.simulate_typing(json.dumps(new_employee, indent=2))
        
        self.wait_for_user("Ready to execute joiner workflow?")
        
        # Simulate joiner workflow
        print("🚀 Executing automated joiner workflow...")
        workflow_result = self.okta.automated_joiner_workflow(new_employee)
        time.sleep(2)
        if workflow_result.get("status") == "success":
            print("✅ Account created successfully!")
            steps = workflow_result.get("workflow_steps", [])
            for step in steps:
                if step["step"] == "group_assignment":
                    print(f"✅ Assigned to groups: {', '.join(step['groups'])}")
                if step["step"] == "application_provisioning":
                    print(f"✅ Provisioned applications: {', '.join(step['apps'])}")
            print("✅ Welcome email sent with setup instructions")
            print("✅ Access review scheduled for 90 days")
        else:
            print(f"❌ Joiner workflow failed: {workflow_result.get('error')}")
        
        self.wait_for_user()
        
        # Step 2: Employee Role Change (Mover)
        self.print_step(2, "Employee Role Change")
        
        print("📝 Sarah gets promoted to Senior Software Engineer...")
        print("🔄 Department change: IT → IT (same)")
        print("🔄 Job title change: Software Engineer → Senior Software Engineer")
        print("🔄 Account type change: regular → privileged")
        
        self.wait_for_user("Execute mover workflow?")
        
        print("🔄 Executing automated mover workflow...")
        mover_attributes = new_employee["profile"].copy()
        mover_attributes["jobTitle"] = "Senior Software Engineer"
        mover_attributes["accountType"] = "privileged"
        workflow_result = self.okta.automated_mover_workflow(workflow_result.get('user_id', ''), mover_attributes)
        time.sleep(2)
        if workflow_result.get("status") == "success":
            print("✅ Profile updated with new job title")
            print("✅ Added to Privileged_Users group")
            print("✅ MFA enforcement applied")
            print("✅ Access recertification triggered")
            print("✅ Manager notified of changes")
        else:
            print(f"❌ Mover workflow failed: {workflow_result.get('error')}")
        
        self.wait_for_user()
        
        # Step 3: Employee Departure (Leaver)
        self.print_step(3, "Employee Departure")
        
        print("👋 Sarah is leaving the company...")
        print("📅 Last working day: Today")
        
        self.wait_for_user("Execute leaver workflow?")
        
        print("🔒 Executing automated leaver workflow...")
        last_day = datetime.now()
        workflow_result = self.okta.automated_leaver_workflow(workflow_result.get('user_id', ''), last_day)
        time.sleep(2)
        if workflow_result.get("status") == "success":
            print("✅ Account suspended immediately")
            print(f"✅ Removed from all groups ({workflow_result['workflow_steps'][1]['count']} groups)")
            print(f"✅ Application access revoked ({workflow_result['workflow_steps'][2]['count']} applications)")
            print("✅ Offboarding report generated")
            print("✅ Account deactivation scheduled for 30 days")
            print("✅ Manager and HR notified")
        else:
            print(f"❌ Leaver workflow failed: {workflow_result.get('error')}")
    
    def demo_privileged_access(self):
        """Demonstrate privileged access management"""
        self.print_banner("PRIVILEGED ACCESS MANAGEMENT DEMO")
        
        # Step 1: Access Request
        self.print_step(1, "Privileged Access Request")
        
        print("👨‍💼 John Smith (regular user) needs temporary admin access")
        print("🎯 Resource: AWS Production Console")
        print("⏱️  Duration: 4 hours")
        print("📋 Justification: Emergency database maintenance")
        
        self.wait_for_user("Submit access request?")
        
        print("📤 Submitting privileged access request...")
        request_data = {
            "request_id": "REQ-20241201-A7B3",
            "user_email": "john.smith@company.com",
            "resource": "AWS Production Console",
            "justification": "Emergency database maintenance for customer issue #12345",
            "duration_hours": 4,
            "status": "pending_approval",
            "approver_required": "security@company.com"
        }
        
        time.sleep(1)
        print(f"✅ Request created: {request_data['request_id']}")
        print(f"✅ Approval notification sent to: {request_data['approver_required']}")
        
        self.wait_for_user()
        
        # Step 2: Approval Process
        self.print_step(2, "Approval Workflow")
        
        print("👨‍💼 Security team reviews the request...")
        print("🔍 Checking user's current permissions")
        print("🔍 Validating business justification")
        print("🔍 Confirming emergency ticket #12345")
        
        self.wait_for_user("Approve the request?")
        
        print("✅ Request approved by security@company.com")
        print("🔐 Granting temporary privileged access...")
        time.sleep(2)
        print("✅ User added to Privileged_Users group")
        print("✅ AWS Console access granted")
        print("✅ Session monitoring enabled")
        print("✅ Auto-revocation scheduled for 4 hours")
        print("📧 User notified: Access granted")
        
        self.wait_for_user()
        
        # Step 3: Access Monitoring
        self.print_step(3, "Real-time Access Monitoring")
        
        print("👀 Monitoring privileged session...")
        time.sleep(1)
        print("📊 Login detected: john.smith@company.com → AWS Console")
        print("🌍 Location: New York, NY (expected)")
        print("🖥️  Device: Company laptop (trusted)")
        print("⏰ Session start: 14:30 UTC")
        print("🔐 MFA verified: Okta Verify")
        
        time.sleep(2)
        print("\n📈 Session Activity:")
        activities = [
            "Accessed RDS Console",
            "Viewed database performance metrics", 
            "Executed read-only queries",
            "Generated performance report",
            "Applied database index optimization"
        ]
        
        for activity in activities:
            print(f"  • {activity}")
            time.sleep(0.5)
        
        self.wait_for_user()
        
        # Step 4: Automatic Revocation
        self.print_step(4, "Automatic Access Revocation")
        
        print("⏰ 4 hours have elapsed...")
        print("🔒 Executing automatic access revocation...")
        time.sleep(2)
        print("✅ Removed from Privileged_Users group")
        print("✅ AWS Console access revoked") 
        print("✅ Session terminated gracefully")
        print("✅ Access revocation logged for audit")
        print("📧 User notified: Access expired")
        
        # Generate access summary
        print("\n📋 Access Summary Report:")
        print(f"  Request ID: {request_data['request_id']}")
        print("  Duration: 4 hours (as requested)")
        print("  Activities: 5 actions logged")
        print("  Violations: None detected")
        print("  Status: Completed successfully")

if __name__ == "__main__":
    demo = IAMProjectDemo()
    demo.demo_user_lifecycle()
    demo.demo_privileged_access()
    # Uncomment below when demo_security_monitoring is implemented
    # demo.demo_security_monitoring()
    
    def demo_security_monitoring(self):
        """Demonstrate security monitoring and anomaly detection"""
        self.print_banner("SECURITY MONITORING & ANOMALY DETECTION")
        
        # Step 1: Real-time Event Processing
        self.print_