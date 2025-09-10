# ==========================================
# Flask Webhook Handler and Dashboard
# ==========================================
from flask import Flask, request, jsonify, render_template_string
import json
import hashlib
import hmac
from datetime import datetime, timedelta
import sqlite3
import threading
import time
from collections import defaultdict

app = Flask(__name__)

# ==========================================
# Health Check Endpoint
# ==========================================
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "Server is running"})

# ==========================================
# Okta API Credentials
# ==========================================
ORG_URL = "https://integrator-4203250-admin.okta.com"
API_TOKEN = "00RpWzcuyAd2gNl1pevZ9wrwapTJlAop9qx57viXS1"

# ==========================================
# Database Setup for Demo
# ==========================================

def init_database():
    conn = sqlite3.connect('iam_events.db')
    cursor = conn.cursor()
    
    # Events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT,
            user_email TEXT,
            timestamp TEXT,
            details TEXT,
            severity TEXT
        )
    ''')
    
    # Access requests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS access_requests (
            request_id TEXT PRIMARY KEY,
            user_email TEXT,
            resource TEXT,
            justification TEXT,
            status TEXT,
            created_date TEXT,
            approved_by TEXT,
            approved_date TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# ==========================================
# Webhook Endpoints
# ==========================================

@app.route('/webhooks/okta', methods=['POST'])
def okta_webhook():
    """Handle Okta webhook events"""
    try:
        # Verify webhook signature (in production)
        # signature = request.headers.get('X-Okta-Verification-Challenge')
        # if not verify_okta_signature(request.data, signature):
        #     return jsonify({"error": "Invalid signature"}), 401
        
        event_data = request.json
        
        # Process the event
        result = process_okta_event(event_data)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def process_okta_event(event_data):
    """Process incoming Okta events"""
    event_type = event_data.get('eventType', '')
    published = event_data.get('published', '')
    actor = event_data.get('actor', {})
    target = event_data.get('target', [{}])
    
    user_email = actor.get('alternateId', 'Unknown')
    
    # Determine event severity
    severity = determine_event_severity(event_type, event_data)
    
    # Store event in database
    store_event(event_type, user_email, published, json.dumps(event_data), severity)
    
    # Process specific event types
    actions = []
    
    if event_type == 'user.lifecycle.create':
        actions.append("User account created - triggering onboarding workflow")
        trigger_onboarding_workflow(target[0].get('id'))
        
    elif event_type == 'user.lifecycle.deactivate':
        actions.append("User account deactivated - triggering offboarding workflow")
        trigger_offboarding_workflow(target[0].get('id'))
        
    elif 'authentication.auth_failure' in event_type:
        actions.append("Failed login detected - checking for brute force")
        check_brute_force_attack(user_email, event_data)
        
    elif 'user.account.privilege' in event_type:
        actions.append("Privilege change detected - logging for audit")
        log_privilege_change(user_email, event_data)
        
    elif event_type == 'user.authentication.auth_via_mfa':
        actions.append("MFA authentication successful - updating compliance metrics")
        update_mfa_metrics(user_email)
    
    return {
        "status": "processed",
        "event_type": event_type,
        "actions": actions,
        "severity": severity
    }

def determine_event_severity(event_type, event_data):
    """Determine event severity (stub)"""
    return "info"

# --- Stub implementations for missing functions ---
def store_event(event_type, user_email, published, details, severity):
    # Stub: Store event in database
    pass

def trigger_onboarding_workflow(user_id):
    # Real Okta API call: Fetch user details
    import requests
    url = f"{ORG_URL}/api/v1/users/{user_id}"
    headers = {
        "Authorization": f"SSWS {API_TOKEN}",
        "Accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        print(f"Onboarding user: {response.json().get('profile', {}).get('email', user_id)}")
    else:
        print(f"Failed to fetch user {user_id}: {response.text}")

def trigger_offboarding_workflow(user_id):
    # Stub: Trigger offboarding workflow
    pass

def check_brute_force_attack(user_email, event_data):
    # Stub: Check for brute force attack
    pass

def log_privilege_change(user_email, event_data):
    # Stub: Log privilege change
    pass

def update_mfa_metrics(user_email):
    # Stub: Update MFA metrics
    pass

@app.route('/')
def index():
    return "<h2>Okta IAM Flask Server is running.<br>Health: <a href='/health'>/health</a><br>Webhook: POST to /webhooks/okta</h2>", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)