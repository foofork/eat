# EAT Framework API Reference

Complete Python API documentation for the EAT Framework, including all classes, methods, and usage examples.

## 📦 Package Overview

```python
from eat import Catalog, Tool, MCPClient
from eat.discovery import CatalogValidator, ToolFilter
from eat.security import JWSVerifier, ContentHasher
from eat.cli.main import generate, serve
```

## 🏗️ Core Classes

### Catalog

The main entry point for tool discovery and management.

```python
class Catalog:
    """
    Manages tool discovery and verification from EAT catalogs.
    
    This is the primary interface for agents to discover and interact
    with tools published via the EAT protocol.
    """
```

#### Constructor

```python
def __init__(
    self,
    catalog_url: str,
    verify_signatures: bool = True,
    cache_ttl: int = 300,
    timeout: int = 30,
    session: Optional[aiohttp.ClientSession] = None
) -> None
```

**Parameters:**
- `catalog_url` (str): URL to the `.well-known/api-catalog` endpoint
- `verify_signatures` (bool): Whether to verify JWS signatures (default: True)
- `cache_ttl` (int): Cache time-to-live in seconds (default: 300)
- `timeout` (int): HTTP request timeout in seconds (default: 30)
- `session` (Optional[ClientSession]): Custom aiohttp session

**Example:**
```python
import asyncio
from eat import Catalog

async def main():
    # Basic usage
    catalog = Catalog("https://api.company.com/.well-known/api-catalog")
    
    # With custom settings
    secure_catalog = Catalog(
        "https://secure-api.company.com/.well-known/api-catalog",
        verify_signatures=True,
        cache_ttl=600,
        timeout=10
    )

asyncio.run(main())
```

#### Methods

##### `fetch()`
```python
async def fetch(self, force_refresh: bool = False) -> None
```

Downloads and parses the catalog from the remote endpoint.

**Parameters:**
- `force_refresh` (bool): Skip cache and fetch fresh catalog

**Raises:**
- `CatalogFetchError`: Failed to download catalog
- `CatalogParseError`: Invalid catalog format
- `SignatureVerificationError`: Invalid JWS signature

**Example:**
```python
catalog = Catalog("https://api.company.com/.well-known/api-catalog")
await catalog.fetch()
print(f"Found {len(catalog.tools)} tools")
```

##### `verify()`
```python
async def verify(self) -> bool
```

Verifies the catalog's cryptographic signature and content integrity.

**Returns:**
- `bool`: True if verification succeeds

**Example:**
```python
catalog = Catalog("https://api.company.com/.well-known/api-catalog")
await catalog.fetch()

if await catalog.verify():
    print("Catalog signature is valid")
else:
    print("WARNING: Catalog signature verification failed")
```

##### `find()`
```python
def find(
    self,
    name: Optional[str] = None,
    capability: Optional[str] = None,
    description: Optional[str] = None,
    version: Optional[str] = None
) -> List[Tool]
```

Searches for tools matching the specified criteria.

**Parameters:**
- `name` (Optional[str]): Exact tool name match
- `capability` (Optional[str]): Capability tag (e.g., "customer-management")
- `description` (Optional[str]): Text search in tool description
- `version` (Optional[str]): Specific version requirement

**Returns:**
- `List[Tool]`: List of matching tools

**Example:**
```python
# Find all customer management tools
customer_tools = catalog.find(capability="customer-management")

# Find specific tool by name
user_tool = catalog.find(name="get_user")

# Find tools by description keywords
search_tools = catalog.find(description="analytics")

# Combine criteria
admin_tools = catalog.find(
    capability="user-management",
    description="admin"
)
```

##### `get_tool()`
```python
def get_tool(self, name: str) -> Tool
```

Retrieves a specific tool by name.

**Parameters:**
- `name` (str): Tool name

**Returns:**
- `Tool`: Tool instance

**Raises:**
- `ToolNotFoundError`: Tool not found in catalog

**Example:**
```python
try:
    customer_tool = catalog.get_tool("get_customer")
    result = await customer_tool.call(customer_id="12345")
except ToolNotFoundError:
    print("Customer tool not available")
```

##### `list_tools()`
```python
def list_tools(self) -> List[Dict[str, Any]]
```

Returns metadata for all tools in the catalog.

**Returns:**
- `List[Dict]`: List of tool metadata dictionaries

**Example:**
```python
tools = catalog.list_tools()
for tool in tools:
    print(f"Tool: {tool['name']} - {tool['description']}")
```

#### Properties

##### `tools`
```python
@property
def tools(self) -> List[Tool]
```

List of all tools in the catalog.

##### `metadata`
```python
@property
def metadata(self) -> Dict[str, Any]
```

