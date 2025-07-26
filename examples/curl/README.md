# Pure HTTP Examples with curl

This directory contains examples of EAT protocol implementation using only HTTP and curl commands. These examples show how to interact with EAT catalogs and MCP servers without any programming language dependencies.

## Prerequisites

- `curl` command line tool
- `jq` for JSON parsing (optional but recommended)

## Discovery Examples

### 1. Fetch a Tool Catalog

```bash
# Basic catalog fetch
curl -H "Accept: application/json" \
     http://localhost:8080/.well-known/api-catalog

# With proper error handling
curl -f -H "Accept: application/json" \
     -H "User-Agent: EAT-Client/1.0" \
     http://localhost:8080/.well-known/api-catalog

# Save catalog to file
curl -o catalog.json \
     -H "Accept: application/json" \
     http://localhost:8080/.well-known/api-catalog
```

### 2. Parse Catalog with jq

```bash
# Extract all tool names
curl -s http://localhost:8080/.well-known/api-catalog | \
  jq -r '.tools[].name'

# Find tools by capability
curl -s http://localhost:8080/.well-known/api-catalog | \
  jq -r '.tools[] | select(.["x-mcp-tool"].capabilities[]? == "user-management") | .name'

# Get MCP server URLs
curl -s http://localhost:8080/.well-known/api-catalog | \
  jq -r '.tools[] | "\(.name): \(.["x-mcp-tool"].server_url)"'

# Extract tool with examples
curl -s http://localhost:8080/.well-known/api-catalog | \
  jq '.tools[] | select(.name == "get_user")'
```

## MCP Protocol Examples

### 3. List Available Tools

```bash
# Basic tools/list request
curl -X POST http://localhost:3001 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "tools/list"
  }'

# With pretty printing
curl -X POST http://localhost:3001 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "list-tools-1",
    "method": "tools/list"
  }' | jq
```

### 4. Call Tools

```bash
# Simple tool call
curl -X POST http://localhost:3001 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "2",
    "method": "tools/call",
    "params": {
      "name": "get_user",
      "arguments": {
        "id": 123
      }
    }
  }' | jq

# Tool call with multiple parameters
curl -X POST http://localhost:3001 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "3",
    "method": "tools/call",
    "params": {
      "name": "create_user",
      "arguments": {
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "role": "developer"
      }
    }
  }' | jq

# Notification tool call
curl -X POST http://localhost:3003 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "4",
    "method": "tools/call",
    "params": {
      "name": "send_notification",
      "arguments": {
        "type": "email",
        "recipient": "user@example.com",
        "subject": "Test Notification",
        "body": "This is a test notification from curl",
        "priority": "normal"
      }
    }
  }' | jq
```

## Complete Workflow Examples

### 5. User Management Workflow

```bash
#!/bin/bash
# Complete user management workflow

# 1. Discover catalog
echo "🔍 Discovering tools..."
CATALOG=$(curl -s http://localhost:8080/.well-known/api-catalog)

# 2. Extract user management server URL
USER_SERVER=$(echo "$CATALOG" | jq -r '.tools[] | select(.["x-mcp-tool"].capabilities[]? == "user-management") | .["x-mcp-tool"].server_url' | head -1)
echo "📡 User server: $USER_SERVER"

# 3. List existing users
echo "📋 Listing users..."
curl -X POST "$USER_SERVER" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "list-1",
    "method": "tools/call",
    "params": {
      "name": "list_users",
      "arguments": {"limit": 5}
    }
  }' | jq '.result.output'

# 4. Create a new user
echo "👤 Creating user..."
NEW_USER=$(curl -X POST "$USER_SERVER" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "create-1",
    "method": "tools/call",
    "params": {
      "name": "create_user",
      "arguments": {
        "name": "Test User",
        "email": "test@example.com",
        "role": "user"
      }
    }
  }')

USER_ID=$(echo "$NEW_USER" | jq -r '.result.output.id')
echo "✅ Created user with ID: $USER_ID"

# 5. Get the created user
echo "🔍 Retrieving user..."
curl -X POST "$USER_SERVER" \
  -H "Content-Type: application/json" \
  -d "{
    \"jsonrpc\": \"2.0\",
    \"id\": \"get-1\",
    \"method\": \"tools/call\",
    \"params\": {
      \"name\": \"get_user\",
      \"arguments\": {
        \"id\": $USER_ID
      }
    }
  }" | jq '.result.output'
```

### 6. Multi-Service Workflow

