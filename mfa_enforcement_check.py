from advanced_iam_scripts import AdvancedOktaManager
import json

ORG_URL = "https://integrator-4203250-admin.okta.com"
API_TOKEN = "00RpWzcuyAd2gNl1pevZ9wrwapTJlAop9qx57viXS1"

okta_mgr = AdvancedOktaManager(ORG_URL, API_TOKEN)

# Example: MFA enforcement check for all users
users = okta_mgr.get_users(limit=1000)
mfa_violations = []

for user in users:
    user_id = user['id']
    factors = okta_mgr.get_user_factors(user_id)
    mfa_enrolled = any(factor.get('factorType') in ['token:software:totp', 'sms', 'push', 'call', 'question', 'webauthn', 'u2f'] for factor in factors)
    # If not enrolled, flag as violation
    if not mfa_enrolled:
        mfa_violations.append({
            "user_id": user_id,
            "user_email": user['profile']['email'],
            "status": user['status'],
            "mfa_enrolled": mfa_enrolled
        })

# Save violations to a file
with open("mfa_enforcement_violations.json", "w") as f:
    json.dump(mfa_violations, f, indent=2)

print(f"Total MFA enforcement violations found: {len(mfa_violations)}")
for v in mfa_violations:
    print(v)
