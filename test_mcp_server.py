#!/usr/bin/env python3
"""
Simple test MCP server for debugging
"""

import asyncio
import json
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server

server = Server("test-server")

@server.list_tools()
async def list_tools() -> list:
    return [
        {
            "name": "test-tool",
            "description": "A simple test tool",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Test message"
                    }
                }
            }
        }
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list:
    if name == "test-tool":
        return [{
            "content": [
                {
                    "type": "text",
                    "text": f"Test successful! Message: {arguments.get('message', 'default')}"
                }
            ]
        }]
    raise ValueError(f"Unknown tool: {name}")

async def main():
    print("Test MCP server starting...", file=sys.stderr)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)

if __name__ == "__main__":
    asyncio.run(main())
