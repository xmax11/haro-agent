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
        # Check if credentials are available
        creds_json = os.getenv("SHEETS_CREDENTIALS")
        if not creds_json:
            print("⚠️ SHEETS_CREDENTIALS environment variable not set. Skipping Google Sheets logging.")
            print("   Pitch was still sent successfully. Continuing...")
            return
        
        client = get_sheets_client()
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.sheet1

        # Ensure headers exist - check and add/update if needed
        expected_headers = ["Timestamp", "Title", "Publication", "Query", "Pitch", "Status"]
        
        try:
            all_values = sheet.get_all_values()
            # If sheet is empty or first row doesn't match headers, set headers
            if not all_values or len(all_values) == 0:
                # Sheet is completely empty, add headers
                sheet.append_row(expected_headers, value_input_option="RAW")
                print("📝 Added headers to empty sheet")
            else:
                # Check if first row matches expected headers
                first_row = all_values[0] if all_values else []
                if first_row != expected_headers:
                    # Update first row with correct headers
                    sheet.update('A1:F1', [expected_headers], value_input_option="RAW")
                    print("📝 Updated first row with headers")
        except Exception as e:
            print(f"⚠️ Warning when checking headers: {e}")
            # Try to add headers as fallback
            try:
                sheet.append_row(expected_headers, value_input_option="RAW")
                print("📝 Added headers (fallback method)")
            except Exception as e2:
                print(f"⚠️ Failed to add headers: {e2}")

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
        print(f"   Error details: {str(e)}")
        print("   Pitch was still sent successfully. Continuing...")
    except json.JSONDecodeError as e:
        print(f"⚠️ Failed to parse SHEETS_CREDENTIALS JSON: {e}")
        print("   Please check that SHEETS_CREDENTIALS is valid JSON.")
        print("   Pitch was still sent successfully. Continuing...")
    except Exception as e:
        # Handle any other errors (network, permissions, etc.)
        print(f"⚠️ Failed to log to Google Sheets: {type(e).__name__}: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        print("   Pitch was still sent successfully. Continuing...")