Catalog metadata (title, description, generated_at, etc.).

##### `url`
```python
@property
def url(self) -> str
```

The catalog URL.

##### `is_valid`
```python
@property
def is_valid(self) -> bool
```

Whether the catalog has been successfully fetched and verified.

---

### Tool

Represents a single tool with its metadata and execution capabilities.

```python
class Tool:
    """
    Represents a tool discovered from an EAT catalog.
    
    Provides methods to inspect tool metadata and execute
    the tool via the MCP protocol.
    """
```

#### Constructor

```python
def __init__(
    self,
    name: str,
    spec_data: Dict[str, Any],
    mcp_metadata: Dict[str, Any],
    catalog_url: str
) -> None
```

**Note:** Tools are typically created by the Catalog class, not instantiated directly.

#### Methods

##### `call()`
```python
async def call(
    self,
    timeout: int = 30,
    **kwargs
) -> Dict[str, Any]
```

Executes the tool with the provided arguments.

**Parameters:**
- `timeout` (int): Execution timeout in seconds
- `**kwargs`: Tool-specific arguments

**Returns:**
- `Dict[str, Any]`: Tool execution result

**Raises:**
- `ToolExecutionError`: Tool execution failed
- `AuthenticationError`: Authentication required or failed
- `ValidationError`: Invalid arguments provided

**Example:**
```python
# Simple tool call
customer = await customer_tool.call(customer_id="12345")

# With additional parameters
detailed_customer = await customer_tool.call(
    customer_id="12345",
    include_preferences=True,
    include_history=True
)

# With timeout
quick_result = await analytics_tool.call(
    metric="revenue",
    period="last_30_days",
    timeout=10
)
```

##### `get_examples()`
```python
def get_examples(self) -> List[Dict[str, Any]]
```

Returns usage examples from the tool specification.

**Returns:**
- `List[Dict]`: List of example input/output pairs

**Example:**
```python
examples = tool.get_examples()
for example in examples:
    print(f"Example: {example['description']}")
    print(f"Input: {example['input']}")
    print(f"Output: {example['output']}")
```

##### `get_schema()`
```python
def get_schema(self) -> Dict[str, Any]
```

Returns the OpenAPI schema for the tool.

**Returns:**
- `Dict[str, Any]`: OpenAPI schema definition

##### `validate_arguments()`
```python
def validate_arguments(self, **kwargs) -> bool
```

Validates arguments against the tool's schema.

**Parameters:**
- `**kwargs`: Arguments to validate

**Returns:**
- `bool`: True if arguments are valid

**Raises:**
- `ValidationError`: Arguments don't match schema

**Example:**
```python
# Validate before calling
if customer_tool.validate_arguments(customer_id="12345"):
    result = await customer_tool.call(customer_id="12345")
```

#### Properties

##### `name`
```python
@property
def name(self) -> str
```

Tool name.

##### `description`
```python
@property
def description(self) -> str
```

Tool description.

##### `version`
```python
@property
def version(self) -> str
```

Tool version.

##### `capabilities`
```python
@property
def capabilities(self) -> List[str]
```

List of capability tags.

##### `server_url`
```python
@property
def server_url(self) -> str
```

MCP server URL for tool execution.

##### `authentication`
```python
@property
def authentication(self) -> Dict[str, Any]
```

Authentication requirements.

##### `rate_limits`
```python
@property
def rate_limits(self) -> Dict[str, Any]
```

Rate limiting information.

---

### MCPClient

Low-level MCP protocol client for tool execution.

```python
class MCPClient:
    """
    Model Context Protocol (MCP) client for tool execution.
    
    Handles the JSON-RPC 2.0 protocol used by EAT framework
    for tool execution.
    """
```

#### Constructor

```python
def __init__(
    self,
    server_url: str,
    auth_token: Optional[str] = None,
    timeout: int = 30,
    session: Optional[aiohttp.ClientSession] = None
) -> None
```

**Parameters:**
- `server_url` (str): MCP server endpoint URL
- `auth_token` (Optional[str]): Authentication token
- `timeout` (int): Request timeout in seconds
- `session` (Optional[ClientSession]): Custom aiohttp session

#### Methods

##### `call_tool()`
```python
async def call_tool(
    self,
    tool_name: str,
    arguments: Dict[str, Any],
    request_id: Optional[str] = None
) -> Dict[str, Any]
```

Executes a tool via MCP protocol.

**Parameters:**
- `tool_name` (str): Name of tool to execute
- `arguments` (Dict): Tool arguments
- `request_id` (Optional[str]): Custom request ID

**Returns:**
- `Dict[str, Any]`: Tool execution result

**Example:**
```python
client = MCPClient("https://api.company.com/mcp")
result = await client.call_tool(
    "get_customer",
    {"customer_id": "12345"}
)
```

