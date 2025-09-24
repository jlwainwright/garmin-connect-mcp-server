#!/usr/bin/env python3
"""
Test script for email-based MFA functionality.
Run this to verify your email settings work before using in production.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Import the email method from headless_auth
sys.path.append(str(Path(__file__).parent))
from headless_auth import HeadlessGarminAuth

def test_email_mfa():
    """Test the email MFA functionality"""
    print("🧪 Testing Email MFA Functionality")
    print("=" * 40)

    # Check authentication method
    email_user = os.environ.get("EMAIL_USER")
    client_secret_file = os.environ.get("GOOGLE_CLIENT_SECRET_FILE")
    email_password = os.environ.get("EMAIL_PASSWORD")

    if not email_user:
        print("❌ EMAIL_USER not configured!")
        print("Run: python setup_email_mfa.py")
        return False

    # Determine auth method
    use_oauth2 = bool(client_secret_file)
    use_basic = bool(email_password)

    if not use_oauth2 and not use_basic:
        print("❌ No authentication method configured!")
        print("Either set EMAIL_PASSWORD (basic auth) or GOOGLE_CLIENT_SECRET_FILE (OAuth2)")
        print("Run: python setup_email_mfa.py")
        return False

    print(f"📧 Testing email: {email_user}")
    if use_oauth2:
        print("🔐 Using OAuth2 authentication")
        print(f"📄 Client secret file: {client_secret_file}")
    else:
        print("🔑 Using basic authentication")
        print(f"📧 Server: {os.environ.get('EMAIL_SERVER', 'imap.gmail.com')}")

    # Create auth instance and test email method
    auth = HeadlessGarminAuth()

    try:
        mfa_code = auth._get_mfa_from_email()
        if mfa_code:
            print(f"✅ Found MFA code: {mfa_code}")
            return True
        else:
            print("ℹ️  No recent Garmin MFA emails found (this is normal if you haven't triggered 2FA recently)")
            print("💡 To test: Trigger a Garmin login that requires 2FA, then run this test")
            return True  # Not an error, just no emails

    except Exception as e:
        print(f"❌ Email test failed: {e}")
        print("\nTroubleshooting:")

        if use_oauth2:
            print("1. Check your GOOGLE_CLIENT_SECRET_FILE path")
            print("2. Ensure Gmail API is enabled in Google Cloud Console")
            print("3. Verify OAuth2 consent screen is configured")
            print("4. Try deleting ~/.gmail_token.json and re-authorizing")
        else:
            print("1. Check your email credentials")
            print("2. For Gmail, make sure you're using an App Password")
            print("3. Verify IMAP is enabled in your email settings")
            print("4. Check if your email provider blocks less secure apps")

        print("5. Run: python setup_email_mfa.py")
        return False

if __name__ == "__main__":
    success = test_email_mfa()
    sys.exit(0 if success else 1)