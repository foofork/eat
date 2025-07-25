"""
Tool discovery and catalog management for the EAT Framework.
"""

import asyncio
import hashlib
import json
from typing import Any, Dict, List, Optional, Union
import aiohttp
import logging
from urllib.parse import urljoin, urlparse

from .security import CatalogVerifier
from .mcp_client import MCPClient

logger = logging.getLogger(__name__)


class Tool:
    """Represents a discoverable tool from an EAT catalog."""
    
    def __init__(self, spec: Dict[str, Any], catalog: 'Catalog'):
        self.catalog = catalog
        self.spec = spec
        self.id = spec.get('name', spec.get('operationId', ''))
        self.description = spec.get('description', '')
        self.parameters = spec.get('parameters', {})
        self.examples = spec.get('x-mcp-tool', {}).get('examples', [])
        self.server_url = spec.get('x-mcp-tool', {}).get('server_url', '')
        self.capabilities = spec.get('x-mcp-tool', {}).get('capabilities', [])
        
    async def call(self, **params) -> Dict[str, Any]:
        """Call this tool via MCP protocol."""
        if not self.server_url:
            raise ValueError(f"No server URL configured for tool {self.id}")
            
        client = MCPClient(self.server_url)
        return await client.call_tool(self, params)
    
    def __repr__(self):
        return f"Tool(id='{self.id}', description='{self.description[:50]}...')"


class Catalog:
    """EAT catalog for tool discovery and management."""
    
    def __init__(self, url: str, verify_signatures: bool = True):
        self.url = url
        self.verify_signatures = verify_signatures
        self._catalog_data: Optional[Dict[str, Any]] = None
        self._tools: Optional[List[Tool]] = None
        self._verifier = CatalogVerifier() if verify_signatures else None
        
    async def fetch(self) -> Dict[str, Any]:
        """Fetch and cache catalog from the configured URL."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url) as response:
                    response.raise_for_status()
                    content = await response.text()
                    
            # Parse catalog data
            if self.url.endswith('.json'):
                self._catalog_data = json.loads(content)
            else:
                # Assume JWS format for non-JSON URLs
                if self._verifier:
                    self._catalog_data = await self._verifier.verify_catalog(content, self.url)
                else:
                    # Try to parse as raw JSON if verification disabled
                    self._catalog_data = json.loads(content)
                    
            logger.info(f"Fetched catalog with {len(self._catalog_data.get('tools', []))} tools")
            return self._catalog_data
            
        except Exception as e:
            logger.error(f"Failed to fetch catalog from {self.url}: {e}")
            raise
    
    async def verify(self) -> bool:
        """Verify catalog signature and content integrity."""
        if not self.verify_signatures or not self._verifier:
            logger.warning("Signature verification disabled")
            return True
            
        if not self._catalog_data:
            await self.fetch()
            
        try:
            # Verify content hashes for referenced specs
            for tool_spec in self._catalog_data.get('tools', []):
                spec_url = tool_spec.get('spec_url')
                expected_hash = tool_spec.get('spec_hash')
                
                if spec_url and expected_hash:
                    if not await self._verify_content_integrity(spec_url, expected_hash):
                        logger.error(f"Content integrity check failed for {spec_url}")
                        return False
                        
            logger.info("Catalog verification successful")
            return True
            
        except Exception as e:
            logger.error(f"Catalog verification failed: {e}")
            return False
    
    async def _verify_content_integrity(self, url: str, expected_hash: str) -> bool:
        """Verify downloaded content matches expected SHA-256 hash."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    content = await response.read()
                    
            actual_hash = hashlib.sha256(content).hexdigest()
            return actual_hash == expected_hash
            
        except Exception as e:
            logger.error(f"Failed to verify content integrity for {url}: {e}")
            return False
    
    def find(self, capability: Optional[str] = None, **filters) -> List[Tool]:
        """Find tools by capability and other criteria."""
        if not self._catalog_data:
            raise RuntimeError("Catalog not fetched. Call fetch() first.")
            
        if not self._tools:
            self._tools = [Tool(spec, self) for spec in self._catalog_data.get('tools', [])]
            
        results = self._tools
        
        # Filter by capability
        if capability:
            results = [tool for tool in results if capability in tool.capabilities]
            
        # Apply additional filters
        for key, value in filters.items():
            if key == 'description_contains':
                results = [tool for tool in results if value.lower() in tool.description.lower()]
            elif key == 'has_examples':
                results = [tool for tool in results if bool(tool.examples) == value]
                
        return results
    
    def get_tool(self, tool_id: str) -> Optional[Tool]:
        """Get specific tool by ID."""
        tools = self.find()
        for tool in tools:
            if tool.id == tool_id:
                return tool
        return None
    
    @property
    def tools(self) -> List[Tool]:
        """Get all available tools."""
        return self.find()
    
    def __repr__(self):
        tool_count = len(self._tools) if self._tools else "unknown"
        return f"Catalog(url='{self.url}', tools={tool_count})"