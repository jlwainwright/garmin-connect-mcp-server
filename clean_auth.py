#!/usr/bin/env python3
"""
Clean authentication script that removes dummy tokens and performs fresh login.
"""

import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
from garminconnect import Garmin, GarminConnectAuthenticationError
from garth.exc import GarthException

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

def get_mfa_from_input() -> str:
    """Prompt user for MFA code."""
    print("\n🔐 Garmin Connect MFA required.")
    print("📧 Please check your email for the verification code.")
    return input("Enter MFA code: ")

def clean_authenticate():
    """Remove dummy tokens and perform clean authentication."""
    email = os.environ.get("GARMIN_EMAIL")
    password = os.environ.get("GARMIN_PASSWORD")
    tokenstore = os.path.expanduser(os.getenv("GARMINTOKENS", "~/.garminconnect"))

    if not email or not password:
        print("❌ GARMIN_EMAIL and GARMIN_PASSWORD must be set in .env")
        return False

    print("🧹 Cleaning up dummy tokens...")
    if os.path.exists(tokenstore):
        shutil.rmtree(tokenstore)
        print(f"🗑️  Removed {tokenstore}")

    print("🔄 Starting clean authentication...")

    try:
        # Initialize with credentials and MFA prompt
        api = Garmin(email, password, prompt_mfa=get_mfa_from_input)

        # This will trigger the login and MFA prompt if needed
        api.login()

        # Manually save the tokens
        api.garth.dump(tokenstore)

        print("\n✅ Authentication successful!")
        print(f"💾 Tokens have been saved to: {tokenstore}")
        print("You can now run the main server script: python garmin_mcp_server_fixed.py")
        return True

    except (GarthException, GarminConnectAuthenticationError) as e:
        print(f"❌ Authentication failed: {e}")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        return False

if __name__ == "__main__":
    print("🧹 Garmin Connect Clean Authentication")
    print("=======================================")
    print("This script will remove dummy tokens and perform a clean login.")
    clean_authenticate()