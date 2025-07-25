# EAT Framework - Ephemeral Agent Toolkit

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**One-hop tool discovery for AI agents with secure, signed catalogs.**

The EAT Framework provides a standardized way for AI agents to discover and use tools through secure, cryptographically-signed catalogs. Built on open standards (OpenAPI, JWS, MCP), it enables agents to find and execute tools without prior configuration.

## 🚀 Quick Start

### 1. Try the Demo (5 minutes)

```bash
# Clone and start the demo
git clone <repository-url>
cd eat-framework/demo
./quickstart.sh

# Visit the interactive catalog browser
open http://localhost:8000
```

### 2. Install the Package

```bash
pip install eat-framework
```

### 3. Use in Your Agent

```python
import asyncio
from eat import Catalog

async def main():
    # Discover tools
    catalog = Catalog("http://localhost:8000/.well-known/api-catalog")
    await catalog.fetch()
    
    # Find and use a tool
    tool = catalog.find(capability="customer")[0]
    result = await tool.call(customer_id=12345)
    
    print(f"Customer: {result['name']} ({result['email']})")

asyncio.run(main())
```

## 🏗️ Architecture

The EAT Framework consists of three main components:

### 1. **Tool Catalogs** 📋
- **Discoverable**: Published at `/.well-known/api-catalog`
- **Secure**: Cryptographically signed with JWS
- **Standard**: Based on OpenAPI 3.0 with `x-mcp-tool` extensions

### 2. **Python Library** 🐍
- **Simple API**: `Catalog`, `Tool`, `MCPClient` classes
- **Secure**: Built-in signature verification
- **Async**: Full async/await support

### 3. **MCP Servers** 🖥️
- **Compatible**: Implements Model Context Protocol
- **Realistic**: Full business logic, not just echo responses
- **Production-ready**: Authentication, error handling, logging

## 📁 Repository Structure

```
eat-framework/
├── eat/                        # Python package
│   ├── discovery.py           # Catalog and tool discovery
│   ├── mcp_client.py          # MCP protocol client
│   ├── security.py            # JWS signing and verification
│   └── cli/                   # Command-line tools
├── demo/                      # Complete working demonstration
│   ├── site/                  # Interactive catalog browser
│   ├── servers/               # 3 realistic MCP servers
│   ├── agents/                # Example AI agents
│   └── docker-compose.yml     # One-command deployment
├── examples/                  # Usage examples
├── tests/                     # Comprehensive test suite
└── docs/                      # Documentation
```

## 🛠️ Features

### Core Features
- ✅ **One-hop Discovery**: Find tools without prior configuration
- ✅ **Cryptographic Security**: JWS signatures with DID:web key resolution
- ✅ **Content Integrity**: SHA-256 verification of all resources
- ✅ **Standards-Based**: OpenAPI 3.0, RFC 8615, MCP compatibility
- ✅ **Async/Await**: Full asynchronous operation support

### Developer Tools
- ✅ **CLI Tools**: `eat-gen` to generate catalogs, `eat-serve` for development
- ✅ **Interactive Browser**: Visual catalog exploration with live examples
- ✅ **Auto-generated Agents**: Download ready-to-run agent code
- ✅ **Docker Support**: Complete containerized demo environment

### Production Ready
- ✅ **Comprehensive Tests**: >90% test coverage with pytest
- ✅ **Error Handling**: Robust error handling and recovery
- ✅ **Performance**: <200ms cold-start discovery, <50ms validation
- ✅ **Security**: Best practices for key management and verification

## 🎯 Demo Components

The included demo showcases three realistic MCP servers:

### 1. Customer Management API (`localhost:3001`)
- **CRUD operations** for customer data
- **Authentication** with JWT tokens
- **SQLite database** with sample data
- **Real business logic** with validation

### 2. Analytics API (`localhost:3002`)
- **Data aggregation** and reporting
- **Customer analytics** with metrics
- **Trend analysis** across time periods
- **Report generation** in multiple formats

### 3. Notifications API (`localhost:3003`)
- **Email notifications** via SMTP
- **Slack integration** with webhooks
- **Bulk processing** with batching
- **Delivery tracking** and status reporting

