import base64
import os
from datetime import datetime, timezone

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def get_gmail_service():
    creds = Credentials(
        None,
        refresh_token=os.getenv("GMAIL_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GMAIL_CLIENT_ID"),
        client_secret=os.getenv("GMAIL_CLIENT_SECRET"),
        scopes=["https://www.googleapis.com/auth/gmail.modify"],
    )
    service = build("gmail", "v1", credentials=creds)
    return service


def _parse_internal_date(ms_str: str) -> datetime:
    """
    Gmail internalDate is in milliseconds since epoch, UTC.
    """
    millis = int(ms_str)
    seconds = millis / 1000.0
    return datetime.fromtimestamp(seconds, tz=timezone.utc)


def fetch_haro_emails(service):
    """
    Fetch unread HARO emails using subject:"HARO".
    Returns list of dicts with:
        id, threadId, subject, body, timestamp (datetime, UTC)
    """
    results = service.users().messages().list(
        userId="me",
        q='is:unread subject:"HARO"'
    ).execute()

    messages = results.get("messages", [])
    emails = []

    for msg in messages:
        msg_detail = service.users().messages().get(
            userId="me", id=msg["id"], format="full"
        ).execute()

        headers = msg_detail.get("payload", {}).get("headers", [])
        subject = ""
        for h in headers:
            if h["name"].lower() == "subject":
                subject = h["value"]
                break

        # Body (simplest: use the first text/plain part or fallback to body)
        body = ""
        payload = msg_detail.get("payload", {})
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    data = part["body"].get("data")
                    if data:
                        body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                        break
        else:
            data = payload.get("body", {}).get("data")
            if data:
                body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

        internal_date = msg_detail.get("internalDate")
        timestamp = _parse_internal_date(internal_date) if internal_date else None

        emails.append({
            "id": msg_detail["id"],
            "threadId": msg_detail.get("threadId"),
            "subject": subject,
            "body": body,
            "timestamp": timestamp
        })

    return emails


def mark_as_read(service, msg_id: str):
    try:
        service.users().messages().modify(
            userId="me",
            id=msg_id,
            body={"removeLabelIds": ["UNREAD"]}
        ).execute()
    except HttpError as e:
        print("⚠️ Failed to mark as read:", e)


def send_reply(service, thread_id: str, original_subject: str,
               body_text: str, from_address: str):
    """
    Simple reply using same thread. Uses plain text.
    """
    if not original_subject.lower().startswith("re:"):
        subject = "Re: " + original_subject
    else:
        subject = original_subject

    message_text = f"Hi,\n\n{body_text}\n"
    raw_message = (
        f"From: {from_address}\r\n"
        f"To: HARO\r\n"
        f"Subject: {subject}\r\n"
        f"In-Reply-To: {thread_id}\r\n"
        f"References: {thread_id}\r\n"
        f"\r\n"
        f"{message_text}"
    )

    encoded = base64.urlsafe_b64encode(raw_message.encode("utf-8")).decode("utf-8")

    message = {
        "raw": encoded,
        "threadId": thread_id
    }

    try:
        sent = service.users().messages().send(userId="me", body=message).execute()
        print("✉️  Reply sent, id:", sent.get("id"))
    except HttpError as e:
        print("⚠️ Failed to send reply:", e)
