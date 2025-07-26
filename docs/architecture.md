# EAT Framework Architecture

This document provides a comprehensive technical overview of the Ephemeral Agent Toolkit (EAT) architecture, design decisions, and implementation patterns.

## 🎯 Architecture Overview

EAT implements **one-hop tool discovery** using web standards to eliminate the complexity of traditional tool registries and discovery protocols.

### Core Principles

1. **Zero Infrastructure**: Uses standard HTTPS and static files
2. **Single Round-Trip**: Complete discovery in one HTTP request
3. **Standards-Based**: Built on RFC 8615, OpenAPI 3.0, JWS, and MCP
4. **Human + AI Friendly**: Same specs readable by browsers and agents
5. **Cryptographically Secure**: JWS signatures with content integrity

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────────────────┐    ┌─────────────────┐
│   AI Agent      │    │    Tool Catalog          │    │   MCP Server    │
│                 │    │                          │    │                 │
│ 1. Discovery    │───▶│ /.well-known/api-catalog │    │                 │
│ 2. Validation   │◀───│ (Signed with JWS)        │    │                 │
│ 3. Selection    │    │                          │    │                 │
│ 4. Execution    │────┼──────────────────────────┼───▶│ Tool Execution  │
└─────────────────┘    └──────────────────────────┘    └─────────────────┘
        │                           │                            │
        │                           ▼                            │
        │               ┌──────────────────────────┐             │
        │               │    OpenAPI Specs         │             │
        └──────────────▶│  (with x-mcp-tool)       │◀────────────┘
                        └──────────────────────────┘
```

### Architecture Layers

#### 1. Discovery Layer
**Purpose**: Enable agents to find available tools in a single request

**Components**:
- **`.well-known/api-catalog`**: RFC 8615 compliant discovery endpoint
- **Catalog format**: JSON linkset with tool metadata
- **Content addressing**: SHA-256 hashes for integrity
- **Cryptographic signatures**: JWS with DID:web key resolution

**Flow**:
```
Agent → GET /.well-known/api-catalog → Signed catalog with tool list
```

#### 2. Specification Layer
**Purpose**: Provide rich tool metadata with execution context

**Components**:
- **OpenAPI 3.0 specs**: Standard API documentation
- **x-mcp-tool extensions**: EAT-specific metadata
- **Usage examples**: Realistic input/output pairs
- **Authentication specs**: Token requirements and flows

**Flow**:
```
Agent → Parse catalog → Download OpenAPI specs → Extract x-mcp-tool metadata
```

#### 3. Execution Layer
**Purpose**: Execute tools via standardized protocol

**Components**:
- **MCP (Model Context Protocol)**: JSON-RPC 2.0 based execution
- **Tool servers**: HTTP endpoints implementing MCP
- **Result handling**: Structured responses with error handling
- **Authentication**: Bearer tokens, API keys, OAuth flows

**Flow**:
```
Agent → MCP JSON-RPC call → Tool server → Structured response
```

## 🔧 Component Architecture

### Catalog Structure

```json
{
  "version": "1.0",
  "metadata": {
    "title": "Enterprise Tool Catalog",
    "description": "All approved tools for AI agents",
    "generated_at": "2024-01-20T10:30:00Z",
    "expires_at": "2024-01-21T10:30:00Z",
    "generator": "eat-cli v1.0.0"
  },
  "tools": [
    {
      "name": "get_customer",
      "description": "Retrieve customer information by ID",
      "version": "2.1.0",
      "spec_url": "https://api.company.com/specs/customer.yaml",
      "spec_hash": "sha256:abc123...",
      "x-mcp-tool": {
        "server_url": "https://api.company.com/mcp",
        "capabilities": ["customer-management", "read-operations"],
        "examples": [...],
        "authentication": {...},
        "rate_limits": {...}
      }
    }
  ]
}
```

### OpenAPI Extension (`x-mcp-tool`)

```yaml
paths:
  /customers/{id}:
    get:
      operationId: get_customer
      summary: Get customer by ID
      x-mcp-tool:
        server_url: https://api.company.com/mcp
        capabilities:
          - customer-management
          - read-operations
        examples:
          - description: Get VIP customer details
            input:
              customer_id: "12345"
              include_preferences: true
            output:
              id: "12345"
              name: "John Doe"
              tier: "VIP"
              preferences: {...}
        authentication:
          type: bearer
          token_url: https://auth.company.com/token
          scopes: ["customers:read"]
        rate_limits:
          requests_per_minute: 1000
          burst_limit: 50
        error_patterns:
          - status: 404
            meaning: "Customer not found"
            action: "Verify customer ID exists in system"
          - status: 403
            meaning: "Insufficient permissions"
            action: "Check authentication token scopes"
        best_practices:
          - "Cache customer data for 5 minutes"
          - "Use batch endpoints for multiple lookups"
          - "Include only required fields in requests"
