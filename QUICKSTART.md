# 🚀 EAT Framework - 5-Minute Quickstart

Get the EAT Framework running in under 5 minutes with this step-by-step guide.

## Prerequisites

Before you begin, ensure you have:

- **Docker & Docker Compose** - [Install Docker](https://docs.docker.com/get-docker/)
- **Python 3.8+** - [Install Python](https://www.python.org/downloads/)
- **Git** - [Install Git](https://git-scm.com/downloads)

## Step 1: Get the Code

```bash
# Clone the repository
git clone <repository-url>
cd eat-framework
```

## Step 2: Start the Demo Environment

The demo includes everything you need: 3 MCP servers, an interactive catalog browser, and example agents.

```bash
# Navigate to demo directory
cd demo

# Start all services (this may take 2-3 minutes on first run)
./quickstart.sh
```

You should see output like:
```
🚀 Starting EAT Framework Demo...
=================================
🔍 Checking dependencies...
✅ Dependencies check passed
🏗️  Building and starting services...
⏳ Waiting for services to start...
🔍 Running health checks...
✅ Catalog server is running
✅ MCP server on port 3001 is running
✅ MCP server on port 3002 is running
✅ MCP server on port 3003 is running
🎉 EAT Framework Demo is ready!
```

## Step 3: Explore the Interactive Catalog

Open your browser and visit: **http://localhost:8000**

You'll see the interactive catalog browser with:
- **Available tools** from all MCP servers
- **Capability filtering** (customer, analytics, notifications)
- **Live examples** with actual parameter schemas
- **Agent code generation** - download ready-to-run Python code

Try these features:
1. **Browse Tools**: Explore the customer, analytics, and notification tools
2. **Filter by Capability**: Use the dropdown to filter tools
3. **Search**: Try searching for "customer" or "report"
4. **Generate Agent Code**: Click "Generate Agent Code" on any tool

## Step 4: Run Your First Agent

The demo includes two example agents you can run immediately:

### Simple Agent (Basic Discovery)

```bash
# From the demo directory
cd agents
python3 simple_agent.py
```

Expected output:
```
🚀 Starting Simple EAT Agent Demo
========================================
🔍 Discovering tools from catalog...
✅ Found 9 tools in catalog
🔧 Using tool: get_customer
📝 Description: Retrieve customer information by ID
📞 Calling tool with sample data...
✅ Tool call successful!
📊 Result: {'id': 1, 'name': 'John Smith', 'email': 'john.smith@example.com'}
```

### Multi-Tool Agent (Advanced Workflow)

```bash
# Advanced agent that chains multiple tools together
python3 multi_tool_agent.py
```

This agent demonstrates:
- **Sequential tool calls** (get customers → analyze → report → notify)
- **Error handling** and graceful fallbacks
- **Data flow** between different MCP servers
- **Real-world workflow** patterns

## Step 5: Install the Python Package

```bash
# Go back to the root directory
cd ..

# Install the EAT Framework package
pip install -e .
```

Now you can use EAT Framework in any Python project:

```python
import asyncio
from eat import Catalog

async def main():
    # Discover tools
    catalog = Catalog("http://localhost:8000/.well-known/api-catalog")
    await catalog.fetch()
    
    # Find customer tools
    customer_tools = catalog.find(capability="customer")
    print(f"Found {len(customer_tools)} customer tools")
    
    # Use a tool
    if customer_tools:
        tool = customer_tools[0]
        try:
            result = await tool.call(customer_id=1)
            print(f"Customer: {result.get('name', 'Unknown')}")
        except Exception as e:
            print(f"Tool call failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Step 6: Create Your Own Catalog

### 1. Create OpenAPI Specifications

Create a `specs/` directory with OpenAPI files that include `x-mcp-tool` extensions:

```yaml
# specs/my-api.yaml
openapi: 3.0.0
info:
  title: My API
  version: 1.0.0
servers:
  - url: http://localhost:3000
paths:
  /tasks:
    get:
      operationId: list_tasks
      summary: List all tasks
      description: Retrieve a list of all tasks
      x-mcp-tool:
        server_url: http://localhost:3000
        capabilities: ["task-management"]
        examples:
          - description: "List all tasks"
            input: {}
            output:
              tasks: [{"id": 1, "title": "Sample task"}]
      responses:
        '200':
          description: List of tasks
```

### 2. Generate a Catalog

```bash
# Use the CLI tool to generate a catalog
eat-gen specs/ --output my-catalog.json

# Or serve it for development
eat-serve specs/ --port 9000
```

### 3. Create Your Agent

```python
# my_agent.py
import asyncio
from eat import Catalog

async def main():
    catalog = Catalog("http://localhost:9000/.well-known/api-catalog")
    await catalog.fetch()
    
    # Use your custom tools
    task_tools = catalog.find(capability="task-management")
    if task_tools:
        tasks = await task_tools[0].call()
        print(f"Found {len(tasks.get('tasks', []))} tasks")

asyncio.run(main())
```

## 🎯 What You've Accomplished

In just 5 minutes, you've:

✅ **Set up a complete EAT environment** with 3 MCP servers  
✅ **Explored the interactive catalog browser** with live tools  
✅ **Run example agents** that discover and use tools automatically  
✅ **Installed the Python package** for your own projects  
✅ **Created your first custom catalog** with OpenAPI specs  

## 🚀 Next Steps

Now that you have EAT Framework running, explore these advanced features:

### Security & Production
- **[Security Guide](docs/security.md)** - Set up JWS signing and verification
- **[Deployment Guide](docs/deployment.md)** - Deploy to production environments
- **[Authentication](docs/authentication.md)** - Secure your MCP servers

### Development
- **[API Reference](docs/api_reference.md)** - Complete Python API documentation
- **[Tutorial](docs/tutorial.md)** - Build more complex agents and workflows
- **[MCP Server Guide](docs/mcp_servers.md)** - Create your own MCP servers

### Integration
- **[GitHub Actions](docs/github_actions.md)** - Automate catalog generation
- **[CI/CD Integration](docs/cicd.md)** - Include EAT in your deployment pipeline
- **[Monitoring](docs/monitoring.md)** - Monitor catalog usage and performance

## 🆘 Troubleshooting

### Demo Won't Start
```bash
# Check Docker is running
docker --version
docker-compose --version

# Check ports aren't in use
lsof -i :8000 -i :3001 -i :3002 -i :3003

# Restart the demo
docker-compose down
./quickstart.sh
```

### Tools Not Working
```bash
# Check MCP server logs
docker-compose logs customer-server
docker-compose logs analytics-server
docker-compose logs notifications-server

# Test catalog directly
curl http://localhost:8000/.well-known/api-catalog
```

### Python Import Errors
```bash
# Reinstall in development mode
pip uninstall eat-framework
pip install -e .

# Check Python path
python3 -c "import eat; print(eat.__file__)"
```

## 💬 Get Help

- **Documentation**: [docs/](docs/) directory
- **Issues**: [GitHub Issues](https://github.com/eat-framework/eat-framework/issues)
- **Examples**: [examples/](examples/) directory
- **Tests**: Run `pytest tests/` to see more usage patterns

---

**🎉 Congratulations!** You now have a working EAT Framework installation. 

Ready to build AI agents that can discover and use tools autonomously? Check out the [Tutorial](docs/tutorial.md) for your next project!