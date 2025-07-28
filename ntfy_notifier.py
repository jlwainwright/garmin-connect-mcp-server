#!/usr/bin/env python3
"""
Ntfy notification system for Garmin Connect authentication alerts.
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

class NtfyNotifier:
    def __init__(self):
        self.server = os.environ.get("NTFY_SERVER", "https://notify.jacqueswainwright.com")
        self.topic = os.environ.get("NTFY_TOPIC", "garmin-auth")
        self.token = os.environ.get("NTFY_TOKEN")
        self.url = f"{self.server}/{self.topic}"
        
        # Fallback to public ntfy.sh if primary server fails
        self.fallback_server = "https://ntfy.sh"
        self.fallback_topic = f"garmin-mcp-{os.environ.get('USER', 'user')}"
        self.fallback_url = f"{self.fallback_server}/{self.fallback_topic}"
        
    def send_notification(self, title: str, message: str, priority: str = "default", tags: list = None):
        """Send notification to ntfy server with fallback"""
        
        # Try primary server first
        success = self._send_to_server(self.url, title, message, priority, tags, use_auth=True)
        
        if not success:
            print(f"⚠️ Primary server failed, trying fallback...")
            # Try fallback server without auth
            success = self._send_to_server(self.fallback_url, title, message, priority, tags, use_auth=False)
            
            if success:
                print(f"📱 Notification sent via fallback: {title}")
                print(f"🔗 Subscribe to: {self.fallback_url}")
        
        return success
    
    def _send_to_server(self, url: str, title: str, message: str, priority: str, tags: list = None, use_auth: bool = True):
        """Send notification to specific server"""
        headers = {
            "Content-Type": "text/plain; charset=utf-8",
            "Title": title,
            "Priority": priority,
        }
        
        if tags:
            headers["Tags"] = ",".join(tags)
            
        if use_auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        try:
            response = requests.post(
                url,
                data=message.encode('utf-8'),
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                if url == self.url:
                    print(f"📱 Notification sent: {title}")
                return True
            else:
                print(f"❌ Server responded with: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending to {url}: {e}")
            return False
    
    def notify_auth_success(self, method: str):
        """Notify successful authentication"""
        title = "Garmin Auth Success"
        message = f"✅ Garmin Connect authentication successful using {method}.\nTokens refreshed and valid for ~3 months."
        
        self.send_notification(
            title=title,
            message=message,
            priority="low",
            tags=["success", "garmin"]
        )
    
    def notify_auth_failure(self, error: str, retry_suggested: bool = True):
        """Notify authentication failure"""
        title = "Garmin Auth Failed"
        message = f"❌ Garmin Connect authentication failed:\n{error}"
        
        if retry_suggested:
            message += "\n\nAction needed: Check credentials or provide MFA code."
        
        self.send_notification(
            title=title,
            message=message,
            priority="high",
            tags=["error", "garmin", "alert"]
        )
    
    def notify_tokens_expiring(self, days_old: int):
        """Notify when tokens are getting old"""
        if days_old > 90:
            title = "Garmin Tokens Critical"
            priority = "urgent"
            tags = ["critical", "garmin", "urgent"]
            message = f"🚨 Garmin tokens are {days_old} days old and may expire soon!\n\nAction required: Re-authenticate before tokens expire."
        elif days_old > 60:
            title = "Garmin Tokens Aging"
            priority = "high"
            tags = ["warning", "garmin"]
            message = f"⚠️ Garmin tokens are {days_old} days old.\n\nRecommended: Plan to re-authenticate soon."
        else:
            return  # Don't notify for newer tokens
        
        self.send_notification(
            title=title,
            message=message,
            priority=priority,
            tags=tags
        )
    
    def notify_mfa_required(self, available_methods: list):
        """Notify that MFA is required for headless operation"""
        title = "Garmin MFA Required"
        message = "📱 Garmin Connect requires 2FA authentication.\n\n"
        
        if available_methods:
            message += "Available automated methods:\n"
            for method in available_methods:
                message += f"• {method}\n"
        else:
            message += "No automated MFA methods configured.\n\nOptions:\n"
            message += "• Set GARMIN_MFA_CODE environment variable\n"
            message += "• Create /tmp/garmin_mfa.txt file\n"
            message += "• Set GARMIN_MFA_WEBHOOK endpoint\n"
            message += "• Run: python authenticate.py"
        
        self.send_notification(
            title=title,
            message=message,
            priority="high",
            tags=["mfa", "garmin", "auth"]
        )
    
    def notify_rate_limited(self, retry_after_minutes: int = 60):
        """Notify about rate limiting"""
        title = "Garmin Rate Limited"
        message = f"⏳ Garmin Connect API rate limit hit.\n\nRetry in ~{retry_after_minutes} minutes.\nTokens will be refreshed automatically."
        
        self.send_notification(
            title=title,
            message=message,
            priority="low",
            tags=["ratelimit", "garmin"]
        )
    
    def test_notification(self):
        """Send test notification"""
        title = "Garmin Ntfy Test"
        message = f"🧪 Test notification from Garmin MCP server.\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_notification(
            title=title,
            message=message,
            priority="low",
            tags=["test", "garmin"]
        )

def send_test_notification():
    """CLI function to test notifications"""
    notifier = NtfyNotifier()
    success = notifier.test_notification()
    
    if success:
        print("✅ Test notification sent successfully!")
        print(f"📱 Check your ntfy app or visit: {notifier.server}/{notifier.topic}")
    else:
        print("❌ Failed to send test notification")
        print("💡 Check your NTFY_SERVER and NTFY_TOPIC settings in .env")

if __name__ == "__main__":
    import sys
    
    if "--test" in sys.argv:
        send_test_notification()
    else:
        print("Ntfy Notifier for Garmin Connect")
        print("Usage: python ntfy_notifier.py --test")
        print(f"Server: {os.environ.get('NTFY_SERVER', 'Not set')}")
        print(f"Topic: {os.environ.get('NTFY_TOPIC', 'Not set')}")