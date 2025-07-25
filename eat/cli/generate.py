"""
Catalog generation functionality.
"""

import json
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
import click

from ..security import CatalogSigner, compute_sha256


async def generate_catalog(
    directory: str,
    output_file: str,
    sign: bool = False,
    private_key_path: Optional[str] = None,
    key_id: Optional[str] = None
):
    """Generate EAT catalog from OpenAPI specifications."""
    
    directory_path = Path(directory)
    specs_dir = directory_path / "specs"
    
    if not specs_dir.exists():
        click.echo(f"Error: specs/ directory not found in {directory}", err=True)
        return
    
    click.echo(f"🔍 Scanning {specs_dir} for OpenAPI specifications...")
    
    # Discover all spec files
    spec_files = list(specs_dir.glob("*.yaml")) + list(specs_dir.glob("*.yml")) + list(specs_dir.glob("*.json"))
    
    if not spec_files:
        click.echo("Error: No OpenAPI specification files found in specs/", err=True)
        return
    
    click.echo(f"📋 Found {len(spec_files)} specification files")
    
    # Generate catalog
    catalog = {
        "version": "1.0",
        "metadata": {
            "title": "EAT Framework Catalog",
            "description": "Auto-generated tool catalog",
            "generated_at": str(Path.cwd()),
            "generator": "eat-gen"
        },
        "tools": []
    }
    
    # Process each spec file
    for spec_file in spec_files:
        click.echo(f"  📄 Processing {spec_file.name}...")
        
        try:
            spec_data = load_spec_file(spec_file)
            tools = extract_tools_from_spec(spec_data, spec_file)
            catalog["tools"].extend(tools)
            
        except Exception as e:
            click.echo(f"    ❌ Error processing {spec_file.name}: {e}", err=True)
            continue
    
    click.echo(f"✅ Generated catalog with {len(catalog['tools'])} tools")
    
    # Sign catalog if requested
    if sign:
        if not private_key_path:
            click.echo("Error: --private-key required when using --sign", err=True)
            return
            
        click.echo("🔐 Signing catalog...")
        signer = CatalogSigner(private_key_path, key_id)
        signed_catalog = signer.sign_catalog(catalog)
        
        # Write signed catalog
        with open(output_file, 'w') as f:
            f.write(signed_catalog)
            
        click.echo(f"✅ Signed catalog written to {output_file}")
    else:
        # Write unsigned catalog
        with open(output_file, 'w') as f:
            json.dump(catalog, f, indent=2)
            
        click.echo(f"✅ Catalog written to {output_file}")


def load_spec_file(spec_file: Path) -> Dict[str, Any]:
    """Load OpenAPI specification from file."""
    with open(spec_file, 'r') as f:
        if spec_file.suffix.lower() == '.json':
            return json.load(f)
        else:
            return yaml.safe_load(f)


def extract_tools_from_spec(spec_data: Dict[str, Any], spec_file: Path) -> List[Dict[str, Any]]:
    """Extract tool definitions from OpenAPI specification."""
    tools = []
    
    # Get base server URL
    servers = spec_data.get('servers', [])
    base_url = servers[0]['url'] if servers else 'http://localhost:3000'
    
    # Process each path and operation
    paths = spec_data.get('paths', {})
    for path, path_item in paths.items():
        for method, operation in path_item.items():
            if method.lower() not in ['get', 'post', 'put', 'delete', 'patch']:
                continue
                
            # Check for x-mcp-tool extension
            mcp_tool_config = operation.get('x-mcp-tool', {})
            if not mcp_tool_config:
                continue
                
            tool = {
                "name": operation.get('operationId', f"{method}_{path.replace('/', '_').strip('_')}"),
                "description": operation.get('description', operation.get('summary', '')),
                "version": spec_data.get('info', {}).get('version', '1.0.0'),
                "spec_url": f"file://{spec_file.absolute()}",
                "spec_hash": compute_sha256(spec_file.read_bytes()),
                "x-mcp-tool": {
                    **mcp_tool_config,
                    "server_url": mcp_tool_config.get('server_url', base_url),
                    "method": method.upper(),
                    "path": path,
                    "capabilities": mcp_tool_config.get('capabilities', []),
                    "examples": mcp_tool_config.get('examples', [])
                }
            }
            
            # Add parameter schema
            parameters = operation.get('parameters', [])
            if parameters or operation.get('requestBody'):
                tool["parameters"] = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
                
                # Process parameters
                for param in parameters:
                    param_name = param['name']
                    tool["parameters"]["properties"][param_name] = param.get('schema', {})
                    if param.get('required', False):
                        tool["parameters"]["required"].append(param_name)
                
                # Process request body
                request_body = operation.get('requestBody')
                if request_body:
                    content = request_body.get('content', {})
                    json_content = content.get('application/json', {})
                    if json_content:
                        schema = json_content.get('schema', {})
                        if schema.get('properties'):
                            tool["parameters"]["properties"].update(schema['properties'])
                            tool["parameters"]["required"].extend(schema.get('required', []))
            
            tools.append(tool)
    
    return tools