import requests
def send_firebase_notification(token, title, body, data=None):
    # Ensure all values in the data dictionary are strings
    expo_url = "https://exp.host/--/api/v2/push/send"
    payload = {
        "to": token,
        "title": title,
        "body": body,
        "data": data or {},  # Optional additional data
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(expo_url, json=payload, headers=headers)
    if response.status_code == 200:
        print("Notification sent successfully:", response.json())
    else:
        print("Failed to send notification:", response.text)