#!/usr/bin/env python3
"""
Setup script for email-based MFA authentication.
This script helps you configure email credentials for automatic 2FA.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv, set_key

def setup_email_mfa():
    """Interactive setup for email MFA"""
    print("📧 Garmin Connect Email MFA Setup")
    print("=" * 40)
    print("This will configure automatic 2FA code retrieval from your email.")
    print()

    # Load existing .env file
    env_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path)

    # Check if .env exists
    if not env_path.exists():
        print("❌ No .env file found. Please create one first with your Garmin credentials.")
        print("Run: cp .env.example .env")
        return False

    print("🔧 Choose Authentication Method:")
    print("1. Basic Authentication (App Password)")
    print("2. OAuth2 (Recommended - More Secure)")
    print()

    auth_choice = input("Choose method (1 or 2) [2]: ").strip()
    if not auth_choice:
        auth_choice = "2"

    if auth_choice == "2":
        # OAuth2 Setup
        print("\n🔐 OAuth2 Setup for Gmail:")
        print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Gmail API: APIs & Services > Library > Gmail API > Enable")
        print("4. Create OAuth2 credentials: APIs & Services > Credentials > Create Credentials > OAuth 2.0 Client IDs")
        print("5. Download the client_secret.json file")
        print()

        client_secret_path = input("Path to client_secret.json file: ").strip()
        if not client_secret_path or not Path(client_secret_path).exists():
            print("❌ Valid client_secret.json file path is required")
            return False

        # Get email address
        email_user = input("Your Gmail address: ").strip()
        if not email_user:
            print("❌ Email address is required")
            return False

        # Save OAuth2 configuration
        try:
            set_key(env_path, "EMAIL_USER", email_user)
            set_key(env_path, "GOOGLE_CLIENT_SECRET_FILE", client_secret_path)
            set_key(env_path, "GMAIL_TOKEN_FILE", "~/.gmail_token.json")

            # Remove basic auth settings if they exist
            from dotenv import unset_key
            try:
                unset_key(env_path, "EMAIL_PASSWORD")
            except:
                pass

            print("✅ OAuth2 configuration saved to .env file")
            print()
            print("🔗 First-time OAuth2 setup:")
            print("The first time you run the server, you'll need to authorize access to your Gmail.")
            print("A browser window will open for you to grant permission.")
            print()

        except Exception as e:
            print(f"❌ Failed to save OAuth2 configuration: {e}")
            return False

    else:
        # Basic Authentication Setup
        print("\n🔧 Basic Authentication Setup:")
        print("For Gmail:")
        print("1. Enable 2FA on your Google account")
        print("2. Generate an App Password: https://myaccount.google.com/apppasswords")
        print("3. Use your Gmail address and the 16-character app password")
        print()

        # Get email credentials
        current_email = os.environ.get("EMAIL_USER", "")
        email_user = input(f"Email address [{current_email}]: ").strip()
        if not email_user:
            email_user = current_email

        if not email_user:
            print("❌ Email address is required")
            return False

        # Mask password input
        import getpass
        email_password = getpass.getpass("Email password (App Password for Gmail): ").strip()

        if not email_password:
            print("❌ Email password is required")
            return False

        # Email server settings
        current_server = os.environ.get("EMAIL_SERVER", "imap.gmail.com")
        email_server = input(f"IMAP server [{current_server}]: ").strip()
        if not email_server:
            email_server = current_server

        current_port = os.environ.get("EMAIL_PORT", "993")
        email_port = input(f"IMAP port [{current_port}]: ").strip()
        if not email_port:
            email_port = current_port

        # Save to .env file
        try:
            set_key(env_path, "EMAIL_USER", email_user)
            set_key(env_path, "EMAIL_PASSWORD", email_password)
            set_key(env_path, "EMAIL_SERVER", email_server)
            set_key(env_path, "EMAIL_PORT", email_port)

            # Remove OAuth2 settings if they exist
            from dotenv import unset_key
            try:
                unset_key(env_path, "GOOGLE_CLIENT_SECRET_FILE")
                unset_key(env_path, "GMAIL_TOKEN_FILE")
            except:
                pass

            print("✅ Basic authentication configuration saved to .env file")

        except Exception as e:
            print(f"❌ Failed to save configuration: {e}")
            return False

    print()
    print("🧪 Testing configuration...")

    # Test the configuration
    from test_email_mfa import test_email_mfa
    success = test_email_mfa()

    if success:
        print()
        print("🎉 Email MFA setup complete!")
        print("The server will now automatically retrieve 2FA codes from your email.")
        print()
        print("Next steps:")
        print("1. Restart your MCP server")
        print("2. The next time 2FA is required, it will be handled automatically")
    else:
        print()
        print("⚠️  Configuration saved but testing failed.")
        print("Check your email settings and run: python test_email_mfa.py")

    return success

if __name__ == "__main__":
    success = setup_email_mfa()
    sys.exit(0 if success else 1)