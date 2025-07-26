#!/bin/bash

# Basic EAT Discovery Example
# This script demonstrates the fundamental EAT discovery flow using curl

set -e  # Exit on any error

echo "🔍 EAT Discovery Example"
echo "======================="

# Configuration
CATALOG_URL="http://localhost:8080/.well-known/api-catalog"
TEMP_DIR="/tmp/eat-discovery"
mkdir -p "$TEMP_DIR"

# 1. Fetch the catalog
echo "📋 Step 1: Fetching catalog from $CATALOG_URL"
if curl -f -s -H "Accept: application/json" "$CATALOG_URL" > "$TEMP_DIR/catalog.json"; then
    echo "✅ Catalog fetched successfully"
else
    echo "❌ Failed to fetch catalog"
    exit 1
fi

# 2. Parse and display catalog info
echo ""
echo "📊 Step 2: Analyzing catalog"
CATALOG_FILE="$TEMP_DIR/catalog.json"

VERSION=$(jq -r '.version' "$CATALOG_FILE")
TITLE=$(jq -r '.metadata.title // "Untitled"' "$CATALOG_FILE")
TOOL_COUNT=$(jq '.tools | length' "$CATALOG_FILE")

echo "  📖 Title: $TITLE"
echo "  🏷️  Version: $VERSION"
echo "  🔧 Tools: $TOOL_COUNT"

# 3. List all tools
echo ""
echo "🛠️  Step 3: Available tools"
jq -r '.tools[] | "  • \(.name): \(.description)"' "$CATALOG_FILE"

# 4. Group tools by capability
echo ""
echo "🏷️  Step 4: Tools by capability"
jq -r '.tools[] | .["x-mcp-tool"].capabilities[]?' "$CATALOG_FILE" | sort -u | while read capability; do
    echo "  📂 $capability:"
    jq -r ".tools[] | select(.\"x-mcp-tool\".capabilities[]? == \"$capability\") | \"    - \(.name)\"" "$CATALOG_FILE"
done

# 5. Find MCP servers
echo ""
echo "🖥️  Step 5: MCP Servers"
jq -r '.tools[] | .["x-mcp-tool"].server_url' "$CATALOG_FILE" | sort -u | while read server_url; do
    echo "  🔗 $server_url"
    
    # Count tools for this server
    tool_count=$(jq -r ".tools[] | select(.\"x-mcp-tool\".server_url == \"$server_url\") | .name" "$CATALOG_FILE" | wc -l)
    echo "     └─ Tools: $tool_count"
done

# 6. Test connectivity to first MCP server
echo ""
echo "🔌 Step 6: Testing MCP server connectivity"
FIRST_SERVER=$(jq -r '.tools[0]["x-mcp-tool"].server_url' "$CATALOG_FILE")
echo "  Testing: $FIRST_SERVER"

if curl -f -s -X POST "$FIRST_SERVER" \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","id":"test","method":"tools/list"}' \
    > "$TEMP_DIR/tools_list.json"; then
    
    echo "  ✅ Server is responding"
    
    # Display available tools from server
    MCP_TOOL_COUNT=$(jq '.result.tools | length' "$TEMP_DIR/tools_list.json")
    echo "  📊 Server reports $MCP_TOOL_COUNT tools"
    
    echo "  📋 Server tools:"
    jq -r '.result.tools[] | "    • \(.name): \(.description)"' "$TEMP_DIR/tools_list.json"
else
    echo "  ❌ Server is not responding"
fi

# 7. Save results
echo ""
echo "💾 Step 7: Saving results"
echo "  📁 Catalog saved to: $TEMP_DIR/catalog.json"
echo "  📁 Tools list saved to: $TEMP_DIR/tools_list.json"

# 8. Generate summary
echo ""
echo "📋 Discovery Summary"
echo "=================="
cat > "$TEMP_DIR/summary.txt" << EOF
EAT Discovery Summary
Generated: $(date)

Catalog: $TITLE (v$VERSION)
Tools discovered: $TOOL_COUNT
MCP servers found: $(jq -r '.tools[] | .["x-mcp-tool"].server_url' "$CATALOG_FILE" | sort -u | wc -l)

Capabilities:
$(jq -r '.tools[] | .["x-mcp-tool"].capabilities[]?' "$CATALOG_FILE" | sort -u | sed 's/^/- /')

Tool list:
$(jq -r '.tools[] | "- \(.name): \(.description)"' "$CATALOG_FILE")
EOF

cat "$TEMP_DIR/summary.txt"
echo ""
echo "📄 Summary saved to: $TEMP_DIR/summary.txt"

echo ""
echo "🎉 Discovery completed successfully!"
echo "💡 Next steps:"
echo "   • Try calling a tool with: examples/curl/call-tool.sh"
echo "   • Run the complete workflow: examples/curl/workflow.sh"

# Cleanup option
echo ""
read -p "🗑️  Remove temporary files? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$TEMP_DIR"
    echo "✅ Cleanup completed"
else
    echo "📁 Files kept in: $TEMP_DIR"
fi