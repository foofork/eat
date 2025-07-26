# EAT Protocol Specification v1.0

The Enhanced Agent Tools (EAT) protocol enables AI agents to discover and execute tools through secure, cryptographically-signed catalogs served via standard HTTP endpoints.

## Table of Contents
1. [Overview](#overview)
2. [API Catalog Format](#api-catalog-format)
3. [OpenAPI Extension](#openapi-extension)
4. [Security Requirements](#security-requirements)
5. [Discovery Protocol](#discovery-protocol)
6. [MCP Execution Protocol](#mcp-execution-protocol)

## Overview

EAT provides a standardized way for AI agents to:
- Discover available tools from a single catalog URL
- Verify tool authenticity through cryptographic signatures
- Execute tools using the Model Context Protocol (MCP)

## API Catalog Format

### Endpoint
Catalogs MUST be served at: `/.well-known/api-catalog`

### Content Type
- MUST return `Content-Type: application/json`
- MAY include JWS signature header: `X-JWS-Signature`

### Catalog Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["version", "tools"],
  "properties": {
    "version": {
      "type": "string",
      "enum": ["1.0"],
      "description": "Protocol version"
    },
    "metadata": {
      "type": "object",
      "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "generated_at": {"type": "string", "format": "date-time"},
        "generator": {"type": "string"},
        "publisher": {"type": "string"}
      }
    },
    "tools": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/tool"
      }
    }
  },
  "definitions": {
    "tool": {
      "type": "object",
      "required": ["name", "description", "spec_url"],
      "properties": {
        "name": {
          "type": "string",
          "pattern": "^[a-zA-Z0-9_-]+$",
          "description": "Unique tool identifier"
        },
        "description": {
          "type": "string",
          "description": "Human-readable tool description"
        },
        "version": {
          "type": "string",
          "pattern": "^\\d+\\.\\d+\\.\\d+$",
          "description": "Semantic version"
        },
        "spec_url": {
          "type": "string",
          "format": "uri",
          "description": "URL to OpenAPI specification"
        },
        "spec_hash": {
          "type": "string",
          "pattern": "^sha256:[a-f0-9]{64}$",
          "description": "SHA-256 hash of specification"
        },
        "x-mcp-tool": {
          "$ref": "#/definitions/mcp-config"
        }
      }
    },
    "mcp-config": {
      "type": "object",
      "required": ["server_url"],
      "properties": {
        "server_url": {
          "type": "string",
          "format": "uri",
          "description": "MCP server endpoint"
        },
        "method": {
          "type": "string",
          "enum": ["GET", "POST"],
          "default": "POST"
        },
        "path": {
          "type": "string",
          "description": "Override path from OpenAPI spec"
        },
        "capabilities": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Semantic capability tags"
        },
        "examples": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "description": {"type": "string"},
              "input": {"type": "object"},
              "output": {"type": "object"}
            }
          }
        }
      }
    }
  }
}
```

### Example Catalog

```json
{
  "version": "1.0",
  "metadata": {
    "title": "Example API Catalog",
    "description": "Sample tools for demonstration",
    "generated_at": "2024-01-20T10:00:00Z",
    "generator": "eat-gen/1.0.0",
    "publisher": "did:web:example.com"
  },
  "tools": [
    {
      "name": "get_customer",
      "description": "Retrieve customer information by ID",
      "version": "1.0.0",
      "spec_url": "https://api.example.com/specs/customers.yaml",
      "spec_hash": "sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
      "x-mcp-tool": {
        "server_url": "http://localhost:3001",
        "capabilities": ["customer-management", "read-only"],
        "examples": [
          {
            "description": "Get customer with ID 123",
            "input": {"customer_id": 123},
            "output": {
              "id": 123,
              "name": "John Doe",
              "email": "john@example.com"
            }
          }
        ]
      }
    }
  ]
}
```

## OpenAPI Extension

The `x-mcp-tool` extension MUST be added to OpenAPI operation objects to enable MCP tool discovery.

### Extension Schema

```yaml
x-mcp-tool:
  type: object
  required: [server_url]
  properties:
    server_url:
      type: string
      format: uri
      description: MCP server endpoint URL
    capabilities:
      type: array
      items:
        type: string
      description: Semantic capability tags for discovery
    examples:
      type: array
      items:
        type: object
        properties:
          description:
            type: string
          input:
            type: object
          output:
            type: object
```

### OpenAPI Example

```yaml
openapi: 3.0.0
info:
  title: Customer API
  version: 1.0.0
paths:
  /customers/{id}:
    get:
      operationId: get_customer
      summary: Get customer by ID
      x-mcp-tool:
        server_url: http://localhost:3001
        capabilities:
          - customer-management
          - read-only
        examples:
          - description: Retrieve customer John Doe
            input:
              id: 123
            output:
              id: 123
              name: John Doe
              email: john@example.com
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Customer found
          content:
            application/json:
              schema:
                type: object
                properties:
                  id:
                    type: integer
                  name:
                    type: string
                  email:
                    type: string
