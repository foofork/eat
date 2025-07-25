"""
Pytest configuration and shared fixtures for EAT Framework tests.
"""

import pytest
import asyncio
import tempfile
import os
import json
from pathlib import Path


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_path:
        yield Path(temp_path)


@pytest.fixture
def sample_openapi_spec():
    """Sample OpenAPI specification with x-mcp-tool extensions."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Test API",
            "version": "1.0.0",
            "description": "Test API for EAT Framework testing"
        },
        "servers": [
            {"url": "http://localhost:3001"}
        ],
        "paths": {
            "/users/{id}": {
                "get": {
                    "operationId": "get_user",
                    "summary": "Get user by ID",
                    "description": "Retrieve user information by user ID",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                            "description": "User ID"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "User information",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "name": {"type": "string"},
                                            "email": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "x-mcp-tool": {
                        "server_url": "http://localhost:3001",
                        "capabilities": ["user-management"],
                        "examples": [
                            {
                                "description": "Get user with ID 123",
                                "input": {"id": 123},
                                "output": {
                                    "id": 123,
                                    "name": "John Doe",
                                    "email": "john@example.com"
                                }
                            }
                        ]
                    }
                }
            },
            "/users": {
                "post": {
                    "operationId": "create_user",
                    "summary": "Create new user",
                    "description": "Create a new user account",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "email": {"type": "string", "format": "email"}
                                    },
                                    "required": ["name", "email"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "User created successfully"
                        }
                    },
                    "x-mcp-tool": {
                        "server_url": "http://localhost:3001",
                        "capabilities": ["user-management"],
                        "examples": [
                            {
                                "description": "Create new user",
                                "input": {
                                    "name": "Jane Smith",
                                    "email": "jane@example.com"
                                },
                                "output": {
                                    "id": 124,
                                    "name": "Jane Smith",
                                    "email": "jane@example.com"
                                }
                            }
                        ]
                    }
                }
            }
        }
    }


@pytest.fixture
def sample_catalog():
    """Sample EAT catalog for testing."""
    return {
        "version": "1.0",
        "metadata": {
            "title": "Test Catalog",
            "description": "Test catalog for unit testing",
            "generated_at": "2024-01-01T00:00:00Z",
            "generator": "test-suite"
        },
        "tools": [
            {
                "name": "get_user",
                "description": "Get user by ID",
                "version": "1.0.0",
                "spec_url": "http://localhost:8000/specs/users.yaml",
                "spec_hash": "abc123def456",
                "x-mcp-tool": {
                    "server_url": "http://localhost:3001",
                    "method": "GET",
                    "path": "/users/{id}",
                    "capabilities": ["user-management"],
                    "examples": [
                        {
                            "description": "Get user 123",
                            "input": {"id": 123},
                            "output": {"id": 123, "name": "John Doe"}
                        }
                    ]
                }
            },
            {
                "name": "create_user",
                "description": "Create new user",
                "version": "1.0.0",
                "spec_url": "http://localhost:8000/specs/users.yaml",
                "spec_hash": "abc123def456",
                "x-mcp-tool": {
                    "server_url": "http://localhost:3001",
                    "method": "POST",
                    "path": "/users",
                    "capabilities": ["user-management"],
                    "examples": [
                        {
                            "description": "Create user",
                            "input": {"name": "Jane", "email": "jane@example.com"},
                            "output": {"id": 124, "name": "Jane"}
                        }
                    ]
                }
            }
        ]
    }


@pytest.fixture
def create_test_spec_file(temp_dir, sample_openapi_spec):
    """Create a test OpenAPI specification file."""
    def _create_spec_file(filename="test-api.yaml", spec_data=None):
        if spec_data is None:
            spec_data = sample_openapi_spec
        
        spec_file = temp_dir / filename
        with open(spec_file, 'w') as f:
            json.dump(spec_data, f, indent=2)
        
        return spec_file
    
    return _create_spec_file


@pytest.fixture
def create_test_catalog_file(temp_dir, sample_catalog):
    """Create a test catalog file."""
    def _create_catalog_file(filename="catalog.json", catalog_data=None):
        if catalog_data is None:
            catalog_data = sample_catalog
        
        catalog_file = temp_dir / filename
        with open(catalog_file, 'w') as f:
            json.dump(catalog_data, f, indent=2)
        
        return catalog_file
    
    return _create_catalog_file


@pytest.fixture
def mock_mcp_server_response():
    """Mock MCP server response data."""
    return {
        "jsonrpc": "2.0",
        "id": "test-request",
        "result": {
            "status": "success",
            "data": {"message": "Test response"}
        }
    }


@pytest.fixture
def mock_mcp_error_response():
    """Mock MCP server error response."""
    return {
        "jsonrpc": "2.0",
        "id": "test-request",
        "error": {
            "code": -32603,
            "message": "Internal server error",
            "data": {"details": "Test error"}
        }
    }


# Test markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network access"
    )