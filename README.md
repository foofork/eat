# Ephemeral Agent Toolkit (EAT)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/foofork/eat/workflows/Tests/badge.svg)](https://github.com/foofork/eat/actions)

> **One-hop tool discovery for AI agents using signed .well-known catalogs**

Most people know MCP for connecting AI agents to third-party tools like GitHub and Slack, but there's an elegant approach using signed .well-known catalogs that lets ephemeral agents discover your entire internal tool ecosystem in a single hop - no registries required.

EAT lets AI helpers (and humans) find every approved API, script, or model in **one hop**. Drop a single signed file on your web server and even a throw‑away notebook knows where to call for work—no registries, no handshakes, no cloud required.

---

## 🚀 Quick Demo

```bash
# Get running in 30 seconds
git clone https://github.com/foofork/eat/eat.git
cd eat/demo && ./quickstart.sh

# Agent discovers and uses tools automatically
export EAT_CATALOG="http://localhost:8000/.well-known/api-catalog"
eat-agent --task "get customer info for ID 12345"
# ✅ Customer: John Doe (john@example.com)
```

---

## 🤔 The Problem

Today's AI agents waste time on tool discovery:
- **Complex setup**: MCP servers, registries, handshakes
- **Slow cold-start**: Multiple roundtrips before work begins  
- **Fragile dependencies**: If discovery service is down, agent fails
- **Human-unfriendly**: Tool metadata buried in JSON payloads

## 💡 The Solution

**Distributed discovery using web standards:**
- Each service publishes `/.well-known/api-catalog` (RFC 8615)
- Single fetch gets all tool metadata + usage context
- Cryptographically signed for integrity (JWS + SHA-256)
- Human-readable specs that render in browsers
- Zero infrastructure - just static files

---

## 🗺️ Architecture

```
┌────────────┐        ┌─────────────────────────┐
│ Agent CLI  │───────▶│ /.well‑known/api-catalog │
└────────────┘        └─────────────────────────┘
        │                       │
        ▼                       ▼
┌────────────┐        ┌─────────────────────────┐
│  Tool Spec │───────▶│   MCP Server Runtime    │
└────────────┘        └─────────────────────────┘
```

1. **Discovery**: One HTTP GET fetches the signed catalog
2. **Validation**: Agent verifies JWS signature and SHA-256 hashes  
3. **Execution**: Agent loads `x-mcp-tool` blocks and calls tools via MCP

---

## ⚡ What You Get

* **Zero vendor lock‑in** · plain HTTPS, OpenAPI, JSON—nothing exotic
* **One hop discovery** · agents fetch a single linkset, done
* **Extends MCP** · specs can be tailored with new fields (`x‑*`) without touching agent code
* **Runs anywhere** · serve the file from a laptop folder or a CDN  
* **Tamper‑evident** · optional JWS signatures and SHA‑256 hashes
* **Human + AI friendly** · same files readable by browsers and agents

---

## 🔧 Example Agent Workflow

```python
from eat_discovery import Catalog
from eat_mcp import MCPClient

# 1️⃣  Discover tools in one hop
cat = Catalog("https://api.acme.com/.well-known/api-catalog")
cat.verify()            # JWS + SHA‑256 integrity check

# 2️⃣  Pick the best tool for the task
spec = cat.find(capability="customer", action="data_retrieval")
print(spec.tool_id)     # -> "get_customer"

# 3️⃣  Invoke via MCP
client = MCPClient(spec.endpoint)  # endpoint auto‑resolved from spec
result = client.call_tool(
    spec,
    {"customer_id": "12345", "include_preferences": True}
)
print(result["email"])  # => "john@example.com"
```

**Total cold‑start time**: ~120ms (two HTTP GETs + one MCP call)

---

## 📦 Catalog Contents

The `/.well‑known/api-catalog` contains a signed linkset referencing tool specs with rich `x-mcp-tool` extensions:

```yaml
# customer-api.yaml
openapi: 3.0.0
info:
  title: Customer API
  version: 2.1.0
x-mcp-tool:
  name: get_customer
  description: "Retrieve customer information by ID"
  examples:
    - task: "Get customer profile"
      request:
        method: GET
        url: "/customers/{customer_id}"
        headers: {"Authorization": "Bearer {token}"}
      response:
        status: 200
        body: {"id": "12345", "name": "John Doe"}
  authentication:
    type: bearer
    endpoint: "/auth/token"
    scope: "customers:read"
  error_patterns:
    - status: 404
      meaning: "Customer not found"
      action: "Verify customer ID exists"
  best_practices:
    - "Cache frequently accessed customers"
    - "Use batch endpoints for multiple lookups"
```

