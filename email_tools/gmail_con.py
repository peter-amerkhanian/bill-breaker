from __future__ import print_function
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

# SCOPES defines the level of access to gmail.
# If modifying SCOPES, delete the token.json file to re-authenticate
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_service() -> Resource:
    """Authenticate user and return Gmail API service instance."""
    creds: Credentials | None = None
    token_path = "token.json"
    creds_path = "credentials.json"
    # Load saved token.json if available
    if os.path.exists(token_path):
        creds: Credentials = Credentials.from_authorized_user_file(token_path, SCOPES)
    # If no valid token.json, go through OAuth flow using your credentials.json
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow: InstalledAppFlow = InstalledAppFlow.from_client_secrets_file(
                creds_path, SCOPES
            )
            creds: Credentials = flow.run_local_server(port=0)
        # Save token.json for future use
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())
    # Build Gmail service
    service: Resource = build("gmail", "v1", credentials=creds)
    return service
