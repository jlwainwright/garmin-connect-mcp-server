#!/usr/bin/env python3
"""
Authentication monitoring and alerting for Garmin MCP server.
Use this to check if tokens are about to expire.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from headless_auth import HeadlessGarminAuth
from ntfy_notifier import NtfyNotifier

def check_auth_status():
    """Check authentication status and provide recommendations"""
    auth = HeadlessGarminAuth()
    notifier = NtfyNotifier()
    auth_log_file = Path(__file__).parent / "auth_log.json"
    
    print("🔍 Garmin Connect Authentication Status")
    print("=" * 40)
    
    # Check current token validity
    is_valid = auth.check_token_validity()
    
    if is_valid:
        print("✅ Current tokens are VALID")
        
        # Check token age from logs
        if auth_log_file.exists():
            try:
                with open(auth_log_file, 'r') as f:
                    logs = json.load(f)
                
                # Find last successful authentication
                last_success = None
                for log in reversed(logs):
                    if log['success'] and log['method'] in ['fresh_login', 'token_validation']:
                        last_success = datetime.fromisoformat(log['timestamp'])
                        break
                
                if last_success:
                    age = datetime.now() - last_success
                    print(f"📅 Last successful auth: {age.days} days ago")
                    
                    # Send notifications based on token age
                    if age.days > 60:
                        notifier.notify_tokens_expiring(age.days)
                        
                        if age.days > 90:  # 3 months
                            print("🚨 CRITICAL: Tokens are very old (>90 days)")
                            print("🔧 Re-authentication recommended immediately")
                        else:  # 60-90 days
                            print("⚠️  WARNING: Tokens are getting old (>60 days)")
                            print("💡 Consider re-authenticating soon")
                
            except Exception as e:
                print(f"⚠️  Could not read auth logs: {e}")
        
    else:
        print("❌ Current tokens are INVALID or MISSING")
        print("🔧 2FA authentication required")
        
        # Check for available MFA methods
        mfa_methods = []
        if os.environ.get("GARMIN_MFA_CODE"):
            mfa_methods.append("Environment variable (GARMIN_MFA_CODE)")
        if Path("/tmp/garmin_mfa.txt").exists():
            mfa_methods.append("Temporary file (/tmp/garmin_mfa.txt)")
        if os.environ.get("GARMIN_MFA_WEBHOOK"):
            mfa_methods.append("Webhook endpoint")
            
        if mfa_methods:
            print("📱 Available MFA methods:")
            for method in mfa_methods:
                print(f"   • {method}")
        else:
            print("📱 No automated MFA methods configured")
            print("💡 Set up one of these for headless operation:")
            print("   • export GARMIN_MFA_CODE='123456'")
            print("   • echo '123456' > /tmp/garmin_mfa.txt")
            print("   • export GARMIN_MFA_WEBHOOK='https://your-api.com/mfa'")
    
    # Recent failures
    if auth_log_file.exists():
        try:
            with open(auth_log_file, 'r') as f:
                logs = json.load(f)
            
            recent_failures = [
                log for log in logs[-10:]  # Last 10 entries
                if not log['success'] and 
                (datetime.now() - datetime.fromisoformat(log['timestamp'])).days < 1
            ]
            
            if recent_failures:
                print(f"\n⚠️  {len(recent_failures)} authentication failures in last 24h:")
                for failure in recent_failures[-3:]:  # Show last 3
                    timestamp = datetime.fromisoformat(failure['timestamp'])
                    print(f"   • {timestamp.strftime('%H:%M:%S')}: {failure.get('error', 'Unknown error')}")
                    
        except Exception as e:
            pass
    
    return is_valid

def setup_cron_monitoring():
    """Generate cron job for monitoring"""
    script_path = Path(__file__).absolute()
    cron_command = f"0 6 * * * cd {script_path.parent} && python {script_path.name} >> auth_monitor.log 2>&1"
    
    print("\n🤖 Automated Monitoring Setup")
    print("=" * 30)
    print("Add this to your crontab (crontab -e) to check daily at 6 AM:")
    print(f"{cron_command}")

if __name__ == "__main__":
    import sys
    
    is_valid = check_auth_status()
    
    if "--setup-cron" in sys.argv:
        setup_cron_monitoring()
    
    print("\n💡 Tips for Production:")
    print("• Run this script daily to monitor token health")
    print("• Set up alerts when tokens are >60 days old")
    print("• Use webhook MFA for fully automated renewals")
    print("• Keep backup authentication tokens in secure storage")