## 📚 Usage Examples

### Basic Tool Discovery

```python
from eat import Catalog

# Initialize catalog
catalog = Catalog("https://api.example.com/.well-known/api-catalog")
await catalog.fetch()
await catalog.verify()  # Verify signatures

# Find tools by capability
customer_tools = catalog.find(capability="customer")
analytics_tools = catalog.find(capability="analytics")

# Get specific tool
user_tool = catalog.get_tool("get_user")
```

### Multi-Tool Workflows

```python
# Chain multiple tools together
customers = []
for customer_id in [1, 2, 3]:
    customer = await customer_tool.call(customer_id=customer_id)
    customers.append(customer)

# Generate analytics
analytics = await analytics_tool.call(
    customer_ids=[c["id"] for c in customers],
    metrics=["engagement", "revenue"]
)

# Create report
report = await report_tool.call(
    template="executive",
    data=analytics,
    format="pdf"
)

# Send notification
await notification_tool.call(
    to="manager@company.com",
    subject="Weekly Customer Report",
    body=f"Report generated for {len(customers)} customers"
)
```

### Error Handling

```python
try:
    catalog = Catalog(catalog_url, verify_signatures=True)
    await catalog.fetch()
    
    if not await catalog.verify():
        raise SecurityError("Catalog signature verification failed")
    
    tool = catalog.get_tool("customer_lookup")
    result = await tool.call(customer_id=12345)
    
except SecurityError as e:
    print(f"Security error: {e}")
except MCPError as e:
    print(f"Tool execution error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## 🔧 CLI Tools

### Generate Signed Catalogs

```bash
# Generate catalog from OpenAPI specs
eat-gen ./specs --output catalog.json

# Sign with private key
eat-gen ./specs --output catalog.jwt --sign --private-key key.pem
```

### Development Server

```bash
# Serve catalog locally
eat-serve --port 8000

# With custom directory
eat-serve ./my-catalog --port 9000
```

## 🔐 Security Model

### Cryptographic Signatures
- **JWS (JSON Web Signature)** using RS256 algorithm
- **DID:web** key resolution for distributed trust
- **Key rotation** support with key identifiers

### Content Integrity
- **SHA-256 hashes** for all referenced content
- **Verification** of downloaded specifications
- **Tamper detection** for catalog modifications

### Best Practices
- **Key management** with secure storage
- **Regular rotation** of signing keys
- **Access control** for catalog publishing
- **Audit logging** of all operations

## 📊 Performance

The EAT Framework is designed for production use with excellent performance:

- **Cold-start discovery**: <200ms
- **Catalog validation**: <50ms
- **Memory usage**: <10MB for typical catalogs
- **Concurrent tools**: 100+ simultaneous calls

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all tests with coverage
pytest tests/ --cov=eat --cov-report=html

# Run specific test categories
pytest -m "not integration"  # Unit tests only
pytest -m integration        # Integration tests only
```

## 📖 Documentation

- **[Quick Start Guide](QUICKSTART.md)** - Get running in 5 minutes
- **[API Reference](docs/api_reference.md)** - Complete Python API documentation
- **[Security Guide](docs/security.md)** - Security model and best practices
- **[Deployment Guide](docs/deployment.md)** - Production deployment instructions
- **[Tutorial](docs/tutorial.md)** - Building your first catalog

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd eat-framework

# Install development dependencies
pip install -r requirements-dev.txt
pip install -e .

# Run tests
pytest

# Start demo environment
cd demo && ./quickstart.sh
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAPI Initiative** for the OpenAPI specification
- **MCP Working Group** for the Model Context Protocol
- **DID:web** specification for decentralized key resolution
- **JWT/JWS** standards for secure token format

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/eat-framework/eat-framework/issues)
- **Discussions**: [GitHub Discussions](https://github.com/eat-framework/eat-framework/discussions)

---

**🚀 Ready to build AI agents that can discover and use tools autonomously?** 

Start with the [Quick Start Guide](QUICKSTART.md) or try the [5-minute demo](demo/)!