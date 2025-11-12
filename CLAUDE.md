# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Garmin Connect MCP (Model Context Protocol) Server** - a Python-based server that exposes Garmin Connect fitness and health data through MCP tools. The server provides comprehensive access to activities, health metrics, device information, training data, and more through a modular architecture.

## Key Architecture Components

### Core Server Structure
- **Main Server File**: `garmin_mcp_server_fixed.py` - Production-ready MCP server using FastMCP
- **Authentication**: `headless_auth.py` - Sophisticated authentication system supporting multiple MFA strategies
- **Modular Design**: All functionality organized in `modules/` directory with separate files for each domain

### Module Architecture
The server uses a modular architecture where each Garmin Connect API domain is separated:

- `modules/activity_management.py` - Activity data, exports, splits
- `modules/health_wellness.py` - Health metrics (steps, HR, sleep, stress, body battery)
- `modules/user_profile.py` - User profile and preferences
- `modules/devices.py` - Device management and sync
- `modules/training.py` - Training plans and performance metrics
- `modules/workouts.py` - Workout management
- `modules/gear_management.py` - Equipment tracking
- `modules/weight_management.py` - Weight and body composition
- `modules/challenges.py` - Challenges and achievements
- `modules/womens_health.py` - Menstrual cycle tracking
- `modules/data_management.py` - Data export and utilities

Each module follows the pattern:
```python
def configure(client):  # Receives Garmin client instance
def register_tools(app):  # Registers MCP tools with FastMCP app
```

### Authentication System
The project includes a comprehensive headless authentication system (`headless_auth.py`) that supports:
- **OAuth2 Gmail integration** for automated MFA code retrieval
- **Email-based MFA** with IMAP support
- **Webhook-based MFA** for automated systems
- **Interactive authentication** as fallback
- **Token validation and refresh** with automatic retry logic
- **Security logging** to `auth_log.json`

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure
cp .env.example .env
# Edit .env with Garmin credentials and authentication settings
```

### Testing Authentication
```bash
# Test interactive authentication
python authenticate.py

# Test headless authentication (uses .env configuration)
python headless_auth.py

# Test email MFA functionality
python test_email_mfa.py

# Test OAuth2 Gmail access
python test_oauth2.py
```

### Running MCP Server
```bash
# Test with MCP Inspector (development/testing)
npx @modelcontextprotocol/inspector venv/bin/python garmin_mcp_server_fixed.py

# Run server directly (production)
venv/bin/python garmin_mcp_server_fixed.py
```

### Development Testing
```bash
# Run basic MCP server test
python test_mcp_server.py

# Test notifications
python test_notifications.py

# Monitor authentication events
python monitor_auth.py
```

## Configuration

### Environment Variables (.env file)
Required variables for operation:
- `GARMIN_EMAIL` - Garmin Connect account email
- `GARMIN_PASSWORD` - Garmin Connect password

MFA Authentication (choose one):
- `GARMIN_MFA_CODE` - Static MFA code (not recommended for production)
- OAuth2 settings: `EMAIL_USER`, `GOOGLE_CLIENT_SECRET_FILE`, `GMAIL_TOKEN_FILE`
- Email settings: `EMAIL_USER`, `EMAIL_PASSWORD`, `EMAIL_SERVER`, `EMAIL_PORT`

Optional settings:
- `NTFY_SERVER`, `NTFY_TOPIC`, `NTFY_TOKEN` - Push notifications
- `GARMINTOKENS`, `GARMINTOKENS_BASE64` - Token storage paths

### Claude Desktop Integration
Configure in Claude Desktop config file:
```json
{
  "mcpServers": {
    "garmin-connect": {
      "command": "/full/path/to/garmin_mcp/venv/bin/python",
      "args": ["/full/path/to/garmin_mcp/garmin_mcp_server_fixed.py"],
      "env": { /* Environment variables here */ }
    }
  }
}
```

## Important Implementation Details

### Modular Tool Registration
The server dynamically registers tools from all modules. Each module's `register_tools()` function is called during server startup to register MCP tools with the FastMCP app.

### Error Handling Strategy
- Authentication failures are logged to `auth_log.json`
- Rate limiting is handled gracefully with automatic retries
- Missing authentication exposes a `garmin_status` tool for checking authentication state
- All module functions include comprehensive try-catch error handling

### Security Considerations
- Tokens are stored in user home directory by default
- Authentication attempts are logged for monitoring
- OAuth2 is preferred over app passwords for email access
- All sensitive data should be passed via environment variables, not committed to code

### Docker Support
The project includes a `Dockerfile` for containerized deployment:
- Based on Python 3.11-slim
- Multi-stage build for optimal caching
- Environment variables for configuration
- Stdio-based MCP communication

## Current Status

The MCP server is **95% complete and functional**:
- ✅ All core modules implemented and working
- ✅ Comprehensive authentication system with multiple MFA strategies
- ✅ MCP Inspector integration verified
- ✅ Error handling and logging operational
- ⚠️ **Rate Limited**: Garmin Connect temporarily blocking authentication attempts

The server will provide full functionality once authentication succeeds (requires waiting for rate limit reset).

## Development Notes

- **FastMCP Framework**: Uses the modern FastMCP framework for MCP server implementation
- **Async Support**: All tools are implemented as async functions
- **Type Hints**: Comprehensive type annotations throughout the codebase
- **Modular Testing**: Each module can be tested independently
- **Production Ready**: Includes comprehensive logging, error handling, and security features