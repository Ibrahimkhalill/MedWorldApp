# your_app/views.py
import openpyxl
from django.http import JsonResponse
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from datetime import datetime
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import traceback 
@api_view(['POST'])
# @permission_classes([IsAuthenticated])
def export_to_google_sheets(request):
    # Get data and title from request
    print("Current working dir:", os.getcwd())
    print("Environment variables:", os.environ)
    print("Received request to export data to Google Sheets")
    
    data = request.data.get('excel_data', [])
    title = request.data.get('title', 'ExportData')
    print(f"Data length: {len(data)}")

    if not data:
        return JsonResponse({"status": "error", "message": "No data provided"}, status=status.HTTP_400_BAD_REQUEST)

    # # Get the authenticated user's username or ID
    # user = request.user
    # user_identifier = user.username or str(user.id)  # Use username or ID as string

    # Format date to MM/DD/YY
    def format_date(date_string):
        if not date_string:
            return ""
        try:
            date = datetime.fromisoformat(date_string.replace("Z", "+00:00"))
            return date.strftime("%m/%d/%y")
        except ValueError:
            return date_string

    # Format values (boolean to Yes/No, date, user object)
    def format_value(value, key):
        if key == "date":
            return format_date(value)
        if isinstance(value, bool):
            return "Yes" if value else "No"
        if key == "user" and isinstance(value, dict):
            return value.get("username", "")
        return value or ""

    # Preprocess data
    formatted_data = [
        {key: format_value(row[key], key) for key in row}
        for row in data
    ]

    # Prepare data for Google Sheets
    headers = list(formatted_data[0].keys()) if formatted_data else []
    values = [headers]  # First row is headers
    for row in formatted_data:
        values.append([row[key] for key in headers])

    try:
        # Google API setup
        SCOPES = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",  # Needed for permissions
        ]
        credentials = Credentials.from_service_account_file(
            os.path.join(BASE_DIR, "secrets", "credentials.json"),
            scopes=SCOPES
        )

        print("Google API credentials loaded successfully")
        sheets_service = build("sheets", "v4", credentials=credentials)
        drive_service = build("drive", "v3", credentials=credentials)

        # Create a new Google Sheets file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in f"{title}_{timestamp}" if c.isalnum() or c in ('_', '-'))
        spreadsheet = {
            "properties": {
                "title": safe_title
            }
        }
        spreadsheet = sheets_service.spreadsheets().create(
            body=spreadsheet,
            fields="spreadsheetId,properties.title,spreadsheetUrl"
        ).execute()
        spreadsheet_id = spreadsheet.get("spreadsheetId")
        sheets_url = spreadsheet.get("spreadsheetUrl")

        # Write data to the spreadsheet
        body = {
            "values": values
        }
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="Sheet1!A1",
            valueInputOption="RAW",
            body=body
        ).execute()

        # Set sharing permissions for the authenticated user
     
        drive_service.permissions().create(
            fileId=spreadsheet_id,
            body={"role": "writer", "type": "anyone"},
            supportsAllDrives=True
        ).execute()

        # Optional: Move to Shared Drive (if using)
        # """
        # drive_service.files().update(
        #     fileId=spreadsheet_id,
        #     addParents="<SHARED_DRIVE_ID>",  # Replace with your Shared Drive ID
        #     removeParents="root",
        #     supportsAllDrives=True
        # ).execute()
        # """

        # Return Google Sheets link
        return JsonResponse({
            "status": "success",
            "message": "File created in Google Sheets",
            "sheets_url": sheets_url,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print("❌ Exception occurred:", str(e))
        print(traceback.format_exc())  # prints full error traceback
        return JsonResponse({
            "status": "error",
            "message": f"Internal Server Error: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)