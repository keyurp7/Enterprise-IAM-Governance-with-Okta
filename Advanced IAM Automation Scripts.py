
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

@dataclass
class UserLifecycleEvent:
    event_type: str
    user_id: str
    user_email: str
    timestamp: datetime
    details: Dict

@dataclass
class AccessRequest:
    request_id: str
    user_email: str
    resource: str
    justification: str
    approver: str
    status: str
    created_date: datetime

class AdvancedOktaManager:
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