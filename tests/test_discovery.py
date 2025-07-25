"""
Tests for EAT Framework discovery functionality.
"""

import pytest
import json
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from eat.discovery import Catalog, Tool
from eat.security import SecurityError


class TestCatalog:
    """Test cases for Catalog class."""
    
    @pytest.fixture
    def sample_catalog_data(self):
        """Sample catalog data for testing."""
        return {
            "version": "1.0",
            "metadata": {
                "title": "Test Catalog",
                "description": "Test catalog for unit tests"
            },
            "tools": [
                {
                    "name": "test_tool",
                    "description": "A test tool",
                    "version": "1.0.0",
                    "x-mcp-tool": {
                        "server_url": "http://localhost:3001",
                        "capabilities": ["testing"],
                        "examples": [{"input": {"test": "value"}}]
                    }
                },
                {
                    "name": "another_tool",
                    "description": "Another test tool",
                    "version": "1.0.0",
                    "x-mcp-tool": {
                        "server_url": "http://localhost:3002",
                        "capabilities": ["other"],
                        "examples": []
                    }
                }
            ]
        }
    
    @pytest.fixture
    def catalog(self):
        """Create a test catalog instance."""
        return Catalog("http://test.example.com/.well-known/api-catalog", verify_signatures=False)
    
    @pytest.mark.asyncio
    async def test_fetch_json_catalog(self, catalog, sample_catalog_data):
        """Test fetching a JSON catalog."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock the HTTP response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.text = AsyncMock(return_value=json.dumps(sample_catalog_data))
            
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Test fetch
            result = await catalog.fetch()
            
            assert result == sample_catalog_data
            assert catalog._catalog_data == sample_catalog_data
    
    @pytest.mark.asyncio
    async def test_fetch_with_network_error(self, catalog):
        """Test handling of network errors during fetch."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            with pytest.raises(Exception, match="Network error"):
                await catalog.fetch()
    
    @pytest.mark.asyncio
    async def test_verify_without_signature_checking(self, catalog, sample_catalog_data):
        """Test verification when signature checking is disabled."""
        catalog._catalog_data = sample_catalog_data
        
        result = await catalog.verify()
        assert result is True
    
    def test_find_tools_by_capability(self, catalog, sample_catalog_data):
        """Test finding tools by capability."""
        catalog._catalog_data = sample_catalog_data
        
        # Find tools with 'testing' capability
        testing_tools = catalog.find(capability="testing")
        assert len(testing_tools) == 1
        assert testing_tools[0].id == "test_tool"
        
        # Find tools with 'other' capability
        other_tools = catalog.find(capability="other")
        assert len(other_tools) == 1
        assert other_tools[0].id == "another_tool"
        
        # Find tools with non-existent capability
        missing_tools = catalog.find(capability="nonexistent")
        assert len(missing_tools) == 0
    
    def test_find_tools_with_filters(self, catalog, sample_catalog_data):
        """Test finding tools with additional filters."""
        catalog._catalog_data = sample_catalog_data
        
        # Find tools with description containing 'test'
        filtered_tools = catalog.find(description_contains="test")
        assert len(filtered_tools) == 2  # Both tools have 'test' in description
        
        # Find tools with examples
        tools_with_examples = catalog.find(has_examples=True)
        assert len(tools_with_examples) == 1
        assert tools_with_examples[0].id == "test_tool"
        
        # Find tools without examples
        tools_without_examples = catalog.find(has_examples=False)
        assert len(tools_without_examples) == 1
        assert tools_without_examples[0].id == "another_tool"
    
    def test_get_tool_by_id(self, catalog, sample_catalog_data):
        """Test getting a specific tool by ID."""
        catalog._catalog_data = sample_catalog_data
        
        # Get existing tool
        tool = catalog.get_tool("test_tool")
        assert tool is not None
        assert tool.id == "test_tool"
        assert tool.description == "A test tool"
        
        # Get non-existent tool
        missing_tool = catalog.get_tool("nonexistent")
        assert missing_tool is None
    
    def test_tools_property(self, catalog, sample_catalog_data):
        """Test the tools property."""
        catalog._catalog_data = sample_catalog_data
        
        tools = catalog.tools
        assert len(tools) == 2
        assert all(isinstance(tool, Tool) for tool in tools)
    
    def test_find_without_fetched_catalog(self, catalog):
        """Test that find raises error when catalog not fetched."""
        with pytest.raises(RuntimeError, match="Catalog not fetched"):
            catalog.find()


