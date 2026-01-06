import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

print("🔄 Loading environment variables...")
load_dotenv()
print("✅ Environment loaded.")

from gmail_client import get_gmail_service, fetch_haro_emails, mark_as_read, send_reply
from haro_parser import parse_haro_email
from pitch_generator import generate_pitch
from sheets_client import log_pitch


load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER")

# Pakistan Time is UTC+5
PAKISTAN_TIMEZONE = timezone(timedelta(hours=5))


def is_within_processing_window() -> bool:
    """
    Check if current time is within processing windows (Pakistan Time):
    - Window 1: 2 PM - 5 PM (14:00 - 17:00)
    - Window 2: 9 PM - 12 AM (21:00 - 00:00)
    - Window 3: 2 AM - 5 AM (02:00 - 05:00) next day
    """
    # Get current time in Pakistan Time
    now_utc = datetime.now(timezone.utc)
    now_pakistan = now_utc.astimezone(PAKISTAN_TIMEZONE)
    current_hour = now_pakistan.hour
    
    print(f"🕒 Current Pakistan Time: {now_pakistan.strftime('%Y-%m-%d %H:%M:%S')} (Hour: {current_hour})")
    
    # Window 1: 2 PM - 5 PM (14:00 - 17:00) Pakistan Time
    window1 = 14 <= current_hour < 17
    
    # Window 2: 9 PM - 12 AM (21:00 - 00:00) Pakistan Time
    window2 = 21 <= current_hour <= 23 or current_hour == 0  # Hours 21 (9 PM), 22 (10 PM), 23 (11 PM), and 0 (12 AM)
    
    # Window 3: 2 AM - 5 AM (02:00 - 05:00) Pakistan Time
    window3 = 2 <= current_hour < 5
    
    in_window = window1 or window2 or window3
    print(f"⏰ In processing window: {in_window} (Window1: {window1}, Window2: {window2}, Window3: {window3})")
    
    return in_window


def is_recent_email(ts: datetime, window_minutes: int = 30) -> bool:
    """
    Checks if email timestamp is within last `window_minutes` minutes (UTC).
    """
    if ts is None:
        return False
    now = datetime.now(timezone.utc)
    delta = now - ts
    return delta <= timedelta(minutes=window_minutes)


def process_haro_once(force_run: bool = False):
    print("🚀 Starting HARO processing...")
    # Check if we're within processing time window (Pakistan Time)
    if not force_run and not is_within_processing_window():
        now_pakistan = datetime.now(timezone.utc).astimezone(PAKISTAN_TIMEZONE)
        print(f"⏰ Outside processing window. Current Pakistan Time: {now_pakistan.strftime('%H:%M:%S')}")
        print("   Processing windows: 2-5 PM, 9 PM-12 AM, and 2-5 AM Pakistan Time")
        return
    
    print("🔍 Checking for HARO emails...")
    print("🔗 Connecting to Gmail API...")
    service = get_gmail_service()
    print("✅ Connected to Gmail.")
    emails = fetch_haro_emails(service)

    if not emails:
        print("❌ No unread HARO emails found.")
        return

    # HARO sends only one per edition, but we'll be safe and sort by timestamp (newest first)
    emails.sort(key=lambda e: e["timestamp"] or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True)

    for email in emails:
        ts = email["timestamp"]

        if not is_recent_email(ts, window_minutes=30):
            print("⏩ Skipping HARO email older than 30 minutes.")
            continue

        print(f"✅ Found recent HARO email: {email['subject']} at {ts}")

        # Parse & filter relevant queries
        queries = parse_haro_email(email["body"])

        if not queries:
            print("⚠️ HARO email has no relevant queries based on niche filter.")
            mark_as_read(service, email["id"])
            return

        # For now, process all relevant queries inside the same HARO email
        for q in queries:
            pitch = generate_pitch(q)
            # Get reply-to address from the query (extracted from each query block)
            reply_to = q.get("reply_to")
            if not reply_to:
                print(f"⚠️ No reply-to address found for query: {q['title'][:50]}...")
                print("   Skipping this query.")
                continue
            
            send_reply(service, email["threadId"], email["subject"], pitch, reply_to, GMAIL_USER)

            log_pitch(q, pitch, status="Sent")
            print(f"✅ Pitch sent for: {q['title']}")

        # Mark the HARO email as read so it is never processed again
        mark_as_read(service, email["id"])
        print("✅ Marked HARO email as read. Stopping until next window.")
        return

    print("❌ No HARO emails within the last 30 minutes.")


if __name__ == "__main__":
    import sys
    force = len(sys.argv) > 1 and sys.argv[1] == "--force"
    # No loops here; GitHub Actions will call this every 15 minutes in your windows
    process_haro_once(force_run=force)
