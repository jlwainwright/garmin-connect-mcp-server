#!/usr/bin/env python3
"""
Test authentication using the working MCP server pattern
"""
import os
from dotenv import load_dotenv
from garminconnect import Garmin, GarminConnectAuthenticationError
from garth.exc import GarthHTTPError

def get_mfa():
    """Get MFA code - use the one provided"""
    return "452943"  # Use the latest code

def test_working_pattern():
    """Test using the same pattern as the working MCP server"""
    
    load_dotenv('.env')
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")
    tokenstore = "~/.garminconnect_test"
    
    print(f"Testing with working pattern...")
    print(f"Email: {email}")
    print(f"garminconnect version: 0.2.25")
    
    try:
        # First try existing tokens
        print("🔍 Trying existing tokens...")
        garmin = Garmin()
        garmin.login(tokenstore)
        print("✅ Success with existing tokens!")
        
        # Test getting user info
        user_name = garmin.get_full_name()
        print(f"✅ User: {user_name}")
        
        return True
        
    except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError) as e:
        print(f"No valid tokens: {e}")
        print("🔄 Performing fresh login...")
        
        try:
            garmin = Garmin(
                email=email,
                password=password,
                is_cn=False,
                prompt_mfa=get_mfa
            )
            
            print("Attempting login...")
            garmin.login()
            print("✅ Login successful!")
            
            # Save tokens for future use
            garmin.garth.dump(tokenstore)
            print(f"💾 Tokens saved to {tokenstore}")
            
            # Test getting user info
            user_name = garmin.get_full_name()
            print(f"✅ User: {user_name}")
            
            # Test getting some data
            activities = garmin.get_activities(0, 3)
            print(f"✅ Retrieved {len(activities)} activities")
            
            return True
            
        except Exception as e:
            import traceback
            print(f"❌ Authentication failed: {e}")
            print(f"Exception type: {type(e)}")
            traceback.print_exc()
            return False

if __name__ == "__main__":
    test_working_pattern()