class TestTool:
    """Test cases for Tool class."""
    
    @pytest.fixture
    def tool_spec(self):
        """Sample tool specification."""
        return {
            "name": "test_tool",
            "description": "A test tool for unit testing",
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "Test input"}
                },
                "required": ["input"]
            },
            "x-mcp-tool": {
                "server_url": "http://localhost:3001",
                "capabilities": ["testing", "demo"],
                "examples": [
                    {"input": "test value", "output": "processed"},
                    {"input": "another test", "output": "result"}
                ]
            }
        }
    
    @pytest.fixture
    def catalog_mock(self):
        """Mock catalog for tool testing."""
        return MagicMock()
    
    def test_tool_initialization(self, tool_spec, catalog_mock):
        """Test tool initialization from specification."""
        tool = Tool(tool_spec, catalog_mock)
        
        assert tool.id == "test_tool"
        assert tool.description == "A test tool for unit testing"
        assert tool.parameters == tool_spec["parameters"]
        assert tool.server_url == "http://localhost:3001"
        assert tool.capabilities == ["testing", "demo"]
        assert len(tool.examples) == 2
        assert tool.catalog == catalog_mock
    
    def test_tool_with_missing_fields(self, catalog_mock):
        """Test tool initialization with missing optional fields."""
        minimal_spec = {"name": "minimal_tool"}
        tool = Tool(minimal_spec, catalog_mock)
        
        assert tool.id == "minimal_tool"
        assert tool.description == ""
        assert tool.parameters == {}
        assert tool.server_url == ""
        assert tool.capabilities == []
        assert tool.examples == []
    
    def test_tool_with_operation_id(self, catalog_mock):
        """Test tool initialization using operationId when name is missing."""
        spec = {"operationId": "get_user", "description": "Get user by ID"}
        tool = Tool(spec, catalog_mock)
        
        assert tool.id == "get_user"
        assert tool.description == "Get user by ID"
    
    @pytest.mark.asyncio
    async def test_tool_call_success(self, tool_spec, catalog_mock):
        """Test successful tool call."""
        tool = Tool(tool_spec, catalog_mock)
        
        # Mock MCPClient
        with patch('eat.discovery.MCPClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.call_tool.return_value = {"result": "success"}
            mock_client_class.return_value = mock_client
            
            result = await tool.call(input="test")
            
            assert result == {"result": "success"}
            mock_client_class.assert_called_once_with("http://localhost:3001")
            mock_client.call_tool.assert_called_once_with(tool, {"input": "test"})
    
    @pytest.mark.asyncio
    async def test_tool_call_without_server_url(self, catalog_mock):
        """Test tool call when server URL is missing."""
        spec = {"name": "no_server_tool"}
        tool = Tool(spec, catalog_mock)
        
        with pytest.raises(ValueError, match="No server URL configured"):
            await tool.call(param="value")
    
    def test_tool_repr(self, tool_spec, catalog_mock):
        """Test tool string representation."""
        tool = Tool(tool_spec, catalog_mock)
        repr_str = repr(tool)
        
        assert "Tool(id='test_tool'" in repr_str
        assert "A test tool for unit testing" in repr_str


class TestCatalogIntegration:
    """Integration tests for catalog functionality."""
    
    @pytest.mark.asyncio
    async def test_full_catalog_workflow(self):
        """Test complete catalog workflow: fetch, verify, find, call."""
        catalog_data = {
            "version": "1.0",
            "tools": [
                {
                    "name": "integration_tool",
                    "description": "Integration test tool",
                    "x-mcp-tool": {
                        "server_url": "http://localhost:3001",
                        "capabilities": ["integration"]
                    }
                }
            ]
        }
        
        catalog = Catalog("http://test.example.com/.well-known/api-catalog", verify_signatures=False)
        
        # Mock the HTTP response
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.text = AsyncMock(return_value=json.dumps(catalog_data))
            
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Fetch catalog
            await catalog.fetch()
            
            # Verify catalog
            verified = await catalog.verify()
            assert verified is True
            
            # Find tools
            tools = catalog.find(capability="integration")
            assert len(tools) == 1
            
            tool = tools[0]
            assert tool.id == "integration_tool"
            
            # Mock tool call
            with patch('eat.discovery.MCPClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client.call_tool.return_value = {"status": "ok"}
                mock_client_class.return_value = mock_client
                
                result = await tool.call(test_param="value")
                assert result == {"status": "ok"}


if __name__ == "__main__":
    pytest.main([__file__])