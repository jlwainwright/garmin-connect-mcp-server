# Ntfy Notification Setup for Garmin MCP Server

## 🔔 Overview

The Garmin MCP server includes comprehensive ntfy.sh notifications for authentication events:

- ✅ **Authentication Success** - When tokens are refreshed
- ❌ **Authentication Failures** - When login fails  
- ⚠️ **Token Expiration Warnings** - When tokens are 60+ days old
- 🚨 **Critical Token Alerts** - When tokens are 90+ days old
- 📱 **MFA Required** - When 2FA is needed for headless operation
- ⏳ **Rate Limited** - When API limits are hit

## 🛠️ Configuration

### 1. Environment Variables (`.env` file)

```bash
# Ntfy notifications
NTFY_SERVER=https://notify.jacqueswainwright.com  # Your ntfy server
NTFY_TOPIC=garmin-auth                           # Your topic name
NTFY_TOKEN=                                      # Optional auth token
```

### 2. Fallback System

If your primary server requires authentication or fails, notifications automatically fall back to:
- **Server**: `https://ntfy.sh` (public)
- **Topic**: `garmin-mcp-{username}` (unique per user)

## 📱 Subscription

### Option 1: Your Private Server
Subscribe to: `https://notify.jacqueswainwright.com/garmin-auth`

### Option 2: Fallback (Public)
Subscribe to: `https://ntfy.sh/garmin-mcp-jacques`

## 🧪 Testing

```bash
# Test basic notification
python ntfy_notifier.py --test

# Test all notification types  
python test_notifications.py

# Monitor authentication status
python monitor_auth.py
```

## 🔐 Authentication Setup

### For Your Private Server

1. **Generate Token**: Create an auth token in your ntfy server settings
2. **Add to .env**: Set `NTFY_TOKEN=your_token_here`
3. **Test**: Run `python ntfy_notifier.py --test`

### For Public Server (Fallback)

No authentication required - works automatically.

## 📊 Monitoring Integration

### Daily Monitoring (Cron)

```bash
# Add to crontab (crontab -e)
0 6 * * * cd /path/to/garmin_mcp && python monitor_auth.py >> auth_monitor.log 2>&1
```

This will:
- Check token health daily at 6 AM
- Send ntfy alerts if tokens are aging
- Log results for troubleshooting

### Manual Monitoring

```bash
# Check current status
python monitor_auth.py

# Setup cron job helper
python monitor_auth.py --setup-cron
```

## 🔔 Notification Types & Priorities

| Event | Priority | When Sent |
|-------|----------|-----------|
| Auth Success | Low | Tokens successfully refreshed |
| Auth Failure | High | Login/authentication fails |
| Rate Limited | Low | API rate limit hit (temporary) |
| MFA Required | High | 2FA needed for headless operation |
| Tokens Aging | High | Tokens 60-90 days old |
| Tokens Critical | Urgent | Tokens 90+ days old |

## 🚀 Production Deployment

### 1. Initial Setup
```bash
# First-time authentication
python authenticate.py

# Test notifications
python ntfy_notifier.py --test
```

### 2. Automated Monitoring
```bash
# Setup daily monitoring
python monitor_auth.py --setup-cron

# Verify cron job added
crontab -l
```

### 3. MCP Server Integration

The MCP server automatically sends notifications when:
- Authentication succeeds or fails
- Tokens expire and need renewal
- MFA is required for headless operation

## 📋 Troubleshooting

### No Notifications Received

1. **Check Subscription**: Ensure you're subscribed to the correct topic
2. **Test Connection**: Run `python ntfy_notifier.py --test`
3. **Check Logs**: Look for error messages in terminal output
4. **Verify Fallback**: Notifications should work via ntfy.sh even if primary server fails

### Authentication Issues

1. **Primary Server 401/403**: Check if `NTFY_TOKEN` is required
2. **Topic Forbidden**: Try a different topic name  
3. **Server Unavailable**: Fallback to ntfy.sh should work automatically

### Token Expiration Alerts

1. **Too Frequent**: Tokens are checked daily - multiple alerts indicate real expiration
2. **False Alarms**: Check `auth_log.json` for actual token age
3. **No Alerts**: Verify monitoring cron job is running

## 🔗 Useful Commands

```bash
# Test notification system
python ntfy_notifier.py --test

# Check authentication status  
python monitor_auth.py

# Authenticate manually (if tokens expired)
python authenticate.py

# Test all notification types
python test_notifications.py

# View authentication logs
cat auth_log.json | python -m json.tool
```

## ⚡ Quick Start

1. **Subscribe** to `https://ntfy.sh/garmin-mcp-jacques`
2. **Test**: `python ntfy_notifier.py --test`  
3. **Monitor**: `python monitor_auth.py`
4. **Setup Cron**: `python monitor_auth.py --setup-cron`

You should now receive notifications for all Garmin authentication events! 🎉