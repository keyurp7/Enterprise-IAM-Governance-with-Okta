#!/usr/bin/env python3
"""
Real-time Security Webhook Dashboard
Enterprise IAM Security Monitoring and Event Processing
"""

from flask import Flask, request, jsonify, render_template_string, Response
from flask_socketio import SocketIO, emit
import json
import logging
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from collections import defaultdict, deque
import hashlib
import hmac
import os
from typing import Dict, List
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables for real-time monitoring
recent_events = deque(maxlen=1000)
security_metrics = defaultdict(int)
active_alerts = []
threat_score = 0
connection_count = 0

# Risk scoring weights
RISK_WEIGHTS = {
    'failed_login': 2,
    'login_from_new_location': 3,
    'off_hours_access': 1,
    'privileged_access_granted': 4,
    'multiple_failed_attempts': 5,
    'account_locked': 3,
    'password_reset': 1,
    'suspicious_activity': 8
}

class SecurityDashboard:
    """Main security dashboard class"""
    
    def __init__(self):
        self.db_path = "security_events.db"
        self.init_database()
        self.anomaly_detector = AnomalyDetector()
        self.alert_manager = AlertManager()
        
    def init_database(self):
        """Initialize SQLite database for event storage"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE,
                    event_type TEXT,
                    user_id TEXT,
                    user_login TEXT,
                    timestamp DATETIME,
                    source_ip TEXT,
                    user_agent TEXT,
                    location TEXT,
                    risk_score INTEGER,
                    details TEXT,
                    processed BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT UNIQUE,
                    alert_type TEXT,
                    severity TEXT,
                    title TEXT,
                    description TEXT,
                    user_id TEXT,
                    created_at DATETIME,
                    resolved_at DATETIME,
                    status TEXT DEFAULT 'active'
                )
            ''')
            
            # Metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT,
                    metric_value INTEGER,
                    timestamp DATETIME
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ Database initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {str(e)}")

    def process_event(self, event_data: Dict) -> Dict:
        """Process incoming security event"""
        try:
            # Extract event details
            event_id = event_data.get('uuid', f"evt_{int(time.time())}")
            event_type = event_data.get('eventType', 'unknown')
            user_id = event_data.get('actor', {}).get('id', 'unknown')
            user_login = event_data.get('actor', {}).get('alternateId', 'unknown')
            timestamp = datetime.fromisoformat(event_data.get('published', datetime.now().isoformat()).replace('Z', '+00:00'))
            
            # Client information
            client_info = event_data.get('client', {})
            source_ip = client_info.get('ipAddress', 'unknown')
            user_agent = client_info.get('userAgent', {}).get('rawUserAgent', 'unknown')
            
            # Geographic information
            geo_info = client_info.get('geographicalContext', {})
            location = f"{geo_info.get('city', 'Unknown')}, {geo_info.get('country', 'Unknown')}"
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(event_type, event_data)
            
            # Store in database
            self._store_event({
                'event_id': event_id,
                'event_type': event_type,
                'user_id': user_id,
                'user_login': user_login,
                'timestamp': timestamp,
                'source_ip': source_ip,
                'user_agent': user_agent,
                'location': location,
                'risk_score': risk_score,
                'details': json.dumps(event_data)
            })
            
            # Add to recent events for real-time display
            display_event = {
                'id': event_id,
                'type': event_type,
                'user': user_login,
                'timestamp': timestamp.isoformat(),
                'ip': source_ip,
                'location': location,
                'risk_score': risk_score,
                'severity': self._get_severity_level(risk_score)
            }
            
            recent_events.appendleft(display_event)
            
            # Update metrics
            security_metrics['total_events'] += 1
            security_metrics[f'event_{event_type.replace(".", "_")}'] += 1
            
            # Check for anomalies and generate alerts
            anomalies = self.anomaly_detector.detect_anomalies(display_event, list(recent_events))
            for anomaly in anomalies:
                alert = self.alert_manager.create_alert(anomaly, display_event)
                if alert:
                    active_alerts.append(alert)
            
            # Emit real-time update
            socketio.emit('new_event', display_event)
            socketio.emit('metrics_update', dict(security_metrics))
            
            return display_event
            
        except Exception as e:
            logger.error(f"❌ Error processing event: {str(e)}")
            return {}

    def _calculate_risk_score(self, event_type: str, event_data: Dict) -> int:
        """Calculate risk score for event"""
        base_score = RISK_WEIGHTS.get(event_type.split('.')[-1], 1)
        
        # Additional risk factors
        multiplier = 1.0
        
        # Check for failed outcomes
        if event_data.get('outcome', {}).get('result') == 'FAILURE':
            multiplier += 0.5
        
        # Check for suspicious patterns
        client_info = event_data.get('client', {})
        if client_info.get('ipAddress', '').startswith('10.'):  # Internal IP
            multiplier -= 0.2
        
        # Geographic risk
        geo_info = client_info.get('geographicalContext', {})
        high_risk_countries = ['CN', 'RU', 'IR', 'KP']  # Example high-risk countries
        if geo_info.get('country') in high_risk_countries:
            multiplier += 1.0
        
        return int(base_score * multiplier)

    def _get_severity_level(self, risk_score: int) -> str:
        """Get severity level based on risk score"""
        if risk_score >= 8:
            return 'critical'
        elif risk_score >= 5:
            return 'high'
        elif risk_score >= 3:
            return 'medium'
        else:
            return 'low'

    def _store_event(self, event: Dict):
        """Store event in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO events 
                (event_id, event_type, user_id, user_login, timestamp, source_ip, 
                 user_agent, location, risk_score, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event['event_id'], event['event_type'], event['user_id'],
                event['user_login'], event['timestamp'], event['source_ip'],
                event['user_agent'], event['location'], event['risk_score'],
                event['details']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error storing event: {str(e)}")

    def get_dashboard_data(self) -> Dict:
        """Get comprehensive dashboard data"""
        try:
            # Get recent events (last 24 hours)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Recent events
            cursor.execute('''
                SELECT event_type, user_login, timestamp, source_ip, location, risk_score
                FROM events 
                WHERE timestamp > datetime('now', '-24 hours')
                ORDER BY timestamp DESC
                LIMIT 100
            ''')
            
            recent_db_events = [
                {
                    'type': row[0],
                    'user': row[1],
                    'timestamp': row[2],
                    'ip': row[3],
                    'location': row[4],
                    'risk_score': row[5],
                    'severity': self._get_severity_level(row[5])
                }
                for row in cursor.fetchall()
            ]
            
            # Security metrics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_events,
                    COUNT(DISTINCT user_id) as unique_users,
                    AVG(risk_score) as avg_risk_score,
                    SUM(CASE WHEN risk_score >= 8 THEN 1 ELSE 0 END) as critical_events,
                    SUM(CASE WHEN risk_score >= 5 THEN 1 ELSE 0 END) as high_risk_events
                FROM events 
                WHERE timestamp > datetime('now', '-24 hours')
            ''')
            
            metrics_row = cursor.fetchone()
            dashboard_metrics = {
                'total_events': metrics_row[0] or 0,
                'unique_users': metrics_row[1] or 0,
                'avg_risk_score': round(metrics_row[2] or 0, 1),
                'critical_events': metrics_row[3] or 0,
                'high_risk_events': metrics_row[4] or 0
            }
            
            # Top risk users
            cursor.execute('''
                SELECT user_login, COUNT(*) as event_count, AVG(risk_score) as avg_risk
                FROM events 
                WHERE timestamp > datetime('now', '-24 hours')
                GROUP BY user_login
                ORDER BY avg_risk DESC, event_count DESC
                LIMIT 10
            ''')
            
            top_risk_users = [
                {
                    'user': row[0],
                    'event_count': row[1],
                    'avg_risk': round(row[2], 1)
                }
                for row in cursor.fetchall()
            ]
            
            # Event timeline (hourly breakdown)
            cursor.execute('''
                SELECT 
                    strftime('%H', timestamp) as hour,
                    COUNT(*) as count,
                    AVG(risk_score) as avg_risk
                FROM events 
                WHERE timestamp > datetime('now', '-24 hours')
                GROUP BY hour
                ORDER BY hour
            ''')
            
            timeline_data = [
                {
                    'hour': int(row[0]),
                    'count': row[1],
                    'avg_risk': round(row[2], 1)
                }
                for row in cursor.fetchall()
            ]
            
            conn.close()
            
            return {
                'recent_events': recent_db_events,
                'metrics': dashboard_metrics,
                'top_risk_users': top_risk_users,
                'timeline': timeline_data,
                'active_alerts': active_alerts[-10:],  # Last 10 alerts
                'current_threat_level': self._calculate_threat_level()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting dashboard data: {str(e)}")
            return {}

    def _calculate_threat_level(self) -> str:
        """Calculate current threat level"""
        if len(active_alerts) >= 5:
            return 'critical'
        elif len(active_alerts) >= 3:
            return 'high'
        elif len(active_alerts) >= 1:
            return 'medium'
        else:
            return 'low'

class AnomalyDetector:
    """Advanced anomaly detection for security events"""
    
    def __init__(self):
        self.user_baselines = defaultdict(dict)
        self.global_patterns = defaultdict(list)
    
    def detect_anomalies(self, current_event: Dict, recent_events: List[Dict]) -> List[Dict]:
        """Detect anomalies in current event"""
        anomalies = []
        
        try:
            user = current_event.get('user', 'unknown')
            event_type = current_event.get('type', '')
            
            # 1. Multiple failed login attempts
            failed_logins = [
                e for e in recent_events[-20:] 
                if e.get('user') == user and 'failed' in e.get('type', '').lower()
                and (datetime.now() - datetime.fromisoformat(e.get('timestamp', datetime.now().isoformat()))).total_seconds() < 300
            ]
            
            if len(failed_logins) >= 3:
                anomalies.append({
                    'type': 'multiple_failed_attempts',
                    'severity': 'high',
                    'description': f'Multiple failed login attempts: {len(failed_logins)} in 5 minutes',
                    'user': user
                })
            
            # 2. Geographic anomaly
            user_locations = [
                e.get('location', '') for e in recent_events[-50:]
                if e.get('user') == user and e.get('location')
            ]
            
            if user_locations:
                current_location = current_event.get('location', '')
                if current_location not in user_locations[-10:] and current_location != 'Unknown, Unknown':
                    anomalies.append({
                        'type': 'geographic_anomaly',
                        'severity': 'medium',
                        'description': f'Login from new location: {current_location}',
                        'user': user
                    })
            
            # 3. Off-hours access
            event_time = datetime.fromisoformat(current_event.get('timestamp', datetime.now().isoformat()))
            if event_time.hour < 6 or event_time.hour > 22:
                if 'login' in event_type.lower():
                    anomalies.append({
                        'type': 'off_hours_access',
                        'severity': 'low',
                        'description': f'Off-hours login at {event_time.strftime("%H:%M")}',
                        'user': user
                    })
            
            # 4. Rapid successive events
            user_events_last_minute = [
                e for e in recent_events[-20:]
                if e.get('user') == user and (datetime.now() - datetime.fromisoformat(e.get('timestamp', datetime.now().isoformat()))).total_seconds() < 60
            ]
            
            if len(user_events_last_minute) >= 10:
                anomalies.append({
                    'type': 'rapid_events',
                    'severity': 'medium',
                    'description': f'Rapid successive events: {len(user_events_last_minute)} in 1 minute',
                    'user': user
                })
            
            # 5. High-risk score pattern
            if current_event.get('risk_score', 0) >= 8:
                anomalies.append({
                    'type': 'high_risk_event',
                    'severity': 'critical',
                    'description': f'High-risk security event detected (score: {current_event.get("risk_score")})',
                    'user': user
                })
        
        except Exception as e:
            logger.error(f"❌ Error in anomaly detection: {str(e)}")
        
        return anomalies

class AlertManager:
    """Manage security alerts and notifications"""
    
    def __init__(self):
        self.alert_history = []
    
    def create_alert(self, anomaly: Dict, event: Dict) -> Dict:
        """Create alert from detected anomaly"""
        try:
            alert = {
                'id': f"ALERT-{int(time.time())}-{len(self.alert_history)}",
                'type': anomaly.get('type'),
                'severity': anomaly.get('severity', 'medium'),
                'title': f"Security Alert: {anomaly.get('type', 'Unknown').replace('_', ' ').title()}",
                'description': anomaly.get('description'),
                'user': anomaly.get('user'),
                'event_id': event.get('id'),
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
            # Store alert
            self.alert_history.append(alert)
            
            # Emit real-time alert
            socketio.emit('new_alert', alert)
            
            logger.warning(f"🚨 Security alert created: {alert['title']}")
            
            return alert
            
        except Exception as e:
            logger.error(f"❌ Error creating alert: {str(e)}")
            return {}

# Initialize dashboard
dashboard = SecurityDashboard()

# Flask Routes

@app.route('/')
def dashboard_home():
    """Serve the main dashboard interface"""
    return render_template_string(DASHBOARD_HTML_TEMPLATE)

@app.route('/api/dashboard-data')
def get_dashboard_data():
    """API endpoint for dashboard data"""
    return jsonify(dashboard.get_dashboard_data())

@app.route('/webhook/okta', methods=['POST'])
def okta_webhook():
    """Okta webhook endpoint for receiving security events"""
    try:
        # Verify webhook signature (in production)
        # signature = request.headers.get('X-Okta-Signature')
        # if not verify_okta_signature(request.data, signature):
        #     return jsonify({'error': 'Invalid signature'}), 401
        
        event_data = request.json
        if not event_data:
            return jsonify({'error': 'No data received'}), 400
        
        # Process the event
        processed_event = dashboard.process_event(event_data)
        
        logger.info(f"📥 Webhook event processed: {event_data.get('eventType', 'unknown')}")
        
        return jsonify({
            'status': 'success',
            'event_id': processed_event.get('id'),
            'processed_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Webhook processing error: {str(e)}")
        return jsonify({'error': 'Processing failed'}), 500

@app.route('/api/alerts')
def get_alerts():
    """Get active security alerts"""
    return jsonify({
        'alerts': active_alerts,
        'count': len(active_alerts)
    })

@app.route('/api/metrics')
def get_metrics():
    """Get current security metrics"""
    return jsonify(dict(security_metrics))

@app.route('/api/events/simulate', methods=['POST'])
def simulate_event():
    """Simulate security event for testing"""
    try:
        event_type = request.json.get('type', 'user.session.start')
        
        # Generate simulated event
        simulated_event = {
            'uuid': f'sim-{int(time.time())}',
            'eventType': event_type,
            'published': datetime.now().isoformat() + 'Z',
            'actor': {
                'id': f'user-{int(time.time()) % 1000}',
                'alternateId': f'test.user{int(time.time()) % 100}@company.com'
            },
            'client': {
                'ipAddress': f'192.168.{int(time.time()) % 255}.{int(time.time()) % 255}',
                'userAgent': {
                    'rawUserAgent': 'Mozilla/5.0 (Simulated Event)'
                },
                'geographicalContext': {
                    'city': 'Test City',
                    'country': 'US'
                }
            },
            'outcome': {
                'result': 'SUCCESS' if int(time.time()) % 2 == 0 else 'FAILURE'
            }
        }
        
        # Process the simulated event
        processed_event = dashboard.process_event(simulated_event)
        
        return jsonify({
            'status': 'success',
            'event': processed_event
        })
        
    except Exception as e:
        logger.error(f"❌ Event simulation error: {str(e)}")
        return jsonify({'error': 'Simulation failed'}), 500

# SocketIO Events

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    global connection_count
    connection_count += 1
    emit('connection_status', {'connected': True, 'total_connections': connection_count})
    logger.info(f"🔌 Client connected (total: {connection_count})")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    global connection_count
    connection_count = max(0, connection_count - 1)
    logger.info(f"🔌 Client disconnected (total: {connection_count})")

@socketio.on('request_dashboard_data')
def handle_dashboard_request():
    """Handle dashboard data request"""
    data = dashboard.get_dashboard_data()
    emit('dashboard_data', data)

# Background Tasks

def cleanup_old_events():
    """Cleanup old events from memory and database"""
    while True:
        try:
            # Clean up old alerts (older than 24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            global active_alerts
            active_alerts = [
                alert for alert in active_alerts
                if datetime.fromisoformat(alert['created_at']) > cutoff_time
            ]
            
            # Clean up database (older than 30 days)
            conn = sqlite3.connect(dashboard.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM events WHERE timestamp < datetime('now', '-30 days')")
            cursor.execute("DELETE FROM alerts WHERE created_at < datetime('now', '-30 days')")
            conn.commit()
            conn.close()
            
            logger.info("🧹 Cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Cleanup error: {str(e)}")
        
        time.sleep(3600)  # Run every hour

# HTML Dashboard Template
DASHBOARD_HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enterprise IAM Security Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }
        
        .dashboard-container {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            grid-template-rows: auto auto 1fr;
            gap: 20px;
            padding: 20px;
            min-height: 100vh;
        }
        
        .header {
            grid-column: 1 / -1;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            text-align: center;
        }
        
        .header h1 {
            color: #4c63d2;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .threat-level {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .threat-low { background: #4ade80; color: white; }
        .threat-medium { background: #fbbf24; color: white; }
        .threat-high { background: #f87171; color: white; }
        .threat-critical { background: #dc2626; color: white; animation: pulse 2s infinite; }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .metrics-grid {
            grid-column: 1 / -1;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .metric-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            text-align: center;
        }
        
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #4c63d2;
            margin-bottom: 5px;
        }
        
        .metric-label {
            color: #666;
            font-size: 0.9em;
        }
        
        .dashboard-panel {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
            padding: 20px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        
        .panel-title {
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 15px;
            color: #4c63d2;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 8px;
        }
        
        .events-list {
            flex: 1;
            overflow-y: auto;
            max-height: 400px;
        }
        
        .event-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            border-left: 4px solid #e5e7eb;
            margin-bottom: 8px;
            background: #f9fafb;
            border-radius: 8px;
            font-size: 0.9em;
        }
        
        .event-item.severity-low { border-left-color: #10b981; }
        .event-item.severity-medium { border-left-color: #f59e0b; }
        .event-item.severity-high { border-left-color: #ef4444; }
        .event-item.severity-critical { border-left-color: #dc2626; animation: glow 2s infinite; }
        
        @keyframes glow {
            0%, 100% { box-shadow: 0 0 5px rgba(220, 38, 38, 0.5); }
            50% { box-shadow: 0 0 15px rgba(220, 38, 38, 0.8); }
        }
        
        .event-user {
            font-weight: bold;
            color: #4c63d2;
        }
        
        .event-time {
            font-size: 0.8em;
            color: #666;
        }
        
        .alert-item {
            background: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 10px;
        }
        
        .alert-title {
            font-weight: bold;
            color: #dc2626;
            margin-bottom: 5px;
        }
        
        .alert-description {
            font-size: 0.9em;
            color: #666;
        }
        
        .status-indicator {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 15px;
            background: rgba(16, 185, 129, 0.9);
            color: white;
            border-radius: 20px;
            font-size: 0.9em;
        }
        
        .status-indicator.disconnected {
            background: rgba(239, 68, 68, 0.9);
        }
        
        .simulate-controls {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.95);
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        }
        
        .simulate-btn {
            background: #4c63d2;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 5px;
            cursor: pointer;
            margin: 2px;
            font-size: 0.8em;
        }
        
        .simulate-btn:hover {
            background: #3730a3;
        }
        
        .chart-container {
            position: relative;
            height: 250px;
            margin-top: 15px;
        }
        
        .risk-user-item {
            display: flex;
            justify-content: space-between;
            padding: 8px;
            background: #f9fafb;
            border-radius: 5px;
            margin-bottom: 5px;
        }
        
        .user-name {
            font-weight: bold;
            color: #4c63d2;
        }
        
        .user-risk {
            color: #ef4444;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <!-- Header -->
        <div class="header">
            <h1>🛡️ Enterprise IAM Security Dashboard</h1>
            <div>
                Current Threat Level: <span id="threatLevel" class="threat-level threat-low">Low</span>
            </div>
        </div>
        
        <!-- Metrics -->
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value" id="totalEvents">0</div>
                <div class="metric-label">Total Events (24h)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="uniqueUsers">0</div>
                <div class="metric-label">Unique Users</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="avgRiskScore">0</div>
                <div class="metric-label">Avg Risk Score</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="criticalEvents">0</div>
                <div class="metric-label">Critical Events</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="activeAlerts">0</div>
                <div class="metric-label">Active Alerts</div>
            </div>
        </div>
        
        <!-- Recent Events -->
        <div class="dashboard-panel">
            <div class="panel-title">🔍 Recent Security Events</div>
            <div class="events-list" id="eventsList">
                <div style="text-align: center; color: #666; padding: 20px;">
                    Waiting for events...
                </div>
            </div>
        </div>
        
        <!-- Active Alerts -->
        <div class="dashboard-panel">
            <div class="panel-title">🚨 Active Alerts</div>
            <div class="events-list" id="alertsList">
                <div style="text-align: center; color: #666; padding: 20px;">
                    No active alerts
                </div>
            </div>
        </div>
        
        <!-- Top Risk Users -->
        <div class="dashboard-panel">
            <div class="panel-title">👥 Top Risk Users</div>
            <div class="events-list" id="riskUsersList">
                <div style="text-align: center; color: #666; padding: 20px;">
                    Loading user data...
                </div>
            </div>
        </div>
    </div>
    
    <!-- Status Indicator -->
    <div class="status-indicator" id="connectionStatus">🔌 Connected</div>
    
    <!-- Simulation Controls -->
    <div class="simulate-controls">
        <div style="margin-bottom: 10px; font-weight: bold;">🧪 Test Events</div>
        <button class="simulate-btn" onclick="simulateEvent('user.session.start')">Login</button>
        <button class="simulate-btn" onclick="simulateEvent('user.authentication.failed')">Failed Auth</button>
        <button class="simulate-btn" onclick="simulateEvent('user.account.lock')">Account Lock</button>
        <button class="simulate-btn" onclick="simulateEvent('user.session.start', true)">Suspicious Login</button>
    </div>
    
    <script>
        // Initialize Socket.IO connection
        const socket = io();
        let isConnected = false;
        
        // Connection status
        socket.on('connect', function() {
            isConnected = true;
            document.getElementById('connectionStatus').textContent = '🔌 Connected';
            document.getElementById('connectionStatus').classList.remove('disconnected');
            loadDashboardData();
        });
        
        socket.on('disconnect', function() {
            isConnected = false;
            document.getElementById('connectionStatus').textContent = '🔌 Disconnected';
            document.getElementById('connectionStatus').classList.add('disconnected');
        });
        
        // Real-time event updates
        socket.on('new_event', function(event) {
            addEventToList(event);
            updateEventCount();
        });
        
        // Real-time alert updates
        socket.on('new_alert', function(alert) {
            addAlertToList(alert);
            updateAlertCount();
            playAlertSound();
        });
        
        // Metrics updates
        socket.on('metrics_update', function(metrics) {
            updateMetrics(metrics);
        });
        
        // Dashboard data update
        socket.on('dashboard_data', function(data) {
            updateDashboard(data);
        });
        
        // Load initial dashboard data
        function loadDashboardData() {
            fetch('/api/dashboard-data')
                .then(response => response.json())
                .then(data => updateDashboard(data))
                .catch(error => console.error('Error loading dashboard data:', error));
        }
        
        // Update entire dashboard
        function updateDashboard(data) {
            // Update metrics
            if (data.metrics) {
                document.getElementById('totalEvents').textContent = data.metrics.total_events || 0;
                document.getElementById('uniqueUsers').textContent = data.metrics.unique_users || 0;
                document.getElementById('avgRiskScore').textContent = data.metrics.avg_risk_score || 0;
                document.getElementById('criticalEvents').textContent = data.metrics.critical_events || 0;
            }
            
            // Update threat level
            if (data.current_threat_level) {
                updateThreatLevel(data.current_threat_level);
            }
            
            // Update events list
            if (data.recent_events) {
                updateEventsList(data.recent_events);
            }
            
            // Update alerts
            if (data.active_alerts) {
                updateAlertsList(data.active_alerts);
                document.getElementById('activeAlerts').textContent = data.active_alerts.length;
            }
            
            // Update top risk users
            if (data.top_risk_users) {
                updateRiskUsersList(data.top_risk_users);
            }
        }
        
        // Update threat level indicator
        function updateThreatLevel(level) {
            const element = document.getElementById('threatLevel');
            element.className = `threat-level threat-${level}`;
            element.textContent = level.charAt(0).toUpperCase() + level.slice(1);
        }
        
        // Update events list
        function updateEventsList(events) {
            const eventsList = document.getElementById('eventsList');
            eventsList.innerHTML = '';
            
            if (events.length === 0) {
                eventsList.innerHTML = '<div style="text-align: center; color: #666; padding: 20px;">No recent events</div>';
                return;
            }
            
            events.slice(0, 20).forEach(event => {
                addEventToList(event, false);
            });
        }
        
        // Add single event to list
        function addEventToList(event, prepend = true) {
            const eventsList = document.getElementById('eventsList');
            
            // Remove "waiting for events" message
            if (eventsList.innerHTML.includes('Waiting for events')) {
                eventsList.innerHTML = '';
            }
            
            const eventElement = document.createElement('div');
            eventElement.className = `event-item severity-${event.severity || 'low'}`;
            
            const timestamp = new Date(event.timestamp).toLocaleTimeString();
            
            eventElement.innerHTML = `
                <div>
                    <div class="event-user">${event.user}</div>
                    <div style="font-size: 0.8em; color: #666;">${event.type}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-weight: bold; color: ${getSeverityColor(event.severity)};">
                        Risk: ${event.risk_score}
                    </div>
                    <div class="event-time">${timestamp}</div>
                </div>
            `;
            
            if (prepend) {
                eventsList.insertBefore(eventElement, eventsList.firstChild);
            } else {
                eventsList.appendChild(eventElement);
            }
            
            // Limit to 50 events in view
            while (eventsList.children.length > 50) {
                eventsList.removeChild(eventsList.lastChild);
            }
        }
        
        // Update alerts list
        function updateAlertsList(alerts) {
            const alertsList = document.getElementById('alertsList');
            alertsList.innerHTML = '';
            
            if (alerts.length === 0) {
                alertsList.innerHTML = '<div style="text-align: center; color: #666; padding: 20px;">No active alerts</div>';
                return;
            }
            
            alerts.forEach(alert => {
                addAlertToList(alert, false);
            });
        }
        
        // Add single alert to list
        function addAlertToList(alert, prepend = true) {
            const alertsList = document.getElementById('alertsList');
            
            // Remove "no alerts" message
            if (alertsList.innerHTML.includes('No active alerts')) {
                alertsList.innerHTML = '';
            }
            
            const alertElement = document.createElement('div');
            alertElement.className = 'alert-item';
            
            const timestamp = new Date(alert.created_at).toLocaleTimeString();
            
            alertElement.innerHTML = `
                <div class="alert-title">${alert.title}</div>
                <div class="alert-description">${alert.description}</div>
                <div style="font-size: 0.8em; color: #666; margin-top: 5px;">
                    User: ${alert.user} | ${timestamp}
                </div>
            `;
            
            if (prepend) {
                alertsList.insertBefore(alertElement, alertsList.firstChild);
            } else {
                alertsList.appendChild(alertElement);
            }
        }
        
        // Update risk users list
        function updateRiskUsersList(riskUsers) {
            const riskUsersList = document.getElementById('riskUsersList');
            riskUsersList.innerHTML = '';
            
            if (riskUsers.length === 0) {
                riskUsersList.innerHTML = '<div style="text-align: center; color: #666; padding: 20px;">No risk data available</div>';
                return;
            }
            
            riskUsers.forEach(user => {
                const userElement = document.createElement('div');
                userElement.className = 'risk-user-item';
                
                userElement.innerHTML = `
                    <div>
                        <div class="user-name">${user.user}</div>
                        <div style="font-size: 0.8em; color: #666;">${user.event_count} events</div>
                    </div>
                    <div class="user-risk">${user.avg_risk}</div>
                `;
                
                riskUsersList.appendChild(userElement);
            });
        }
        
        // Utility functions
        function getSeverityColor(severity) {
            const colors = {
                'low': '#10b981',
                'medium': '#f59e0b',
                'high': '#ef4444',
                'critical': '#dc2626'
            };
            return colors[severity] || '#666';
        }
        
        function updateEventCount() {
            // This could be enhanced to show real-time event counts
        }
        
        function updateAlertCount() {
            const alertCount = document.querySelectorAll('.alert-item').length;
            document.getElementById('activeAlerts').textContent = alertCount;
        }
        
        function playAlertSound() {
            // Simple alert sound (can be enhanced with actual audio)
            if ('vibrate' in navigator) {
                navigator.vibrate(200);
            }
        }
        
        // Simulation functions
        function simulateEvent(eventType, highRisk = false) {
            const payload = {
                type: eventType
            };
            
            if (highRisk) {
                // Add parameters that would trigger higher risk scores
                payload.suspicious = true;
            }
            
            fetch('/api/events/simulate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            })
            .then(response => response.json())
            .then(data => {
                console.log('Event simulated:', data);
            })
            .catch(error => {
                console.error('Simulation error:', error);
            });
        }
        
        // Auto-refresh dashboard data every 30 seconds
        setInterval(() => {
            if (isConnected) {
                socket.emit('request_dashboard_data');
            }
        }, 30000);
        
        // Initialize dashboard on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadDashboardData();
        });
    </script>
</body>
</html>
'''

def verify_okta_signature(payload: bytes, signature: str) -> bool:
    """Verify Okta webhook signature"""
    try:
        webhook_secret = os.getenv('OKTA_WEBHOOK_SECRET', 'default-secret')
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception:
        return False

def start_background_tasks():
    """Start background cleanup tasks"""
    cleanup_thread = threading.Thread(target=cleanup_old_events, daemon=True)
    cleanup_thread.start()

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('audit_logs', exist_ok=True)
    os.makedirs('certifications', exist_ok=True)
    os.makedirs('scheduled_jobs', exist_ok=True)
    os.makedirs('welcome_packages', exist_ok=True)
    os.makedirs('approvals/pending', exist_ok=True)
    
    # Start background tasks
    start_background_tasks()
    
    # Print startup information
    print("🚀 Starting Enterprise IAM Security Dashboard...")
    print("📊 Dashboard URL: http://localhost:5000")
    print("🔗 Webhook URL: http://localhost:5000/webhook/okta")
    print("📱 API Docs: http://localhost:5000/api/dashboard-data")
    print("🧪 Test Events: Use the simulation controls in the dashboard")
    print("="*60)
    
    # Start the Flask-SocketIO server
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False,
        allow_unsafe_werkzeug=True
    )