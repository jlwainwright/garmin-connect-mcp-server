#!/usr/bin/env python3
"""
Headless authentication handler for Garmin Connect MCP server.
Supports multiple authentication strategies for automated deployments.
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from garminconnect import Garmin, GarminConnectAuthenticationError
from garth.exc import GarthHTTPError
import requests
from ntfy_notifier import NtfyNotifier

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

class HeadlessGarminAuth:
    def __init__(self):
        self.email = os.environ.get("GARMIN_EMAIL")
        self.password = os.environ.get("GARMIN_PASSWORD")
        self.tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
        self.tokenstore_base64 = os.getenv("GARMINTOKENS_BASE64") or "~/.garminconnect_base64"
        self.auth_log_file = Path(__file__).parent / "auth_log.json"
        self.notifier = NtfyNotifier()
        
    def log_auth_attempt(self, success: bool, method: str, error: str = None):
        """Log authentication attempts for monitoring"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "method": method,
            "error": error
        }
        
        try:
            if self.auth_log_file.exists():
                with open(self.auth_log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(log_entry)
            
            # Keep only last 50 entries
            logs = logs[-50:]
            
            with open(self.auth_log_file, 'w') as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            # Don't fail if logging fails
            pass
    
    def get_mfa_headless(self) -> str:
        """Get MFA code for headless operation"""
        strategies = [
            self._get_mfa_from_env,
            self._get_mfa_from_file,
            self._get_mfa_from_webhook,
            self._fail_with_instructions
        ]
        
        for strategy in strategies:
            try:
                mfa_code = strategy()
                if mfa_code:
                    return mfa_code
            except Exception as e:
                continue
        
        raise Exception("No MFA code available for headless operation")
    
    def _get_mfa_from_env(self) -> str:
        """Get MFA from environment variable"""
        mfa_code = os.environ.get("GARMIN_MFA_CODE")
        if mfa_code:
            print(f"📱 Using MFA from environment variable")
            return mfa_code
        return None
    
    def _get_mfa_from_file(self) -> str:
        """Get MFA from temporary file (for CI/CD)"""
        mfa_file = Path("/tmp/garmin_mfa.txt")
        if mfa_file.exists():
            mfa_code = mfa_file.read_text().strip()
            if mfa_code and len(mfa_code) >= 4:
                print(f"📄 Using MFA from temporary file")
                # Clean up the file after use
                mfa_file.unlink()
                return mfa_code
        return None
    
    def _get_mfa_from_webhook(self) -> str:
        """Get MFA from webhook/API endpoint"""
        webhook_url = os.environ.get("GARMIN_MFA_WEBHOOK")
        if webhook_url:
            try:
                response = requests.get(webhook_url, timeout=10)
                if response.status_code == 200:
                    mfa_code = response.text.strip()
                    if mfa_code and len(mfa_code) >= 4:
                        print(f"🌐 Using MFA from webhook")
                        return mfa_code
            except Exception as e:
                pass
        return None
    
    def _fail_with_instructions(self) -> str:
        """Provide clear instructions for manual intervention"""
        available_methods = []
        if os.environ.get("GARMIN_MFA_CODE"):
            available_methods.append("Environment variable (GARMIN_MFA_CODE)")
        if Path("/tmp/garmin_mfa.txt").exists():
            available_methods.append("Temporary file (/tmp/garmin_mfa.txt)")
        if os.environ.get("GARMIN_MFA_WEBHOOK"):
            available_methods.append("Webhook endpoint")
        
        # Send ntfy notification
        self.notifier.notify_mfa_required(available_methods)
        
        instructions = """
🚨 HEADLESS 2FA REQUIRED 🚨

Your Garmin Connect tokens have expired and 2FA is required.
For headless operation, use one of these methods:

1. Environment Variable:
   export GARMIN_MFA_CODE="123456"

2. Temporary File:
   echo "123456" > /tmp/garmin_mfa.txt

3. Webhook/API:
   export GARMIN_MFA_WEBHOOK="https://your-api.com/mfa"

4. Pre-authenticate:
   python authenticate.py

Then restart the MCP server.
        """
        print(instructions)
        raise Exception("2FA required for headless operation")
    
    def check_token_validity(self) -> bool:
        """Check if existing tokens are still valid"""
        try:
            garmin = Garmin()
            garmin.login(self.tokenstore)
            # Try a simple API call to verify tokens work
            garmin.get_full_name()
            self.log_auth_attempt(True, "token_validation")
            return True
        except Exception as e:
            self.log_auth_attempt(False, "token_validation", str(e))
            return False
    
    def authenticate(self) -> Garmin:
        """Main authentication method with fallback strategies"""
        if not self.email or not self.password:
            raise Exception("GARMIN_EMAIL and GARMIN_PASSWORD must be set")
        
        # Try existing tokens first
        if self.check_token_validity():
            print("✅ Using existing valid tokens")
            garmin = Garmin()
            garmin.login(self.tokenstore)
            return garmin
        
        print("🔄 Tokens invalid or missing, performing fresh authentication...")
        
        try:
            garmin = Garmin(
                email=self.email,
                password=self.password,
                is_cn=False,
                prompt_mfa=self.get_mfa_headless
            )
            garmin.login()
            
            # Save tokens in both formats
            garmin.garth.dump(self.tokenstore)
            token_base64 = garmin.garth.dumps()
            dir_path = os.path.expanduser(self.tokenstore_base64)
            with open(dir_path, "w") as token_file:
                token_file.write(token_base64)
            
            self.log_auth_attempt(True, "fresh_login")
            print("✅ Authentication successful, tokens saved")
            
            # Send success notification
            self.notifier.notify_auth_success("fresh login with 2FA")
            
            return garmin
            
        except Exception as e:
            self.log_auth_attempt(False, "fresh_login", str(e))
            
            if "429" in str(e):
                print("⏳ Rate limited. Tokens will retry automatically.")
                self.notifier.notify_rate_limited()
                raise Exception("Rate limited - please wait before retrying")
            else:
                # Send failure notification
                self.notifier.notify_auth_failure(str(e))
            
            raise e

def create_headless_auth_client():
    """Factory function to create authenticated Garmin client"""
    auth = HeadlessGarminAuth()
    return auth.authenticate()

if __name__ == "__main__":
    print("🤖 Headless Garmin Authentication Test")
    print("=" * 40)
    
    try:
        auth = HeadlessGarminAuth()
        client = auth.authenticate()
        name = client.get_full_name()
        print(f"🎉 Success! Authenticated as: {name}")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")