#!/usr/bin/env python3
"""
Minimal EAT Client Implementation
A complete EAT-compatible client in under 50 lines of Python.
"""

import requests
import json
from typing import Dict, List, Any, Optional


class EATClient:
    """Minimal EAT client for tool discovery and execution."""
    
    def __init__(self, catalog_url: str):
        """Initialize client with catalog URL."""
        self.catalog_url = catalog_url
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._discover()
    
    def _discover(self) -> None:
        """Fetch and parse the tool catalog."""
        try:
            response = requests.get(self.catalog_url, timeout=10)
            response.raise_for_status()
            catalog = response.json()
            
            # Validate catalog format
            if catalog.get('version') != '1.0':
                raise ValueError(f"Unsupported catalog version: {catalog.get('version')}")
            
            # Extract tool information
            for tool in catalog.get('tools', []):
                mcp_config = tool.get('x-mcp-tool', {})
                self.tools[tool['name']] = {
                    'description': tool.get('description', ''),
                    'server_url': mcp_config['server_url'],
                    'capabilities': mcp_config.get('capabilities', []),
                    'examples': mcp_config.get('examples', [])
                }
                
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to fetch catalog: {e}")
        except (KeyError, ValueError) as e:
            raise ValueError(f"Invalid catalog format: {e}")
    
    def list_tools(self) -> List[str]:
        """List all available tool names."""
        return list(self.tools.keys())
    
    def find_tools(self, capability: str) -> List[str]:
        """Find tools by capability."""
        return [
            name for name, info in self.tools.items()
            if capability in info['capabilities']
        ]
    
    def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """Get detailed information about a tool."""
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        return self.tools[tool_name].copy()
    
    def call_tool(self, tool_name: str, **arguments) -> Any:
        """Execute a tool via MCP protocol."""
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        server_url = self.tools[tool_name]['server_url']
        
        # Prepare MCP request
        request_data = {
            "jsonrpc": "2.0",
            "id": f"call-{hash(str(arguments))}",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        try:
            # Make MCP call
            response = requests.post(
                server_url,
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            # Handle MCP errors
            if 'error' in result:
                error = result['error']
                raise RuntimeError(f"MCP Error {error['code']}: {error['message']}")
            
            return result['result']['output']
            
        except requests.RequestException as e:
            raise ConnectionError(f"MCP call failed: {e}")
        except (KeyError, ValueError) as e:
            raise ValueError(f"Invalid MCP response: {e}")


def main():
    """Example usage of the EAT client."""
    # Initialize client (change URL for your catalog)
    client = EATClient("http://localhost:8080/catalog.json")
    
    print("🔍 EAT Client Demo")
    print("=" * 40)
    
    # List all tools
    tools = client.list_tools()
    print(f"📋 Found {len(tools)} tools:")
    for tool in tools:
        info = client.get_tool_info(tool)
        print(f"  • {tool}: {info['description']}")
    
    # Find tools by capability
    user_tools = client.find_tools("user-management")
    if user_tools:
        print(f"\n👥 User management tools: {', '.join(user_tools)}")
    
    greeting_tools = client.find_tools("greeting")
    if greeting_tools:
        print(f"👋 Greeting tools: {', '.join(greeting_tools)}")
    
    # Call a tool
    if tools:
        tool_name = tools[0]
        print(f"\n🚀 Calling tool: {tool_name}")
        
        try:
            # Try to use an example from the catalog
            info = client.get_tool_info(tool_name)
            if info['examples']:
                example = info['examples'][0]
                args = example.get('input', {})
                print(f"📝 Using example arguments: {args}")
                result = client.call_tool(tool_name, **args)
            else:
                # Default arguments for common tools
                if tool_name == "say_hello":
                    result = client.call_tool(tool_name, name="EAT Framework")
                elif tool_name == "get_user":
                    result = client.call_tool(tool_name, id=1)
                elif tool_name == "list_users":
                    result = client.call_tool(tool_name, limit=5)
                else:
                    result = client.call_tool(tool_name)
            
            print(f"✅ Result: {json.dumps(result, indent=2)}")
            
        except Exception as e:
            print(f"❌ Error calling tool: {e}")
    
    print("\n🎉 Demo completed!")


if __name__ == "__main__":
    main()