from advanced_iam_scripts import AdvancedOktaManager
import json

ORG_URL = "https://integrator-4203250-admin.okta.com"
API_TOKEN = "00RpWzcuyAd2gNl1pevZ9wrwapTJlAop9qx57viXS1"

okta_mgr = AdvancedOktaManager(ORG_URL, API_TOKEN)

# Define privileged groups (adjust as needed)
privileged_groups = [
    "System_Administrators",
    "Privileged_Users",
    "External_Auditors"
]

users = okta_mgr.get_users(limit=1000)
least_privilege_violations = []

for user in users:
    user_groups = okta_mgr.get_user_groups(user['id'])
    user_group_names = [g['profile']['name'] for g in user_groups]
    # If user is in any privileged group, check if they are also in non-privileged groups
    if any(group in user_group_names for group in privileged_groups):
        # Example: flag if user is in more than one privileged group or in both privileged and regular groups
        priv_count = sum(1 for group in user_group_names if group in privileged_groups)
        if priv_count > 1 or (priv_count >= 1 and len(user_group_names) > priv_count):
            least_privilege_violations.append({
                "user_id": user['id'],
                "user_email": user['profile']['email'],
                "groups": user_group_names,
                "privileged_group_count": priv_count,
                "detected_date": str(json.dumps(user.get('lastLogin', 'N/A')))
            })

# Save violations to a file
with open("least_privilege_violations.json", "w") as f:
    json.dump(least_privilege_violations, f, indent=2)

print(f"Total least privilege violations found: {len(least_privilege_violations)}")
for v in least_privilege_violations:
    print(v)
