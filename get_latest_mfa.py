#!/usr/bin/env python3
"""
Get the latest Garmin MFA code from Gmail.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

def get_latest_mfa():
    """Get the latest Garmin MFA code from Gmail."""
    try:
        import base64
        import re
        from datetime import datetime, timedelta
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
        creds = None
        gmail_token_file = os.path.expanduser("~/.gmail_token.json")
        client_secret_file = os.environ.get("GOOGLE_CLIENT_SECRET_FILE")

        if not client_secret_file:
            print("❌ GOOGLE_CLIENT_SECRET_FILE not set")
            return None

        # Load existing token
        if os.path.exists(gmail_token_file):
            creds = Credentials.from_authorized_user_file(gmail_token_file, SCOPES)

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secret_file, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(gmail_token_file, 'w') as token:
                token.write(creds.to_json())

        # Search for Garmin MFA email (last 30 minutes for more results)
        service = build('gmail', 'v1', credentials=creds)
        after_time = int((datetime.now() - timedelta(minutes=30)).timestamp())
        query = f'from:garmin.com after:{after_time}'

        results = service.users().messages().list(
            userId='me', q=query, maxResults=10).execute()
        messages = results.get('messages', [])

        if not messages:
            print("❌ No recent Garmin emails found")
            return None

        print(f"📬 Found {len(messages)} Garmin email(s)")

        # Get the latest message
        msg = service.users().messages().get(
            userId='me', id=messages[0]['id']).execute()

        # Get headers
        headers = msg['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No subject')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'No date')

        print(f"📨 Latest email: {subject}")
        print(f"📅 Date: {date}")

        # Extract body
        payload = msg['payload']
        body = ""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    break
        else:
            data = payload['body']['data']
            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

        print(f"📄 Body preview: {body[:200]}...")

        # Find 6-digit code
        mfa_pattern = r'\b(\d{6})\b'
        match = re.search(mfa_pattern, body)
        if match:
            code = match.group(1)
            print(f"✅ Found MFA code: {code}")
            return code

        print("❌ No 6-digit code found in email")
        return None

    except Exception as e:
        print(f"❌ Gmail MFA retrieval failed: {e}")
        return None

if __name__ == "__main__":
    print("🔍 Getting Latest Garmin MFA Code")
    print("===================================")
    code = get_latest_mfa()
    if code:
        print(f"\n🎯 Latest MFA code: {code}")
        print("Use this code for manual authentication if needed.")
    else:
        print("\n❌ No MFA code found.")