#!/bin/bash

# Tool Execution Example
# This script demonstrates calling tools via MCP protocol using curl

set -e  # Exit on any error

echo "🔧 EAT Tool Execution Example"
echo "============================="

# Configuration
CATALOG_URL="http://localhost:8080/.well-known/api-catalog"
TEMP_DIR="/tmp/eat-tool-call"
mkdir -p "$TEMP_DIR"

# Helper function to make MCP calls
make_mcp_call() {
    local server_url="$1"
    local method="$2"
    local tool_name="$3"
    local arguments="$4"
    local request_id="call-$(date +%s)"
    
    if [ "$method" = "tools/list" ]; then
        curl -f -s -X POST "$server_url" \
            -H "Content-Type: application/json" \
            -d "{\"jsonrpc\":\"2.0\",\"id\":\"$request_id\",\"method\":\"$method\"}"
    else
        curl -f -s -X POST "$server_url" \
            -H "Content-Type: application/json" \
            -d "{\"jsonrpc\":\"2.0\",\"id\":\"$request_id\",\"method\":\"$method\",\"params\":{\"name\":\"$tool_name\",\"arguments\":$arguments}}"
    fi
}

# Helper function to handle errors
handle_mcp_response() {
    local response="$1"
    local description="$2"
    
    if echo "$response" | jq -e '.error' > /dev/null; then
        echo "❌ $description failed:"
        echo "$response" | jq '.error'
        return 1
    else
        echo "✅ $description succeeded"
        echo "$response" | jq '.result'
        return 0
    fi
}

# 1. Fetch catalog
echo "📋 Step 1: Fetching catalog"
if ! curl -f -s "$CATALOG_URL" > "$TEMP_DIR/catalog.json"; then
    echo "❌ Failed to fetch catalog"
    exit 1
fi

# 2. Select a tool to call
echo ""
echo "🔧 Step 2: Selecting tool to call"
echo "Available tools:"
jq -r '.tools[] | "  \(.name): \(.description)"' "$TEMP_DIR/catalog.json"

# Use the first user management tool
TOOL_NAME=$(jq -r '.tools[] | select(.["x-mcp-tool"].capabilities[]? == "user-management") | .name' "$TEMP_DIR/catalog.json" | head -1)
SERVER_URL=$(jq -r ".tools[] | select(.name == \"$TOOL_NAME\") | .\"x-mcp-tool\".server_url" "$TEMP_DIR/catalog.json")

if [ -z "$TOOL_NAME" ] || [ "$TOOL_NAME" = "null" ]; then
    echo "⚠️  No user management tools found, using first available tool"
    TOOL_NAME=$(jq -r '.tools[0].name' "$TEMP_DIR/catalog.json")
    SERVER_URL=$(jq -r '.tools[0]["x-mcp-tool"].server_url' "$TEMP_DIR/catalog.json")
fi

echo "🎯 Selected tool: $TOOL_NAME"
echo "🔗 Server URL: $SERVER_URL"

# 3. Get tool schema from MCP server
echo ""
echo "📋 Step 3: Getting available tools from MCP server"
TOOLS_RESPONSE=$(make_mcp_call "$SERVER_URL" "tools/list" "" "")

if ! handle_mcp_response "$TOOLS_RESPONSE" "Tools list"; then
    exit 1
fi

echo "$TOOLS_RESPONSE" > "$TEMP_DIR/mcp_tools.json"

# 4. Find the tool schema
echo ""
echo "🔍 Step 4: Examining tool schema"
TOOL_SCHEMA=$(echo "$TOOLS_RESPONSE" | jq ".result.tools[] | select(.name == \"$TOOL_NAME\")")

if [ -z "$TOOL_SCHEMA" ] || [ "$TOOL_SCHEMA" = "null" ]; then
    echo "❌ Tool $TOOL_NAME not found on MCP server"
    echo "Available tools on server:"
    echo "$TOOLS_RESPONSE" | jq -r '.result.tools[] | "  • \(.name): \(.description)"'
    exit 1
fi

echo "📊 Tool schema:"
echo "$TOOL_SCHEMA" | jq

# 5. Prepare tool arguments
echo ""
echo "⚙️  Step 5: Preparing tool arguments"

# Get example from catalog
EXAMPLE=$(jq -r ".tools[] | select(.name == \"$TOOL_NAME\") | .\"x-mcp-tool\".examples[0].input" "$TEMP_DIR/catalog.json")

