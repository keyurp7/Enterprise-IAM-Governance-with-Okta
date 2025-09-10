
import csv
from advanced_iam_scripts import AdvancedOktaManager

ORG_URL = "https://integrator-4203250-admin.okta.com"
API_TOKEN = "00RpWzcuyAd2gNl1pevZ9wrwapTJlAop9qx57viXS1"
EMPLOYEE_CSV = "bulk_import_summary.csv"  # Change if your file is different

# Read employeeNumber and managerId (as employeeId) from CSV
employee_data = []
with open(EMPLOYEE_CSV, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        employeeNumber = row.get('employeeNumber')
        employeeId = row.get('managerId') or row.get('employeeId') or row.get('employeeNumber')
        employee_data.append({
            'employeeNumber': employeeNumber,
            'employeeId': employeeId
        })

okta_mgr = AdvancedOktaManager(ORG_URL, API_TOKEN)

# Update method to accept dicts and set both employeeNumber and employeeId
def bulk_update_employee_number_and_id(okta_mgr, employee_data):
    users = okta_mgr.get_users(limit=len(employee_data))
    count = min(len(users), len(employee_data))
    results = []
    for i in range(count):
        user = users[i]
        user_id = user['id']
        emp_num = employee_data[i]['employeeNumber']
        emp_id = employee_data[i]['employeeId']
        payload = {"employeeNumber": emp_num, "employeeId": emp_id}
        try:
            update_result = okta_mgr.update_user_profile(user_id, payload)
            results.append({"user_id": user_id, "email": user['profile'].get('email'), "employeeNumber": emp_num, "employeeId": emp_id, "status": "success"})
            print(f"Updated user {user['profile'].get('email')} with employeeNumber {emp_num} and employeeId {emp_id}")
        except Exception as e:
            results.append({"user_id": user_id, "email": user['profile'].get('email'), "employeeNumber": emp_num, "employeeId": emp_id, "status": "failed", "error": str(e)})
            print(f"Failed to update user {user['profile'].get('email')}: {str(e)}")
    return results

results = bulk_update_employee_number_and_id(okta_mgr, employee_data)
