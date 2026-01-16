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
    print(f"🔵 log_pitch called - Title: {query.get('title', 'N/A')[:50]}...")
    print(f"   Query keys: {list(query.keys())}")
    print(f"   Pitch length: {len(pitch)}")
    print(f"   Status: {status}")
    try:
        # Check if credentials are available
        creds_json = os.getenv("SHEETS_CREDENTIALS")
        if not creds_json:
            print("⚠️ SHEETS_CREDENTIALS environment variable not set. Skipping Google Sheets logging.")
            print("   Pitch was still sent successfully. Continuing...")
            return
        
        print(f"📋 Connecting to Google Sheets (ID: {SPREADSHEET_ID})...")
        client = get_sheets_client()
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.sheet1
        print(f"✅ Connected to sheet: {sheet.title}")

        # Get all values once to minimize API calls
        all_values = sheet.get_all_values()
        print(f"📊 Retrieved {len(all_values)} rows from sheet")

        # Ensure headers exist - only add if sheet is completely empty
        expected_headers = ["Timestamp", "Title", "Publication", "Query", "Pitch", "Status"]
        
        if not all_values or len(all_values) == 0:
            # Sheet is completely empty, add headers
            sheet.update('A1:F1', [expected_headers], value_input_option="RAW")
            print("📝 Added headers to A1:F1")
            # Refresh data after adding headers
            all_values = [expected_headers]
        else:
            # Sheet has data, verify headers
            first_row = all_values[0] if all_values else []
            if first_row and len(first_row) > 0 and first_row[0].strip() == "Timestamp":
                print(f"✅ Headers verified (first row starts with 'Timestamp')")
            else:
                print(f"⚠️ First row doesn't appear to be headers: {first_row[:3] if first_row else 'empty'}")

        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        row = [
            now,
            query.get("title", ""),
            query.get("publication", ""),
            query.get("query", "")[:500],
            pitch[:500],
            status
        ]

        print(f"📊 Attempting to log pitch to Google Sheets...")
        print(f"   Row data: {len(row)} columns, Title: {row[1][:50]}...")
        print(f"   Full row: {[str(x)[:100] for x in row]}")
        
        # Find the next available row (after headers)
        next_row = len(all_values) + 1
        range_to_update = f'A{next_row}:F{next_row}'
        
        # Append the row
        try:
            sheet.update(range_to_update, [row], value_input_option="RAW")
            print(f"✅ Successfully updated Google Sheets range: {range_to_update}")
            
            # Optional verification (only if DEBUG_SHEETS is set)
            if os.getenv("DEBUG_SHEETS") == "true":
                try:
                    # Quick check of the specific row we just updated
                    check_values = sheet.get(range_to_update)
                    if check_values and len(check_values) > 0:
                        print(f"✅ Verified: Row {next_row} has data: {check_values[0][:3]}...")
                except Exception as verify_error:
                    print(f"⚠️ Warning: Could not verify row addition: {verify_error}")
        except Exception as append_error:
            print(f"❌ Failed to update Google Sheets: {type(append_error).__name__}: {append_error}")
            raise  # Re-raise to be caught by outer exception handler
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
