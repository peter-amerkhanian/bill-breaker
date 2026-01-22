from __future__ import print_function
import os
import pandas as pd
from email.utils import parseaddr, parsedate_to_datetime
from email_tools import parse_email, gmail_con


def fetch_latest_emails(service, max_results=10):
    """Fetch the latest emails from the inbox with rich metadata."""
    results = (
        service.users()
        .messages()
        .list(userId="me", maxResults=max_results)
        .execute()
    )
    messages = results.get("messages", [])
    if not messages:
        print("No messages found.")
        return []
    email_data = []
    for msg in messages:
        msg_detail = (
            service.users()
            .messages()
            .get(userId="me", id=msg["id"], format="full")
            .execute()
        )
        payload = msg_detail.get("payload", {})
        headers = payload.get("headers", [])
        label_ids = msg_detail.get("labelIds", [])
        # ---- Headers ----
        sender_raw = next(
            (h["value"] for h in headers if h["name"] == "From"),
            "(Unknown Sender)",
        )
        sender_name, sender_email = parseaddr(sender_raw)
        sender_domain = (
            sender_email.split("@")[-1].lower()
            if sender_email and "@" in sender_email
            else None
        )
        subject = next(
            (h["value"] for h in headers if h["name"] == "Subject"),
            "(No Subject)",
        )
        date_raw = next(
            (h["value"] for h in headers if h["name"] == "Date"),
            None,
        )
        date = (
            parsedate_to_datetime(date_raw)
            if date_raw
            else None
        )
        reply_to = next(
            (h["value"] for h in headers if h["name"] == "Reply-To"),
            None,
        )
        list_unsubscribe = next(
            (h["value"] for h in headers if h["name"] == "List-Unsubscribe"),
            None,
        )
        # ---- Body / Snippet ----
        snippet = msg_detail.get("snippet", "")
        msg_body = parse_email.parse_email_body(service, msg["id"])
        # ---- Amount extraction ----
        bill_amounts = list(
            set(
                parse_email.extract_amounts(msg_body)
                + parse_email.extract_amounts(snippet)
            )
        )
        # ---- Other metadata ----
        mime_type = payload.get("mimeType")
        thread_id = msg_detail.get("threadId")
        email_data.append(
            {
                # Identity
                "sender_name": sender_name,
                "sender_email": sender_email,
                "sender_domain": sender_domain,
                # Content
                "subject": subject,
                "raw_date": date,
                "date": date.date(),
                "snippet": snippet,
                "body": msg_body,
                "amounts_raw": bill_amounts,
                'amounts': [float(a.replace("$", "").replace(",", "")) for a in bill_amounts],
                # Gmail metadata
                "labels": label_ids,
                "thread_id": thread_id,
                "mime_type": mime_type,
                "is_html": mime_type in ("text/html", "multipart/alternative"),
                "reply_to": reply_to,
                "has_list_unsubscribe": list_unsubscribe is not None,
                "has_masked_account":  "****" in snippet or "****" in msg_body
            }
        )
    return email_data

if __name__ == "__main__":
    service = gmail_con.get_gmail_service()
    emails = fetch_latest_emails(service, max_results=10)
    emails_df = pd.DataFrame(emails)
    os.makedirs("data", exist_ok=True)
    emails_df.to_csv("data/test_output.csv", index=False)
    # Debug print
    for email in emails:
        print(f"Sender: {email['sender_name']} <{email['sender_email']}>")
        print(f"Domain: {email['sender_domain']}")
        print(f"Subject: {email['subject']}")
        print(f"Date: {email['date']}")
        print(f"Labels: {email['labels']}")
        print(f"Amounts: {email['amounts']}")
        print("-" * 50)