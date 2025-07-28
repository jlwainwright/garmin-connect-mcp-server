#!/usr/bin/env python3
"""
Standalone Garmin Connect authentication script.
Run this first to authenticate and save tokens, then use the MCP server.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from garminconnect import Garmin, GarminConnectAuthenticationError
from garth.exc import GarthHTTPError
import requests

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

def get_mfa() -> str:
    """Get MFA code from user input"""
    print("\n🔐 Garmin Connect MFA required.")
    print("📧 Please check your email/phone for the verification code.")
    return input("Enter MFA code: ")

def authenticate():
    """Authenticate with Garmin Connect"""
    email = os.environ.get("GARMIN_EMAIL")
    password = os.environ.get("GARMIN_PASSWORD")
    tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
    
    if not email or not password:
        print("❌ Please set GARMIN_EMAIL and GARMIN_PASSWORD in your .env file")
        return False
    
    print(f"🔄 Attempting to authenticate with Garmin Connect...")
    print(f"📧 Email: {email}")
    
    try:
        # Try existing tokens first
        print(f"🔍 Checking for existing tokens in '{tokenstore}'...")
        garmin = Garmin()
        garmin.login(tokenstore)
        print("✅ Authentication successful using existing tokens!")
        return True
        
    except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
        print("🔄 No valid tokens found. Performing fresh login...")
        
        try:
            garmin = Garmin(
                email=email, 
                password=password, 
                is_cn=False, 
                prompt_mfa=get_mfa
            )
            garmin.login()
            
            # Save tokens
            garmin.garth.dump(tokenstore)
            print(f"✅ Authentication successful!")
            print(f"💾 Tokens saved to '{tokenstore}' for future use.")
            return True
            
        except Exception as e:
            print(f"❌ Authentication failed: {str(e)}")
            if "429" in str(e):
                print("⏳ Rate limited. Please wait a few minutes before trying again.")
            return False

if __name__ == "__main__":
    print("🏃‍♂️ Garmin Connect Authentication")
    print("=" * 40)
    
    success = authenticate()
    
    if success:
        print("\n🎉 Ready to use the MCP server!")
        print("You can now run: npx @modelcontextprotocol/inspector venv/bin/python garmin_mcp_server_fixed.py")
    else:
        print("\n💡 Tips:")
        print("1. Check your .env file has correct GARMIN_EMAIL and GARMIN_PASSWORD")
        print("2. If rate limited (429 error), wait 5-10 minutes")
        print("3. Make sure you have access to your email/phone for MFA")