# EAT Framework Troubleshooting Guide

Comprehensive troubleshooting guide for common issues encountered when implementing, deploying, and using the EAT Framework.

## 🚨 Quick Issue Resolution

### Most Common Issues

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| **Catalog not found (404)** | Missing .well-known/api-catalog | Verify file exists at `/.well-known/api-catalog` |
| **Signature verification failed** | Invalid or expired JWS | Check DID document and key validity |
| **Tool execution timeout** | MCP server unavailable | Verify MCP server is running and accessible |
| **Import error: No module named 'aiohttp'** | Missing dependencies | Run `pip install -r requirements.txt` |
| **SSL certificate error** | Invalid or self-signed cert | Check HTTPS configuration and certificates |

## 🔍 Diagnostic Tools

### Health Check Script

```python
#!/usr/bin/env python3
"""
EAT Framework health check and diagnostic tool.
"""

import asyncio
import aiohttp
import time
import json
from urllib.parse import urlparse

async def diagnose_eat_setup(catalog_url: str):
    """
    Comprehensive diagnostic check for EAT Framework setup.
    """
    print(f"🔍 Diagnosing EAT setup for: {catalog_url}")
    print("=" * 60)
    
    results = {
        "catalog_reachable": False,
        "catalog_valid_json": False,
        "signature_present": False,
        "did_document_accessible": False,
        "mcp_servers_reachable": False,
        "specs_accessible": False
    }
    
    # Test 1: Catalog Accessibility
    print("1️⃣ Testing catalog accessibility...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(catalog_url, timeout=10) as response:
                if response.status == 200:
                    print("   ✅ Catalog URL is reachable")
                    results["catalog_reachable"] = True
                    
                    # Test 2: Valid JSON
                    try:
                        catalog_data = await response.json()
                        print("   ✅ Catalog returns valid JSON")
                        results["catalog_valid_json"] = True
                        
                        # Test 3: Signature Check
                        if "signature" in catalog_data or "jws" in catalog_data:
                            print("   ✅ Catalog contains signature")
                            results["signature_present"] = True
                        else:
                            print("   ⚠️  No signature found in catalog")
                        
                        # Test 4: DID Document
                        if "metadata" in catalog_data and "issuer" in catalog_data["metadata"]:
                            issuer = catalog_data["metadata"]["issuer"]
                            if issuer.startswith("did:web:"):
                                domain = issuer.replace("did:web:", "")
                                did_url = f"https://{domain}/.well-known/did.json"
                                
                                try:
                                    async with session.get(did_url, timeout=5) as did_response:
                                        if did_response.status == 200:
                                            print("   ✅ DID document accessible")
                                            results["did_document_accessible"] = True
                                        else:
                                            print(f"   ❌ DID document not accessible: {did_response.status}")
                                except Exception as e:
                                    print(f"   ❌ DID document error: {e}")
                        
                        # Test 5: MCP Servers
                        print("2️⃣ Testing MCP server accessibility...")
                        if "tools" in catalog_data:
                            mcp_servers = set()
                            for tool in catalog_data["tools"]:
                                if "x-mcp-tool" in tool and "server_url" in tool["x-mcp-tool"]:
                                    mcp_servers.add(tool["x-mcp-tool"]["server_url"])
                            
                            if mcp_servers:
                                reachable_servers = 0
                                for server_url in mcp_servers:
                                    try:
                                        health_url = f"{server_url}/health"
                                        async with session.get(health_url, timeout=5) as health_response:
                                            if health_response.status == 200:
                                                print(f"   ✅ MCP server reachable: {server_url}")
                                                reachable_servers += 1
                                            else:
                                                print(f"   ❌ MCP server not healthy: {server_url} ({health_response.status})")
                                    except Exception as e:
                                        print(f"   ❌ MCP server error: {server_url} - {e}")
                                
                                if reachable_servers > 0:
                                    results["mcp_servers_reachable"] = True
                            else:
                                print("   ⚠️  No MCP servers found in catalog")
                        
                        # Test 6: OpenAPI Specs
                        print("3️⃣ Testing OpenAPI specification accessibility...")
                        if "tools" in catalog_data:
                            reachable_specs = 0
                            for tool in catalog_data["tools"]:
                                if "spec_url" in tool:
                                    try:
                                        async with session.get(tool["spec_url"], timeout=5) as spec_response:
                                            if spec_response.status == 200:
                                                print(f"   ✅ Spec accessible: {tool['name']}")
                                                reachable_specs += 1
                                            else:
                                                print(f"   ❌ Spec not accessible: {tool['name']} ({spec_response.status})")
                                    except Exception as e:
                                        print(f"   ❌ Spec error: {tool['name']} - {e}")
                            
                            if reachable_specs > 0:
                                results["specs_accessible"] = True
                    
                    except json.JSONDecodeError as e:
                        print(f"   ❌ Invalid JSON in catalog: {e}")
                else:
                    print(f"   ❌ Catalog not accessible: HTTP {response.status}")
    
    except Exception as e:
        print(f"   ❌ Catalog request failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for check, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check.replace('_', ' ').title():<30} {status}")
    
    print(f"\nOverall Health: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All checks passed! EAT setup is healthy.")
    elif passed >= total * 0.7:
        print("⚠️  Most checks passed. Review failed checks above.")
    else:
        print("🚨 Multiple failures detected. EAT setup needs attention.")
    
    return results

# Command-line usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python diagnose.py <catalog-url>")
        sys.exit(1)
    
    catalog_url = sys.argv[1]
    asyncio.run(diagnose_eat_setup(catalog_url))
```

