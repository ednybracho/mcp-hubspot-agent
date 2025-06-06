#!/usr/bin/env python3
"""
Simple test script to verify MCP Client can connect to HubSpot Server
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the client directory to Python path
client_dir = Path(__file__).parent / "client"
sys.path.insert(0, str(client_dir))

from agent import HubSpotAgent

async def test_connection():
    """Test the connection between client and server"""
    
    server_path = str(Path(__file__).parent / "server" / "hubspot_server.py")
    
    agent = HubSpotAgent()
    
    try:
        print("Testing connection to HubSpot MCP Server...")
        await agent.connect_to_server(server_path)
        print("✅ Successfully connected to HubSpot server!")
        
        # Test if we can list tools
        if agent.session:
            response = await agent.session.list_tools()
            tools = [tool.name for tool in response.tools]
            print(f"✅ Available tools: {', '.join(tools)}")
        
        print("\\nConnection test completed successfully!")
        
    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")
        return False
    finally:
        await agent.cleanup()
    
    return True

async def main():
    """Main function"""
    print("HubSpot MCP Agent - Connection Test")
    print("=" * 40)
    
    success = await test_connection()
    
    if success:
        print("\\n🎉 Ready to run the agent! Use:")
        print("python client/agent.py server/hubspot_server.py")
    else:
        print("\\n❌ Please check your setup and try again.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())