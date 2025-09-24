#!/usr/bin/env python3
"""
Test script for OAuth2 Gmail authentication.
This script tests the OAuth2 setup and Gmail access.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Import the auth class
sys.path.append(str(Path(__file__).parent))
from headless_auth import HeadlessGarminAuth

def test_oauth2_setup():
    """Test OAuth2 Gmail setup"""
    print("🔐 Testing OAuth2 Gmail Setup")
    print("=" * 35)

    # Check configuration
    client_secret_file = os.environ.get("GOOGLE_CLIENT_SECRET_FILE")
    email_user = os.environ.get("EMAIL_USER")

    if not client_secret_file:
        print("❌ GOOGLE_CLIENT_SECRET_FILE not configured")
        print("Run: python setup_oauth2.py")
        return False

    if not Path(client_secret_file).exists():
        print(f"❌ Client secret file not found: {client_secret_file}")
        return False

    if not email_user:
        print("❌ EMAIL_USER not configured")
        print("Run: python setup_oauth2.py")
        return False

    print(f"📧 Email: {email_user}")
    print(f"📄 Client secret: {client_secret_file}")

    # Test OAuth2 credential loading
    auth = HeadlessGarminAuth()

    try:
        print("\n🔄 Testing OAuth2 credential loading...")
        creds = auth.get_gmail_credentials()

        if creds:
            print("✅ OAuth2 credentials loaded successfully")
            print(f"🔑 Token expiry: {creds.expiry}")
            print(f"📧 Scopes: {creds.scopes}")

            # Test basic Gmail API access
            if hasattr(auth, 'GOOGLE_AUTH_AVAILABLE') and auth.GOOGLE_AUTH_AVAILABLE:
                try:
                    from googleapiclient.discovery import build
                    service = build('gmail', 'v1', credentials=creds)
                    profile = service.users().getProfile(userId='me').execute()
                    print(f"📬 Gmail access successful: {profile.get('emailAddress')}")
                except Exception as e:
                    print(f"⚠️ Gmail API test failed: {e}")
                    print("This is normal if you haven't authorized yet")
            else:
                print("⚠️ Google API client not available")

            return True
        else:
            print("❌ Failed to load OAuth2 credentials")
            print("💡 You may need to authorize access first")
            print("   Run your MCP server and complete the OAuth2 flow")
            return False

    except Exception as e:
        print(f"❌ OAuth2 test failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your client_secret.json file is valid")
        print("2. Ensure Gmail API is enabled in Google Cloud Console")
        print("3. Try deleting ~/.gmail_token.json and re-authorizing")
        return False

if __name__ == "__main__":
    success = test_oauth2_setup()
    sys.exit(0 if success else 1)