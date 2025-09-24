#!/usr/bin/env python3
"""
Test Gmail API access using OAuth2
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Google OAuth2 imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    print("❌ Google API libraries not installed!")
    print("Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    """Get authenticated Gmail service"""
    creds = None
    token_file = os.path.expanduser(os.environ.get("GMAIL_TOKEN_FILE", "~/.gmail_token.json"))
    client_secret_file = os.environ.get("GOOGLE_CLIENT_SECRET_FILE")
    
    if not client_secret_file:
        print("❌ GOOGLE_CLIENT_SECRET_FILE not set!")
        return None
    
    # Load existing token
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    
    # If no valid creds, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("🔐 Need to authenticate...")
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secret_file, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
        print(f"💾 Token saved to {token_file}")
    
    return build('gmail', 'v1', credentials=creds)

def check_garmin_mfa_emails():
    """Check for Garmin MFA emails using Gmail API"""
    service = get_gmail_service()
    if not service:
        return None
    
    try:
        # Calculate time 10 minutes ago
        after_time = int((datetime.now() - timedelta(minutes=10)).timestamp())
        
        # Search for recent Garmin emails
        query = f'from:garmin.com after:{after_time}'  # Broader search without subject filter
        print(f"🔍 Searching: {query}")
        
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=10
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            print("📧 No recent Garmin MFA emails found")
            return None
        
        print(f"📬 Found {len(messages)} Garmin email(s)")
        
        # Get the most recent message
        msg = service.users().messages().get(
            userId='me',
            id=messages[0]['id']
        ).execute()
        
        # Extract the message body
        payload = msg['payload']
        headers = payload.get('headers', [])
        
        # Get subject
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No subject')
        print(f"📨 Latest email: {subject}")
        
        # Get body
        body = extract_body(payload)
        if body:
            # Look for 6-digit code
            mfa_pattern = r'\b(\d{6})\b'
            match = re.search(mfa_pattern, body)
            if match:
                mfa_code = match.group(1)
                print(f"✅ Found MFA code: {mfa_code}")
                return mfa_code
            else:
                print("⚠️ No 6-digit code found in email body")
                print(f"📄 Body preview: {body[:200]}...")
        
    except Exception as e:
        print(f"❌ Error accessing Gmail API: {e}")
        return None

def extract_body(payload):
    """Extract body from email payload"""
    body = ""
    
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                break
            elif part['mimeType'] == 'text/html' and not body:
                data = part['body']['data']
                import base64
                html_body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                # Simple HTML to text (remove tags)
                body = re.sub('<[^<]+?>', '', html_body)
    else:
        if payload['body'].get('data'):
            import base64
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
    
    return body

if __name__ == "__main__":
    print("🧪 Testing Gmail API Access")
    print("=" * 40)
    
    result = check_garmin_mfa_emails()
    if result:
        print(f"\n✅ Success! Found MFA code: {result}")
    else:
        print("\nℹ️ No MFA codes found (this is normal if you haven't triggered 2FA recently)")
        print("💡 To test: Trigger a Garmin login that requires 2FA, then run this test again")