"""
Main CLI entry point for EAT Framework tools.
"""

import click
import asyncio
import json
import os
from pathlib import Path
from typing import Optional

from ..security import CatalogSigner
from .generate import generate_catalog
from .serve import serve_catalog


@click.group()
@click.version_option()
def cli():
    """EAT - Ephemeral Agent Toolkit
    
    Tool discovery and execution framework for AI agents.
    """
    pass


@cli.command()
@click.argument('directory', default='.', type=click.Path(exists=True))
@click.option('--output', '-o', default='catalog.json', help='Output catalog file')
@click.option('--sign', is_flag=True, help='Sign the catalog with JWS')
@click.option('--private-key', type=click.Path(exists=True), help='Private key for signing')
@click.option('--key-id', help='Key ID for signature header')
def generate(directory: str, output: str, sign: bool, private_key: Optional[str], key_id: Optional[str]):
    """Generate signed catalog from specs/ directory."""
    asyncio.run(generate_catalog(directory, output, sign, private_key, key_id))


@cli.command()
@click.option('--port', default=8000, help='Port to serve on')
@click.option('--host', default='localhost', help='Host to bind to')
@click.argument('directory', default='.', type=click.Path(exists=True))
def serve(port: int, host: str, directory: str):
    """Serve catalog locally for development."""
    asyncio.run(serve_catalog(host, port, directory))


if __name__ == '__main__':
    cli()