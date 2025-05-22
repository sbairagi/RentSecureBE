import requests

BASE_URL = "http://localhost:8000/api"

# === CONFIGURATION (All Unique) ===
USERNAME = "shubh"  # unique
EMAIL = "shubh@example.com"  # unique
PASSWORD = "Start2025@1234"
NEW_PASSWORD = "Changed2025@1234"
RESET_PASSWORD = "ResetNow2025@1234"
FULL_NAME = "Shubham Bairagi"
PHONE = "9876543211"  # unique

# 1. Register a new user
def register_user():
    print("\n--- Registering User ---")
    data = {
        "username": USERNAME,
        "email": EMAIL,
        "password": PASSWORD,
        "full_name": FULL_NAME,
        "phone": PHONE
    }
    res = requests.post(f"{BASE_URL}/register/", json=data)
    print(res.status_code, res.json())

# 2. Login user to get JWT tokens
def login_user():
    print("\n--- Logging In ---")
    data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    res = requests.post(f"{BASE_URL}/login/", data=data)
    print(res.status_code, res.json())
    return res.json().get("access"), res.json().get("refresh")

# 3. Refresh token
def refresh_token(refresh):
    print("\n--- Refreshing Token ---")
    res = requests.post(f"{BASE_URL}/api/token/refresh/", json={"refresh": refresh})
    print(res.status_code, res.json())
    return res.json().get("access")

# 4. Change Password
def change_password(token):
    print("\n--- Changing Password ---")
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "old_password": PASSWORD,
        "new_password": NEW_PASSWORD
    }
    res = requests.put(f"{BASE_URL}/change-password/", json=data, headers=headers)
    print(res.status_code, res.json())

# 5. Reset Password without login
def reset_password():
    print("\n--- Resetting Password ---")
    data = {
        "username": USERNAME,
        "new_password": RESET_PASSWORD
    }
    res = requests.post(f"{BASE_URL}/reset-password/", json=data)
    print(res.status_code, res.json())

# 6. Get App List (protected)
def get_apps(token):
    print("\n--- Getting App List ---")
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(f"{BASE_URL}/apps/", headers=headers)
    print(res.status_code, res.json())

# 7. Post & Get Logs
def test_logs(token):
    print("\n--- Posting Log ---")
    headers = {"Authorization": f"Bearer {token}"}
    post_data = {
        "app": 1,
        "prompt": "What's the weather today?",
        "response": "It's sunny and warm."
    }
    res_post = requests.post(f"{BASE_URL}/logs/", json=post_data, headers=headers)
    print("POST:", res_post.status_code, res_post.json())

    print("\n--- Getting Logs ---")
    res_get = requests.get(f"{BASE_URL}/logs/", headers=headers)
    print("GET:", res_get.status_code, res_get.json())

# === Run All ===
if __name__ == "__main__":
    register_user()
    access_token, refresh = login_user()

    if access_token and refresh:
        access_token = refresh_token(refresh)
        change_password(access_token)
        get_apps(access_token)
        test_logs(access_token)

    reset_password()  # works without login