```bash
#!/bin/bash
# Workflow spanning multiple services

# 1. Get dashboard stats
echo "📊 Getting analytics..."
curl -X POST http://localhost:3002 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "analytics-1",
    "method": "tools/call",
    "params": {
      "name": "get_dashboard_stats",
      "arguments": {"timeframe": "7d"}
    }
  }' | jq '.result.output'

# 2. Generate a report
echo "📄 Generating report..."
REPORT=$(curl -X POST http://localhost:3002 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "report-1",
    "method": "tools/call",
    "params": {
      "name": "generate_report",
      "arguments": {
        "report_type": "user_activity",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "format": "pdf"
      }
    }
  }')

REPORT_ID=$(echo "$REPORT" | jq -r '.result.output.report_id')
echo "📄 Report ID: $REPORT_ID"

# 3. Send notification about report
echo "📧 Sending notification..."
curl -X POST http://localhost:3003 \
  -H "Content-Type: application/json" \
  -d "{
    \"jsonrpc\": \"2.0\",
    \"id\": \"notify-1\",
    \"method\": \"tools/call\",
    \"params\": {
      \"name\": \"send_notification\",
      \"arguments\": {
        \"type\": \"email\",
        \"recipient\": \"admin@example.com\",
        \"subject\": \"Report Generated\",
        \"body\": \"Your report $REPORT_ID has been generated and is ready for download.\",
        \"priority\": \"normal\"
      }
    }
  }" | jq '.result.output'
```

## Error Handling Examples

### 7. Handle HTTP Errors

```bash
# Check if catalog exists
if curl -f -s http://localhost:8080/.well-known/api-catalog > /dev/null; then
  echo "✅ Catalog is available"
else
  echo "❌ Catalog not found"
  exit 1
fi

# Retry with exponential backoff
retry_count=0
max_retries=3
while [ $retry_count -lt $max_retries ]; do
  if curl -f -s http://localhost:8080/.well-known/api-catalog > catalog.json; then
    echo "✅ Catalog fetched successfully"
    break
  else
    retry_count=$((retry_count + 1))
    sleep_time=$((2 ** retry_count))
    echo "⏳ Retry $retry_count/$max_retries in ${sleep_time}s..."
    sleep $sleep_time
  fi
done
```

### 8. Handle MCP Errors

```bash
# Tool call with error handling
RESPONSE=$(curl -X POST http://localhost:3001 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-1",
    "method": "tools/call",
    "params": {
      "name": "get_user",
      "arguments": {"id": 99999}
    }
  }')

# Check for JSON-RPC error
if echo "$RESPONSE" | jq -e '.error' > /dev/null; then
  ERROR_CODE=$(echo "$RESPONSE" | jq -r '.error.code')
  ERROR_MSG=$(echo "$RESPONSE" | jq -r '.error.message')
  echo "❌ Error $ERROR_CODE: $ERROR_MSG"
else
  echo "✅ Success:"
  echo "$RESPONSE" | jq '.result.output'
fi
```

## Security Examples

### 9. Verify JWS Signatures

```bash
# Extract signature from catalog
CATALOG=$(curl -s http://localhost:8080/.well-known/api-catalog)
JWS_SIGNATURE=$(echo "$CATALOG" | jq -r '.metadata.signature.jws // empty')

if [ -n "$JWS_SIGNATURE" ]; then
  echo "🔐 Catalog is signed"
  
  # Extract header and payload (for inspection only)
  HEADER=$(echo "$JWS_SIGNATURE" | cut -d. -f1)
  PAYLOAD=$(echo "$JWS_SIGNATURE" | cut -d. -f2)
  
  # Decode header (requires base64 with URL-safe alphabet)
  echo "📋 JWS Header:"
  echo "$HEADER" | base64 -d 2>/dev/null | jq 2>/dev/null || echo "Could not decode header"
  
  echo "📋 JWS Payload:"
  echo "$PAYLOAD" | base64 -d 2>/dev/null | jq 2>/dev/null || echo "Could not decode payload"
else
  echo "⚠️  Catalog is not signed"
fi
```

### 10. Authenticate Requests

```bash
# Using API key authentication
API_KEY="your-api-key-here"

curl -X POST http://localhost:3001 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "jsonrpc": "2.0",
    "id": "auth-1",
    "method": "tools/call",
    "params": {
      "name": "get_user",
      "arguments": {"id": 123}
    }
  }' | jq

# Using custom headers
curl -X POST http://localhost:3001 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -H "X-Client-Version: 1.0.0" \
  -d '{
    "jsonrpc": "2.0",
    "id": "auth-2",
    "method": "tools/list"
  }' | jq
```

