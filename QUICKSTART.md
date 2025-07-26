# Build EAT Support in 10 Minutes

Get your AI agent discovering and using tools in under 10 minutes with this quickstart guide.

## For Tool Publishers (5 minutes)

### 1. Copy this OpenAPI template (30 seconds)

Save as `api-spec.yaml`:

```yaml
openapi: 3.0.0
info:
  title: My API
  version: 1.0.0
paths:
  /hello/{name}:
    get:
      operationId: say_hello
      x-mcp-tool:
        server_url: http://localhost:3001
        capabilities: ["greeting"]
        examples:
          - description: "Say hello to Alice"
            input: {"name": "Alice"}
            output: {"message": "Hello, Alice!"}
      parameters:
        - name: name
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Greeting message
          content:
            application/json:
              schema:
                type: object
                properties:
                  message:
                    type: string
```

### 2. Create and serve catalog (2 minutes)

Save as `catalog.json`:

```json
{
  "version": "1.0",
  "metadata": {
    "title": "My First EAT Catalog",
    "generated_at": "2024-01-20T10:00:00Z"
  },
  "tools": [
    {
      "name": "say_hello",
      "description": "Greet someone by name",
      "spec_url": "http://localhost:8080/api-spec.yaml",
      "x-mcp-tool": {
        "server_url": "http://localhost:3001",
        "capabilities": ["greeting"]
      }
    }
  ]
}
```

Serve with Python:
```bash
# Serve catalog and spec
python3 -m http.server 8080 &

# The catalog is now available at:
# http://localhost:8080/catalog.json
```

### 3. Run a minimal MCP server (2 minutes)

Save as `mcp-server.py`:

```python
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class MCPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        request = json.loads(self.rfile.read(content_length))
        
        response = {
            "jsonrpc": "2.0",
            "id": request["id"]
        }
        
        if request["method"] == "tools/list":
            response["result"] = {
                "tools": [{
                    "name": "say_hello",
                    "description": "Greet someone by name",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"}
                        },
                        "required": ["name"]
                    }
                }]
            }
        elif request["method"] == "tools/call":
            name = request["params"]["arguments"]["name"]
            response["result"] = {
                "output": {"message": f"Hello, {name}!"}
            }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

HTTPServer(('localhost', 3001), MCPHandler).serve_forever()
```

Run it:
```bash
python3 mcp-server.py
```

### 4. Test your setup (30 seconds)

```bash
# Your catalog should be accessible:
curl http://localhost:8080/catalog.json

# Your MCP server should respond:
curl -X POST http://localhost:3001 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/list"}'
```

**Done!** Your tool is now discoverable by any EAT-compatible agent.

---

## For Agent Developers (5 minutes)

### 1. Discover tools (2 minutes)

Using curl:
```bash
# Discover available tools
CATALOG=$(curl -s http://localhost:8080/catalog.json)
echo "$CATALOG" | jq '.tools'

# Extract MCP server URL
SERVER_URL=$(echo "$CATALOG" | jq -r '.tools[0]["x-mcp-tool"].server_url')
```

### 2. List available tools (1 minute)

```bash
# Ask MCP server what tools it has
curl -X POST "$SERVER_URL" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/list"}' | jq
```

### 3. Call a tool (2 minutes)

```bash
# Execute the say_hello tool
curl -X POST "$SERVER_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "2",
    "method": "tools/call",
    "params": {
      "name": "say_hello",
      "arguments": {"name": "World"}
    }
  }' | jq
```

Expected output:
```json
{
  "jsonrpc": "2.0",
  "id": "2",
  "result": {
    "output": {
      "message": "Hello, World!"
    }
  }
}
```

---

## Minimal Implementation (50 lines)

Here's a complete EAT client in 50 lines of Python:

```python
#!/usr/bin/env python3
import requests
import json

class EATClient:
    def __init__(self, catalog_url):
        self.catalog_url = catalog_url
        self.tools = {}
        self._discover()
    
    def _discover(self):
        """Fetch and parse the tool catalog"""
        resp = requests.get(self.catalog_url)
        catalog = resp.json()
        
        for tool in catalog['tools']:
            self.tools[tool['name']] = {
                'server_url': tool['x-mcp-tool']['server_url'],
                'capabilities': tool['x-mcp-tool'].get('capabilities', [])
            }
    
    def find_tools(self, capability):
        """Find tools by capability"""
        return [name for name, info in self.tools.items() 
                if capability in info['capabilities']]
    
    def call_tool(self, tool_name, **arguments):
        """Execute a tool via MCP"""
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        server_url = self.tools[tool_name]['server_url']
        
        request = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        resp = requests.post(server_url, json=request)
        result = resp.json()
        
        if 'error' in result:
            raise Exception(result['error']['message'])
        
        return result['result']['output']

# Usage example:
if __name__ == "__main__":
    client = EATClient("http://localhost:8080/catalog.json")
    result = client.call_tool("say_hello", name="EAT Framework")
    print(result['message'])  # "Hello, EAT Framework!"
```

---

## Next Steps

### Make it production-ready:

1. **Add error handling**
   ```python
   try:
       result = client.call_tool("tool_name", param="value")
   except requests.exceptions.RequestException as e:
       print(f"Network error: {e}")
   except KeyError as e:
       print(f"Invalid response format: {e}")
   ```

2. **Add caching**
   ```python
   # Cache catalogs for 5 minutes
   if cached_catalog and time.time() - cache_time < 300:
       return cached_catalog
   ```

3. **Add authentication**
   ```python
   headers = {"Authorization": f"Bearer {api_token}"}
   requests.get(catalog_url, headers=headers)
   ```

4. **Add signature verification**
   ```python
   # Check X-JWS-Signature header
   signature = response.headers.get('X-JWS-Signature')
   if signature:
       verify_jws(signature, response.content)
   ```

### Learn more:

- Read the full [PROTOCOL.md](PROTOCOL.md) for complete specification
- See [IMPLEMENTATION.md](IMPLEMENTATION.md) for detailed implementation guide
- Check [examples/](examples/) for more complex scenarios

---

## Troubleshooting

**Catalog not found?**
- Ensure server is running on correct port
- Check firewall settings
- Verify URL ends with exact path

**MCP server errors?**
- Check JSON-RPC request format
- Verify tool name matches exactly
- Ensure all required parameters are provided

**Tool execution fails?**
- Validate arguments match schema
- Check MCP server logs
- Test with tools/list first

---

**Congratulations!** You've implemented EAT support in under 10 minutes. Your AI agent can now discover and use tools from any EAT-compatible catalog.