#!/usr/bin/env python3
"""
Direct Garth authentication with MFA code provided programmatically.
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

def direct_garth_mfa():
    """Direct Garth authentication with programmatic MFA."""
    email = os.environ.get("GARMIN_EMAIL")
    password = os.environ.get("GARMIN_PASSWORD")
    tokenstore = os.path.expanduser(os.getenv("GARMINTOKENS", "~/.garminconnect"))

    if not email or not password:
        print("❌ Credentials not set")
        return False

    print("🎯 Starting direct Garth MFA authentication...")

    try:
        # Create Garth client
        client = Client()

        # Try login with credentials first
        print("🔐 Attempting initial login...")
        try:
            client.login(email, password)
            print("✅ Login successful without MFA!")
        except GarthException as e:
            if "mfa" in str(e).lower() or "code" in str(e).lower():
                print("🔐 MFA required, retrieving from Gmail...")

                # Wait for email
                print("⏳ Waiting 15 seconds for MFA email...")
                time.sleep(15)

                # Get MFA code
                mfa_code = get_mfa_from_gmail()
                if not mfa_code:
                    print("❌ Failed to get MFA code")
                    return False

                # Try login with MFA code
                print("🔄 Completing authentication with MFA...")
                client.login(email, password, mfa_code=mfa_code)
                print("✅ MFA authentication successful!")
            else:
                raise e

        # Save tokens
        client.dump(tokenstore)
        print(f"💾 Tokens saved to: {tokenstore}")

        # Test tokens
        print("🔍 Testing token validity...")
        test_client = Client()
        test_client.load(tokenstore)
        profile = test_client.get("userprofile-service/socialProfile")
        print(f"✅ Token test successful! User: {profile.get('displayName', 'Unknown')}")

        print("🎉 Fully automated authentication complete!")
        return True

    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Direct Garth MFA Authentication")
    print("==================================")
    print("Fully automated authentication using Gmail API for MFA.")
    direct_garth_mfa()