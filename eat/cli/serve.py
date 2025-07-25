"""
Development server for testing EAT catalogs locally.
"""

import asyncio
import json
import mimetypes
from pathlib import Path
from typing import Optional
import click
from aiohttp import web, web_request
from aiohttp.web_response import Response


async def serve_catalog(host: str, port: int, directory: str):
    """Serve EAT catalog and related files locally."""
    
    directory_path = Path(directory).resolve()
    
    click.echo(f"🚀 Starting EAT development server...")
    click.echo(f"📁 Serving directory: {directory_path}")
    
    app = web.Application()
    
    # Add routes
    app.router.add_get('/.well-known/api-catalog', catalog_handler)
    app.router.add_get('/', index_handler)
    app.router.add_static('/', path=str(directory_path), show_index=True)
    
    # Store directory path in app for handlers
    app['directory'] = directory_path
    
    # Start server
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    catalog_url = f"http://{host}:{port}/.well-known/api-catalog"
    browser_url = f"http://{host}:{port}"
    
    click.echo(f"✅ Server running at:")
    click.echo(f"   📋 Catalog: {catalog_url}")
    click.echo(f"   🌐 Browser: {browser_url}")
    click.echo(f"")
    click.echo(f"Press Ctrl+C to stop the server")
    
    try:
        # Keep server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        click.echo(f"\n🛑 Shutting down server...")
        await runner.cleanup()


async def catalog_handler(request: web_request.Request) -> Response:
    """Serve the API catalog."""
    directory = request.app['directory']
    
    # Look for catalog file
    catalog_files = ['catalog.json', 'catalog.jwt', 'api-catalog.json', 'api-catalog.jwt']
    
    for filename in catalog_files:
        catalog_file = directory / filename
        if catalog_file.exists():
            content = catalog_file.read_text()
            
            # Determine content type
            if filename.endswith('.jwt'):
                content_type = 'application/jwt'
            else:
                content_type = 'application/json'
            
            return Response(
                text=content,
                content_type=content_type,
                headers={
                    'Access-Control-Allow-Origin': '*',
                    'Cache-Control': 'no-cache'
                }
            )
    
    # Generate minimal catalog if none found
    minimal_catalog = {
        "version": "1.0",
        "metadata": {
            "title": "EAT Development Catalog",
            "description": "Auto-generated development catalog",
            "generator": "eat-serve"
        },
        "tools": []
    }
    
    return Response(
        text=json.dumps(minimal_catalog, indent=2),
        content_type='application/json',
        headers={
            'Access-Control-Allow-Origin': '*',
            'Cache-Control': 'no-cache'
        }
    )


async def index_handler(request: web_request.Request) -> Response:
    """Serve the catalog browser interface."""
    directory = request.app['directory']
    
    # Look for custom index.html
    index_file = directory / 'index.html'
    site_index = directory / 'site' / 'index.html'
    
    if index_file.exists():
        return Response(
            text=index_file.read_text(),
            content_type='text/html'
        )
    elif site_index.exists():
        return Response(
            text=site_index.read_text(),
            content_type='text/html'
        )
    
    # Generate default catalog browser
    browser_html = generate_catalog_browser(request)
    
    return Response(
        text=browser_html,
        content_type='text/html'
    )


def generate_catalog_browser(request: web_request.Request) -> str:
    """Generate default catalog browser HTML."""
    base_url = f"{request.scheme}://{request.host}"
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EAT Framework - Tool Catalog Browser</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ padding: 20px; }}
        .tool {{ border: 1px solid #ddd; border-radius: 4px; padding: 15px; margin-bottom: 15px; }}
        .tool-name {{ font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 5px; }}
        .tool-description {{ color: #666; margin-bottom: 10px; }}
        .capabilities {{ display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: 10px; }}
        .capability {{ background: #3498db; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; }}
        .example {{ background: #ecf0f1; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 14px; }}
        .loading {{ text-align: center; padding: 40px; color: #666; }}
        .error {{ background: #e74c3c; color: white; padding: 15px; border-radius: 4px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 EAT Framework Tool Catalog</h1>
            <p>Discoverable tools for AI agents</p>
        </div>
        <div class="content">
            <div id="status" class="loading">Loading catalog...</div>
            <div id="tools"></div>
        </div>
    </div>

    <script>
        async function loadCatalog() {{
            try {{
                const response = await fetch('{base_url}/.well-known/api-catalog');
                if (!response.ok) throw new Error(`HTTP ${{response.status}}: ${{response.statusText}}`);
                
                const catalog = await response.json();
                displayCatalog(catalog);
            }} catch (error) {{
                document.getElementById('status').innerHTML = `
                    <div class="error">
                        <strong>Error loading catalog:</strong> ${{error.message}}
                        <br><br>
                        <strong>Troubleshooting:</strong>
                        <ul style="text-align: left; display: inline-block;">
                            <li>Make sure you have a catalog.json file in the directory</li>
                            <li>Run <code>eat-gen</code> to generate a catalog from specs/</li>
                            <li>Check that your OpenAPI specs have x-mcp-tool extensions</li>
                        </ul>
                    </div>
                `;
            }}
        }}

        function displayCatalog(catalog) {{
            const statusDiv = document.getElementById('status');
            const toolsDiv = document.getElementById('tools');
            
            if (!catalog.tools || catalog.tools.length === 0) {{
                statusDiv.innerHTML = '<div class="error">No tools found in catalog. Add OpenAPI specs with x-mcp-tool extensions to the specs/ directory.</div>';
                return;
            }}
            
            statusDiv.innerHTML = `<p>✅ Loaded ${{catalog.tools.length}} tools from catalog</p>`;
            
            toolsDiv.innerHTML = catalog.tools.map(tool => `
                <div class="tool">
                    <div class="tool-name">${{tool.name}}</div>
                    <div class="tool-description">${{tool.description || 'No description available'}}</div>
                    ${{tool['x-mcp-tool']?.capabilities ? `
                        <div class="capabilities">
                            ${{tool['x-mcp-tool'].capabilities.map(cap => `<span class="capability">${{cap}}</span>`).join('')}}
                        </div>
                    ` : ''}}
                    ${{tool['x-mcp-tool']?.examples?.[0] ? `
                        <div class="example">
                            <strong>Example usage:</strong><br>
                            ${{JSON.stringify(tool['x-mcp-tool'].examples[0], null, 2)}}
                        </div>
                    ` : ''}}
                </div>
            `).join('');
        }}

        loadCatalog();
    </script>
</body>
</html>"""