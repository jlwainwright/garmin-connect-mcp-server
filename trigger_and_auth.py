#!/usr/bin/env python3
"""
Trigger Garmin login to generate fresh MFA email, then authenticate.
"""

import os
import time
import builtins
from pathlib import Path
from dotenv import load_dotenv
from garth import Client

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

def get_fresh_mfa_code():
    """Get a fresh MFA code after triggering login."""
    print("📧 Getting fresh MFA code from Gmail...")

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

        # Search for very recent Garmin emails (last 2 minutes)
        service = build('gmail', 'v1', credentials=creds)
        after_time = int((datetime.now() - timedelta(minutes=2)).timestamp())
        query = f'from:garmin.com after:{after_time}'

        results = service.users().messages().list(
            userId='me', q=query, maxResults=5).execute()
        messages = results.get('messages', [])

        if not messages:
            return None

        # Get the most recent message
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
            print(f"✅ Found fresh MFA code: {code}")
            return code

        return None

    except Exception as e:
        print(f"❌ Gmail error: {e}")
        return None

def patched_input_with_fresh_code():
    """Get fresh MFA code when prompted."""
    mfa_code = get_fresh_mfa_code()
    if mfa_code:
        return mfa_code
    else:
        print("❌ Could not get fresh MFA code")
        return "000000"  # Fallback

def trigger_and_auth():
    """Trigger fresh login and authenticate."""
    email = os.environ.get("GARMIN_EMAIL")
    password = os.environ.get("GARMIN_PASSWORD")
    tokenstore = os.path.expanduser(os.getenv("GARMINTOKENS", "~/.garminconnect"))

    if not email or not password:
        print("❌ Credentials not set")
        return False

    print("🚀 Trigger & Authenticate")
    print("=========================")
    print("This will trigger a fresh Garmin login and use the MFA code.")

    # Monkey patch input to get fresh code
    builtins.original_input = builtins.input
    builtins.input = lambda prompt: patched_input_with_fresh_code() if "MFA" in prompt or "code" in prompt.lower() else builtins.original_input(prompt)

    try:
        # First, try to trigger MFA by attempting login
        print("📧 Step 1: Triggering fresh MFA email...")
        temp_client = Client()
        try:
            temp_client.login(email, password)
            print("⚠️ Login succeeded without MFA")
            return False
        except:
            print("✅ MFA email triggered")

        # Wait for email
        print("⏳ Waiting 15 seconds for email...")
        time.sleep(15)

        # Now authenticate with fresh code
        print("🔄 Step 2: Authenticating with fresh MFA code...")
        client = Client()
        client.login(email, password)

        print("✅ Authentication successful!")

        # Save tokens
        client.dump(tokenstore)
        print(f"💾 Tokens saved to: {tokenstore}")

        # Test tokens
        print("🔍 Testing token validity...")
        test_client = Client()
        test_client.load(tokenstore)
        profile = test_client.get("userprofile-service/socialProfile")
        print(f"✅ Token test successful! User: {profile.get('displayName', 'Unknown')}")

        print("\n🎉 SUCCESS! Garmin MCP is fully automated!")
        return True

    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False
    finally:
        builtins.input = builtins.original_input

if __name__ == "__main__":
    trigger_and_auth()