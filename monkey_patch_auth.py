#!/usr/bin/env python3
"""
Monkey-patched Garth authentication with automatic Gmail MFA.
"""

import os
import time
import builtins
from pathlib import Path
from dotenv import load_dotenv
from garth import Client
from garth.exc import GarthException

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Global variable to store MFA code
mfa_code_cache = None

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
        query = f'from:garmin.com after:{after_time}'  # Broader search

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

def monkey_patch_input():
    """Monkey patch input() to return MFA code when prompted."""
    original_input = builtins.input

    def patched_input(prompt=""):
        if "MFA" in prompt or "code" in prompt.lower():
            print(f"🤖 Intercepted MFA prompt: {prompt.strip()}")
            global mfa_code_cache
            if mfa_code_cache is None:
                print("⏳ Retrieving MFA code from Gmail...")
                mfa_code_cache = get_mfa_from_gmail()
                if not mfa_code_cache:
                    raise Exception("Could not retrieve MFA code from Gmail")
            return mfa_code_cache
        else:
            return original_input(prompt)

    builtins.input = patched_input
    return original_input

def monkey_patch_auth():
    """Use monkey-patched input for Garth authentication."""
    email = os.environ.get("GARMIN_EMAIL")
    password = os.environ.get("GARMIN_PASSWORD")
    tokenstore = os.path.expanduser(os.getenv("GARMINTOKENS", "~/.garminconnect"))

    if not email or not password:
        print("❌ Credentials not set")
        return False

    print("🐒 Starting monkey-patched Garth authentication...")

    # Monkey patch input function BEFORE any login attempts
    original_input = monkey_patch_input()

    try:
        # First, try to trigger MFA email by attempting login and letting it fail
        print("📧 Step 1: Triggering MFA email...")
        try:
            temp_client = Client()
            temp_client.login(email, password)
            print("⚠️ Login succeeded without MFA - this shouldn't happen")
            return False
        except:
            print("✅ MFA email should be sent now")

        # Wait for email to arrive
        print("⏳ Waiting 20 seconds for MFA email to arrive...")
        time.sleep(20)

        # Now try login again with the MFA code ready
        print("🔄 Step 2: Attempting login with MFA...")
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

        print("🎉 Fully automated authentication complete!")
        return True

    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False
    finally:
        # Restore original input function
        builtins.input = original_input

if __name__ == "__main__":
    print("🐒 Monkey-Patched Garth Authentication")
    print("=====================================")
    print("Using input() monkey-patching for automatic MFA.")
    monkey_patch_auth()