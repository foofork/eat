# EAT Framework Demo

This directory contains a complete working demonstration of the EAT (Enhanced Agent Tools) framework with three MCP servers, an interactive catalog browser, and example agents.

## Quick Start

```bash
# Start the complete demo environment
./quickstart.sh

# The demo will be available at:
# - Catalog Browser: http://localhost:8000
# - API Catalog: http://localhost:8000/.well-known/api-catalog
# - Customer API: http://localhost:3001
# - Analytics API: http://localhost:3002  
# - Notifications API: http://localhost:3003
```

## What's Included

### 🏗️ Infrastructure
- **3 MCP Servers**: Customer management, analytics, and notifications
- **Nginx Catalog Server**: Serves the tool catalog and web interface
- **Docker Compose**: One-command setup and teardown

### 📋 API Catalog
- **13 Tools**: Complete business application toolkit
- **Capabilities**: customer-management, analytics, notifications, reporting
- **Examples**: Real input/output examples for each tool
- **OpenAPI Specs**: Full API documentation with x-mcp-tool extensions

### 🤖 Example Agents
- **Simple Agent**: Basic tool discovery and execution
- **Multi-Tool Agent**: Complex workflow spanning multiple services

### 🌐 Interactive Browser
- **Visual Catalog**: Browse all available tools
- **Live Examples**: See real tool parameters and responses
- **Agent Code Generator**: Download ready-to-use Python agents

## Directory Structure

```
demo/
├── quickstart.sh           # Main setup script
├── docker-compose.yml      # Service orchestration
├── nginx.conf             # Web server configuration
├── site/                  # Static web content
│   ├── index.html         # Interactive catalog browser
│   ├── .well-known/       # EAT catalog endpoint
│   │   └── api-catalog    # Main tool catalog
│   └── specs/             # OpenAPI specifications
│       ├── customer-api.yaml
│       ├── analytics-api.yaml
│       └── notifications-api.yaml
├── servers/               # MCP server implementations
│   ├── customer_server.py
│   ├── analytics_server.py
│   ├── notifications_server.py
│   ├── requirements.txt
│   └── Dockerfile
└── agents/                # Example agent implementations
    ├── simple_agent.py
    ├── multi_tool_agent.py
    └── requirements.txt
```

## Available Tools

### 👥 Customer Management (Port 3001)
- `list_customers` - Paginated customer listing
- `get_customer` - Get customer details by ID
- `create_customer` - Create new customer records
- `update_customer` - Update customer information
- `delete_customer` - Remove customer records

### 📊 Analytics & Reporting (Port 3002)
- `get_dashboard_metrics` - Key business metrics
- `generate_analytics_report` - Custom report generation
- `track_custom_metric` - Business metric tracking

### 📧 Notifications (Port 3003)
- `send_notification` - Single notifications (email/SMS/webhook)
- `send_bulk_notifications` - Batch notification sending
- `get_notification_status` - Delivery status tracking
- `list_notification_templates` - Available templates

## Using the Demo

### 1. Browse Tools Visually

Visit http://localhost:8000 to see the interactive catalog:

- **Filter by capability**: customer-management, analytics, notifications
- **View examples**: See real input/output for each tool
- **Generate agents**: Download Python code for any tool
- **Test tools**: Live tool execution examples

### 2. Run Example Agents

```bash
cd agents

# Basic tool discovery
python simple_agent.py

# Complex multi-service workflow
python multi_tool_agent.py
```

### 3. Call Tools Directly

```bash
# List customers
curl -X POST http://localhost:3001 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"list_customers","arguments":{"limit":5}}}'

# Get dashboard metrics
curl -X POST http://localhost:3002 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"2","method":"tools/call","params":{"name":"get_dashboard_metrics","arguments":{"timeframe":"7d"}}}'

# Send a notification
curl -X POST http://localhost:3003 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"3","method":"tools/call","params":{"name":"send_notification","arguments":{"type":"email","recipient":"test@example.com","subject":"Test","message":"Hello from EAT!"}}}'
```

### 4. Discover Tools Programmatically

```python
import asyncio
from eat import Catalog

async def discover_tools():
    # Load catalog
    catalog = Catalog("http://localhost:8000/.well-known/api-catalog")
    await catalog.fetch()
    
    # Find customer tools
    customer_tools = catalog.find(capability="customer-management")
    print(f"Found {len(customer_tools)} customer tools")
    
    # Use a tool
    if customer_tools:
        tool = customer_tools[0]
        result = await tool.call(limit=3)
        print(f"Result: {result}")

asyncio.run(discover_tools())
```

## Development

### Adding New Tools

1. **Create OpenAPI Spec** with x-mcp-tool extension:
```yaml
paths:
  /my-endpoint:
    post:
      operationId: my_tool
      x-mcp-tool:
        server_url: http://localhost:3004
        capabilities: ["my-capability"]
        examples:
          - description: "Example usage"
            input: {"param": "value"}
            output: {"result": "success"}
```

2. **Update Catalog** in `site/.well-known/api-catalog`

3. **Implement MCP Server** following the existing patterns

4. **Add to Docker Compose** and update nginx routing

### Testing New Configurations

```bash
# Restart services
docker-compose down
./quickstart.sh

# Check health
curl http://localhost:8000/.well-known/api-catalog
curl -X POST http://localhost:3001 -d '{"jsonrpc":"2.0","id":"1","method":"tools/list"}'

# Run agents
python agents/simple_agent.py
```

## Troubleshooting

### Services Won't Start
```bash
# Check Docker logs
docker-compose logs

# Verify ports aren't in use
lsof -i :8000 -i :3001 -i :3002 -i :3003

# Clean restart
docker-compose down --volumes
./quickstart.sh
```

### Tools Not Working
```bash
# Test MCP servers directly
curl -X POST http://localhost:3001 -d '{"jsonrpc":"2.0","id":"1","method":"tools/list"}'

# Check nginx serving
curl http://localhost:8000/.well-known/api-catalog

# Verify specs are accessible
curl http://localhost:8000/specs/customer-api.yaml
```

### Agent Errors
```bash
# Check Python dependencies
cd agents
pip install -r requirements.txt

# Verify catalog access
python -c "import requests; print(requests.get('http://localhost:8000/.well-known/api-catalog').status_code)"
```

## Next Steps

- **Build Custom Agents**: Use the catalog to create domain-specific AI agents
- **Extend APIs**: Add new tools and capabilities to the servers
- **Production Deploy**: Use the Docker Compose setup as a foundation
- **Integrate**: Connect to real databases and external services

## Learn More

- [EAT Protocol Specification](../PROTOCOL.md)
- [Implementation Guide](../IMPLEMENTATION.md) 
- [Quick Start Tutorial](../QUICKSTART.md)
- [Example Implementations](../examples/)

The demo provides a complete, working EAT environment that you can modify and extend for your own use cases.