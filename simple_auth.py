#!/usr/bin/env python3
"""
Simple authentication test to understand Garmin library behavior.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

def test_garmin_init():
    """Test different ways to initialize Garmin client."""
    email = os.environ.get("GARMIN_EMAIL")
    password = os.environ.get("GARMIN_PASSWORD")

    if not email or not password:
        print("❌ Credentials not found")
        return

    print(f"Testing Garmin initialization...")
    print(f"Email: {email}")

    try:
        # Try importing and basic initialization
        from garminconnect import Garmin
        print("✅ Garmin import successful")

        # Try different initialization approaches
        print("Testing basic initialization...")
        garmin = Garmin()
        print("✅ Basic Garmin() initialization successful")

        print("Testing with credentials...")
        garmin2 = Garmin(email, password)
        print("✅ Garmin(email, password) initialization successful")

        print("Testing login...")
        def mfa_prompt():
            return input("Enter MFA code: ")

        garmin2.login()
        print("✅ Login successful!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_garmin_init()