### Network Connectivity Test

```bash
#!/bin/bash
# network-test.sh - Test network connectivity to EAT endpoints

CATALOG_URL="$1"

if [ -z "$CATALOG_URL" ]; then
    echo "Usage: $0 <catalog-url>"
    exit 1
fi

echo "🌐 Testing network connectivity for EAT Framework"
echo "=================================================="

# Extract domain from URL
DOMAIN=$(echo "$CATALOG_URL" | sed -E 's|https?://([^/]+).*|\1|')

echo "1️⃣ DNS Resolution Test"
if nslookup "$DOMAIN" > /dev/null 2>&1; then
    echo "   ✅ DNS resolution successful for $DOMAIN"
else
    echo "   ❌ DNS resolution failed for $DOMAIN"
    exit 1
fi

echo "2️⃣ SSL Certificate Test"
if echo | openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" 2>/dev/null | openssl x509 -noout -dates; then
    echo "   ✅ SSL certificate is valid"
else
    echo "   ❌ SSL certificate issues detected"
fi

echo "3️⃣ HTTP Response Test"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$CATALOG_URL")
if [ "$HTTP_STATUS" = "200" ]; then
    echo "   ✅ HTTP response OK (200)"
else
    echo "   ❌ HTTP response error: $HTTP_STATUS"
fi

echo "4️⃣ Response Time Test"
RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" "$CATALOG_URL")
echo "   ⏱️  Response time: ${RESPONSE_TIME}s"

if (( $(echo "$RESPONSE_TIME < 2.0" | bc -l) )); then
    echo "   ✅ Response time acceptable"
else
    echo "   ⚠️  Response time slow (>2s)"
fi

echo "5️⃣ Content-Type Test"
CONTENT_TYPE=$(curl -s -I "$CATALOG_URL" | grep -i content-type | cut -d: -f2 | tr -d ' \r\n')
if [[ "$CONTENT_TYPE" == *"application/json"* ]]; then
    echo "   ✅ Content-Type is application/json"
else
    echo "   ⚠️  Content-Type is not application/json: $CONTENT_TYPE"
fi

echo "6️⃣ CORS Headers Test"
CORS_HEADERS=$(curl -s -I "$CATALOG_URL" | grep -i "access-control-allow-origin")
if [ -n "$CORS_HEADERS" ]; then
    echo "   ✅ CORS headers present"
else
    echo "   ⚠️  No CORS headers found"
fi

echo "=================================================="
echo "Network connectivity test completed"
```

## 🔧 Installation Issues

### Problem: Import Errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'aiohttp'
ModuleNotFoundError: No module named 'eat'
```

**Solutions:**

1. **Install dependencies:**
```bash
# Option 1: Install from requirements
pip install -r requirements.txt

# Option 2: Install individual packages
pip install aiohttp cryptography pyjwt click pydantic requests pyyaml jsonschema

# Option 3: Install in development mode
pip install -e .
```

2. **Check Python version:**
```bash
python --version  # Must be 3.8+
```

3. **Use virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Problem: Permission Errors

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied
```

**Solutions:**

1. **Use virtual environment instead of system-wide install:**
```bash
python -m venv venv
source venv/bin/activate
pip install -e .
```

2. **Install with user flag:**
```bash
pip install --user -e .
```

3. **Check file permissions:**
```bash
ls -la /path/to/eat-framework/
chmod 755 /path/to/eat-framework/
```

## 🌐 Network and Connectivity Issues

### Problem: Catalog Not Found (404)

**Symptoms:**
```
CatalogFetchError: Failed to fetch catalog: 404 Not Found
```

**Diagnosis:**
```bash
# Test catalog URL directly
curl -I https://api.company.com/.well-known/api-catalog

# Check if .well-known directory exists
curl -I https://api.company.com/.well-known/

# Test with verbose output
curl -v https://api.company.com/.well-known/api-catalog
```

**Solutions:**

1. **Verify file exists:**
```bash
# On server
ls -la /var/www/html/.well-known/api-catalog
```