##### `list_tools()`
```python
async def list_tools(self) -> List[Dict[str, Any]]
```

Lists available tools on the MCP server.

##### `get_tool_info()`
```python
async def get_tool_info(self, tool_name: str) -> Dict[str, Any]
```

Gets detailed information about a specific tool.

##### `close()`
```python
async def close(self) -> None
```

Closes the client session.

---

## 🔒 Security Classes

### JWSVerifier

Handles JWS signature verification and DID:web key resolution.

```python
class JWSVerifier:
    """
    Verifies JWS signatures using DID:web key resolution.
    """
```

#### Methods

##### `verify_catalog_signature()`
```python
async def verify_catalog_signature(
    self,
    catalog_data: Dict[str, Any],
    jws_token: str
) -> bool
```

Verifies a catalog's JWS signature.

**Parameters:**
- `catalog_data` (Dict): Catalog JSON data
- `jws_token` (str): JWS signature token

**Returns:**
- `bool`: True if signature is valid

**Example:**
```python
verifier = JWSVerifier()
is_valid = await verifier.verify_catalog_signature(catalog_data, jws_token)
```

##### `resolve_did_web_key()`
```python
async def resolve_did_web_key(
    self,
    did_identifier: str,
    key_id: str
) -> str
```

Resolves a DID:web identifier to a public key.

### ContentHasher

Handles SHA-256 content integrity verification.

```python
class ContentHasher:
    """
    Handles content hashing and verification for integrity checks.
    """
```

#### Methods

##### `calculate_hash()`
```python
@staticmethod
def calculate_hash(content: str) -> str
```

Calculates SHA-256 hash of content.

##### `verify_hash()`
```python
@staticmethod
def verify_hash(content: str, expected_hash: str) -> bool
```

Verifies content matches expected hash.

---

## 🔍 Discovery Classes

### CatalogValidator

Validates catalog structure and content.

```python
class CatalogValidator:
    """
    Validates EAT catalog structure and content.
    """
```

#### Methods

##### `validate_catalog()`
```python
def validate_catalog(self, catalog_data: Dict[str, Any]) -> ValidationResult
```

Validates catalog against EAT schema.

##### `validate_tool_spec()`
```python
def validate_tool_spec(self, spec_data: Dict[str, Any]) -> ValidationResult
```

Validates OpenAPI specification with x-mcp-tool extensions.

### ToolFilter

Advanced tool filtering and search capabilities.

```python
class ToolFilter:
    """
    Advanced filtering and search for tools.
    """
```

#### Methods

##### `filter_by_capability()`
```python
def filter_by_capability(
    self,
    tools: List[Tool],
    capabilities: List[str]
) -> List[Tool]
```

Filters tools by capability tags.

##### `search_by_keywords()`
```python
def search_by_keywords(
    self,
    tools: List[Tool],
    keywords: List[str]
) -> List[Tool]
```

Searches tools by keywords in name/description.

---

## 🛠️ CLI Functions

### generate()

```python
def generate(
    specs_dir: str,
    output_file: str,
    sign: bool = False,
    private_key: Optional[str] = None
) -> None
```

Generates a catalog from OpenAPI specifications.

**Parameters:**
- `specs_dir` (str): Directory containing OpenAPI specs
- `output_file` (str): Output catalog file path
- `sign` (bool): Whether to sign the catalog
- `private_key` (Optional[str]): Private key file for signing

**Example:**
```python
from eat.cli.main import generate

generate(
    specs_dir="./specs",
    output_file="api-catalog",
    sign=True,
    private_key="private-key.pem"
)
```

### serve()

```python
def serve(
    catalog_dir: str = ".",
    port: int = 8000,
    host: str = "localhost"
) -> None
```

Serves catalog files locally for development.

---

## 🚨 Exception Classes

### EATError

Base exception class for EAT Framework errors.

```python
class EATError(Exception):
    """Base exception for EAT Framework."""
    pass
```

### CatalogFetchError

```python
class CatalogFetchError(EATError):
    """Raised when catalog cannot be fetched."""
    pass
```

### CatalogParseError

```python
class CatalogParseError(EATError):
    """Raised when catalog cannot be parsed."""
    pass
```

### SignatureVerificationError

```python
class SignatureVerificationError(EATError):
    """Raised when signature verification fails."""
    pass
```

### ToolNotFoundError

```python
class ToolNotFoundError(EATError):
    """Raised when requested tool is not found."""
    pass
```

### ToolExecutionError

```python
class ToolExecutionError(EATError):
    """Raised when tool execution fails."""
    pass
```

### AuthenticationError

