#!/usr/bin/env python3
"""
Simple EAT agent demonstrating basic tool discovery and usage.
This is a minimal implementation showing the core EAT workflow.
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from eat import Catalog


async def main():
    """Simple agent that discovers and uses a customer management tool."""
    print("🚀 Starting Simple EAT Agent Demo")
    print("=" * 40)
    
    try:
        # Step 1: Discover tools
        print("🔍 Discovering tools from catalog...")
        catalog = Catalog("http://localhost:8000/.well-known/api-catalog", verify_signatures=False)
        await catalog.fetch()
        
        print(f"✅ Found {len(catalog.tools)} tools in catalog")
        
        # Step 2: Find customer management tools
        customer_tools = catalog.find(capability="customer")
        if not customer_tools:
            print("⚠️  No customer management tools found")
            print("💡 Available tools:")
            for tool in catalog.tools:
                print(f"   • {tool.id}: {tool.description}")
            return
        
        # Step 3: Use the first customer tool
        tool = customer_tools[0]
        print(f"🔧 Using tool: {tool.id}")
        print(f"📝 Description: {tool.description}")
        
        # Step 4: Call the tool (example: get customer by ID)
        print("📞 Calling tool with sample data...")
        
        try:
            result = await tool.call(customer_id=1)
            print("✅ Tool call successful!")
            print(f"📊 Result: {result}")
            
        except Exception as tool_error:
            print(f"⚠️  Tool call failed: {tool_error}")
            print("💡 This is expected if MCP servers are not running")
            print("   Run 'docker-compose up' in the demo directory to start servers")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure the demo server is running: cd demo && ./quickstart.sh")
        print("   2. Check that the catalog is available at: http://localhost:8000/.well-known/api-catalog")
        print("   3. Ensure OpenAPI specs are in the specs/ directory with x-mcp-tool extensions")


if __name__ == "__main__":
    asyncio.run(main())