```

## 🔐 Security Architecture

### Cryptographic Model

#### JWS Signing Process
```
1. Canonicalize catalog JSON (deterministic serialization)
2. Generate SHA-256 hash of canonical form
3. Create JWS payload with catalog hash and metadata
4. Sign with RS256 algorithm using private key
5. Publish signed catalog and verification key
```

#### DID:web Key Resolution
```
1. Extract issuer from JWS header: "did:web:api.company.com"
2. Resolve to HTTPS URL: https://api.company.com/.well-known/did.json
3. Download DID document with public key
4. Verify JWS signature using resolved public key
5. Validate certificate chain if using X.509
```

### Content Integrity
- **SHA-256 hashes**: All referenced OpenAPI specs
- **Signature verification**: Catalog integrity and authenticity
- **HTTPS enforcement**: All traffic encrypted in transit
- **Cache validation**: Detect stale or modified content

### Threat Model

| Threat | Mitigation | Implementation |
|--------|------------|----------------|
| **Catalog tampering** | JWS signatures | Cryptographic verification |
| **Spec substitution** | SHA-256 hashes | Content integrity checking |
| **MITM attacks** | HTTPS/TLS | Transport layer security |
| **Key compromise** | Key rotation | DID:web with versioned keys |
| **Replay attacks** | Timestamp validation | JWT `iat` and `exp` claims |

## ⚡ Performance Architecture

### Optimization Strategies

#### Discovery Performance
- **Single request**: Complete tool list in one HTTP GET
- **Parallel downloads**: Concurrent spec retrieval
- **Aggressive caching**: HTTP cache headers and ETag support
- **Compression**: gzip/brotli for catalog and specs

#### Execution Performance
- **Connection pooling**: Reuse HTTP connections to MCP servers
- **Request batching**: Multiple tool calls in single MCP request
- **Async processing**: Non-blocking I/O throughout stack
- **Circuit breakers**: Fail fast on unavailable tools

#### Caching Strategy
```
Level 1: HTTP Cache (5-15 minutes)
├── Catalog: Cache-Control: public, max-age=300
├── Specs: Cache-Control: public, max-age=900
└── Keys: Cache-Control: public, max-age=3600

Level 2: Application Cache (In-memory)
├── Parsed catalogs: 15 minutes
├── Validated signatures: 1 hour
└── Tool metadata: 30 minutes

