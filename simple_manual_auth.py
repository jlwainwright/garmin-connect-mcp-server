#!/usr/bin/env python3
"""
Simple manual authentication using known MFA code.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from garth import Client

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

def simple_auth():
    """Simple authentication with manual MFA entry."""
    email = os.environ.get("GARMIN_EMAIL")
    password = os.environ.get("GARMIN_PASSWORD")
    tokenstore = os.path.expanduser(os.getenv("GARMINTOKENS", "~/.garminconnect"))

    if not email or not password:
        print("❌ Credentials not set")
        return False

    print("🔐 Garmin Connect Authentication")
    print("===============================")
    print(f"Email: {email}")
    print("MFA Code: 000000 (from Gmail)")

    try:
        # Create Garth client
        client = Client()

        # Login with known MFA code
        print("🔄 Authenticating...")
        client.login(email, password, mfa_code="000000")

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

        print("\n🎉 SUCCESS! Garmin MCP is ready!")
        print("Run: python garmin_mcp_server_fixed.py")

        return True

    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False

if __name__ == "__main__":
    simple_auth()