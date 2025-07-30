from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import os
import gspread

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

credentials = Credentials.from_service_account_file(
            os.path.join(BASE_DIR, "secrets", "credentials.json"),
            scopes=SCOPES
        )
gc = gspread.authorize(credentials)
sheets_service = build('sheets', 'v4', credentials=credentials)
drive_service = build('drive', 'v3', credentials=credentials)

spreadsheet_body = {
    'properties': {'title': 'Test Spreadsheet'}
}

response = sheets_service.spreadsheets().create(body=spreadsheet_body).execute()
print("Spreadsheet created:", response['spreadsheetId'])
