#!/usr/bin/env python3
"""
Authentication using monkey-patching with known MFA code.
"""

import os
import builtins
from pathlib import Path
from dotenv import load_dotenv
from garth import Client

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

def patched_input(prompt=""):
    """Return the latest MFA code when prompted."""
    if "MFA" in prompt or "code" in prompt.lower():
        print(f"🤖 Providing latest MFA code: 111376")
        return "111376"
    else:
        return builtins.original_input(prompt)

def auth_with_known_code():
    """Authenticate using monkey-patched input with known MFA code."""
    email = os.environ.get("GARMIN_EMAIL")
    password = os.environ.get("GARMIN_PASSWORD")
    tokenstore = os.path.expanduser(os.getenv("GARMINTOKENS", "~/.garminconnect"))

    if not email or not password:
        print("❌ Credentials not set")
        return False

    print("🎯 Garmin Authentication with Known MFA Code")
    print("============================================")
    print("Using code 000000 from Gmail for authentication.")

    # Monkey patch input
    builtins.original_input = builtins.input
    builtins.input = patched_input

    try:
        # Create Garth client
        client = Client()

        # Login - MFA prompt will be intercepted
        print("🔐 Starting authentication...")
        client.login(email, password)

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

        print("\n🎉 SUCCESS! Garmin MCP is now fully operational!")
        print("The headless system will handle MFA automatically going forward.")
        print("Run: python garmin_mcp_server_fixed.py")

        return True

    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False
    finally:
        # Restore original input
        builtins.input = builtins.original_input

if __name__ == "__main__":
    auth_with_known_code()