```python
class AuthenticationError(EATError):
    """Raised when authentication fails."""
    pass
```

### ValidationError

```python
class ValidationError(EATError):
    """Raised when validation fails."""
    pass
```

---

## 📝 Usage Examples

### Complete Agent Implementation

```python
import asyncio
import logging
from eat import Catalog, ToolExecutionError

class EATAgent:
    """
    Complete AI agent using EAT Framework for tool discovery.
    """
    
    def __init__(self, catalog_url: str):
        self.catalog = Catalog(catalog_url, verify_signatures=True)
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize agent by fetching and verifying catalog."""
        try:
            await self.catalog.fetch()
            if not await self.catalog.verify():
                raise SecurityError("Catalog signature verification failed")
            
            self.logger.info(f"Initialized with {len(self.catalog.tools)} tools")
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            raise
    
    async def get_customer_insights(self, customer_id: str):
        """
        Multi-tool workflow: get customer data and analytics.
        """
        try:
            # Find required tools
            customer_tool = self.catalog.get_tool("get_customer")
            analytics_tool = self.catalog.get_tool("get_customer_analytics")
            
            # Execute tools in sequence
            customer_data = await customer_tool.call(customer_id=customer_id)
            analytics_data = await analytics_tool.call(customer_id=customer_id)
            
            # Combine results
            return {
                "customer": customer_data,
                "analytics": analytics_data,
                "insights": self.generate_insights(customer_data, analytics_data)
            }
            
        except ToolExecutionError as e:
            self.logger.error(f"Tool execution failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise
    
    def generate_insights(self, customer_data, analytics_data):
        """Generate insights from combined data."""
        # Implementation would include AI/ML logic
        return {
            "summary": f"Customer {customer_data['name']} has high engagement",
            "recommendations": ["Offer premium upgrade", "Send loyalty rewards"]
        }

# Usage
async def main():
    agent = EATAgent("https://api.company.com/.well-known/api-catalog")
    await agent.initialize()
    
    insights = await agent.get_customer_insights("12345")
    print(f"Customer insights: {insights}")

asyncio.run(main())
```

### Error Handling and Retry Logic

```python
import asyncio
import time
from eat import Catalog, CatalogFetchError, ToolExecutionError

async def robust_tool_execution():
    """
    Demonstrates robust error handling and retry logic.
    """
    catalog = Catalog("https://api.company.com/.well-known/api-catalog")
    
    # Retry catalog fetching
    for attempt in range(3):
        try:
            await catalog.fetch()
            break
        except CatalogFetchError as e:
            if attempt == 2:  # Last attempt
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    # Find tool with fallback
    customer_tools = catalog.find(capability="customer-management")
    if not customer_tools:
        raise RuntimeError("No customer management tools available")
    
    primary_tool = customer_tools[0]
    
    # Execute with retry and fallback
    for tool in customer_tools:
        try:
            result = await tool.call(customer_id="12345", timeout=10)
            return result
        except ToolExecutionError as e:
            logging.warning(f"Tool {tool.name} failed: {e}")
            continue
    
    raise RuntimeError("All customer tools failed")

# Usage
try:
    result = await robust_tool_execution()
    print(f"Success: {result}")
except Exception as e:
    print(f"All attempts failed: {e}")
```

### Custom Authentication

```python
import aiohttp
from eat import Catalog, MCPClient

class AuthenticatedEATClient:
    """
    EAT client with custom authentication.
    """
    
    def __init__(self, catalog_url: str, auth_endpoint: str):
        self.catalog_url = catalog_url
        self.auth_endpoint = auth_endpoint
        self.access_token = None
    
    async def authenticate(self, username: str, password: str):
        """Authenticate and obtain access token."""
        async with aiohttp.ClientSession() as session:
            auth_data = {
                "username": username,
                "password": password,
                "grant_type": "password"
            }
            
            async with session.post(self.auth_endpoint, json=auth_data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data["access_token"]
                else:
                    raise AuthenticationError("Authentication failed")
    
    async def discover_tools(self):
        """Discover tools with authenticated session."""
        # Create authenticated session
        headers = {"Authorization": f"Bearer {self.access_token}"}
        session = aiohttp.ClientSession(headers=headers)
        
        # Create catalog with authenticated session
        catalog = Catalog(self.catalog_url, session=session)
        await catalog.fetch()
        
        return catalog

# Usage
client = AuthenticatedEATClient(
    "https://secure-api.company.com/.well-known/api-catalog",
    "https://auth.company.com/token"
)

await client.authenticate("agent-user", "secure-password")
catalog = await client.discover_tools()
```

---

This API reference provides comprehensive documentation for all public interfaces in the EAT Framework, enabling developers to effectively integrate tool discovery into their AI agents.