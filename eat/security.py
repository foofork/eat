"""
Security implementation for EAT Framework including JWS signing and verification.
"""

import json
import hashlib
import logging
from typing import Any, Dict, Optional
from urllib.parse import urlparse
import aiohttp
import jwt
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class CatalogSigner:
    """Signs EAT catalogs using JWS (JSON Web Signature)."""
    
    def __init__(self, private_key_path: str, key_id: Optional[str] = None):
        self.private_key = self._load_private_key(private_key_path)
        self.key_id = key_id
        
    def _load_private_key(self, private_key_path: str):
        """Load private key from PEM file."""
        try:
            with open(private_key_path, 'rb') as f:
                private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                    backend=default_backend()
                )
            return private_key
        except Exception as e:
            logger.error(f"Failed to load private key from {private_key_path}: {e}")
            raise
    
    def sign_catalog(self, catalog: Dict[str, Any]) -> str:
        """Sign catalog with JWS using RS256 algorithm."""
        try:
            # Add content hashes for all referenced specs
            catalog_with_hashes = self._add_content_hashes(catalog)
            
            # Prepare JWS headers
            headers = {
                "alg": "RS256",
                "typ": "JWT"
            }
            if self.key_id:
                headers["kid"] = self.key_id
                
            # Sign the catalog
            signed_token = jwt.encode(
                catalog_with_hashes,
                self.private_key,
                algorithm="RS256",
                headers=headers
            )
            
            logger.info("Catalog signed successfully")
            return signed_token
            
        except Exception as e:
            logger.error(f"Failed to sign catalog: {e}")
            raise
    
    def _add_content_hashes(self, catalog: Dict[str, Any]) -> Dict[str, Any]:
        """Add SHA-256 hashes for all referenced content."""
        catalog_copy = catalog.copy()
        
        # Add hashes for tool specifications
        for tool in catalog_copy.get('tools', []):
            spec_url = tool.get('spec_url')
            if spec_url and 'spec_hash' not in tool:
                # Note: In production, you'd fetch and hash the actual content
                # For now, we'll generate a placeholder hash
                tool['spec_hash'] = self._compute_placeholder_hash(spec_url)
                
        return catalog_copy
    
    def _compute_placeholder_hash(self, url: str) -> str:
        """Compute placeholder hash for development purposes."""
        # In production, this should fetch the actual content and hash it
        return hashlib.sha256(url.encode()).hexdigest()


class CatalogVerifier:
    """Verifies EAT catalog signatures and content integrity."""
    
    def __init__(self, trusted_keys: Optional[Dict[str, str]] = None):
        self.trusted_keys = trusted_keys or {}
        
    async def verify_catalog(self, signed_catalog: str, catalog_url: str) -> Dict[str, Any]:
        """Verify JWS signature and return catalog content."""
        try:
            # Decode JWT header to get key information
            header = jwt.get_unverified_header(signed_catalog)
            algorithm = header.get('alg', 'RS256')
            key_id = header.get('kid')
            
            # Get public key for verification
            public_key = await self._get_public_key(catalog_url, key_id)
            
            # Verify and decode the catalog
            catalog = jwt.decode(
                signed_catalog,
                public_key,
                algorithms=[algorithm],
                options={"verify_exp": False}  # EAT catalogs don't typically expire
            )
            
            logger.info("Catalog signature verified successfully")
            return catalog
            
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid JWT token: {e}")
            raise SecurityError(f"Catalog signature verification failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during verification: {e}")
            raise SecurityError(f"Catalog verification failed: {e}")
    
    async def _get_public_key(self, catalog_url: str, key_id: Optional[str] = None):
        """Get public key for signature verification using DID:web resolution."""
        try:
            # Extract domain from catalog URL for DID:web resolution
            parsed_url = urlparse(catalog_url)
            domain = parsed_url.netloc
            
            # Construct DID:web URL for key resolution
            did_web_url = f"https://{domain}/.well-known/did.json"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(did_web_url) as response:
                    if response.status == 200:
                        did_document = await response.json()
                        return self._extract_public_key_from_did(did_document, key_id)
                    
            # Fallback: look for trusted key in configuration
            if key_id and key_id in self.trusted_keys:
                return self._load_public_key_from_string(self.trusted_keys[key_id])
                
            # Fallback: use jwks_uri from catalog metadata
            return await self._get_key_from_jwks(catalog_url, key_id)
            
        except Exception as e:
            logger.error(f"Failed to get public key: {e}")
            raise SecurityError(f"Could not retrieve public key for verification: {e}")
    
    def _extract_public_key_from_did(self, did_document: Dict[str, Any], key_id: Optional[str]):
        """Extract public key from DID document."""
        verification_methods = did_document.get('verificationMethod', [])
        
        for method in verification_methods:
            if not key_id or method.get('id', '').endswith(key_id):
                public_key_jwk = method.get('publicKeyJwk')
                if public_key_jwk:
                    return jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(public_key_jwk))
                    
        raise SecurityError("No suitable public key found in DID document")
    
    async def _get_key_from_jwks(self, catalog_url: str, key_id: Optional[str]):
        """Get public key from JWKS endpoint."""
        parsed_url = urlparse(catalog_url)
        jwks_url = f"{parsed_url.scheme}://{parsed_url.netloc}/.well-known/jwks.json"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(jwks_url) as response:
                    response.raise_for_status()
                    jwks = await response.json()
                    
            keys = jwks.get('keys', [])
            for key in keys:
                if not key_id or key.get('kid') == key_id:
                    return jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
                    
            raise SecurityError("No suitable key found in JWKS")
            
        except Exception as e:
            logger.error(f"Failed to fetch JWKS from {jwks_url}: {e}")
            raise SecurityError(f"Could not retrieve JWKS: {e}")
    
    def _load_public_key_from_string(self, key_string: str):
        """Load public key from PEM string."""
        try:
            return serialization.load_pem_public_key(
                key_string.encode(),
                backend=default_backend()
            )
        except Exception as e:
            logger.error(f"Failed to load public key from string: {e}")
            raise SecurityError(f"Invalid public key format: {e}")


def compute_sha256(content: bytes) -> str:
    """Compute SHA-256 hash for content integrity verification."""
    return hashlib.sha256(content).hexdigest()


async def verify_content_integrity(url: str, expected_hash: str) -> bool:
    """Verify downloaded content matches expected SHA-256 hash."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                content = await response.read()
                
        actual_hash = compute_sha256(content)
        return actual_hash == expected_hash
        
    except Exception as e:
        logger.error(f"Failed to verify content integrity for {url}: {e}")
        return False


class SecurityError(Exception):
    """Exception raised for security-related errors."""
    pass