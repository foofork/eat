"""
Tests for EAT Framework MCP client functionality.
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock

from eat.mcp_client import MCPClient, MCPError


class TestMCPClient:
    """Test cases for MCPClient class."""
    
    @pytest.fixture
    def client(self):
        """Create test MCP client."""
        return MCPClient("http://localhost:3001", timeout=10)
    
    @pytest.fixture
    def mock_tool(self):
        """Mock tool for testing."""
        tool = MagicMock()
        tool.id = "test_tool"
        return tool
    
    @pytest.mark.asyncio
    async def test_call_tool_success(self, client, mock_tool):
        """Test successful tool call."""
        expected_result = {"output": "test result", "status": "success"}
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock HTTP response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.json = AsyncMock(return_value={
                "jsonrpc": "2.0",
                "id": "test_id",
                "result": expected_result
            })
            
            mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Test tool call
            result = await client.call_tool(mock_tool, {"input": "test"})
            
            assert result == expected_result
            
            # Verify the request was made correctly
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            
            # Check URL
            assert call_args[1]['url'] == "http://localhost:3001/mcp"
            
            # Check request body
            request_data = call_args[1]['json']
            assert request_data['jsonrpc'] == "2.0"
            assert request_data['method'] == "tools/call"
            assert request_data['params']['name'] == "test_tool"
            assert request_data['params']['arguments'] == {"input": "test"}
    
    @pytest.mark.asyncio
    async def test_call_tool_with_mcp_error(self, client, mock_tool):
        """Test tool call that returns MCP error."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock HTTP response with MCP error
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.json = AsyncMock(return_value={
                "jsonrpc": "2.0",
                "id": "test_id",
                "error": {
                    "code": -32603,
                    "message": "Tool execution failed"
                }
            })
            
            mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Test that MCPError is raised
            with pytest.raises(MCPError, match="MCP Error -32603: Tool execution failed"):
                await client.call_tool(mock_tool, {"input": "test"})
    
    @pytest.mark.asyncio
    async def test_call_tool_with_http_error(self, client, mock_tool):
        """Test tool call with HTTP error."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock HTTP error
            from aiohttp import ClientError
            mock_post.side_effect = ClientError("Connection failed")
            
            with pytest.raises(MCPError, match="Network error: Connection failed"):
                await client.call_tool(mock_tool, {"input": "test"})
    
    @pytest.mark.asyncio
    async def test_list_tools_success(self, client):
        """Test successful tools listing."""
        expected_tools = [
            {
                "name": "tool1",
                "description": "First tool",
                "inputSchema": {"type": "object"}
            },
            {
                "name": "tool2",
                "description": "Second tool",
                "inputSchema": {"type": "object"}
            }
        ]
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock HTTP response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.json = AsyncMock(return_value={
                "jsonrpc": "2.0",
                "id": "list_tools",
                "result": {"tools": expected_tools}
            })
            
            mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Test list tools
            result = await client.list_tools()
            
            assert result == expected_tools
            
            # Verify the request
            call_args = mock_post.call_args
            request_data = call_args[1]['json']
            assert request_data['method'] == "tools/list"
            assert request_data['params'] == {}
    
    @pytest.mark.asyncio
    async def test_get_tool_schema_success(self, client):
        """Test successful tool schema retrieval."""
        expected_schema = {
            "name": "test_tool",
            "description": "Test tool",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "input": {"type": "string"}
                },
                "required": ["input"]
            }
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Mock HTTP response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.json = AsyncMock(return_value={
                "jsonrpc": "2.0",
                "id": "schema_test_tool",
                "result": expected_schema
            })
            
            mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Test get tool schema
            result = await client.get_tool_schema("test_tool")
            
            assert result == expected_schema
            
            # Verify the request
            call_args = mock_post.call_args
            request_data = call_args[1]['json']
            assert request_data['method'] == "tools/get"
            assert request_data['params']['name'] == "test_tool"
    
    @pytest.mark.asyncio
    async def test_client_session_management(self):
        """Test client session creation and cleanup."""
        client = MCPClient("http://localhost:3001")
        
        # Test that session is created when needed
        assert client._session is None
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            session = await client._get_session()
            assert session == mock_session
            assert client._session == mock_session
            
            # Test that same session is returned on subsequent calls
            session2 = await client._get_session()
            assert session2 == mock_session
            
            # Test session cleanup
            await client.close()
            mock_session.close.assert_called_once()
            assert client._session is None
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using MCPClient as context manager."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            async with MCPClient("http://localhost:3001") as client:
                assert isinstance(client, MCPClient)
                # Session should be created
                session = await client._get_session()
                assert session == mock_session
            
            # Session should be closed after context exit
            mock_session.close.assert_called_once()
    
    def test_client_initialization(self):
        """Test client initialization with different parameters."""
        # Default timeout
        client1 = MCPClient("http://localhost:3001")
        assert client1.endpoint == "http://localhost:3001"
        assert client1.timeout == 30
        
        # Custom timeout
        client2 = MCPClient("http://localhost:3002", timeout=60)
        assert client2.endpoint == "http://localhost:3002"
        assert client2.timeout == 60
        
        # URL normalization (trailing slash removal)
        client3 = MCPClient("http://localhost:3003/")
        assert client3.endpoint == "http://localhost:3003"


class TestMCPError:
    """Test cases for MCPError exception."""
    
    def test_mcp_error_creation(self):
        """Test MCPError exception creation."""
        error = MCPError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    def test_mcp_error_inheritance(self):
        """Test that MCPError inherits from Exception."""
        error = MCPError("Test error")
        assert isinstance(error, Exception)


class TestMCPClientIntegration:
    """Integration tests for MCP client."""
    
    @pytest.mark.asyncio
    async def test_full_mcp_workflow(self):
        """Test complete MCP workflow: list tools, get schema, call tool."""
        client = MCPClient("http://localhost:3001")
        
        # Mock tool for call
        mock_tool = MagicMock()
        mock_tool.id = "integration_tool"
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Set up responses for different calls
            responses = [
                # list_tools response
                {
                    "jsonrpc": "2.0",
                    "id": "list_tools",
                    "result": {
                        "tools": [
                            {
                                "name": "integration_tool",
                                "description": "Integration test tool"
                            }
                        ]
                    }
                },
                # get_tool_schema response
                {
                    "jsonrpc": "2.0",
                    "id": "schema_integration_tool",
                    "result": {
                        "name": "integration_tool",
                        "inputSchema": {"type": "object"}
                    }
                },
                # call_tool response
                {
                    "jsonrpc": "2.0",
                    "id": "call_integration_tool",
                    "result": {"output": "integration success"}
                }
            ]
            
            # Mock HTTP responses
            mock_responses = []
            for response_data in responses:
                mock_response = AsyncMock()
                mock_response.status_code = 200
                mock_response.raise_for_status = MagicMock()
                mock_response.json = AsyncMock(return_value=response_data)
                mock_responses.append(mock_response)
            
            # Set up context managers for responses
            for i, mock_response in enumerate(mock_responses):
                mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
                mock_post.return_value.__aexit__ = AsyncMock(return_value=None)
                
                if i == 0:
                    # Test list tools
                    tools = await client.list_tools()
                    assert len(tools) == 1
                    assert tools[0]["name"] == "integration_tool"
                
                elif i == 1:
                    # Test get tool schema
                    schema = await client.get_tool_schema("integration_tool")
                    assert schema["name"] == "integration_tool"
                
                elif i == 2:
                    # Test call tool
                    result = await client.call_tool(mock_tool, {"param": "value"})
                    assert result == {"output": "integration success"}
        
        await client.close()


if __name__ == "__main__":
    pytest.main([__file__])