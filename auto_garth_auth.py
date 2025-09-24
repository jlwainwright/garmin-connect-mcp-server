#!/usr/bin/env python3
"""
Automated Garth authentication with Gmail MFA retrieval.
"""

import os
import time
from pathlib import Path
from dotenv import load_dotenv
from garth import Client
from garth.exc import GarthException

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

def get_mfa_from_gmail() -> str:
    """Get MFA code from Gmail automatically."""
    print("📧 Checking Gmail for Garmin MFA code...")

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

        # Search for Garmin MFA email
        service = build('gmail', 'v1', credentials=creds)
        after_time = int((datetime.now() - timedelta(minutes=5)).timestamp())
        query = f'from:garmin.com subject:"Garmin Connect" after:{after_time}'

        results = service.users().messages().list(
            userId='me', q=query, maxResults=5).execute()
        messages = results.get('messages', [])

        if not messages:
            print("❌ No recent Garmin MFA emails found")
            return None

        # Get the latest message
        msg = service.users().messages().get(
            userId='me', id=messages[0]['id']).execute()

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

def auto_garth_auth():
    """Automated Garth authentication with Gmail MFA."""
    email = os.environ.get("GARMIN_EMAIL")
    password = os.environ.get("GARMIN_PASSWORD")
    tokenstore = os.path.expanduser(os.getenv("GARMINTOKENS", "~/.garminconnect"))

    if not email or not password:
        print("❌ GARMIN_EMAIL and GARMIN_PASSWORD must be set in .env")
        return False

    print("🤖 Starting automated Garth authentication...")

    try:
        # Create Garth client
        client = Client()

        # Start login process
        print("🔐 Initiating login...")
        client.login(email, password)

        # If we get here without MFA exception, login succeeded
        print("✅ Login successful without MFA!")

    except GarthException as e:
        error_str = str(e).lower()
        if "mfa" in error_str or "verification" in error_str or "code" in error_str:
            print("🔐 MFA required, retrieving from Gmail...")

            # Wait a moment for email to arrive
            print("⏳ Waiting 10 seconds for email to arrive...")
            time.sleep(10)

            # Get MFA code from Gmail
            mfa_code = get_mfa_from_gmail()
            if not mfa_code:
                print("❌ Could not retrieve MFA code from Gmail")
                return False

            # Complete MFA
            print("🔄 Completing MFA...")
            try:
                client.login(email, password, mfa_code=mfa_code)
                print("✅ MFA completed successfully!")
            except Exception as mfa_error:
                print(f"❌ MFA completion failed: {mfa_error}")
                return False
        else:
            print(f"❌ Login failed: {e}")
            return False

    # Save tokens
    try:
        client.dump(tokenstore)
        print(f"💾 Tokens saved to: {tokenstore}")

        # Test the tokens
        print("🔍 Testing token validity...")
        test_client = Client()
        test_client.load(tokenstore)
        profile = test_client.get("userprofile-service/socialProfile")
        print(f"✅ Token test successful! User: {profile.get('displayName', 'Unknown')}")

        print("🎉 Automated authentication complete!")
        print("You can now run the main server script: python garmin_mcp_server_fixed.py")
        return True

    except Exception as e:
        print(f"❌ Token save/test failed: {e}")
        return False

if __name__ == "__main__":
    print("🤖 Automated Garth Authentication")
    print("=================================")
    print("This script will automatically retrieve MFA codes from Gmail.")
    auto_garth_auth()