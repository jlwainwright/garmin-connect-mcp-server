#!/usr/bin/env python3
"""Test MCP server without authentication"""

from mcp.server.fastmcp import FastMCP

def main():
    # Create the MCP app
    app = FastMCP("Test Garmin Server")
    
    @app.tool()
    async def test_tool() -> str:
        """Test tool to verify MCP is working"""
        return "MCP server is working!"
    
    # Run the MCP server
    app.run()

if __name__ == "__main__":
    main()