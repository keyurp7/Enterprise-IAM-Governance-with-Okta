"""
IAM Project Deployment Script (Python)
Automates IAM project setup, dependency installation, and Flask server startup for Windows.
Optimized for clarity, error handling, and idempotency.
"""
import os
import sys
import subprocess
from pathlib import Path

# Utility function for safe file creation
def write_file(path, content):
    if not os.path.exists(path):
        with open(path, 'w') as f:
            f.write(content)

# Step 1: Create project directory structure
folders = [
    'scripts/user-management',
    'scripts/monitoring',
    'scripts/reporting',
    'scripts/automation',
    'configs/okta',
    'configs/security',
    'docs/screenshots',
    'docs/architecture',
    'docs/procedures',
    'data',
    'logs',
    'tests'
]
for folder in folders:
    Path(folder).mkdir(parents=True, exist_ok=True)

# Step 2: Create requirements.txt
requirements = (
    "requests>=2.28.0\n"
    "flask>=2.0.0\n"
    "pandas>=1.4.0\n"
    "faker>=18.0.0\n"
    "python-dotenv>=0.19.0\n"
    "schedule>=1.1.0\n"
    "cryptography>=3.4.0\n"
    "matplotlib>=3.5.0\n"
    "seaborn>=0.11.0\n"
    "openpyxl>=3.0.0\n"
    "jinja2>=3.0.0\n"
)
write_file('requirements.txt', requirements)

# Step 3: Create .env.template
env_template = (
    "# Okta Configuration\n"
    "OKTA_ORG_URL=https://integrator-4203250-admin.okta.com\n"
    "OKTA_API_TOKEN=00RpWzcuyAd2gNl1pevZ9wrwapTJlAop9qx57viX...\n"
    "OKTA_CLIENT_ID=your-client-id\n"
    "OKTA_CLIENT_SECRET=your-client-secret\n\n"
    "# Security Configuration\n"
    "WEBHOOK_SECRET=your-webhook-secret-here\n"
    "JWT_SECRET=your-jwt-secret-here\n"
    "ENCRYPTION_KEY=your-32-byte-encryption-key-here\n\n"
    "# Database Configuration\n"
    "DATABASE_URL=sqlite:///iam_events.db\n\n"
    "# Email Configuration (Optional)\n"
    "SMTP_SERVER=smtp.gmail.com\n"
    "SMTP_PORT=587\n"
    "SMTP_USERNAME=your-email@company.com\n"
    "SMTP_PASSWORD=your-app-password\n\n"
    "# Dashboard Configuration\n"
    "DASHBOARD_PORT=5000\n"
    "DASHBOARD_HOST=0.0.0.0\n"
    "DEBUG_MODE=True\n\n"
    "# Logging Configuration\n"
    "LOG_LEVEL=INFO\n"
    "LOG_FILE=logs/iam-project.log\n"
)
write_file('.env.template', env_template)

# Step 4: Create Dockerfile
write_file('Dockerfile',
    "FROM python:3.9-slim\n"
    "WORKDIR /app\n"
    "COPY requirements.txt .\n"
    "RUN pip install --no-cache-dir -r requirements.txt\n"
    "COPY . .\n"
    "EXPOSE 5000\n"
    "CMD [\"python\", \"webhook_dashboard.py\"]\n"
)

# Step 5: Create docker-compose.yml
write_file('docker-compose.yml',
    "version: '3.8'\n"
    "services:\n"
    "  iam-dashboard:\n"
    "    build: .\n"
    "    ports:\n"
    "      - '5000:5000'\n"
    "    environment:\n"
    "      - FLASK_ENV=production\n"
    "    volumes:\n"
    "      - ./data:/app/data\n"
    "      - ./logs:/app/logs\n"
    "    restart: unless-stopped\n"
    "  iam-scheduler:\n"
    "    build: .\n"
    "    command: python automation_scheduler.py\n"
    "    volumes:\n"
    "      - ./data:/app/data\n"
    "      - ./logs:/app/logs\n"
    "    depends_on:\n"
    "      - iam-dashboard\n"
    "    restart: unless-stopped\n"
)

# Step 6: Create virtual environment
venv_dir = ".venv"
if not os.path.exists(venv_dir):
    print("Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
else:
    print("Virtual environment already exists.")

# Step 7: Install dependencies
pip_path = os.path.join(venv_dir, "Scripts", "python.exe")
print("Installing dependencies...")
subprocess.run([pip_path, "-m", "pip", "install", "--upgrade", "pip"], check=True)
subprocess.run([pip_path, "-m", "pip", "install", "-r", "requirements.txt"], check=True)

# Step 8: Print next steps
print("\n🎉 IAM Project deployment completed successfully!")
print("📋 Next Steps:")
print("1. Copy .env.template to .env and update with your Okta credentials")
print("2. Run validation: python scripts/validate_deployment.py")
print("3. Start the dashboard: python Webhook Handler and Security Dashboard.py")
print("4. Generate documentation: python scripts/generate_docs.py")
print("🔗 Dashboard: http://localhost:5000")
print("🔗 Webhook endpoint: http://localhost:5000/webhooks/okta")