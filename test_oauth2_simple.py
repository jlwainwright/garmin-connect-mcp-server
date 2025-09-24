#!/usr/bin/env python3
"""
Simple OAuth2 Gmail test - tests OAuth2 setup without Garmin dependencies.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

def test_oauth2_simple():
    """Test OAuth2 Gmail setup"""
    print("🔐 Testing OAuth2 Gmail Setup (Simple)")
    print("=" * 40)

    # Check configuration
    client_secret_file = os.environ.get("GOOGLE_CLIENT_SECRET_FILE")
    email_user = os.environ.get("EMAIL_USER")

    if not client_secret_file:
        print("❌ GOOGLE_CLIENT_SECRET_FILE not configured")
        print("Set GOOGLE_CLIENT_SECRET_FILE in your .env file")
        return False

    if not Path(client_secret_file).exists():
        print(f"❌ Client secret file not found: {client_secret_file}")
        return False

    if not email_user:
        print("❌ EMAIL_USER not configured")
        print("Set EMAIL_USER in your .env file")
        return False

    print(f"📧 Email: {email_user}")
    print(f"📄 Client secret: {client_secret_file}")

    # Test OAuth2 imports and basic functionality
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        print("✅ Google API libraries imported successfully")

        # Test loading client secrets
        flow = InstalledAppFlow.from_client_secrets_file(
            client_secret_file, ['https://www.googleapis.com/auth/gmail.readonly'])
        print("✅ Client secret file loaded successfully")

        # Check for existing token
        token_file = os.path.expanduser(os.environ.get("GMAIL_TOKEN_FILE", "~/.gmail_token.json"))
        if os.path.exists(token_file):
            print(f"✅ Token file exists: {token_file}")
            try:
                creds = Credentials.from_authorized_user_file(token_file, ['https://www.googleapis.com/auth/gmail.readonly'])
                if creds and creds.valid:
                    print("✅ Existing token is valid")
                    return True
                elif creds and creds.expired and creds.refresh_token:
                    print("🔄 Token exists but expired - will refresh on first use")
                    return True
                else:
                    print("⚠️ Token exists but needs re-authorization")
            except Exception as e:
                print(f"⚠️ Error reading token file: {e}")
        else:
            print(f"ℹ️ No token file found: {token_file}")
            print("First run will require browser authorization")

        print("\n🎉 OAuth2 configuration is valid!")
        print("Run your MCP server to complete authorization:")
        print("python garmin_mcp_server_fixed.py")

        return True

    except ImportError as e:
        print(f"❌ Missing Google API libraries: {e}")
        print("Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        return False
    except Exception as e:
        print(f"❌ OAuth2 test failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your client_secret.json file is valid")
        print("2. Ensure Gmail API is enabled in Google Cloud Console")
        print("3. Verify OAuth2 consent screen is configured")
        return False

if __name__ == "__main__":
    success = test_oauth2_simple()
    sys.exit(0 if success else 1)