2. **Check web server configuration:**
```nginx
# Nginx configuration
location /.well-known/api-catalog {
    root /var/www/html;
    try_files /api-catalog =404;
}
```

3. **Verify MIME type:**
```nginx
location /.well-known/api-catalog {
    add_header Content-Type application/json;
}
```

### Problem: SSL Certificate Errors

**Symptoms:**
```
aiohttp.client_exceptions.ClientConnectorSSLError: Cannot connect to host
```

**Solutions:**

1. **Check certificate validity:**
```bash
openssl s_client -connect api.company.com:443 -servername api.company.com
```

2. **Test with curl:**
```bash
curl -v https://api.company.com/.well-known/api-catalog
```

3. **Disable SSL verification (development only):**
```python
import ssl
import aiohttp

# Create SSL context that doesn't verify certificates
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Use with aiohttp
connector = aiohttp.TCPConnector(ssl=ssl_context)
session = aiohttp.ClientSession(connector=connector)
```

### Problem: Timeout Errors

**Symptoms:**
```
asyncio.TimeoutError: Timeout after 30 seconds
```

**Solutions:**

1. **Increase timeout:**
```python
catalog = Catalog(catalog_url, timeout=60)
```

2. **Test network latency:**
```bash
ping api.company.com
traceroute api.company.com
```

3. **Check for proxy issues:**
```bash
# Test with proxy
curl --proxy http://proxy.company.com:8080 https://api.company.com/.well-known/api-catalog

# Test without proxy
curl --noproxy "*" https://api.company.com/.well-known/api-catalog
```

## 🔒 Security and Signature Issues

### Problem: Signature Verification Failed

**Symptoms:**
```
SignatureVerificationError: JWS signature verification failed
```

**Diagnosis:**
```python
# Debug signature verification
import json
from eat.security import JWSVerifier

async def debug_signature():
    verifier = JWSVerifier()
    
    # Load catalog
    with open('api-catalog') as f:
        catalog_data = json.load(f)
    
    # Extract JWS token
    jws_token = catalog_data.get('jws')
    
    # Verify step by step
    try:
        # Parse JWS
        header, payload, signature = verifier.parse_jws(jws_token)
        print(f"Header: {header}")
        print(f"Payload: {payload}")
        
        # Resolve key
        issuer = payload.get('iss')
        key_id = header.get('kid')
        public_key = await verifier.resolve_did_web_key(issuer, key_id)
        print(f"Public key resolved: {len(public_key)} characters")
        
        # Verify signature
        is_valid = verifier.verify_signature(header, payload, signature, public_key)
        print(f"Signature valid: {is_valid}")
        
    except Exception as e:
        print(f"Verification error: {e}")

asyncio.run(debug_signature())
```

**Solutions:**

1. **Check DID document accessibility:**
```bash
curl https://api.company.com/.well-known/did.json
```

2. **Verify key format:**
```bash
# Check if public key is valid PEM
openssl rsa -in public-key.pem -pubin -text -noout
```

3. **Regenerate signature:**
```bash
eat-gen sign catalog.json --key private-key.pem --output api-catalog
```

### Problem: DID:web Resolution Failed

**Symptoms:**
```
KeyResolutionError: Failed to resolve DID:web key
```

**Solutions:**

1. **Test DID document manually:**
```bash
# For did:web:api.company.com
curl https://api.company.com/.well-known/did.json
```

2. **Check DID document format:**
```json
{
  "@context": ["https://www.w3.org/ns/did/v1"],
  "id": "did:web:api.company.com",
  "verificationMethod": [
    {
      "id": "did:web:api.company.com#key-1",
      "type": "RsaVerificationKey2018",
      "controller": "did:web:api.company.com",
      "publicKeyPem": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
    }
  ]
}
```

3. **Verify web server serves JSON:**
```nginx
location /.well-known/did.json {
    add_header Content-Type application/json;
}
```

## 🛠️ Tool Execution Issues

### Problem: MCP Server Not Responding

**Symptoms:**
```
ToolExecutionError: MCP server not responding
```

**Diagnosis:**
```bash
# Check if MCP server is running
netstat -tlpn | grep :3001

# Test MCP health endpoint
curl http://localhost:3001/health

# Test MCP tools endpoint
curl -X POST http://localhost:3001 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/list","params":{}}'
```

**Solutions:**

1. **Check MCP server logs:**
```bash
docker logs mcp-server
journalctl -u mcp-server -f
```

2. **Verify MCP server configuration:**
```python
# Test MCP client directly
from eat import MCPClient

client = MCPClient("http://localhost:3001")
tools = await client.list_tools()
print(f"Available tools: {tools}")
```

3. **Check network connectivity:**
```bash
# Test internal network
curl -v http://mcp-server:3001/health

# Test with different timeouts
curl --connect-timeout 5 --max-time 10 http://localhost:3001/health
```

