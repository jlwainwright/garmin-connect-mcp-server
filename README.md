[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/taxuspt-garmin-mcp-badge.png)](https://mseep.ai/app/taxuspt-garmin-mcp)

# Garmin Connect MCP Server

A comprehensive Model Context Protocol (MCP) server that connects to Garmin Connect and exposes your fitness and health data to Claude and other MCP-compatible clients. This server provides access to activities, health metrics, devices, training data, and much more.

## 🚀 Features

### Core Data Access
- **Activities**: List recent activities, get detailed activity information, export data
- **Health Metrics**: Steps, heart rate, sleep data, stress levels, body battery
- **Body Composition**: Weight, BMI, body fat percentage, muscle mass
- **User Profile**: Personal information, preferences, device settings

### Advanced Features
- **Device Management**: List connected devices, sync status, device details
- **Training Data**: Training plans, workouts, performance metrics
- **Gear Management**: Track equipment usage and maintenance
- **Challenges**: View active challenges and achievements
- **Women's Health**: Menstrual cycle tracking and health insights

### Authentication & Security
- **Headless 2FA Support**: Multiple authentication strategies for automated deployments
- **Token Management**: Automatic token refresh and validation
- **Notification System**: Real-time alerts via ntfy for authentication events
- **Rate Limiting**: Built-in protection against API rate limits
- **Security Logging**: Comprehensive authentication attempt logging

## 📋 Requirements

- Python 3.7+
- Garmin Connect account
- Valid email/phone for 2FA verification

## 🛠️ Installation

1. **Clone and setup virtual environment:**

```bash
git clone <repository-url>
cd garmin_mcp
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment variables:**

Create a `.env` file in the project root:

```env
# Garmin Connect Credentials (Required)
GARMIN_EMAIL=your.email@example.com
GARMIN_PASSWORD=your-password

# 2FA Authentication (Choose one method)
GARMIN_MFA_CODE=123456                    # Manual MFA code entry
# GARMIN_MFA_WEBHOOK=https://api.com/mfa   # Webhook for automated MFA
# Or use temporary file: echo "123456" > /tmp/garmin_mfa.txt

# Email-based MFA (Automatic - Recommended)
EMAIL_USER=your.email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_SERVER=imap.gmail.com
EMAIL_PORT=993

# Notification Settings (Optional)
NTFY_SERVER=https://ntfy.sh
NTFY_TOPIC=garmin-notifications
NTFY_TOKEN=your-ntfy-token

# Token Storage (Optional)
GARMINTOKENS=~/.garminconnect
GARMINTOKENS_BASE64=~/.garminconnect_base64
```

## 🔐 Authentication Setup

The server supports multiple authentication strategies for different deployment scenarios:

### Method 1: Interactive Authentication (Recommended for first-time setup)

```bash
# Activate virtual environment
source venv/bin/activate

# Run interactive authentication
python authenticate.py
```

This will:
- Prompt for 2FA code when needed
- Save tokens for future headless operation
- Verify authentication works properly

### Method 2: Headless Authentication

For automated deployments, use one of these methods:

#### Email-based MFA Setup

**Option A: OAuth2 (Recommended - Most Secure)**
1. **Setup Google Cloud Project:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Gmail API: APIs & Services > Library > Gmail API > Enable

2. **Create OAuth2 Credentials:**
   - Go to APIs & Services > Credentials
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Desktop application" as application type
   - Download the `client_secret.json` file

3. **Configure Environment:**
   ```bash
   export EMAIL_USER="your.email@gmail.com"
   export GOOGLE_CLIENT_SECRET_FILE="/path/to/client_secret.json"
   export GMAIL_TOKEN_FILE="~/.gmail_token.json"
   ```

4. **First Run Authorization:**
   - The first time you run the server, OAuth2 will open a browser for authorization
   - Grant permission to access your Gmail
   - Tokens will be saved for future use

**Option B: App Password (Alternative)**
1. Enable 2FA on your Google account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Configure environment:
   ```bash
   export EMAIL_USER="your.email@gmail.com"
   export EMAIL_PASSWORD="16_character_app_password"
   export EMAIL_SERVER="imap.gmail.com"
   export EMAIL_PORT="993"
   ```

**Test Email Setup:**
```bash
python test_email_mfa.py
```

**Test OAuth2 Setup:**
```bash
python test_oauth2.py
```

#### Other MFA Methods

**Email-based with OAuth2 (Most Secure - Recommended):**
```bash
export EMAIL_USER="your.email@gmail.com"
export GOOGLE_CLIENT_SECRET_FILE="/path/to/client_secret.json"
export GMAIL_TOKEN_FILE="~/.gmail_token.json"
```

**Email-based with App Password:**
```bash
export EMAIL_USER="your.email@gmail.com"
export EMAIL_PASSWORD="your_app_password"  # Use App Password for Gmail
export EMAIL_SERVER="imap.gmail.com"
export EMAIL_PORT="993"
```

**Environment Variable:**
```bash
export GARMIN_MFA_CODE="123456"
```

**Temporary File:**
```bash
echo "123456" > /tmp/garmin_mfa.txt
```

**Webhook API:**
```bash
export GARMIN_MFA_WEBHOOK="https://your-api.com/mfa"
```

## 🖥️ Running the Server

### With Claude Desktop (Recommended)

1. **Configure Claude Desktop:**

Edit your Claude Desktop configuration file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add this server configuration:

```json
{
  "mcpServers": {
    "garmin-connect": {
      "command": "/full/path/to/garmin_mcp/venv/bin/python",
      "args": [
        "/full/path/to/garmin_mcp/garmin_mcp_server_fixed.py"
      ],
      "env": {
        "GARMIN_EMAIL": "your.email@example.com",
        "GARMIN_PASSWORD": "your-password",
        "EMAIL_USER": "your.email@gmail.com",
        "GOOGLE_CLIENT_SECRET_FILE": "/path/to/client_secret.json",
        "GMAIL_TOKEN_FILE": "~/.gmail_token.json",
        "NTFY_SERVER": "https://ntfy.sh",
        "NTFY_TOPIC": "garmin-notifications",
        "NTFY_TOKEN": "your-token"
      }
    }
  }
}
```

2. **Restart Claude Desktop**

The server will automatically authenticate and be available for use.

### With MCP Inspector (For Testing)

```bash
# Test the server
npx @modelcontextprotocol/inspector venv/bin/python garmin_mcp_server_fixed.py
```

Open the provided URL to test tools interactively.

## 📊 Available Tools

### Activity Management
- `list_activities(limit)` - List recent activities
- `get_activity_details(activity_id)` - Get detailed activity information
- `get_activity_splits(activity_id)` - Get activity lap/split data
- `export_activity(activity_id, format)` - Export activity data

### Health & Wellness
- `get_user_profile()` - Get user profile information
- `get_steps(date)` - Get daily step count
- `get_heart_rate(date)` - Get heart rate data
- `get_sleep_data(date)` - Get sleep information
- `get_stress_data(date)` - Get stress levels
- `get_body_battery(date)` - Get body battery data

### Device Management
- `list_devices()` - List connected devices
- `get_device_info(device_id)` - Get device details
- `sync_device(device_id)` - Trigger device sync

### Training & Workouts
- `list_workouts()` - List saved workouts
- `get_training_plan()` - Get current training plan
- `get_performance_stats()` - Get performance metrics

### Body Composition
- `get_weight_data(date)` - Get weight measurements
- `get_body_composition(date)` - Get body composition data

## 💬 Usage Examples

Once connected in Claude, you can ask questions like:

**Activities:**
- "Show me my recent activities"
- "What was my latest run like?"
- "Export my last cycling activity as GPX"

**Health Data:**
- "How many steps did I take yesterday?"
- "What was my sleep like last night?"
- "Show me my heart rate trends this week"

**Training:**
- "What workouts do I have planned?"
- "How is my fitness progress?"
- "Show me my training load"

**Devices:**
- "What devices do I have connected?"
- "When was my watch last synced?"

## 🔧 Advanced Features

### Headless Authentication System

The server includes a sophisticated headless authentication system (`headless_auth.py`) that:

- **Auto-validates existing tokens** before attempting fresh authentication
- **Supports multiple MFA strategies** for different deployment scenarios
- **Provides clear instructions** when manual intervention is needed
- **Logs all authentication attempts** for monitoring and debugging
- **Handles rate limiting** gracefully with automatic retry logic

### Notification System

Integrated ntfy notifications keep you informed about:

- Authentication success/failure
- Rate limiting events  
- MFA requirements
- Server status changes

### Monitoring & Logging

- **Authentication logs** stored in `auth_log.json`
- **Performance tracking** for optimization
- **Error handling** with detailed logging
- **Rate limit monitoring** and alerting

## 🛡️ Security Considerations

- **Never commit** your `.env` file to version control
- **Use environment variables** for production deployments  
- **Rotate MFA codes** regularly when using static codes
- **Monitor authentication logs** for suspicious activity
- **Use webhook authentication** for enhanced security in automated systems

## 🐛 Troubleshooting

### Authentication Issues

**Problem**: "Authentication failed: No MFA code available"
**Solution**: 
1. Check your email/phone for Garmin 2FA code
2. Set `GARMIN_MFA_CODE` in `.env` file
3. Or use interactive authentication: `python authenticate.py`

**Problem**: "Rate limited (429 error)"
**Solution**: 
1. Wait 5-10 minutes before retrying
2. Server will automatically retry after rate limit expires
3. Monitor `auth_log.json` for retry status

**Problem**: "Token validation failed"
**Solution**:
1. Delete existing token files: `rm ~/.garminconnect*`
2. Run fresh authentication: `python authenticate.py`
3. Restart the MCP server

### Connection Issues

**Problem**: "spawn venv/bin/python ENOENT"
**Solution**: Use absolute paths in Claude Desktop configuration

**Problem**: "Server disconnected"
**Solution**: 
1. Check Claude Desktop logs
2. Verify Python virtual environment is activated
3. Test server manually with MCP Inspector

### Debugging Steps

1. **Test authentication manually:**
   ```bash
   source venv/bin/activate
   python headless_auth.py
   ```

2. **Test email MFA functionality:**
   ```bash
   source venv/bin/activate
   python test_email_mfa.py
   ```

3. **Test OAuth2 Gmail access:**
   ```bash
   source venv/bin/activate
   python test_oauth2.py
   ```

3. **Check server startup:**
   ```bash
   npx @modelcontextprotocol/inspector venv/bin/python garmin_mcp_server_fixed.py
   ```

4. **Review logs:**
   - Authentication: `auth_log.json`
   - Claude Desktop: `~/Library/Logs/Claude/`
   - Server output: Check terminal/console output

## 📝 Logging

The server maintains detailed logs:

- **Authentication attempts** with timestamps and outcomes
- **API call performance** metrics
- **Error conditions** with stack traces
- **Rate limiting** events and recovery

Check `auth_log.json` for authentication history and troubleshooting information.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all authentication methods work
5. Update documentation
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built on [garminconnect](https://github.com/cyberjunky/python-garminconnect) library
- Uses [FastMCP](https://github.com/jlowin/fastmcp) for MCP server implementation
- Notification system powered by [ntfy](https://ntfy.sh)

---

**Note**: This server requires a valid Garmin Connect account and handles sensitive authentication data. Always follow security best practices when deploying.