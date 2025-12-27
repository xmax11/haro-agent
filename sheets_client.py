import json
import os
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = "10lYfPW_1ZjmOGkxfTsTw9iHulLXjDtgr_1DpklxTzN8"


def get_sheets_client():
    creds_json = os.getenv("SHEETS_CREDENTIALS")
    info = json.loads(creds_json)

    creds = Credentials.from_service_account_info(
        info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    return client


def log_pitch(query: dict, pitch: str, status: str = "Sent"):
    """
    Log pitch to Google Sheets. If logging fails, prints warning but doesn't crash.
    Google Sheets automatically expands rows (limit ~10 million rows for new sheets).
    """
    try:
        client = get_sheets_client()
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1

        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        row = [
            now,
            query.get("title", ""),
            query.get("publication", ""),
            query.get("query", "")[:500],
            pitch[:500],
            status
        ]

        sheet.append_row(row, value_input_option="RAW")
        print(f"✅ Logged pitch to Google Sheets")
    except gspread.exceptions.APIError as e:
        # Handle API errors (quota exceeded, sheet full, etc.)
        print(f"⚠️ Failed to log to Google Sheets (API Error): {e}")
        print("   Pitch was still sent successfully. Continuing...")
    except Exception as e:
        # Handle any other errors (network, permissions, etc.)
        print(f"⚠️ Failed to log to Google Sheets: {e}")
        print("   Pitch was still sent successfully. Continuing...")
