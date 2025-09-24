#!/usr/bin/env python3
"""
Headless authentication handler for Garmin Connect MCP server.
Supports multiple authentication strategies for automated deployments.
"""

import os
import json
import time
import re
import imaplib
import email
import base64
import hashlib
import hmac
from email.header import decode_header
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from garminconnect import Garmin, GarminConnectAuthenticationError
from garth.exc import GarthHTTPError
import requests
from ntfy_notifier import NtfyNotifier

# Google OAuth2 imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

class HeadlessGarminAuth:
    def __init__(self):
        self.email = os.environ.get("GARMIN_EMAIL")
        self.password = os.environ.get("GARMIN_PASSWORD")
        self.tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
        self.tokenstore_base64 = os.getenv("GARMINTOKENS_BASE64") or "~/.garminconnect_base64"
        self.auth_log_file = Path(__file__).parent / "auth_log.json"
        self.notifier = NtfyNotifier()

        # OAuth2 settings
        self.client_secret_file = os.environ.get("GOOGLE_CLIENT_SECRET_FILE")
        self.gmail_token_file = os.environ.get("GMAIL_TOKEN_FILE", "~/.gmail_token.json")
        self.scopes = ['https://www.googleapis.com/auth/gmail.readonly']

        # Expand token file path
        self.gmail_token_file = os.path.expanduser(self.gmail_token_file)
        
    def log_auth_attempt(self, success: bool, method: str, error: str = None):
        """Log authentication attempts for monitoring"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "method": method,
            "error": error
        }
        
        try:
            if self.auth_log_file.exists():
                with open(self.auth_log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(log_entry)
            
            # Keep only last 50 entries
            logs = logs[-50:]
            
            with open(self.auth_log_file, 'w') as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            # Don't fail if logging fails
            pass

    def get_gmail_credentials(self):
        """Get OAuth2 credentials for Gmail access"""
        if not GOOGLE_AUTH_AVAILABLE:
            print("⚠️ Google Auth libraries not available. Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
            return None

        if not self.client_secret_file:
            return None

        creds = None

        # Check if token file exists
        if os.path.exists(self.gmail_token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.gmail_token_file, self.scopes)
            except Exception as e:
                print(f"⚠️ Failed to load Gmail token: {e}")

        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"⚠️ Failed to refresh Gmail token: {e}")
                    creds = None

            if not creds:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.client_secret_file, self.scopes)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    print(f"❌ Gmail OAuth2 authentication failed: {e}")
                    return None

            # Save the credentials for the next run
            try:
                with open(self.gmail_token_file, 'w') as token:
                    token.write(creds.to_json())
                print("💾 Gmail OAuth2 token saved")
            except Exception as e:
                print(f"⚠️ Failed to save Gmail token: {e}")

        return creds

    def get_xoauth2_string(self, user, access_token):
        """Generate XOAUTH2 authentication string for IMAP"""
        # XOAUTH2 format: base64("user=" + user + "^Aauth=Bearer " + access_token + "^A^A")
        auth_string = f"user={user}\x01auth=Bearer {access_token}\x01\x01"
        return base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    
    def _get_mfa_from_gmail_api(self, creds):
        """Get MFA code using Gmail API"""
        try:
            service = build('gmail', 'v1', credentials=creds)
            
            # Search for recent Garmin emails (last 10 minutes)
            after_time = int((datetime.now() - timedelta(minutes=10)).timestamp())
            query = f'from:garmin.com after:{after_time}'  # Broader search
            
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
            body = self._extract_email_body(payload)
            
            if body:
                # Look for 6-digit code
                mfa_pattern = r'\b(\d{6})\b'
                match = re.search(mfa_pattern, body)
                if match:
                    mfa_code = match.group(1)
                    print(f"✅ Found MFA code in email: {mfa_code}")
                    
                    # Mark as read/delete
                    service.users().messages().modify(
                        userId='me',
                        id=messages[0]['id'],
                        body={'removeLabelIds': ['UNREAD']}
                    ).execute()
                    
                    return mfa_code
            
            return None
            
        except Exception as e:
            print(f"📧 Gmail API error: {e}")
            return None
    
    def _extract_email_body(self, payload):
        """Extract body from Gmail API payload"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    break
                elif part['mimeType'] == 'text/html' and not body:
                    data = part['body']['data']
                    html_body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    # Simple HTML to text (remove tags)
                    body = re.sub('<[^<]+?>', '', html_body)
        else:
            if payload['body'].get('data'):
                body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
        
        return body
    
    def get_mfa_headless(self) -> str:
        """Get MFA code for headless operation"""
        print("🔍 Getting MFA code for headless operation...")
        strategies = [
            self._get_mfa_from_env,
            self._get_mfa_from_file,
            self._get_mfa_from_email,
            self._get_mfa_from_webhook,
            self._fail_with_instructions
        ]

        for i, strategy in enumerate(strategies):
            try:
                print(f"🎯 Trying strategy {i+1}: {strategy.__name__}")
                mfa_code = strategy()
                if mfa_code:
                    print(f"✅ Strategy {i+1} succeeded: {mfa_code}")
                    return mfa_code
                else:
                    print(f"❌ Strategy {i+1} returned no code")
            except Exception as e:
                print(f"⚠️ Strategy {i+1} failed: {e}")
                continue

        raise Exception("No MFA code available for headless operation")
    
    def _get_mfa_from_env(self) -> str:
        """Get MFA from environment variable"""
        mfa_code = os.environ.get("GARMIN_MFA_CODE")
        if mfa_code:
            print(f"📱 Using MFA from environment variable")
            return mfa_code
        return None
    
    def _get_mfa_from_file(self) -> str:
        """Get MFA from temporary file (for CI/CD)"""
        mfa_file = Path("/tmp/garmin_mfa.txt")
        if mfa_file.exists():
            mfa_code = mfa_file.read_text().strip()
            if mfa_code and len(mfa_code) >= 4:
                print(f"📄 Using MFA from temporary file")
                # Clean up the file after use
                mfa_file.unlink()
                return mfa_code
        return None

    def _get_mfa_from_email(self) -> str:
        """Get MFA code from email (checks Gmail for Garmin MFA emails)"""
        # First try Gmail API with OAuth2
        if self.client_secret_file and GOOGLE_AUTH_AVAILABLE:
            creds = self.get_gmail_credentials()
            if creds:
                print(f"🔐 Using Gmail API with OAuth2")
                mfa_code = self._get_mfa_from_gmail_api(creds)
                if mfa_code:
                    return mfa_code
        
        # Fallback to IMAP with basic auth
        email_server = os.environ.get("EMAIL_SERVER", "imap.gmail.com")
        email_user = os.environ.get("EMAIL_USER")
        email_password = os.environ.get("EMAIL_PASSWORD")
        email_port = int(os.environ.get("EMAIL_PORT", "993"))

        if not all([email_user, email_password]):
            return None

        try:
            print(f"📧 Checking email via IMAP...")

            # Connect to email server
            mail = imaplib.IMAP4_SSL(email_server, email_port)
            mail.login(email_user, email_password)

            mail.select('inbox')

            # Search for recent Garmin MFA emails (last 10 minutes)
            since_date = (datetime.now() - timedelta(minutes=10)).strftime("%d-%b-%Y")
            search_criteria = f'(FROM "garmin.com" SUBJECT "Garmin Connect" SINCE "{since_date}")'

            status, messages = mail.search(None, search_criteria)

            if status != 'OK' or not messages[0]:
                print("📧 No recent Garmin MFA emails found")
                mail.logout()
                return None

            # Get the latest email
            latest_email_id = messages[0].split()[-1]
            status, msg_data = mail.fetch(latest_email_id, '(RFC822)')

            if status != 'OK':
                print("📧 Failed to fetch email")
                mail.logout()
                return None

            # Parse email content
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)

            # Extract text content
            text_content = ""
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        text_content += part.get_payload(decode=True).decode('utf-8', errors='ignore')
            else:
                text_content = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')

            # Look for MFA code patterns in the email
            # Common patterns: "code is: 123456", "verification code: 123456", "MFA code: 123456"
            mfa_patterns = [
                r'code\s+is\s*:\s*(\d{6})',
                r'verification\s+code\s*:\s*(\d{6})',
                r'MFA\s+code\s*:\s*(\d{6})',
                r'code\s*:\s*(\d{6})',
                r'(\d{6})',  # Fallback: just 6 digits
            ]

            for pattern in mfa_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    mfa_code = match.group(1)
                    if len(mfa_code) == 6 and mfa_code.isdigit():
                        print(f"📧 Found MFA code in email: {mfa_code}")
                        mail.logout()

                        # Mark email as read/deleted to avoid reuse
                        mail.store(latest_email_id, '+FLAGS', '\\Deleted')
                        mail.expunge()

                        return mfa_code

            print("📧 No valid MFA code found in email")
            mail.logout()
            return None

        except Exception as e:
            print(f"📧 Email check failed: {e}")
            return None

    def _get_mfa_from_webhook(self) -> str:
        """Get MFA from webhook/API endpoint"""
        webhook_url = os.environ.get("GARMIN_MFA_WEBHOOK")
        if webhook_url:
            try:
                response = requests.get(webhook_url, timeout=10)
                if response.status_code == 200:
                    mfa_code = response.text.strip()
                    if mfa_code and len(mfa_code) >= 4:
                        print(f"🌐 Using MFA from webhook")
                        return mfa_code
            except Exception as e:
                pass
        return None
    
    def _fail_with_instructions(self) -> str:
        """Provide clear instructions for manual intervention"""
        available_methods = []
        if os.environ.get("GARMIN_MFA_CODE"):
            available_methods.append("Environment variable (GARMIN_MFA_CODE)")
        if Path("/tmp/garmin_mfa.txt").exists():
            available_methods.append("Temporary file (/tmp/garmin_mfa.txt)")
        if os.environ.get("EMAIL_USER") and os.environ.get("EMAIL_PASSWORD"):
            available_methods.append("Email inbox (automatic)")
        if os.environ.get("GARMIN_MFA_WEBHOOK"):
            available_methods.append("Webhook endpoint")
        
        # Send ntfy notification
        self.notifier.notify_mfa_required(available_methods)
        
        instructions = """
🚨 HEADLESS 2FA REQUIRED 🚨

Your Garmin Connect tokens have expired and 2FA is required.
For headless operation, use one of these methods:

1. Environment Variable:
   export GARMIN_MFA_CODE="123456"

2. Temporary File:
   echo "123456" > /tmp/garmin_mfa.txt

3. Email (Automatic):
   export EMAIL_USER="your-email@gmail.com"
   export EMAIL_PASSWORD="your-app-password"
   # For Gmail, use an App Password, not your regular password

4. Webhook/API:
   export GARMIN_MFA_WEBHOOK="https://your-api.com/mfa"

5. Pre-authenticate:
   python authenticate.py

Then restart the MCP server.
        """
        print(instructions)
        raise Exception("2FA required for headless operation")
    
    def check_token_validity(self) -> bool:
        """Check if existing tokens are still valid"""
        try:
            garmin = Garmin()
            garmin.login(self.tokenstore)
            # Try a simple API call to verify tokens work
            garmin.get_full_name()
            self.log_auth_attempt(True, "token_validation")
            return True
        except Exception as e:
            self.log_auth_attempt(False, "token_validation", str(e))
            return False
    
    def authenticate(self) -> Garmin:
        """Main authentication method with fallback strategies"""
        if not self.email or not self.password:
            raise Exception("GARMIN_EMAIL and GARMIN_PASSWORD must be set")
        
        token_path = Path(os.path.expanduser(self.tokenstore))
        
        # Workaround: If the token directory exists but is empty or invalid,
        # garth will fail. We remove it to force a clean login.
        if token_path.exists() and not any(token_path.iterdir()):
             print(f"Found empty token directory at {token_path}, removing to force fresh login.")
             token_path.rmdir()

        # If token directory exists and has files, try to use existing tokens
        if token_path.exists() and any(token_path.iterdir()):
            print("Found existing token directory, attempting to resume session...")
            try:
                # The library will automatically use the tokenstore
                garmin = Garmin(self.email, self.password)
                garmin.login()
                garmin.get_full_name() # Verify token validity
                print("✅ Successfully resumed session with existing tokens.")
                self.log_auth_attempt(True, "token_resume")
                return garmin
            except Exception as e:
                print(f"⚠️ Could not resume with existing tokens: {e}. Proceeding to fresh login.")
                self.log_auth_attempt(False, "token_resume", str(e))

        # If no valid tokens, perform a fresh login
        print("🔄 Tokens invalid or missing, performing fresh authentication...")
        
        try:
            print(f"🔐 Attempting login with email: {self.email}")
            garmin = Garmin(
                email=self.email,
                password=self.password,
                is_cn=False,
                prompt_mfa=self.get_mfa_headless
            )
            print("📡 Calling garmin.login()...")
            garmin.login()
            print("✅ Login completed successfully")
            
            # Tokens are saved automatically by garth to the tokenstore
            self.log_auth_attempt(True, "fresh_login")
            print("✅ Authentication successful, tokens saved")
            self.notifier.notify_auth_success("fresh login with 2FA")
            return garmin
            
        except Exception as e:
            self.log_auth_attempt(False, "fresh_login", str(e))
            if "429" in str(e):
                self.notifier.notify_rate_limited()
                raise Exception("Rate limited - please wait before retrying")
            else:
                self.notifier.notify_auth_failure(str(e))
            raise e

def create_headless_auth_client():
    """Factory function to create authenticated Garmin client"""
    auth = HeadlessGarminAuth()
    return auth.authenticate()

if __name__ == "__main__":
    print("🤖 Headless Garmin Authentication Test")
    print("=" * 40)
    
    try:
        auth = HeadlessGarminAuth()
        client = auth.authenticate()
        name = client.get_full_name()
        print(f"🎉 Success! Authenticated as: {name}")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")