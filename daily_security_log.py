from advanced_iam_scripts import AdvancedOktaManager
import json
import logging
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

ORG_URL = "https://integrator-4203250-admin.okta.com"
API_TOKEN = "00RpWzcuyAd2gNl1pevZ9wrwapTJlAop9qx57viXS1"
KEYUR_EMAIL = "Keyur_7@outlook.com"

okta_mgr = AdvancedOktaManager(ORG_URL, API_TOKEN)

# Collect security events (SOD, least privilege, MFA)
log_entries = []

# SOD violations
try:
    users = okta_mgr.get_users(limit=1000)
    sod_violations = []
    fine_grained_conflicts = [
        {"group_names": ["Finance_Department", "System_Administrators"]},
        {"group_names": ["HR_Department", "System_Administrators"]},
        {"group_names": ["Privileged_Users", "External_Auditors"]},
    ]
    for user in users:
        user_groups = okta_mgr.get_user_groups(user['id'])
        user_group_names = [g['profile']['name'] for g in user_groups]
        for conflict in fine_grained_conflicts:
            if all(group in user_group_names for group in conflict['group_names']):
                sod_violations.append({
                    "user_id": user['id'],
                    "user_email": user['profile']['email'],
                    "conflicting_groups": conflict['group_names'],
                    "risk_level": "high",
                    "detected_date": datetime.now().isoformat()
                })
    if sod_violations:
        log_entries.append({"type": "SOD Violation", "details": sod_violations})
except Exception as e:
    log_entries.append({"type": "SOD Error", "details": str(e)})

# Least privilege violations
try:
    privileged_groups = ["System_Administrators", "Privileged_Users", "External_Auditors"]
    least_privilege_violations = []
    for user in users:
        user_groups = okta_mgr.get_user_groups(user['id'])
        user_group_names = [g['profile']['name'] for g in user_groups]
        priv_count = sum(1 for group in user_group_names if group in privileged_groups)
        if priv_count > 1 or (priv_count >= 1 and len(user_group_names) > priv_count):
            least_privilege_violations.append({
                "user_id": user['id'],
                "user_email": user['profile']['email'],
                "groups": user_group_names,
                "privileged_group_count": priv_count,
                "detected_date": datetime.now().isoformat()
            })
    if least_privilege_violations:
        log_entries.append({"type": "Least Privilege Violation", "details": least_privilege_violations})
except Exception as e:
    log_entries.append({"type": "Least Privilege Error", "details": str(e)})

# MFA enforcement violations
try:
    mfa_violations = []
    for user in users:
        user_id = user['id']
        factors = okta_mgr.get_user_factors(user_id)
        mfa_enrolled = any(factor.get('factorType') in ['token:software:totp', 'sms', 'push', 'call', 'question', 'webauthn', 'u2f'] for factor in factors)
        if not mfa_enrolled:
            mfa_violations.append({
                "user_id": user_id,
                "user_email": user['profile']['email'],
                "status": user['status'],
                "mfa_enrolled": mfa_enrolled,
                "detected_date": datetime.now().isoformat()
            })
    if mfa_violations:
        log_entries.append({"type": "MFA Enforcement Violation", "details": mfa_violations})
except Exception as e:
    log_entries.append({"type": "MFA Enforcement Error", "details": str(e)})

# Write log file
log_filename = f"security_log_{datetime.now().strftime('%Y-%m-%d')}.json"
with open(log_filename, "w") as f:
    json.dump(log_entries, f, indent=2)

# Email log file to Keyur
try:
    with open(log_filename, "r") as f:
        log_content = f.read()
    msg = MIMEText(log_content)
    msg['Subject'] = f"Daily Okta Security Log {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = "noreply@company.com"
    msg['To'] = KEYUR_EMAIL
    # SMTP config required for real email
    # smtp = smtplib.SMTP('localhost')
    # smtp.sendmail(msg['From'], [msg['To']], msg.as_string())
    # smtp.quit()
    print(f"Security log file '{log_filename}' prepared and would be sent to {KEYUR_EMAIL}.")
except Exception as e:
    print(f"Failed to prepare/send email: {str(e)}")