```

## Security Requirements

### JWS Signing

Catalogs SHOULD be signed using JSON Web Signatures (JWS) with the following requirements:

#### Algorithm
- MUST use RS256 (RSA with SHA-256)
- Key size MUST be at least 2048 bits

#### JWS Structure
```
Header.Payload.Signature
```

#### Header Format
```json
{
  "alg": "RS256",
  "typ": "JWS",
  "kid": "key-identifier"
}
```

#### Payload Format
```json
{
  "iss": "did:web:example.com",
  "iat": 1705752000,
  "exp": 1705838400,
  "catalog_hash": "sha256:abcdef1234567890..."
}
```

#### Signing Process
1. Compute SHA-256 hash of catalog JSON (canonical form)
2. Create JWS payload with hash and metadata
3. Sign using RS256 algorithm
4. Return compact JWS format

#### Verification Process
1. Parse JWS and extract header, payload, signature
2. Resolve signing key from issuer DID
3. Verify signature using public key
4. Compute catalog hash and compare with payload
5. Check timestamp validity (iat/exp)

### Key Resolution

#### DID:web Resolution
For issuer `did:web:example.com`:

1. Fetch `https://example.com/.well-known/did.json`
2. Extract public key from DID document:

```json
{
  "@context": ["https://www.w3.org/ns/did/v1"],
  "id": "did:web:example.com",
  "verificationMethod": [{
    "id": "did:web:example.com#key-1",
    "type": "JsonWebKey2020",
    "controller": "did:web:example.com",
    "publicKeyJwk": {
      "kty": "RSA",
      "n": "...",
      "e": "AQAB",
      "alg": "RS256",
      "use": "sig"
    }
  }]
}
```

#### Fallback JWKS
If DID resolution fails, try `https://example.com/.well-known/jwks.json`:

```json
{
  "keys": [{
    "kty": "RSA",
    "kid": "key-1",
    "use": "sig",
    "alg": "RS256",
    "n": "...",
    "e": "AQAB"
  }]
}
```

## Discovery Protocol

### Basic Discovery Flow

1. **Fetch Catalog**
   ```http
   GET /.well-known/api-catalog HTTP/1.1
   Host: example.com
   Accept: application/json
   ```

2. **Verify Signature** (if present)
   - Extract `X-JWS-Signature` header
   - Verify according to JWS requirements

3. **Parse Tools**
   - Extract tool definitions from catalog
   - Resolve OpenAPI specifications as needed

4. **Filter by Capability**
   - Match tools by semantic capabilities
   - Apply additional filters (version, etc.)

### Caching Requirements

- Catalogs MAY be cached according to HTTP cache headers
- Cached catalogs MUST be revalidated if signature expires
- Tools SHOULD NOT be cached longer than catalog TTL

### Error Handling

| Status Code | Description | Required Action |
|------------|-------------|-----------------|
| 404 | Catalog not found | Fail discovery |
| 401/403 | Authentication required | Retry with credentials |
| 5xx | Server error | Retry with exponential backoff |

## MCP Execution Protocol

Once tools are discovered, execution follows the Model Context Protocol.

### MCP Request Format

```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "method": "tools/call",
  "params": {
    "name": "tool_name",
    "arguments": {
      "param1": "value1",
      "param2": "value2"
    }
  }
}
```

### MCP Response Format

Success:
```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "result": {
    "output": {
      "field1": "value1",
      "field2": "value2"
    }
  }
}
```

Error:
```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {
      "details": "Missing required parameter: customer_id"
    }
  }
}
```

### MCP Methods

| Method | Description | Required |
|--------|-------------|----------|
| `tools/list` | List available tools | Yes |
| `tools/call` | Execute a tool | Yes |
| `tools/get` | Get tool schema | No |

### Transport Requirements

- MUST support HTTP/HTTPS transport
- SHOULD support HTTP/2 for efficiency
- MAY support WebSocket for streaming

## Conformance

To be EAT-compliant:

### Tool Publishers MUST:
1. Serve catalog at `/.well-known/api-catalog`
2. Include valid tool definitions with `x-mcp-tool`
3. Provide accessible OpenAPI specifications
4. Implement MCP server for tool execution

### Tool Publishers SHOULD:
1. Sign catalogs with JWS
2. Provide DID:web identity
3. Include comprehensive examples
4. Support capability-based discovery

### Discovery Clients MUST:
1. Fetch and parse catalogs
2. Handle HTTP errors gracefully
3. Execute tools via MCP protocol
4. Respect caching headers

### Discovery Clients SHOULD:
1. Verify JWS signatures
2. Validate spec hashes
3. Cache catalogs appropriately
4. Support authentication