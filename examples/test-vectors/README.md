# EAT Protocol Test Vectors

This directory contains validation test cases for EAT protocol implementations. Use these vectors to verify that your implementation correctly handles various scenarios.

## Test Categories

### 1. Catalog Format Tests
- Valid and invalid catalog structures
- Version compatibility tests
- Required field validation

### 2. Tool Definition Tests
- Valid tool configurations
- x-mcp-tool extension validation
- Capability and example format tests

### 3. MCP Protocol Tests
- JSON-RPC request/response validation
- Error handling test cases
- Method parameter validation

### 4. Security Tests
- JWS signature verification
- Catalog integrity validation
- DID resolution test cases

### 5. Edge Cases
- Empty catalogs and tools
- Network error scenarios
- Malformed data handling

## Running Tests

```bash
# Python implementations
python test_catalog_validation.py
python test_mcp_protocol.py
python test_security.py

# Using curl for HTTP tests
bash test_http_scenarios.sh

# Validate against schemas
jsonschema -i valid_catalog.json catalog_schema.json
```

## Test Vector Format

Each test vector includes:
- **Input**: The data to test
- **Expected**: Expected result or behavior
- **Description**: What the test validates
- **Category**: Type of test (valid/invalid/edge-case)

## Validation Checklist

Use this checklist to verify your EAT implementation:

### Catalog Discovery
- [ ] Fetches catalogs from `.well-known/api-catalog`
- [ ] Handles HTTP errors gracefully
- [ ] Validates catalog version
- [ ] Parses tool definitions correctly
- [ ] Extracts x-mcp-tool configurations

### Tool Execution
- [ ] Implements JSON-RPC 2.0 correctly
- [ ] Handles MCP errors properly
- [ ] Validates tool arguments
- [ ] Processes responses correctly
- [ ] Manages timeouts appropriately

### Security
- [ ] Verifies JWS signatures when present
- [ ] Validates catalog hashes
- [ ] Resolves DID documents
- [ ] Handles signature failures gracefully

### Error Handling
- [ ] Network connection errors
- [ ] Invalid JSON responses
- [ ] Missing required fields
- [ ] Timeout scenarios
- [ ] Authentication failures