### Problem: Authentication Errors

**Symptoms:**
```
AuthenticationError: Invalid or missing authentication token
```

**Solutions:**

1. **Check token format:**
```python
# Verify JWT token
import jwt

token = "your-jwt-token"
decoded = jwt.decode(token, options={"verify_signature": False})
print(f"Token payload: {decoded}")
```

2. **Test authentication endpoint:**
```bash
curl -X POST https://auth.company.com/token \
  -H "Content-Type: application/json" \
  -d '{"username":"agent","password":"secret"}'
```

3. **Use authentication in requests:**
```python
# Include auth token in requests
headers = {"Authorization": f"Bearer {token}"}
session = aiohttp.ClientSession(headers=headers)
catalog = Catalog(catalog_url, session=session)
```

## 📊 Performance Issues

### Problem: Slow Catalog Discovery

**Symptoms:**
- Discovery takes >5 seconds
- High memory usage
- Frequent timeouts

**Solutions:**

1. **Enable caching:**
```python
# Use longer cache TTL
catalog = Catalog(catalog_url, cache_ttl=3600)

# Use external cache
import aioredis

redis = aioredis.from_url("redis://localhost")
catalog = Catalog(catalog_url, cache_backend=redis)
```

2. **Optimize catalog size:**
```bash
# Check catalog size
curl -I https://api.company.com/.well-known/api-catalog

# Compress catalog
gzip -c api-catalog > api-catalog.gz
```

3. **Use CDN:**
```nginx
# Add cache headers
location /.well-known/api-catalog {
    add_header Cache-Control "public, max-age=300";
    add_header ETag "catalog-v1.0";
}
```

### Problem: High Memory Usage

**Symptoms:**
- Process memory grows over time
- Out of memory errors
- Slow garbage collection

**Solutions:**

1. **Monitor memory usage:**
```python
import psutil
import gc

def check_memory():
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"Memory usage: {memory_mb:.1f} MB")
    
    # Force garbage collection
    gc.collect()

# Check periodically
check_memory()
```

2. **Use session pooling:**
```python
# Reuse HTTP session
session = aiohttp.ClientSession()
catalog = Catalog(catalog_url, session=session)

# Close session when done
await session.close()
```

3. **Limit concurrent operations:**
```python
import asyncio

# Use semaphore to limit concurrency
semaphore = asyncio.Semaphore(10)

async def limited_operation():
    async with semaphore:
        # Perform operation
        pass
```

## 🐛 Development and Testing Issues

### Problem: Tests Failing

**Symptoms:**
```
FAILED tests/test_discovery.py::test_catalog_fetch - AssertionError
```

**Solutions:**

1. **Run specific test with verbose output:**
```bash
pytest tests/test_discovery.py::test_catalog_fetch -v -s
```

2. **Check test fixtures:**
```bash
ls -la tests/fixtures/
cat tests/fixtures/valid_catalog.json
```

3. **Update test data:**
```python
# Generate fresh test catalog
eat-gen generate tests/fixtures/specs/ --output tests/fixtures/valid_catalog.json
```

### Problem: CLI Commands Not Working

**Symptoms:**
```
bash: eat-gen: command not found
```

**Solutions:**

1. **Install in development mode:**
```bash
pip install -e .
```

2. **Check entry points:**
```bash
# Verify installation
pip show eat-framework

# Use module syntax
python -m eat.cli.main generate --help
```

3. **Add to PATH:**
```bash
export PATH=$PATH:~/.local/bin
```

## 📞 Getting Help

### Diagnostic Information to Collect

When reporting issues, include:

1. **Environment information:**
```bash
python --version
pip list | grep -E "(eat|aiohttp|cryptography)"
uname -a
```

2. **Error details:**
```python
import traceback
try:
    # Problematic code
    pass
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
```

3. **Network diagnostics:**
```bash
curl -v https://api.company.com/.well-known/api-catalog
nslookup api.company.com
```

### Support Channels

- **GitHub Issues**: [Create issue](https://github.com/foofork/eat/issues)
- **Documentation**: Check [docs/](.) directory
- **Examples**: Review [examples/](../examples/) directory
- **Demo**: Test with [demo/](../demo/) environment

### Creating Minimal Reproduction

```python
#!/usr/bin/env python3
"""
Minimal reproduction case for EAT Framework issues.
"""

import asyncio
from eat import Catalog

async def reproduce_issue():
    """
    Minimal code that reproduces the issue.
    """
    try:
        catalog = Catalog("https://api.company.com/.well-known/api-catalog")
        await catalog.fetch()
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(reproduce_issue())
```

---

This troubleshooting guide covers the most common issues encountered with EAT Framework. For additional help, please consult the documentation or create an issue with detailed diagnostic information.