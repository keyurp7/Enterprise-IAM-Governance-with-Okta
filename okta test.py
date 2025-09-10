def list_groups():
    url = f"{OKTA_DOMAIN}/api/v1/groups"
    print(f"Requesting: {url}")
    response = requests.get(url, headers=headers)
    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        groups = response.json()
        for group in groups:
            print(f"Group: {group.get('profile', {}).get('name')}, ID: {group.get('id')}")
    else:
        print("Full response:")
        print(response.text)
        if response.status_code == 401:
            print("401 Unauthorized: Check your API token, Okta domain, and permissions.")
        elif response.status_code == 403:
            print("403 Forbidden: Your token may not have the required permissions.")
        else:
            print(f"Error: {response.status_code}")
import requests


OKTA_DOMAIN = "https://integrator-4203250-admin.okta.com"   # Your Okta domain (no trailing slash)
API_TOKEN = "00RpWzcuyAd2gNl1pevZ9wrwapTJlAop9qx57viXS1"   # API token you created

# Common headers for authentication
headers = {
    "Authorization": f"SSWS {API_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}


def list_users():
    url = f"{OKTA_DOMAIN}/api/v1/users"
    print(f"Requesting: {url}")
    print(f"Using token: {API_TOKEN}")
    print(f"Headers: {headers}")
    response = requests.get(url, headers=headers)

    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        users = response.json()
        for user in users:
            profile = user.get("profile", {})
            print(f"Login: {profile.get('login')}, Email: {profile.get('email')}")
    else:
        print("Full response:")
        print(response.text)
        if response.status_code == 401:
            print("401 Unauthorized: Check your API token, Okta domain, and permissions.")
        elif response.status_code == 403:
            print("403 Forbidden: Your token may not have the required permissions.")
        else:
            print(f"Error: {response.status_code}")

if __name__ == "__main__":
    # list_users()
    list_groups()
