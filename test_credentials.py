#!/usr/bin/env python3
"""
Test basic Garmin credentials without MFA.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

def test_credentials():
    """Test if Garmin credentials are valid."""
    email = os.environ.get("GARMIN_EMAIL")
    password = os.environ.get("GARMIN_PASSWORD")

    if not email or not password:
        print("❌ Credentials not set in .env")
        return False

    print(f"Testing credentials for: {email}")
    print(f"Password length: {len(password)} characters")

    try:
        from garminconnect import Garmin, GarminConnectAuthenticationError
        from garth.exc import GarthException

        # Try a very basic test - just initialize
        print("🔧 Testing Garmin client initialization...")
        garmin = Garmin(email, password)
        print("✅ Client initialized successfully")

        # Try to see what happens with login (expect MFA or 401)
        print("🔐 Testing login (expecting MFA or error)...")
        try:
            garmin.login()
            print("✅ Login successful (unexpected - should require MFA)")
        except Exception as e:
            error_msg = str(e).lower()
            if "mfa" in error_msg or "verification" in error_msg:
                print("✅ Login prompted for MFA (this is expected)")
                return True
            elif "401" in error_msg or "unauthorized" in error_msg:
                print("❌ Login failed with 401 Unauthorized - check credentials")
                return False
            else:
                print(f"⚠️ Login failed with unexpected error: {e}")
                return False

    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Garmin Credentials Test")
    print("==========================")
    success = test_credentials()
    if success:
        print("\n✅ Credentials appear valid (MFA required as expected)")
    else:
        print("\n❌ Credentials test failed")