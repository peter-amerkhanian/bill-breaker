# main.py
from __future__ import print_function
import base64
from typing import List, Dict
from googleapiclient.discovery import Resource
from bs4 import BeautifulSoup
import re


def fetch_msg_ids(
    service: Resource, max_results: int | None = None
) -> List[Dict[str, str]]:
    """Fetch the latest emails from the inbox."""
    message_ids = (
        service.users().messages().list(userId="me", maxResults=max_results).execute()
    )
    messages = message_ids.get("messages", [])
    if not messages:
        print("No messages found.")
    return messages


def decode_text(data: str, mime_type: str) -> str:
    """Decode a base64 encoded email body."""
    decoded_data = base64.urlsafe_b64decode(data).decode("utf-8")
    if mime_type == "text/plain":
        text = decoded_data
    elif mime_type == "text/html":
        soup = BeautifulSoup(decoded_data, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
    return text


def parse_email_body(service: Resource, id: str) -> str:
    msg = service.users().messages().get(userId="me", id=id, format="full").execute()
    payload = msg["payload"]
    parts = payload.get("parts")
    if parts:
        text = ""
        for part in parts:
            mime_type = part.get("mimeType")
            body_data = part.get("body", {}).get("data")
            if body_data:
                text += decode_text(body_data, mime_type)
    else:
        body_data = payload.get("body", {}).get("data")
        mime_type = payload.get("mimeType")
        if body_data:
            text = decode_text(body_data, mime_type)
    return text


def extract_amounts(text: str) -> list[str]:
    pattern = r"\$\d+(?:,\d{3})*(?:\.\d{2})?"
    return re.findall(pattern, text)