Level 3: CDN Cache (Global)
├── Static catalogs: 1 hour
├── OpenAPI specs: 4 hours
└── Public keys: 24 hours
```

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Cold start discovery** | <200ms | First catalog fetch to tool list |
| **Warm discovery** | <50ms | Cached catalog to tool selection |
| **Signature verification** | <25ms | JWS validation with key lookup |
| **Tool execution** | <500ms | MCP call round-trip (median) |
| **Memory usage** | <10MB | Typical catalog with 100 tools |

## 🌐 Distribution Architecture

### Deployment Patterns

#### Pattern 1: Centralized Catalog
```
Enterprise API Gateway
├── /.well-known/api-catalog (central)
├── /specs/* (all OpenAPI specs)
└── /mcp/* (proxied tool servers)

Benefits: Single source of truth, centralized governance
Challenges: Single point of failure, scaling bottlenecks
```

#### Pattern 2: Federated Catalogs
```
Service A: api-a.company.com/.well-known/api-catalog
Service B: api-b.company.com/.well-known/api-catalog
Service C: api-c.company.com/.well-known/api-catalog

Gateway: api.company.com/.well-known/api-catalog
├── Aggregates all service catalogs
└── Signs unified catalog

Benefits: Distributed ownership, service autonomy
Challenges: Coordination complexity, signature management
```

#### Pattern 3: Hybrid Architecture
```
Core Platform
├── /.well-known/api-catalog (platform tools)
├── /federated/team-a/api-catalog (team catalogs)
├── /federated/team-b/api-catalog
└── /unified/api-catalog (merged view)

Benefits: Balance of autonomy and governance
Challenges: Complex routing, version management
```

### Multi-Environment Support

#### Development → Staging → Production
```yaml
environments:
  development:
    catalog_url: https://dev-api.company.com/.well-known/api-catalog
    mcp_servers: 
      - https://dev-customer.company.com/mcp
      - https://dev-analytics.company.com/mcp
    
  staging:
    catalog_url: https://staging-api.company.com/.well-known/api-catalog
    mcp_servers:
      - https://staging-customer.company.com/mcp
      - https://staging-analytics.company.com/mcp
    
  production:
    catalog_url: https://api.company.com/.well-known/api-catalog
    mcp_servers:
      - https://customer.company.com/mcp
      - https://analytics.company.com/mcp
```

## 🔄 Data Flow Architecture

### Discovery Flow
```
┌─────────────┐
│ Agent Start │
└─────┬───────┘
      │
      ▼
┌─────────────────────┐
│ GET /.well-known/   │
│ api-catalog         │
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ Verify JWS          │
│ Signature           │
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ Parse Tool List     │
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ Filter by           │
│ Capability          │
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ Download OpenAPI    │
│ Specs (parallel)    │
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ Verify SHA-256      │
│ Hashes              │
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ Extract x-mcp-tool  │
│ Metadata            │
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ Ready for Tool      │
│ Execution           │
└─────────────────────┘
```

### Execution Flow
```
┌─────────────────────┐
│ Select Tool from    │
│ Filtered List       │
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ Prepare MCP         │
│ Request             │
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ Handle              │
│ Authentication      │
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ POST to MCP         │
│ Server              │
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ Parse JSON-RPC      │
│ Response            │
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ Handle Errors or    │
│ Return Results      │
└─────────────────────┘
```

## 🔧 Implementation Architecture

### Language-Agnostic Design

The EAT protocol is implemented using standard web technologies, making it accessible to any language that can:

1. **Make HTTP requests** (GET for discovery, POST for execution)
2. **Parse JSON** (for catalogs and MCP responses)
3. **Verify JWS signatures** (using standard crypto libraries)
4. **Calculate SHA-256 hashes** (for content integrity)

### Reference Implementation (Python)

```python
# Core architecture classes
class Catalog:
    """Manages tool discovery and verification"""
    def __init__(self, catalog_url, verify_signatures=True)
    async def fetch(self) -> None
    async def verify(self) -> bool
    def find(self, capability=None, name=None) -> List[Tool]
    def get_tool(self, name) -> Tool

class Tool:
    """Represents a single tool with metadata"""
    def __init__(self, spec, mcp_metadata)
    async def call(self, **kwargs) -> Dict
    def get_examples(self) -> List[Dict]
    def get_auth_requirements(self) -> Dict

class MCPClient:
    """Handles MCP protocol communication"""
    def __init__(self, server_url, auth_token=None)
    async def call_tool(self, tool_name, arguments) -> Dict
    async def list_tools(self) -> List[Dict]
    def close(self) -> None
```

### Extension Points

The architecture supports extension through:

1. **Custom x-* fields**: Add domain-specific metadata to OpenAPI specs
2. **Plugin authentication**: Support for custom auth flows
3. **Result processors**: Transform tool outputs for specific use cases
4. **Cache backends**: Custom caching strategies (Redis, Memcached)
5. **Signature algorithms**: Additional JWS algorithms beyond RS256

## 📊 Monitoring Architecture

### Observability Stack

#### Metrics Collection
- **Discovery latency**: Time from catalog request to tool selection
- **Verification performance**: JWS signature validation time
- **Tool execution metrics**: Success rate, latency, error patterns
- **Cache hit rates**: Effectiveness of caching strategy

#### Structured Logging
```json
{
  "timestamp": "2024-01-20T10:30:00Z",
  "level": "INFO",
  "component": "catalog_discovery",
  "action": "fetch_catalog",
  "catalog_url": "https://api.company.com/.well-known/api-catalog",
  "duration_ms": 145,
  "tools_found": 23,
  "signature_valid": true,
  "cache_hit": false
}
```

#### Health Checks
- **Catalog availability**: Monitor catalog endpoint health
- **Signature validity**: Ensure catalogs remain properly signed
- **Tool server health**: Monitor MCP server availability
- **Certificate expiry**: Alert on key rotation needs

## 🚀 Scalability Architecture

### Horizontal Scaling
- **Stateless design**: No server-side state requirements
- **CDN-friendly**: Static catalog files cache globally
- **Load balancing**: Standard HTTP load balancing for MCP servers
- **Database-free**: No persistent storage requirements

### Vertical Scaling
- **Memory efficiency**: Minimal memory footprint per agent
- **CPU optimization**: Efficient signature verification
- **I/O patterns**: Optimized for concurrent tool execution
- **Resource pooling**: Shared HTTP connections and crypto contexts

## 🔮 Future Architecture

### Planned Enhancements
1. **Catalog federation**: Cross-organization tool sharing
2. **Tool composition**: Chaining tools into workflows
3. **Real-time updates**: WebSocket-based catalog notifications
4. **Advanced caching**: Intelligent prefetching and invalidation
5. **Tool analytics**: Usage patterns and optimization recommendations

---

This architecture enables EAT to provide **one-hop tool discovery** with security, performance, and scalability suitable for enterprise deployment while maintaining simplicity for individual developers.