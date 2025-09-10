from advanced_iam_scripts import AdvancedOktaManager

ORG_URL = "https://integrator-4203250-admin.okta.com"
API_TOKEN = "00RpWzcuyAd2gNl1pevZ9wrwapTJlAop9qx57viXS1"

okta_mgr = AdvancedOktaManager(ORG_URL, API_TOKEN)
activated_users = okta_mgr.activate_all_staged_users()

print(f"Activated {len(activated_users)} staged users.")

def activate_all_users_except_excluded(excluded_emails=None):
	manager = AdvancedOktaManager()
	users = manager.get_all_users()
	activated_count = 0
	for user in users:
		email = user.get('profile', {}).get('email', '').lower()
		status = user.get('status', '').lower()
		if excluded_emails and email in excluded_emails:
			continue
		if status != 'active':
			success = manager.activate_user(user['id'])
			if success:
				activated_count += 1
	print(f"Activated {activated_count} users.")

if __name__ == "__main__":
	# Exclude Keyur and Vishal
	excluded_emails = ["keyur@corp.com", "vishal@corp.com"]
	activate_all_users_except_excluded(excluded_emails)
from advanced_iam_scripts import AdvancedOktaManager

ORG_URL = "https://integrator-4203250-admin.okta.com"
API_TOKEN = "00RpWzcuyAd2gNl1pevZ9wrwapTJlAop9qx57viXS1"

okta_mgr = AdvancedOktaManager(ORG_URL, API_TOKEN)
activated_users = okta_mgr.activate_all_staged_users()

print(f"Activated {len(activated_users)} staged users.")
