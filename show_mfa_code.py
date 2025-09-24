#!/usr/bin/env python3
"""
Display the latest Garmin MFA code from Gmail for manual use.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

def show_latest_mfa():
    """Show the latest Garmin MFA code for manual entry."""
    print("🔍 Garmin MFA Code Display")
    print("===========================")
    print("This script shows the latest MFA code from your Gmail.")
    print("Use this code for manual authentication.\n")

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
            print("❌ GOOGLE_CLIENT_SECRET_FILE not set in .env")
            return

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

        # Search for Garmin MFA email - search ALL Garmin emails
        service = build('gmail', 'v1', credentials=creds)
        query = f'from:garmin.com subject:"security passcode"'  # Search all with this subject

        results = service.users().messages().list(
            userId='me', q=query, maxResults=10).execute()
        messages = results.get('messages', [])

        if not messages:
            print("❌ No Garmin emails found in the last 2 hours")
            print("💡 Try triggering a Garmin login first to generate an MFA email")
            return

        print(f"📬 Found {len(messages)} Garmin email(s)")

        # Show all recent emails
        for i, msg_data in enumerate(messages[:5]):  # Show last 5
            msg = service.users().messages().get(
                userId='me', id=msg_data['id']).execute()

            headers = msg['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No subject')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'No date')

            # Extract body and find code
            payload = msg['payload']
            body = ""
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body']['data']
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    elif part['mimeType'] == 'text/html' and not body:  # Fallback to HTML if no text
                        data = part['body']['data']
                        html_content = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        # Remove HTML tags to get text content
                        import re as html_re
                        body = html_re.sub('<[^<]+?>', '', html_content)
            else:
                data = payload['body']['data']
                raw_content = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                # Try to remove HTML tags if it's HTML content
                import re as html_re
                body = html_re.sub('<[^<]+?>', '', raw_content)

            print(f"\n📧 Email {i+1}:")
            print(f"   Subject: {subject}")
            print(f"   Date: {date}")
            print(f"   Body preview: {body[:200]}...")

            # Look for the specific pattern from user's message
            # "Use this one-time code for your account XXXXXX"
            account_pattern = r'account\s+(\d{6})'
            match = re.search(account_pattern, body, re.IGNORECASE)

            if match:
                found_code = match.group(1)
                print(f"   ✅ MFA Code: {found_code}")
                if i == 0:  # Latest email
                    print(f"\n🎯 LATEST CODE TO USE: {found_code}")
                    print("Copy this code and use it for Garmin authentication.")
            else:
                print("   ❌ No account code pattern found")
                # Debug: show all 6-digit sequences found
                all_codes = re.findall(r'\b(\d{6})\b', body)
                if all_codes:
                    print(f"   🔍 All 6-digit sequences: {all_codes}")
                    # Try to find codes that aren't 000000
                    real_codes = [code for code in all_codes if code != '000000']
                    if real_codes:
                        print(f"   🎯 Potential real codes: {real_codes}")
                        found_code = real_codes[0]
                        print(f"   ✅ Using code: {found_code}")
                        if i == 0:
                            print(f"\n🎯 LATEST CODE TO USE: {found_code}")
                    else:
                        print("   ❌ No non-zero codes found")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    show_latest_mfa()