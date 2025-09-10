from advanced_iam_scripts import AdvancedOktaManager
import json

ORG_URL = "https://integrator-4203250-admin.okta.com"
API_TOKEN = "00RpWzcuyAd2gNl1pevZ9wrwapTJlAop9qx57viXS1"

okta_mgr = AdvancedOktaManager(ORG_URL, API_TOKEN)

# Define fine-grained SOD rules (example: cannot be in both Finance and IT, or HR and System Admin, etc.)
fine_grained_conflicts = [
    {"group_names": ["Finance_Department", "System_Administrators"]},
    {"group_names": ["HR_Department", "System_Administrators"]},
    {"group_names": ["Privileged_Users", "External_Auditors"]},
    # Add more fine-grained rules as needed
]

users = okta_mgr.get_users(limit=1000)
violations = []

for user in users:
    user_groups = okta_mgr.get_user_groups(user['id'])
    user_group_names = [g['profile']['name'] for g in user_groups]
    for conflict in fine_grained_conflicts:
        if all(group in user_group_names for group in conflict['group_names']):
            violations.append({
                "user_id": user['id'],
                "user_email": user['profile']['email'],
                "conflicting_groups": conflict['group_names'],
                "risk_level": "high",
                "detected_date": str(json.dumps(user.get('lastLogin', 'N/A')))
            })

# Save violations to a file
with open("sod_violations_fine_grained.json", "w") as f:
    json.dump(violations, f, indent=2)

print(f"Total fine-grained SOD violations found: {len(violations)}")
for v in violations:
    print(v)
