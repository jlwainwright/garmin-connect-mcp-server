#!/usr/bin/env python3
"""
Test all ntfy notification types for Garmin Connect authentication.
"""

import time
from ntfy_notifier import NtfyNotifier

def test_all_notifications():
    """Test all notification types"""
    notifier = NtfyNotifier()
    
    print("🧪 Testing Garmin Connect Ntfy Notifications")
    print("=" * 50)
    print(f"Server: {notifier.server}")
    print(f"Topic: {notifier.topic}")
    print()
    
    tests = [
        ("Basic Test", lambda: notifier.test_notification()),
        ("Auth Success", lambda: notifier.notify_auth_success("test authentication")),
        ("Auth Failure", lambda: notifier.notify_auth_failure("Invalid credentials for testing")),
        ("Rate Limited", lambda: notifier.notify_rate_limited(15)),
        ("MFA Required", lambda: notifier.notify_mfa_required(["Environment variable", "Temporary file"])),
        ("Tokens Warning (65 days)", lambda: notifier.notify_tokens_expiring(65)),
        ("Tokens Critical (95 days)", lambda: notifier.notify_tokens_expiring(95)),
    ]
    
    for test_name, test_func in tests:
        print(f"🔄 Sending: {test_name}")
        try:
            success = test_func()
            if success != False:  # Some functions don't return boolean
                print("✅ Sent successfully")
            else:
                print("❌ Failed to send")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("⏳ Waiting 2 seconds...")
        time.sleep(2)
        print()
    
    print("🎉 All test notifications sent!")
    print(f"📱 Check your ntfy app or visit: {notifier.server}/{notifier.topic}")

if __name__ == "__main__":
    test_all_notifications()