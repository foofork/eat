"""
EAT Framework - Ephemeral Agent Toolkit

One-hop tool discovery for AI agents with secure, signed catalogs.
"""

from .discovery import Catalog, Tool
from .mcp_client import MCPClient
from .security import CatalogSigner, CatalogVerifier

__version__ = "0.1.0"
__all__ = ["Catalog", "Tool", "MCPClient", "CatalogSigner", "CatalogVerifier"]