if [ -z "$EXAMPLE" ] || [ "$EXAMPLE" = "null" ]; then
    echo "⚠️  No example found in catalog, using default arguments"
    case "$TOOL_NAME" in
        "get_user")
            ARGUMENTS='{"id": 1}'
            ;;
        "list_users")
            ARGUMENTS='{"limit": 5}'
            ;;
        "say_hello")
            ARGUMENTS='{"name": "EAT Framework"}'
            ;;
        "calculate")
            ARGUMENTS='{"operation": "add", "a": 5, "b": 3}'
            ;;
        *)
            ARGUMENTS='{}'
            ;;
    esac
else
    ARGUMENTS="$EXAMPLE"
fi

echo "📝 Using arguments: $ARGUMENTS"

# 6. Call the tool
echo ""
echo "🚀 Step 6: Calling tool '$TOOL_NAME'"
CALL_RESPONSE=$(make_mcp_call "$SERVER_URL" "tools/call" "$TOOL_NAME" "$ARGUMENTS")

if handle_mcp_response "$CALL_RESPONSE" "Tool call"; then
    echo ""
    echo "📄 Tool output:"
    echo "$CALL_RESPONSE" | jq '.result.output'
    
    # Save response
    echo "$CALL_RESPONSE" > "$TEMP_DIR/tool_response.json"
    echo "💾 Response saved to: $TEMP_DIR/tool_response.json"
else
    exit 1
fi

# 7. Try calling a few more tools if available
echo ""
echo "🔄 Step 7: Testing additional tools"

# Get all tools that have examples
ALL_TOOLS=$(jq -r '.tools[] | select(.["x-mcp-tool"].examples | length > 0) | .name' "$TEMP_DIR/catalog.json")

count=0
for tool in $ALL_TOOLS; do
    if [ $count -ge 3 ]; then  # Limit to 3 additional tools
        break
    fi
    
    if [ "$tool" = "$TOOL_NAME" ]; then
        continue  # Skip the one we already called
    fi
    
    echo ""
    echo "🧪 Testing tool: $tool"
    
    tool_server=$(jq -r ".tools[] | select(.name == \"$tool\") | .\"x-mcp-tool\".server_url" "$TEMP_DIR/catalog.json")
    tool_args=$(jq -r ".tools[] | select(.name == \"$tool\") | .\"x-mcp-tool\".examples[0].input" "$TEMP_DIR/catalog.json")
    
    test_response=$(make_mcp_call "$tool_server" "tools/call" "$tool" "$tool_args")
    
    if handle_mcp_response "$test_response" "Tool $tool"; then
        echo "📊 Output summary:"
        echo "$test_response" | jq -c '.result.output'
    else
        echo "⚠️  Tool $tool failed, continuing..."
    fi
    
    count=$((count + 1))
done

# 8. Performance test
echo ""
echo "⚡ Step 8: Performance test"
echo "Running 5 parallel tool calls..."

# Start timer
start_time=$(date +%s)

# Run 5 calls in parallel
for i in {1..5}; do
    (
        response=$(make_mcp_call "$SERVER_URL" "tools/call" "$TOOL_NAME" "$ARGUMENTS" 2>/dev/null)
        if echo "$response" | jq -e '.result' > /dev/null 2>&1; then
            echo "✅ Call $i: Success"
        else
            echo "❌ Call $i: Failed"
        fi
    ) &
done

# Wait for all background jobs
wait

end_time=$(date +%s)
duration=$((end_time - start_time))

echo "⏱️  5 parallel calls completed in ${duration}s"

# 9. Generate summary
echo ""
echo "📋 Execution Summary"
echo "==================="

cat > "$TEMP_DIR/execution_summary.txt" << EOF
EAT Tool Execution Summary
Generated: $(date)

Tool called: $TOOL_NAME
Server: $SERVER_URL
Arguments: $ARGUMENTS

$(if [ -f "$TEMP_DIR/tool_response.json" ]; then
    echo "Result:"
    jq -r '.result.output' "$TEMP_DIR/tool_response.json" | sed 's/^/  /'
fi)

Additional tools tested: $count
Parallel performance: 5 calls in ${duration}s
EOF

cat "$TEMP_DIR/execution_summary.txt"

echo ""
echo "🎉 Tool execution completed!"
echo "📁 Files saved in: $TEMP_DIR"
echo ""
echo "💡 Next steps:"
echo "   • Try the complete workflow: examples/curl/workflow.sh"
echo "   • Test error handling: examples/curl/error-handling.sh"

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