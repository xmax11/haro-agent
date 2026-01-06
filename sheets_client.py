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

        # Ensure headers exist - only add if sheet is completely empty
        expected_headers = ["Timestamp", "Title", "Publication", "Query", "Pitch", "Status"]
        
        try:
            all_values = sheet.get_all_values()
            # Only add headers if sheet is completely empty
            if not all_values or len(all_values) == 0:
                # Sheet is completely empty, add headers
                sheet.append_row(expected_headers, value_input_option="USER_ENTERED")
                print("📝 Added headers to empty sheet")
            else:
                # Sheet has data, assume headers already exist - just verify first row starts with "Timestamp"
                first_row = all_values[0] if all_values else []
                if first_row and len(first_row) > 0 and first_row[0].strip() != "Timestamp":
                    # First row doesn't look like headers, but we won't overwrite existing data
                    # Just log a warning - user should manually fix headers if needed
                    print(f"⚠️ First row doesn't appear to be headers, but not overwriting existing data")
                    print(f"   First row starts with: {first_row[0] if first_row else 'empty'}")
                else:
                    print(f"✅ Headers verified (first row starts with 'Timestamp')")
        except Exception as e:
            print(f"⚠️ Warning when checking headers: {e}")
            # Only try to add headers if we're sure the sheet is empty
            try:
                # Try to check one more time if it's really empty
                test_values = sheet.get_all_values()
                if not test_values or len(test_values) == 0:
                    sheet.append_row(expected_headers, value_input_option="USER_ENTERED")
                    print("📝 Added headers (fallback method - sheet was empty)")
            except Exception as e2:
                print(f"⚠️ Could not verify/add headers: {e2}, continuing anyway...")

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
        
        # Append the row
        try:
            sheet.append_row(row, value_input_option="USER_ENTERED")
            print(f"✅ Successfully appended row to Google Sheets")
            
            # Verify it was added by checking the last row
            try:
                all_values_after = sheet.get_all_values()
                if all_values_after and len(all_values_after) > 0:
                    last_row = all_values_after[-1]
                    print(f"✅ Verified: Last row in sheet has {len(last_row)} columns")
                else:
                    print("⚠️ Warning: Could not verify row was added (sheet appears empty)")
            except Exception as verify_error:
                print(f"⚠️ Warning: Could not verify row addition: {verify_error}")
        except Exception as append_error:
            print(f"❌ Failed to append row: {type(append_error).__name__}: {append_error}")
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