## Performance Examples

### 11. Parallel Requests

```bash
# Run multiple requests in parallel
echo "🚀 Starting parallel requests..."

# Background jobs
curl -X POST http://localhost:3001 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"get_user","arguments":{"id":1}}}' \
  > user1.json &

curl -X POST http://localhost:3001 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"2","method":"tools/call","params":{"name":"get_user","arguments":{"id":2}}}' \
  > user2.json &

curl -X POST http://localhost:3002 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"3","method":"tools/call","params":{"name":"get_dashboard_stats","arguments":{"timeframe":"24h"}}}' \
  > stats.json &

# Wait for all to complete
wait

echo "✅ All requests completed"
cat user1.json | jq '.result.output'
cat user2.json | jq '.result.output'
cat stats.json | jq '.result.output'

# Cleanup
rm user1.json user2.json stats.json
```

### 12. Batch Operations

```bash
# Send multiple notifications at once
curl -X POST http://localhost:3003 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "batch-1",
    "method": "tools/call",
    "params": {
      "name": "send_batch_notifications",
      "arguments": {
        "type": "email",
        "template": "welcome_email",
        "recipients": [
          {
            "email": "user1@example.com",
            "data": {"name": "Alice"}
          },
          {
            "email": "user2@example.com", 
            "data": {"name": "Bob"}
          },
          {
            "email": "user3@example.com",
            "data": {"name": "Charlie"}
          }
        ]
      }
    }
  }' | jq '.result.output'
```

## Testing Examples

### 13. Validate Catalog Format

```bash
# Basic catalog validation
CATALOG=$(curl -s http://localhost:8080/.well-known/api-catalog)

# Check required fields
echo "🔍 Validating catalog format..."

VERSION=$(echo "$CATALOG" | jq -r '.version // empty')
if [ "$VERSION" = "1.0" ]; then
  echo "✅ Version is valid: $VERSION"
else
  echo "❌ Invalid version: $VERSION"
fi

TOOLS_COUNT=$(echo "$CATALOG" | jq '.tools | length')
echo "📊 Found $TOOLS_COUNT tools"

# Validate each tool
echo "$CATALOG" | jq -r '.tools[] | .name' | while read tool_name; do
  echo "🔧 Validating tool: $tool_name"
  
  # Check required fields
  SERVER_URL=$(echo "$CATALOG" | jq -r ".tools[] | select(.name == \"$tool_name\") | .\"x-mcp-tool\".server_url")
  if [ -n "$SERVER_URL" ] && [ "$SERVER_URL" != "null" ]; then
    echo "  ✅ Has server_url: $SERVER_URL"
  else
    echo "  ❌ Missing server_url"
  fi
done
```

### 14. Health Checks

```bash
#!/bin/bash
# Comprehensive health check

echo "🏥 EAT System Health Check"
echo "========================="

# 1. Check catalog availability
echo "📋 Checking catalog..."
if curl -f -s http://localhost:8080/.well-known/api-catalog > /dev/null; then
  echo "✅ Catalog is accessible"
else
  echo "❌ Catalog is not accessible"
  exit 1
fi

# 2. Check each MCP server
for port in 3001 3002 3003; do
  echo "🔧 Checking MCP server on port $port..."
  RESPONSE=$(curl -X POST http://localhost:$port \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","id":"health","method":"tools/list"}' \
    2>/dev/null)
  
  if echo "$RESPONSE" | jq -e '.result' > /dev/null; then
    TOOL_COUNT=$(echo "$RESPONSE" | jq '.result.tools | length')
    echo "✅ MCP server on port $port is healthy ($TOOL_COUNT tools)"
  else
    echo "❌ MCP server on port $port is not responding"
  fi
done

echo "🎉 Health check completed"
```

## Usage Tips

1. **Save these scripts**: Copy the examples to executable files for reuse
2. **Use jq for parsing**: Install `jq` for better JSON handling
3. **Add error handling**: Always check HTTP status codes and JSON-RPC errors
4. **Use variables**: Store URLs and common parameters in variables
5. **Parallel execution**: Use background jobs (`&`) for better performance
6. **Authentication**: Add proper headers for production environments

## Next Steps

- Try modifying the examples for your specific use case
- Combine multiple examples into complete workflows
- Add authentication and error handling for production use
- Test with different catalog configurations