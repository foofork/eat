#!/bin/bash

# EAT Framework Quick Start Script
# This script sets up and runs the complete EAT demo environment

set -e

echo "🚀 Starting EAT Framework Demo..."
echo "================================="

# Check dependencies
echo "🔍 Checking dependencies..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is required but not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Dependencies check passed"

# Build and start services
echo ""
echo "🏗️  Building and starting services..."
docker-compose down --remove-orphans 2>/dev/null || true
docker-compose up -d --build

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Health checks
echo ""
echo "🔍 Running health checks..."

# Check catalog server
if curl -f -s http://localhost:8000/.well-known/api-catalog > /dev/null; then
    echo "✅ Catalog server is running"
else
    echo "❌ Catalog server failed to start"
    docker-compose logs catalog-server
    exit 1
fi

# Check MCP servers
for port in 3001 3002 3003; do
    if curl -f -s http://localhost:$port/health > /dev/null 2>&1; then
        echo "✅ MCP server on port $port is running"
    else
        echo "⚠️  MCP server on port $port may not be ready yet"
    fi
done

# Test tool discovery
echo ""
echo "🧪 Testing tool discovery..."
cd agents

if python -c "
import sys
sys.path.insert(0, '../../')
import asyncio
from eat import Catalog

async def test():
    catalog = Catalog('http://localhost:8000/.well-known/api-catalog')
    await catalog.fetch()
    print(f'Discovered {len(catalog.tools)} tools')
    return len(catalog.tools) > 0

result = asyncio.run(test())
sys.exit(0 if result else 1)
" 2>/dev/null; then
    echo "✅ Tool discovery test passed"
else
    echo "⚠️  Tool discovery test failed (this is expected if no catalog exists yet)"
fi

# Test simple agent
echo ""
echo "🤖 Testing simple agent..."
if python simple_agent.py 2>/dev/null; then
    echo "✅ Simple agent test passed"
else
    echo "⚠️  Simple agent test failed (this is expected without proper MCP servers)"
fi

cd ..

echo ""
echo "🎉 EAT Framework Demo is ready!"
echo "==============================="
echo ""
echo "📋 Available endpoints:"
echo "   • Catalog: http://localhost:8000/.well-known/api-catalog"
echo "   • Browser: http://localhost:8000"
echo "   • Customer API: http://localhost:3001"
echo "   • Analytics API: http://localhost:3002"
echo "   • Notifications API: http://localhost:3003"
echo ""
echo "🔧 Next steps:"
echo "   1. Visit http://localhost:8000 to browse available tools"
echo "   2. Run 'python agents/simple_agent.py' to test tool discovery"
echo "   3. Try the multi-tool workflow: 'python agents/multi_tool_agent.py'"
echo ""
echo "📚 Documentation:"
echo "   • README.md - Overview and setup"
echo "   • QUICKSTART.md - 5-minute tutorial"
echo "   • docs/ - Detailed documentation"
echo ""
echo "🛑 To stop the demo:"
echo "   docker-compose down"
echo ""