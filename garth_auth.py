#!/usr/bin/env python3
"""
Direct Garth authentication to bypass Garmin library token requirements.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from garth import Client
from garth.exc import GarthException

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

def get_mfa_from_gmail() -> str:
    """Get MFA code from Gmail automatically."""
    print("\n🔐 Garmin Connect MFA required.")
    print("📧 Checking Gmail for verification code...")

    try:
        # Import Gmail functionality
        import base64
        import re
        from datetime import datetime, timedelta
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        # Gmail OAuth2 setup
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
        after_time = int((datetime.now() - timedelta(minutes=10)).timestamp())
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

def garth_authenticate():
    """Use Garth directly for authentication."""
    email = os.environ.get("GARMIN_EMAIL")
    password = os.environ.get("GARMIN_PASSWORD")
    tokenstore = os.path.expanduser(os.getenv("GARMINTOKENS", "~/.garminconnect"))

    if not email or not password:
        print("❌ GARMIN_EMAIL and GARMIN_PASSWORD must be set in .env")
        return False

    print("🔄 Starting Garth-based authentication...")

    try:
        # Create Garth client
        client = Client()

        # Try login - this may raise an exception requiring MFA
        try:
            client.login(email, password)
        except GarthException as mfa_error:
            if "mfa" in str(mfa_error).lower() or "verification" in str(mfa_error).lower():
                print("🔐 MFA required, checking Gmail...")
                mfa_code = get_mfa_from_gmail()
                if mfa_code:
                    # Complete MFA
                    client.login(email, password, mfa_code=mfa_code)
                else:
                    raise Exception("Could not retrieve MFA code from Gmail")
            else:
                raise mfa_error

        # Save tokens
        client.dump(tokenstore)

        print("\n✅ Authentication successful!")
        print(f"💾 Tokens have been saved to: {tokenstore}")

        # Test that we can use the tokens
        print("🔍 Testing token validity...")
        test_client = Client()
        test_client.load(tokenstore)
        # Try a simple API call
        profile = test_client.get("userprofile-service/socialProfile")
        print(f"✅ Token test successful! User: {profile.get('displayName', 'Unknown')}")

        print("You can now run the main server script: python garmin_mcp_server_fixed.py")
        return True

    except GarthException as e:
        print(f"❌ Garth authentication failed: {e}")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔑 Garth Direct Authentication")
    print("==============================")
    print("Using Garth library directly to bypass Garmin token requirements.")
    garth_authenticate()