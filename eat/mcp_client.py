"""
MCP (Model Context Protocol) client implementation for tool execution.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
import aiohttp
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for communicating with MCP servers."""
    
    def __init__(self, endpoint: str, timeout: int = 30):
        self.endpoint = endpoint.rstrip('/')
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
            
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if not self._session:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self._session
    
    async def call_tool(self, tool: 'Tool', params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool call via MCP protocol."""
        session = await self._get_session()
        
        # Prepare MCP request
        request_data = {
            "jsonrpc": "2.0",
            "id": f"tool_{tool.id}_{id(params)}",
            "method": "tools/call",
            "params": {
                "name": tool.id,
                "arguments": params
            }
        }
        
        try:
            url = urljoin(self.endpoint, "/mcp")
            async with session.post(url, json=request_data) as response:
                response.raise_for_status()
                result = await response.json()
                
            # Handle MCP response format
            if "error" in result:
                error = result["error"]
                raise MCPError(f"MCP Error {error.get('code', 'unknown')}: {error.get('message', 'Unknown error')}")
                
            return result.get("result", {})
            
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error calling tool {tool.id}: {e}")
            raise MCPError(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error calling tool {tool.id}: {e}")
            raise MCPError(f"Unexpected error: {e}")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from MCP server."""
        session = await self._get_session()
        
        request_data = {
            "jsonrpc": "2.0",
            "id": "list_tools",
            "method": "tools/list",
            "params": {}
        }
        
        try:
            url = urljoin(self.endpoint, "/mcp")
            async with session.post(url, json=request_data) as response:
                response.raise_for_status()
                result = await response.json()
                
            if "error" in result:
                error = result["error"]
                raise MCPError(f"MCP Error {error.get('code', 'unknown')}: {error.get('message', 'Unknown error')}")
                
            return result.get("result", {}).get("tools", [])
            
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error listing tools: {e}")
            raise MCPError(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error listing tools: {e}")
            raise MCPError(f"Unexpected error: {e}")
    
    async def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """Get schema for a specific tool."""
        session = await self._get_session()
        
        request_data = {
            "jsonrpc": "2.0",
            "id": f"schema_{tool_name}",
            "method": "tools/get",
            "params": {
                "name": tool_name
            }
        }
        
        try:
            url = urljoin(self.endpoint, "/mcp")
            async with session.post(url, json=request_data) as response:
                response.raise_for_status()
                result = await response.json()
                
            if "error" in result:
                error = result["error"]
                raise MCPError(f"MCP Error {error.get('code', 'unknown')}: {error.get('message', 'Unknown error')}")
                
            return result.get("result", {})
            
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error getting tool schema for {tool_name}: {e}")
            raise MCPError(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting tool schema for {tool_name}: {e}")
            raise MCPError(f"Unexpected error: {e}")
    
    async def close(self):
        """Close the HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None


class MCPError(Exception):
    """Exception raised for MCP protocol errors."""
    pass