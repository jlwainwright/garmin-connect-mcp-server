"""
Modular MCP Server for Garmin Connect Data
"""

import asyncio
import os
import datetime
import requests
from pathlib import Path
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

from garth.exc import GarthHTTPError
from garminconnect import Garmin, GarminConnectAuthenticationError

# Import all modules
from modules import activity_management
from modules import health_wellness
from modules import user_profile
from modules import devices
from modules import gear_management
from modules import weight_management
from modules import challenges
from modules import training
from modules import workouts
from modules import data_management
from modules import womens_health

def get_mfa() -> str:
    """Get MFA code from environment variable or user input"""
    import sys
    
    # Try to get MFA from environment variable first
    mfa_code = os.environ.get("GARMIN_MFA_CODE")
    if mfa_code:
        sys.stderr.write(f"Using MFA code from environment variable.\n")
        sys.stderr.flush()
        return mfa_code
    
    # Fallback to interactive input
    sys.stderr.write("\nGarmin Connect MFA required. Please check your email/phone for the code.\n")
    sys.stderr.write("You can also set GARMIN_MFA_CODE environment variable to avoid this prompt.\n")
    sys.stderr.flush()
    return input("Enter MFA code: ")

# Get credentials from environment
email = os.environ.get("GARMIN_EMAIL")
password = os.environ.get("GARMIN_PASSWORD")
tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
tokenstore_base64 = os.getenv("GARMINTOKENS_BASE64") or "~/.garminconnect_base64"


def init_api(email, password):
    """Initialize Garmin API with your credentials."""
    import sys
    from headless_auth import HeadlessGarminAuth
    
    try:
        # Use headless authentication system
        auth = HeadlessGarminAuth()
        garmin = auth.authenticate()
        return garmin
    except Exception as err:
        sys.stderr.write(f"Authentication failed: {str(err)}\n")
        sys.stderr.flush()
        return None


def main():
    """Initialize the MCP server and register all tools"""
    import sys
    
    # Create the MCP app first so it can start even if auth fails
    app = FastMCP("Garmin Connect v1.0")
    
    # Try to initialize Garmin client
    garmin_client = init_api(email, password)
    
    if garmin_client:
        sys.stderr.write("Garmin Connect client initialized successfully.\n")
        sys.stderr.flush()
        
        # Configure all modules with the Garmin client
        activity_management.configure(garmin_client)
        health_wellness.configure(garmin_client)
        user_profile.configure(garmin_client)
        devices.configure(garmin_client)
        gear_management.configure(garmin_client)
        weight_management.configure(garmin_client)
        challenges.configure(garmin_client)
        training.configure(garmin_client)
        workouts.configure(garmin_client)
        data_management.configure(garmin_client)
        womens_health.configure(garmin_client)
        
        # Register tools from all modules
        app = activity_management.register_tools(app)
        app = health_wellness.register_tools(app)
        app = user_profile.register_tools(app)
        app = devices.register_tools(app)
        app = gear_management.register_tools(app)
        app = weight_management.register_tools(app)
        app = challenges.register_tools(app)
        app = training.register_tools(app)
        app = workouts.register_tools(app)
        app = data_management.register_tools(app)
        app = womens_health.register_tools(app)
        
        # Add activity listing tool directly to the app
        @app.tool()
        async def list_activities(limit: int = 5) -> str:
            """List recent Garmin activities"""
            try:
                activities = garmin_client.get_activities(0, limit)

                if not activities:
                    return "No activities found."

                result = f"Last {len(activities)} activities:\n\n"
                for idx, activity in enumerate(activities, 1):
                    result += f"--- Activity {idx} ---\n"
                    result += f"Activity: {activity.get('activityName', 'Unknown')}\n"
                    result += (
                        f"Type: {activity.get('activityType', {}).get('typeKey', 'Unknown')}\n"
                    )
                    result += f"Date: {activity.get('startTimeLocal', 'Unknown')}\n"
                    result += f"ID: {activity.get('activityId', 'Unknown')}\n\n"

                return result
            except Exception as e:
                return f"Error retrieving activities: {str(e)}"
    else:
        sys.stderr.write("Failed to initialize Garmin Connect client. Starting MCP server without authentication.\n")
        sys.stderr.flush()
        
        # Add a fallback tool when authentication fails
        @app.tool()
        async def garmin_status() -> str:
            """Check Garmin Connect authentication status"""
            return "Garmin Connect authentication failed. Please check your credentials and network connection."
    
    # Run the MCP server
    app.run()


if __name__ == "__main__":
    main()
