import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

from gmail_client import get_gmail_service, fetch_haro_emails, mark_as_read, send_reply
from haro_parser import parse_haro_email
from pitch_generator import generate_pitch
from sheets_client import log_pitch


load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER")


def is_recent_email(ts: datetime, window_minutes: int = 30) -> bool:
    """
    Checks if email timestamp is within last `window_minutes` minutes (UTC).
    """
    if ts is None:
        return False
    now = datetime.now(timezone.utc)
    delta = now - ts
    return delta <= timedelta(minutes=window_minutes)


def process_haro_once():
    print("🔍 Checking for HARO emails...")
    service = get_gmail_service()
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
            from gmail_client import extract_reply_to_address
            reply_to = extract_reply_to_address(email["body"])
            send_reply(service, email["threadId"], email["subject"], pitch, reply_to, GMAIL_USER)

            log_pitch(q, pitch, status="Sent")
            print(f"✅ Pitch sent for: {q['title']}")

        # Mark the HARO email as read so it is never processed again
        mark_as_read(service, email["id"])
        print("✅ Marked HARO email as read. Stopping until next window.")
        return

    print("❌ No HARO emails within the last 30 minutes.")


if __name__ == "__main__":
    # No loops here; GitHub Actions will call this every 15 minutes in your windows
    process_haro_once()
