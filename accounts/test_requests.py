import requests

try:
    response = requests.get("https://accounts.google.com")
    print("Success:", response.status_code)
except Exception as e:
    print("Error:", e)