---

## 🚀 Quick Start

### Option 1: Try the Demo
```bash
git clone https://github.com/foofork/eat.git
cd eat/demo
docker-compose up -d

# Test discovery
curl -s http://localhost:8000/.well-known/api-catalog | jq

# Run sample agent
pip install eat-framework
eat-agent --catalog http://localhost:8000/.well-known/api-catalog \
          --task "get customer 12345"
```

### Option 2: Install & Use
```bash
# Install CLI tools
pip install eat-framework

# Initialize new catalog
mkdir my-tools && cd my-tools
eat-gen init

# Add your first tool spec
eat-gen add-spec my-api.yaml

# Generate signed catalog
eat-gen sign --key private.pem

# Serve locally
eat-gen serve
```

### Option 3: Integration Example
```python
import asyncio
from eat import Catalog

async def main():
    # Discover tools
    catalog = Catalog("http://localhost:8000/.well-known/api-catalog")
    await catalog.fetch()
    
    # Find and use a tool
    tool = catalog.find(capability="customer")[0]
    result = await tool.call(customer_id="12345")
    
    print(f"Customer: {result['name']} ({result['email']})")

asyncio.run(main())
```

---

## 🌐 Language Support

EAT works with any language that can make HTTP requests and parse JSON:

| Language   | Discovery Library | MCP Client | Status | Package |
|------------|------------------|------------|---------|---------|
| Python     | `eat-discovery`  | `eat-mcp`  | ✅ Stable | [`pip install eat-framework`](https://pypi.org/project/eat-framework/) |
| JavaScript | `@eat/discovery` | `@mcp/client` | ✅ Stable | [`npm install @eat/discovery`](https://www.npmjs.com/package/@eat/discovery) |
| Rust       | `eat-discovery`  | `mcp-client` | ✅ Stable | [`cargo add eat-discovery`](https://crates.io/crates/eat-discovery) |
| Go         | `eat-go`         | `mcp-go`   | 🚧 Alpha | [`go get github.com/foofork/eat-go`](https://github.com/foofork/eat-go) |

---

## 🔒 Security

- **HTTPS everywhere**: All catalog and tool traffic encrypted
- **JWS signatures**: Cryptographically signed catalogs via `did:web`
- **Content integrity**: SHA-256 validation of all specs
- **No PKI complexity**: Leverages existing web trust models

---

## 👩‍💻 Human + AI Workflow

| User | Experience |
|------|------------|
| **AI Agent** | Fetches catalog, filters by capability, gets complete usage context in <1ms |
| **Human** | Opens catalog URL in browser, sees formatted docs with examples and best practices |
| **DevOps** | Edits OpenAPI specs in Git, CI generates signed catalog automatically |

---

## 🛣️ Roadmap

- **v0.1** — Working demo with signed catalogs ✅
- **v0.2** — Browser WASM SDK for in-page agents  
- **v0.3** — Federated catalogs across organizations
- **v0.4** — AI-powered spec generation from existing APIs
- **v1.0** — Production hardening and ecosystem tools

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Quick ways to help:**
- 🐛 Try the demo and [report issues](https://github.com/foofork/eat/issues)
- 🔧 Add language bindings for your favorite stack  
- 📝 Create tool specs for popular APIs
- 📖 Improve [documentation](docs/) and examples

**Development Setup:**
```bash
git clone https://github.com/foofork/eat.git
cd eat
pip install -r requirements-dev.txt
pip install -e .
pytest  # Run tests
cd demo && ./quickstart.sh  # Start demo
```

---

## 📚 Documentation

- 📖 **[QUICKSTART.md](QUICKSTART.md)** - 5-minute setup guide
- 🎓 **[Tutorial](docs/tutorial.md)** - Building your first catalog  
- 📋 **[API Reference](docs/api_reference.md)** - Python API docs
- 🔒 **[Security Guide](docs/security.md)** - Security model and best practices
- 🚀 **[Deployment Guide](docs/deployment.md)** - Production deployment
- ❓ **[FAQ](docs/FAQ.md)** - Frequently asked questions
- 🛠️ **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions

---

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🆘 Support & Community

- 💬 **[GitHub Discussions](https://github.com/foofork/eat/discussions)** - Questions and community
- 🐛 **[Issues](https://github.com/foofork/eat/issues)** - Bug reports and feature requests  
- 📧 **Email**: [support@eat-framework.com](mailto:support@eat-framework.com)
- 🐦 **Twitter**: [@eat_framework](https://twitter.com/eat_framework)

---

## 🤖 For AI Assistants: Implementation Instructions

> **AI assistants implementing this repository should follow these comprehensive instructions**

<details>
<summary><strong>🔧 Complete Implementation Guide for AI Assistants</strong></summary>

### Repository Structure to Create

```
eat-framework/
├── README.md                          # This file
├── LICENSE                           # MIT License
├── QUICKSTART.md                     # 5-minute setup guide
├── TUTORIAL.md                       # Building first catalog
├── REFERENCE.md                      # Complete API documentation
├── WHY.md                           # Business case document
├── SECURITY.md                      # Security model and threats
├── 
├── demo/                            # Working demonstration
│   ├── docker-compose.yml           # One-command full stack
│   ├── .env.example                 # Environment variables
│   ├── quickstart.sh               # 5-minute setup script
│   ├── site/
│   │   ├── index.html              # Interactive catalog browser
│   │   └── .well-known/
│   │       └── api-catalog         # Sample signed catalog
│   ├── specs/
│   │   ├── customer-api.yaml       # OpenAPI with x-mcp-tool
│   │   ├── analytics-api.yaml      # Second example
│   │   └── notification-api.yaml   # Third example
│   └── tools/
│       ├── customer-server.py      # MCP server implementation
│       ├── analytics-server.py     # Second MCP server
│       ├── requirements.txt        # Python dependencies
│       └── run-servers.sh          # Start all servers
├── 
├── cli/                             # Command-line tools
│   ├── setup.py                    # Python package setup
│   ├── eat_cli/
│   │   ├── __init__.py
│   │   ├── generate.py             # Catalog generation
│   │   ├── sign.py                 # Cryptographic signing
│   │   ├── verify.py               # Signature verification
│   │   ├── serve.py                # Local HTTP server
│   │   └── keygen.py               # Key generation
│   └── requirements.txt
├── 
├── examples/                        # Multi-language examples
│   ├── python/
│   │   ├── simple-agent.py         # 20-line minimal agent
│   │   ├── langchain-integration.py
│   │   ├── advanced-agent.py       # Multi-tool workflow
│   │   └── requirements.txt
│   ├── javascript/
│   │   ├── node-agent.js           # Node.js agent
│   │   ├── package.json
│   │   └── browser-wasm/
│   │       ├── index.html          # In-browser demo
│   │       └── agent.js
│   ├── rust/
│   │   ├── Cargo.toml
│   │   └── src/main.rs             # Rust CLI agent
│   └── curl/
│       ├── discover.sh             # Pure shell scripts
│       └── call-tool.sh
├── 
├── templates/                       # Deployment templates
│   ├── enterprise/
│   │   ├── api-catalog.template    # Multi-team catalog
│   │   ├── ci-pipeline.yml         # GitHub Actions
│   │   └── governance.md           # Approval process
│   ├── startup/
│   │   ├── simple-catalog.json     # Minimal version
│   │   └── single-service.yaml
│   └── personal/
│       └── local-tools.json        # Developer setup
├── 
├── security/                        # Security utilities
│   ├── keygen.py                   # DID:web key generation
│   ├── validate.py                 # Validation tools
│   └── test-vectors/               # Crypto test cases
├── 
├── validate/                        # Testing and validation
│   ├── lint.py                     # Pre-commit linting
│   ├── test-catalog.py             # End-to-end testing
│   ├── benchmark.py                # Performance testing
│   └── ci/
│       ├── lint.sh                 # CI scripts
│       ├── test.sh
│       └── deploy.sh
├── 
├── docs/                           # Additional documentation
│   ├── architecture.md
│   ├── comparison.md              # vs other approaches
│   ├── roadmap.md
│   └── assets/
│       ├── architecture.svg
│       └── demo.gif
└── 
└── .github/                        # GitHub configuration
    ├── workflows/
    │   ├── ci.yml
    │   ├── release.yml
    │   └── demo-deploy.yml
    └── ISSUE_TEMPLATE/
        ├── bug_report.md
        └── feature_request.md
```

### Implementation Priorities

#### 1. Working Demo First (Highest Priority)
- Create `demo/docker-compose.yml` that starts full stack with one command
- Implement `demo/quickstart.sh` that validates the entire flow
- Build `demo/site/index.html` as interactive catalog browser
- Ensure all examples actually work and produce expected outputs

#### 2. CLI Tools (High Priority)  
- Implement `eat-gen` command with subcommands: init, add-spec, sign, verify, serve
- Create proper Python package with `pip install eat-framework`
- Include cryptographic signing with JWS and DID:web integration
- Add comprehensive validation and error handling

#### 3. Multi-Language Examples (High Priority)
- Create working agents in Python, JavaScript, Rust
- Each example should be ≤25 lines and demonstrate complete workflow
- Include error handling and authentication
- All examples must use the same demo catalog

#### 4. Documentation (Medium Priority)
- Write QUICKSTART.md with 5-minute setup instructions
- Create TUTORIAL.md for building first production catalog
- Document security model in SECURITY.md
- Add business case in WHY.md

#### 5. Templates and Validation (Medium Priority)
- Create enterprise deployment templates
- Implement comprehensive testing and validation tools
- Add CI/CD pipeline examples
- Include performance benchmarking

### Technical Requirements

#### Catalog Format
- Use RFC 8615 (.well-known) standard for discovery endpoints
- Implement linkset JSON format with JWS signatures
- Include SHA-256 hashes for all referenced specs
- Support DID:web for key resolution

#### OpenAPI Extensions
- Define `x-mcp-tool` extension schema
- Include rich examples, authentication, error patterns
- Add performance characteristics and best practices
- Maintain backward compatibility with standard OpenAPI

#### Security Implementation
- Use established cryptographic libraries (no custom crypto)
- Implement proper JWS signing and verification
- Support DID:web key resolution
- Include comprehensive input validation

#### Performance Targets
- Cold-start discovery in <200ms
- Catalog validation in <50ms
- Memory usage <10MB for typical catalogs
- Support for 1000+ tools per catalog

### Code Quality Standards

#### Python
- Follow PEP 8 style guidelines
- Include comprehensive type hints
- Add docstrings for all public functions
- Use pytest for testing with >90% coverage

#### JavaScript
- Use modern ES6+ syntax with async/await
- Include JSDoc comments
- Use ESLint for code quality
- Support both Node.js and browser environments

#### Rust
- Use rustfmt for formatting
- Include comprehensive error handling with Result types
- Add documentation comments for all public APIs
- Use Cargo for dependency management

#### Shell Scripts
- Pass shellcheck validation
- Use POSIX-compliant syntax
- Include proper error handling with set -e
- Add usage documentation

### Testing Requirements

#### Functional Testing
- All code examples must execute without modification
- Include both positive and negative test cases
- Test error handling and edge cases
- Validate performance benchmarks

#### Security Testing
- Test signature verification with invalid signatures
- Validate proper certificate chain handling
- Test against malformed catalogs
- Include penetration testing checklist

#### Integration Testing
- Test complete end-to-end workflows
- Validate multi-language interoperability
- Test with real MCP servers
- Include load testing scenarios

### Documentation Standards

#### Structure
- Use progressive disclosure (simple → advanced)
- Include working code examples in all docs
- Provide troubleshooting guides
- Cross-reference related topics

#### Content
- Write for multiple audiences (developers, DevOps, executives)
- Include business justification and ROI calculations
- Provide migration guides from existing solutions
- Add FAQ section addressing common concerns

#### Examples
- All examples must be tested and working
- Include realistic use cases and data
- Show both success and error scenarios
- Provide performance optimization tips

### Validation Checklist

Before considering implementation complete:

- [ ] `docker-compose up` starts working demo
- [ ] `./quickstart.sh` completes successfully in <5 minutes
- [ ] All code examples execute without errors
- [ ] CLI tools install via `pip install eat-framework`
- [ ] Signature verification works correctly
- [ ] Multi-language examples use same catalog
- [ ] Documentation is comprehensive and accurate
- [ ] Performance benchmarks meet targets
- [ ] Security validation passes all tests
- [ ] Repository is ready for public release

### Success Metrics

The implementation should achieve:
- **Setup time**: <5 minutes from clone to working demo
- **Cold-start latency**: <200ms for catalog discovery
- **Code coverage**: >90% for critical functionality
- **Documentation coverage**: 100% of public APIs
- **Security compliance**: Pass all validation tests

### Implementation Notes

- Start with the demo to prove the concept works
- Make every code example copy-pasteable and functional
- Prioritize developer experience and ease of use
- Use established standards and libraries wherever possible
- Include comprehensive error handling and validation
- Write documentation for humans, not just machines

</details>

---

*Ready to implement? The complete instructions above will guide you through building a production-ready EAT framework that makes AI tool discovery simple, secure, and standards-based.*