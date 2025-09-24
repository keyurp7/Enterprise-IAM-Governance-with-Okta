"""Enterprise IAM Platform Settings

Centralized configuration management for the IAM platform.
Supports multiple environments and secure credential handling.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings with environment-based configuration."""
    
    def __init__(self):
        self.BASE_DIR = Path(__file__).parent.parent
        self.load_settings()
        
    def load_settings(self):
        """Load all configuration settings."""
        # Core Application
        self.DEBUG = self.get_bool('DEBUG', False)
        self.ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
        self.SECRET_KEY = os.getenv('SECRET_KEY', self._generate_secret_key())
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        
        # Server Configuration
        self.HOST = os.getenv('HOST', '0.0.0.0')
        self.PORT = int(os.getenv('PORT', 8000))
        self.WEB_CONCURRENCY = int(os.getenv('WEB_CONCURRENCY', 4))
        
        # Okta Configuration
        self.OKTA_DOMAIN = os.getenv('OKTA_DOMAIN')
        self.OKTA_API_TOKEN = os.getenv('OKTA_API_TOKEN')
        self.OKTA_CLIENT_ID = os.getenv('OKTA_CLIENT_ID')
        self.OKTA_CLIENT_SECRET = os.getenv('OKTA_CLIENT_SECRET')
        
        # Database Configuration
        self.DATABASE_URL = os.getenv('DATABASE_URL')
        self.REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        
        # Security Configuration
        self.JWT_SECRET = os.getenv('JWT_SECRET', self.SECRET_KEY)
        self.ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
        self.SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', 3600))
        
        # External Integrations
        self.SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
        self.SPLUNK_HEC_TOKEN = os.getenv('SPLUNK_HEC_TOKEN')
        self.SPLUNK_HEC_URL = os.getenv('SPLUNK_HEC_URL')
        
        # Monitoring & Alerting
        self.MONITORING_ENABLED = self.get_bool('MONITORING_ENABLED', True)
        self.ALERT_EMAIL = os.getenv('ALERT_EMAIL')
        
        # Compliance Settings
        self.AUDIT_LOG_RETENTION_DAYS = int(os.getenv('AUDIT_LOG_RETENTION_DAYS', 365))
        self.COMPLIANCE_REPORTS_ENABLED = self.get_bool('COMPLIANCE_REPORTS_ENABLED', True)
        self.SOX_COMPLIANCE = self.get_bool('SOX_COMPLIANCE', False)
        self.PCI_COMPLIANCE = self.get_bool('PCI_COMPLIANCE', False)
        
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean environment variable."""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def _generate_secret_key(self) -> str:
        """Generate a random secret key for development."""
        import secrets
        return secrets.token_urlsafe(32)
    
    def validate_required_settings(self) -> Dict[str, Any]:
        """Validate that all required settings are present."""
        errors = []
        
        if not self.OKTA_DOMAIN:
            errors.append('OKTA_DOMAIN is required')
        if not self.OKTA_API_TOKEN:
            errors.append('OKTA_API_TOKEN is required')
            
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def get_database_config(self) -> Dict[str, str]:
        """Get database configuration dictionary."""
        if not self.DATABASE_URL:
            return {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': str(self.BASE_DIR / 'db.sqlite3'),
                }
            }
        
        return {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': self.DATABASE_URL.split('/')[-1],
                'USER': self.DATABASE_URL.split('@')[0].split(':')[-2],
                'PASSWORD': self.DATABASE_URL.split('@')[0].split(':')[-1],
                'HOST': self.DATABASE_URL.split('@')[1].split(':')[0],
                'PORT': self.DATABASE_URL.split('@')[1].split(':')[1].split('/')[0],
            }
        }

# Global settings instance
settings = Settings()

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
        'json': {
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'detailed',
            'level': settings.LOG_LEVEL
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/iam_platform.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
            'level': settings.LOG_LEVEL
        }
    },
    'root': {
        'level': settings.LOG_LEVEL,
        'handlers': ['console', 'file']
    }
}