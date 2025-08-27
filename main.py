# main.py
from __future__ import print_function
import os
import base64
import json
from email import message_from_bytes

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# SCOPES defines the level of access to gmail.
# If modifying SCOPES, delete the token.json file to re-authenticate
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    """Authenticate user and return Gmail API service instance."""
    creds = None
    token_path = 'token.json'
    creds_path = 'credentials.json'

    # Load saved token.json if available
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If no valid token.json, go through OAuth flow using your credentials.json
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save token.json for future use
        with open(token_path, 'w') as token_file:
            token_file.write(creds.to_json())

    # Build Gmail service
    service = build('gmail', 'v1', credentials=creds)
    return service


def fetch_latest_emails(service, max_results=10):
    """Fetch the latest emails from the inbox."""
    results = service.users().messages().list(userId='me', maxResults=max_results).execute()
    messages = results.get('messages', [])

    if not messages:
        print("No messages found.")
        return []

    email_data = []
    for msg in messages:
        msg_detail = service.users().messages().get(userId='me', id=msg['id']).execute()

        payload = msg_detail.get('payload', {})
        headers = payload.get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), '(No Date)')

        # Extract plain text content
        body_data = ''
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    data = part['body'].get('data')
                    if data:
                        body_data = base64.urlsafe_b64decode(data).decode('utf-8')
                        break

        email_data.append({
            'subject': subject,
            'date': date,
            'snippet': msg_detail.get('snippet', ''),
            'body': body_data
        })

    return email_data


if __name__ == '__main__':
    service = get_gmail_service()
    emails = fetch_latest_emails(service, max_results=5)
    for email in emails:
        print(f"Subject: {email['subject']}")
        print(f"Date: {email['date']}")
        print(f"Snippet: {email['snippet']}\n{'-'*40}")
