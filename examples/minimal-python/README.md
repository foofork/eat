# Minimal Python EAT Client

This directory contains a complete EAT (Enhanced Agent Tools) client implementation in under 80 lines of Python code. It demonstrates the core EAT protocol features:

- Tool discovery from catalogs
- Capability-based tool filtering  
- MCP protocol tool execution
- Error handling and validation

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the demo
python eat_client.py
```

## Usage

```python
from eat_client import EATClient

# Initialize client
client = EATClient("http://localhost:8080/.well-known/api-catalog")

# Discover tools
tools = client.list_tools()
user_tools = client.find_tools("user-management")

# Get tool information
info = client.get_tool_info("get_user")
print(f"Description: {info['description']}")
print(f"Capabilities: {info['capabilities']}")

# Execute tools
result = client.call_tool("get_user", id=123)
print(f"User: {result}")
```

## Features

### Discovery
- Fetches catalogs from standard `.well-known/api-catalog` endpoint
- Validates catalog format and version
- Extracts tool metadata and MCP configuration

### Tool Management
- Lists all available tools
- Filters tools by capability tags
- Provides detailed tool information including examples

### Execution
- Implements JSON-RPC 2.0 MCP protocol
- Handles MCP errors gracefully
- Supports arbitrary tool arguments
- Includes connection timeout and error handling

### Error Handling
- Network error handling with clear error messages
- MCP protocol error detection and reporting
- Catalog format validation
- Tool existence validation

## Code Structure

The implementation consists of a single `EATClient` class with these core methods:

- `__init__(catalog_url)` - Initialize and discover tools
- `list_tools()` - Get all available tool names
- `find_tools(capability)` - Filter tools by capability
- `get_tool_info(tool_name)` - Get detailed tool information
- `call_tool(tool_name, **args)` - Execute a tool via MCP

## Example Output

```
🔍 EAT Client Demo
========================================
📋 Found 3 tools:
  • say_hello: Greet someone by name
  • get_user: Get user by ID  
  • list_users: Retrieve a paginated list of all users

👥 User management tools: get_user, list_users
👋 Greeting tools: say_hello

🚀 Calling tool: say_hello
📝 Using example arguments: {'name': 'Alice'}
✅ Result: {
  "message": "Hello, Alice!",
  "timestamp": "2024-01-20T10:00:00Z"
}

🎉 Demo completed!
```

## Extending the Client

### Add Authentication

```python
def call_tool(self, tool_name: str, **arguments) -> Any:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {self.api_token}"
    }
    response = requests.post(server_url, json=request_data, headers=headers)
```

### Add Caching

```python
import time

class EATClient:
    def __init__(self, catalog_url: str, cache_ttl: int = 300):
        self.cache_ttl = cache_ttl
        self.catalog_cache = None
        self.cache_time = 0
        
    def _discover(self) -> None:
        now = time.time()
        if self.catalog_cache and (now - self.cache_time) < self.cache_ttl:
            return  # Use cached catalog
        # ... fetch new catalog
        self.cache_time = now
```

### Add Async Support

```python
import asyncio
import aiohttp

class AsyncEATClient:
    async def call_tool(self, tool_name: str, **arguments) -> Any:
        async with aiohttp.ClientSession() as session:
            async with session.post(server_url, json=request_data) as response:
                result = await response.json()
                # ... handle response
```

### Add Signature Verification

```python
import jwt
from cryptography.hazmat.primitives import serialization

def verify_catalog_signature(self, catalog: dict, jws_signature: str) -> bool:
    try:
        # Extract public key from DID document
        did_url = f"https://{catalog['metadata']['publisher'].split(':')[-1]}/.well-known/did.json"
        did_doc = requests.get(did_url).json()
        
        # Find verification method
        for method in did_doc['verificationMethod']:
            if 'publicKeyJwk' in method:
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(method['publicKeyJwk'])
                
                # Verify JWS
                payload = jwt.decode(jws_signature, public_key, algorithms=['RS256'])
                
                # Verify catalog hash
                import hashlib
                catalog_hash = hashlib.sha256(json.dumps(catalog, sort_keys=True).encode()).hexdigest()
                return payload['catalog_hash'] == f"sha256:{catalog_hash}"
                
    except Exception as e:
        print(f"Signature verification failed: {e}")
        return False
```

## Testing

Test against the demo servers:

```bash
# Start the demo environment
cd ../../demo
./quickstart.sh

# Run the client
cd ../examples/minimal-python
python eat_client.py
```

## Production Considerations

1. **Error Handling**: Add retry logic with exponential backoff
2. **Logging**: Add proper logging for debugging and monitoring
3. **Configuration**: Use environment variables for URLs and credentials
4. **Security**: Implement signature verification for production catalogs
5. **Performance**: Add connection pooling and request batching
6. **Monitoring**: Add metrics and health checks

## Next Steps

- Try modifying the client for your specific use case
- Add the extensions shown above
- Integrate with your existing Python applications
- Build agents that use multiple tools in workflows