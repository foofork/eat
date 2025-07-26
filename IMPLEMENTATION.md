# How to Implement EAT in Any Language

This guide provides language-agnostic instructions for implementing the Enhanced Agent Tools (EAT) protocol. Examples use JSON and HTTP to remain universal.

## Table of Contents
1. [For Tool Publishers](#for-tool-publishers)
2. [For Agent Developers](#for-agent-developers)
3. [Security Implementation](#security-implementation)
4. [Testing Your Implementation](#testing-your-implementation)

## For Tool Publishers

### Step 1: Create OpenAPI Specification with x-mcp-tool

Start with your existing OpenAPI spec and add the `x-mcp-tool` extension:

```yaml
# api-spec.yaml
openapi: 3.0.0
info:
  title: Your API
  version: 1.0.0
paths:
  /users/{id}:
    get:
      operationId: get_user
      summary: Get user by ID
      # Add this extension:
      x-mcp-tool:
        server_url: http://your-mcp-server.com:3001
        capabilities:
          - user-management
          - read-operations
        examples:
          - description: Get test user
            input:
              id: 123
            output:
              id: 123
              name: "Test User"
              email: "test@example.com"
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
```

### Step 2: Generate and Serve the Catalog

#### 2.1 Create Catalog JSON

```json
{
  "version": "1.0",
  "metadata": {
    "title": "My API Tools",
    "description": "Tools for user management",
    "generated_at": "2024-01-20T10:00:00Z",
    "generator": "my-catalog-generator/1.0"
  },
  "tools": [
    {
      "name": "get_user",
      "description": "Get user by ID",
      "version": "1.0.0",
      "spec_url": "https://api.example.com/specs/users.yaml",
      "spec_hash": "sha256:calculate_actual_hash_here",
      "x-mcp-tool": {
        "server_url": "http://localhost:3001",
        "capabilities": ["user-management", "read-operations"],
        "examples": [
          {
            "description": "Get test user",
            "input": {"id": 123},
            "output": {
              "id": 123,
              "name": "Test User",
              "email": "test@example.com"
            }
          }
        ]
      }
    }
  ]
}
```

#### 2.2 Calculate Spec Hash

```bash
# Calculate SHA-256 hash of your OpenAPI spec
sha256sum api-spec.yaml
# Output: 1234567890abcdef...

# Format as: sha256:1234567890abcdef...
```

#### 2.3 Serve at /.well-known/api-catalog

Configure your web server to serve the catalog:

**nginx example:**
```nginx
location /.well-known/api-catalog {
    add_header Content-Type application/json;
    alias /path/to/catalog.json;
}
```

**Apache example:**
```apache
<Location "/.well-known/api-catalog">
    Header set Content-Type "application/json"
</Location>
Alias /.well-known/api-catalog /path/to/catalog.json
```

**Express.js example:**
```javascript
app.get('/.well-known/api-catalog', (req, res) => {
    res.json(catalogData);
});
```

### Step 3: Implement MCP Server

Your MCP server must handle JSON-RPC 2.0 requests:

#### 3.1 Handle tools/list

Request:
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tools/list"
}
```

Response:
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "tools": [
      {
        "name": "get_user",
        "description": "Get user by ID",
        "inputSchema": {
          "type": "object",
          "properties": {
            "id": {"type": "integer"}
          },
          "required": ["id"]
        }
      }
    ]
  }
}
```

#### 3.2 Handle tools/call

Request:
```json
{
  "jsonrpc": "2.0",
  "id": "2",
  "method": "tools/call",
  "params": {
    "name": "get_user",
    "arguments": {
      "id": 123
    }
  }
}
```

Response:
```json
{
  "jsonrpc": "2.0",
  "id": "2",
  "result": {
    "output": {
      "id": 123,
      "name": "Test User",
      "email": "test@example.com"
    }
  }
}
```

## For Agent Developers

### Step 1: Discover Tools

#### 1.1 Fetch Catalog

```http
GET /.well-known/api-catalog HTTP/1.1
Host: example.com
Accept: application/json

HTTP/1.1 200 OK
Content-Type: application/json
X-JWS-Signature: eyJhbGciOiJSUzI1NiI...

{
  "version": "1.0",
  "tools": [...]
}
```

#### 1.2 Parse and Validate

Pseudocode:
```
function fetch_catalog(base_url):
    response = http_get(base_url + "/.well-known/api-catalog")
    
    if response.status != 200:
        throw CatalogNotFoundError
    
    catalog = parse_json(response.body)
    
    if catalog.version != "1.0":
        throw UnsupportedVersionError
    
    if response.headers["X-JWS-Signature"]:
        verify_signature(response.headers["X-JWS-Signature"], catalog)
    
    return catalog
```

### Step 2: Find Tools by Capability

```
function find_tools(catalog, capability):
    matching_tools = []
    
    for tool in catalog.tools:
        if capability in tool["x-mcp-tool"]["capabilities"]:
            matching_tools.append(tool)
    
    return matching_tools
```

### Step 3: Execute Tools via MCP

#### 3.1 Prepare MCP Request

```
function call_tool(tool, arguments):
    mcp_request = {
        "jsonrpc": "2.0",
        "id": generate_uuid(),
        "method": "tools/call",
        "params": {
            "name": tool.name,
            "arguments": arguments
        }
    }
    
    server_url = tool["x-mcp-tool"]["server_url"]
    return http_post(server_url, mcp_request)
```

#### 3.2 Handle Response

```
function handle_response(response):
    if response.error:
        throw MCPError(response.error.message)
    
    return response.result.output
```

### Complete Discovery Flow Example

```
# 1. Discover tools
catalog = fetch_catalog("https://api.example.com")

# 2. Find specific capability
user_tools = find_tools(catalog, "user-management")

# 3. Get the tool
get_user_tool = find_tool_by_name(user_tools, "get_user")

# 4. Execute
result = call_tool(get_user_tool, {"id": 123})
print(result)  # {"id": 123, "name": "Test User", ...}
```

## Security Implementation

### JWS Signing (For Publishers)

#### 1. Generate Signing Keys

```bash
# Generate RSA private key (2048 bits minimum)
openssl genrsa -out private.pem 2048

# Extract public key
openssl rsa -in private.pem -pubout -out public.pem
```

#### 2. Create JWS

Pseudocode:
```
function sign_catalog(catalog_json, private_key):
    # 1. Canonicalize and hash catalog
    canonical_json = canonicalize_json(catalog_json)
    catalog_hash = sha256(canonical_json)
    
    # 2. Create JWS payload
    payload = {
        "iss": "did:web:yourdomain.com",
        "iat": current_timestamp(),
        "exp": current_timestamp() + 86400,  # 24 hours
        "catalog_hash": "sha256:" + catalog_hash
    }
    
    # 3. Create JWS header
    header = {
        "alg": "RS256",
        "typ": "JWS",
        "kid": "key-1"
    }
    
    # 4. Sign
    message = base64url(header) + "." + base64url(payload)
    signature = rs256_sign(message, private_key)
    
    return message + "." + base64url(signature)
```

### JWS Verification (For Agents)

Pseudocode:
```
function verify_catalog(jws_signature, catalog_json):
    # 1. Parse JWS
    parts = jws_signature.split(".")
    header = base64url_decode(parts[0])
    payload = base64url_decode(parts[1])
    signature = base64url_decode(parts[2])
    
    # 2. Resolve public key
    public_key = resolve_did_key(payload.iss, header.kid)
    
    # 3. Verify signature
    message = parts[0] + "." + parts[1]
    if not rs256_verify(message, signature, public_key):
        throw InvalidSignatureError
    
    # 4. Verify catalog hash
    actual_hash = sha256(canonicalize_json(catalog_json))
    expected_hash = payload.catalog_hash.replace("sha256:", "")
    
    if actual_hash != expected_hash:
        throw HashMismatchError
    
    # 5. Check expiration
    if payload.exp < current_timestamp():
        throw ExpiredSignatureError
    
    return True
```

### DID:web Key Resolution

```
function resolve_did_key(did, kid):
    # Extract domain from DID
    # did:web:example.com -> example.com
    domain = did.replace("did:web:", "")
    
    # Fetch DID document
    did_doc = http_get("https://" + domain + "/.well-known/did.json")
    
    # Find verification method
    for method in did_doc.verificationMethod:
        if method.id.endswith("#" + kid):
            return method.publicKeyJwk
    
    throw KeyNotFoundError
```

## Testing Your Implementation

### Test Vectors

#### Valid Catalog
```json
{
  "version": "1.0",
  "tools": [{
    "name": "test_tool",
    "description": "Test tool",
    "spec_url": "https://example.com/spec.yaml",
    "x-mcp-tool": {
      "server_url": "http://localhost:3001"
    }
  }]
}
```

#### Valid MCP Request
```json
{
  "jsonrpc": "2.0",
  "id": "test-1",
  "method": "tools/call",
  "params": {
    "name": "test_tool",
    "arguments": {}
  }
}
```

#### Valid MCP Response
```json
{
  "jsonrpc": "2.0",
  "id": "test-1",
  "result": {
    "output": {
      "status": "success"
    }
  }
}
```

### Integration Testing

1. **Test Discovery**
   ```bash
   curl https://your-domain.com/.well-known/api-catalog
   ```

2. **Test MCP Server**
   ```bash
   curl -X POST http://your-mcp-server:3001 \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":"1","method":"tools/list"}'
   ```

3. **Test Tool Execution**
   ```bash
   curl -X POST http://your-mcp-server:3001 \
     -H "Content-Type: application/json" \
     -d '{
       "jsonrpc": "2.0",
       "id": "2",
       "method": "tools/call",
       "params": {
         "name": "your_tool",
         "arguments": {"param": "value"}
       }
     }'
   ```

### Common Implementation Errors

1. **Catalog Errors**
   - Missing required fields
   - Invalid version number
   - Malformed URLs
   - Missing x-mcp-tool extension

2. **MCP Errors**
   - Invalid JSON-RPC format
   - Missing request ID
   - Incorrect error codes
   - Malformed responses

3. **Security Errors**
   - Expired signatures
   - Invalid key format
   - Hash mismatches
   - Untrusted issuers

## Implementation Checklist

### For Publishers
- [ ] OpenAPI spec includes x-mcp-tool extensions
- [ ] Catalog served at /.well-known/api-catalog
- [ ] Catalog includes all required fields
- [ ] Spec URLs are accessible
- [ ] MCP server handles tools/list
- [ ] MCP server handles tools/call
- [ ] (Optional) JWS signing implemented
- [ ] (Optional) DID document published

### For Agents
- [ ] Can fetch catalogs from URLs
- [ ] Parses catalog JSON correctly
- [ ] Filters tools by capability
- [ ] Sends valid MCP requests
- [ ] Handles MCP responses
- [ ] Implements error handling
- [ ] (Optional) Verifies JWS signatures
- [ ] (Optional) Resolves DID keys

## Next Steps

1. Start with basic HTTP/JSON implementation
2. Add MCP protocol support
3. Test with reference implementations
4. Add security features (JWS signing)
5. Optimize with caching and batching