from __future__ import print_function
from email_tools import parse_email, gmail_con
import pandas as pd


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
        sender = next((h['value'] for h in headers if h['name'] == 'From'), '(Unknown Sender)')
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), '(No Date)')
        msg_body = parse_email.parse_email_body(service, msg['id'])
        snippet = msg_detail.get('snippet', '')
        bill_amounts = list(set(
            parse_email.extract_amounts(msg_body) +
            parse_email.extract_amounts(snippet)
        ))
        email_data.append({
            'sender': sender,
            'subject': subject,
            'date': date,
            'snippet': msg_detail.get('snippet', ''),
            'body': msg_body,
            'amounts': bill_amounts
        })
    return email_data


if __name__ == '__main__':
    service = gmail_con.get_gmail_service()
    emails = fetch_latest_emails(service, max_results=10)
    emails_df = pd.DataFrame(emails)
    emails_df.to_csv('data/test_output.csv', index=False)
    for email in emails:
        print(f"Sender: {email['sender']}")
        print(f"Subject: {email['subject']}")
        print(f"Date: {email['date']}")
        print(f"Snippet: {email['snippet']}")
        print(f"Body: {email['body'][:80]}...")
        print(f"Amounts: {email['amounts']}\n{'-'*40}")
