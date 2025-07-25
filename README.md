# EAT Framework - Ephemeral Agent Toolkit

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**One-hop tool discovery for AI agents with secure, signed catalogs.**

The EAT Framework provides a standardized way for AI agents to discover and use tools through secure, cryptographically-signed catalogs. Built on open standards (OpenAPI, JWS, MCP), it enables agents to find and execute tools without prior configuration.

## 🚀 Quick Start

### 1. Try the Demo (5 minutes)

```bash
# Clone the repository
git clone https://github.com/foofork/eat.git
cd eat/demo
./quickstart.sh

# Visit the interactive catalog browser
open http://localhost:8000
```

### 2. Install the Package

```bash
# Install in development mode
pip install -e .
```

### 3. Use in Your Agent

```python
import asyncio
from eat import Catalog

async def main():
    # Discover tools from local demo
    catalog = Catalog("http://localhost:8000/.well-known/api-catalog", verify_signatures=False)
    await catalog.fetch()
    
    # Find available tools
    tools = catalog.tools
    print(f"Found {len(tools)} tools")
    
    # Example: use a customer tool if available
    customer_tools = catalog.find(capability="customer")
    if customer_tools:
        tool = customer_tools[0]
        try:
            result = await tool.call(customer_id=1)
            print(f"Customer: {result.get('name', 'Unknown')}")
        except Exception as e:
            print(f"Tool call failed: {e}")

asyncio.run(main())
```

## 🏗️ What's Included

This initial release includes:

### ✅ Core Python Package (`eat/`)
- **`discovery.py`** - Catalog fetching and tool discovery
- **`mcp_client.py`** - MCP protocol client implementation
- **`security.py`** - JWS signing and verification framework
- **`cli/`** - Command-line tools (`eat-gen`, `eat-serve`)

### ✅ Working Demo (`demo/`)
- **3 MCP Servers**: Customer management, analytics, and notifications
- **Interactive Browser**: Visual catalog exploration at `demo/site/index.html`
- **Docker Setup**: One-command deployment with `docker-compose.yml`
- **Example Agents**: Simple and multi-tool workflow examples

### ✅ Development Tools
- **Test Suite**: Comprehensive tests in `tests/` directory
- **Examples**: Ready-to-run examples in `examples/`
- **CLI Tools**: Generate catalogs and serve locally

### ⚠️ Implementation Status

**What Works Now:**
- ✅ Tool discovery from catalogs
- ✅ MCP protocol client
- ✅ Interactive catalog browser
- ✅ Demo MCP servers with realistic business logic
- ✅ Basic CLI tools for development
- ✅ Comprehensive test framework

**What's Planned/In Progress:**
- 🔄 Full JWS signature verification (framework exists)
- 🔄 DID:web key resolution (basic structure in place)
- 🔄 Production-ready security features
- 🔄 Complete CLI tool functionality
- 🔄 Comprehensive documentation

## 📁 Repository Structure

```
eat/
├── README.md                   # This file
├── QUICKSTART.md              # 5-minute setup guide
├── setup.py                   # Python package configuration
├── eat/                       # Core Python package
│   ├── discovery.py          # Catalog and tool discovery
│   ├── mcp_client.py         # MCP protocol client
│   ├── security.py           # Security framework
│   └── cli/                  # Command-line tools
├── demo/                     # Working demonstration
│   ├── quickstart.sh         # One-command setup
│   ├── site/index.html       # Interactive catalog browser
│   ├── servers/              # 3 MCP servers
│   └── agents/               # Example AI agents
├── examples/                 # Usage examples
└── tests/                    # Test suite
```

## 🎯 Demo Components

The demo showcases three realistic MCP servers:

### 1. Customer Management (`localhost:3001`)
- CRUD operations for customer data
- JWT authentication
- SQLite database with sample data

### 2. Analytics (`localhost:3002`)
- Customer analytics and reporting
- Data aggregation
- Multiple output formats

### 3. Notifications (`localhost:3003`)
- Email and webhook notifications
- Bulk processing
- Delivery tracking

## 📚 Usage Examples

### Basic Tool Discovery

```python
from eat import Catalog

# Initialize catalog (signature verification disabled for demo)
catalog = Catalog("http://localhost:8000/.well-known/api-catalog", verify_signatures=False)
await catalog.fetch()

# Find tools by capability
customer_tools = catalog.find(capability="customer")
analytics_tools = catalog.find(capability="analytics")

# Get specific tool
customer_tool = catalog.get_tool("get_customer")
```

### Multi-Tool Workflow

See `demo/agents/multi_tool_agent.py` for a complete example of:
- Sequential tool calls
- Error handling and fallbacks
- Data flow between different MCP servers
- Real-world workflow patterns

## 🔧 CLI Tools

### Generate Catalogs

```bash
# Generate catalog from OpenAPI specs (basic functionality)
python -m eat.cli.main generate specs/ --output catalog.json
```

### Development Server

```bash
# Serve catalog locally
python -m eat.cli.main serve --port 8000
```

## 🧪 Testing

Run the test suite:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/ -v
```

## 🚀 Getting Started

1. **Clone and setup**:
   ```bash
   git clone https://github.com/foofork/eat.git
   cd eat
   pip install -e .
   ```

2. **Try the demo**:
   ```bash
   cd demo
   ./quickstart.sh
   ```

3. **Explore interactively**:
   - Visit http://localhost:8000 for the catalog browser
   - Run `python agents/simple_agent.py` for basic discovery
   - Run `python agents/multi_tool_agent.py` for advanced workflows

## 🤝 Contributing

This is an initial implementation with room for growth! Areas where contributions are welcome:

- **Security**: Complete JWS signature verification
- **CLI Tools**: Enhanced catalog generation and management
- **Documentation**: API reference and tutorials  
- **MCP Servers**: Additional realistic server examples
- **Testing**: Expand test coverage and integration tests

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- **OpenAPI Initiative** for the OpenAPI specification
- **MCP Working Group** for the Model Context Protocol
- Built with guidance from the ROADMAP-INIT.md specification

---

**🚀 Ready to try AI tool discovery?**

Start with: `cd demo && ./quickstart.sh`