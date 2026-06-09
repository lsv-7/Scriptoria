import requests

url = "http://localhost:5001/signup"
payload = {
    "uid": "test_uid_999",
    "name": "Christopher Nolan",
    "email": "nolan@cineforge.local"
}

try:
    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    print("Headers:", response.headers)
    print("Response JSON:", response.json())
except Exception as e:
    print("Request failed:", e)
