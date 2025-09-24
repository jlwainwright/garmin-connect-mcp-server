#!/usr/bin/env python3
"""
Setup script for Gmail OAuth2 authentication.
This script configures OAuth2 for secure email access.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv, set_key

def setup_oauth2():
    """Setup OAuth2 for Gmail access"""
    print("🔐 Gmail OAuth2 Setup for Garmin MFA")
    print("=" * 40)
    print("This will configure secure OAuth2 access to your Gmail for automatic 2FA.")
    print()

    # Load existing .env file
    env_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path)

    # Check if .env exists
    if not env_path.exists():
        print("❌ No .env file found. Please create one first with your Garmin credentials.")
        print("Run: cp .env.example .env")
        return False

    print("📋 Prerequisites:")
    print("1. Google Cloud Project with Gmail API enabled")
    print("2. OAuth2 Desktop Application credentials (client_secret.json)")
    print("3. Gmail account with IMAP enabled")
    print()

    # Get client secret file path
    default_path = "/Users/jacques/DevFolder/mcp_servers/garmin_mcp/client_secret.json"
    if Path(default_path).exists():
        client_secret_path = input(f"Path to client_secret.json file [{default_path}]: ").strip()
        if not client_secret_path:
            client_secret_path = default_path
    else:
        client_secret_path = input("Path to client_secret.json file: ").strip()

    if not client_secret_path:
        print("❌ Client secret file path is required")
        return False

    if not Path(client_secret_path).exists():
        print(f"❌ File not found: {client_secret_path}")
        return False

    # Get Gmail address
    email_user = input("Your Gmail address: ").strip()
    if not email_user or '@' not in email_user:
        print("❌ Valid Gmail address is required")
        return False

    # Set token file path
    token_file = input("Token file path [~/.gmail_token.json]: ").strip()
    if not token_file:
        token_file = "~/.gmail_token.json"

    # Save configuration
    try:
        set_key(env_path, "EMAIL_USER", email_user)
        set_key(env_path, "GOOGLE_CLIENT_SECRET_FILE", client_secret_path)
        set_key(env_path, "GMAIL_TOKEN_FILE", token_file)

        # Remove basic auth settings if they exist
        from dotenv import unset_key
        try:
            unset_key(env_path, "EMAIL_PASSWORD")
            unset_key(env_path, "EMAIL_SERVER")
            unset_key(env_path, "EMAIL_PORT")
        except:
            pass

        print("✅ OAuth2 configuration saved to .env file")
        print()
        print("🔗 Next Steps:")
        print("1. Run your MCP server for the first time")
        print("2. A browser will open for OAuth2 authorization")
        print("3. Grant Gmail access permission")
        print("4. The server will save tokens for future use")
        print()
        print("🧪 After authorization, test with:")
        print("   python test_email_mfa.py")

        return True

    except Exception as e:
        print(f"❌ Failed to save configuration: {e}")
        return False

if __name__ == "__main__":
    success = setup_oauth2()
    sys.exit(0 if success else 1)