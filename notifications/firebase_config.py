import os
import firebase_admin
from firebase_admin import credentials

# Get the absolute path to the current directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Construct the full path to the service account key JSON file
json_path = os.path.join(BASE_DIR, "push-notification-5b47e-firebase-adminsdk-wrd04-6b83bf2a4e.json")
print("json_path",json_path)

# Initialize Firebase with the absolute path
cred = credentials.Certificate(json_path)
firebase_admin.initialize_app(cred)
