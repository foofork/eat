"""
Tests for EAT Framework security functionality.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, AsyncMock, MagicMock

from eat.security import CatalogSigner, CatalogVerifier, SecurityError, compute_sha256, verify_content_integrity


class TestCatalogSigner:
    """Test cases for CatalogSigner class."""
    
    @pytest.fixture
    def private_key_file(self):
        """Create a temporary private key file for testing."""
        # This is a test RSA private key - DO NOT use in production
        test_private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA1fI7k8VTfP8aL5wN9xK7XVBZ5YpJ6Zw5H5N8cFqJ5Y9sF3qw
E7l5X5K5r5qJ5N8s5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s
5q5w5K5N8s5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s5q5w5K
5N8s5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s5q5w5K5N8s5F
8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9
s5q5w5K5N8s5F8qJ5Y9s5q5wIDAQABAoIBAG7yJ5K5r5qJ5N8s5F8qJ5Y9s5q5w
5K5N8s5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s5q5w5K5N8s
5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s5q5w5K5N8s5F8qJ5
Y9s5q5w5K5N8s5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s5q5
w5K5N8s5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s5q5w5K5N8
s5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s5q5w5K5N8s5F8qJ
5Y9s5q5wECgYEA9fI7k8VTfP8aL5wN9xK7XVBZ5YpJ6Zw5H5N8cFqJ5Y9sF3qw
E7l5X5K5r5qJ5N8s5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s
5q5w5K5N8s5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s5q5w5K
ECgYEA3fI7k8VTfP8aL5wN9xK7XVBZ5YpJ6Zw5H5N8cFqJ5Y9sF3qwE7l5X5K5
r5qJ5N8s5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s5q5w5K5N
8s5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s5q5w5K5N8s5F8qJ5Y9s5q5w5K5N8s5F8q
-----END RSA PRIVATE KEY-----"""
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem') as f:
            f.write(test_private_key)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        os.unlink(temp_path)
    
    @pytest.fixture
    def sample_catalog(self):
        """Sample catalog for signing tests."""
        return {
            "version": "1.0",
            "metadata": {
                "title": "Test Catalog",
                "description": "Catalog for testing signature functionality"
            },
            "tools": [
                {
                    "name": "test_tool",
                    "description": "A test tool",
                    "spec_url": "http://example.com/spec.yaml"
                }
            ]
        }
    
    def test_signer_initialization_with_valid_key(self, private_key_file):
        """Test signer initialization with valid private key."""
        signer = CatalogSigner(private_key_file)
        assert signer.private_key is not None
        assert signer.key_id is None
        
        # Test with key ID
        signer_with_id = CatalogSigner(private_key_file, key_id="test-key-1")
        assert signer_with_id.key_id == "test-key-1"
    
    def test_signer_initialization_with_invalid_key(self):
        """Test signer initialization with invalid private key."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("invalid key content")
            invalid_key_path = f.name
        
        try:
            with pytest.raises(Exception):  # Should raise some exception for invalid key
                CatalogSigner(invalid_key_path)
        finally:
            os.unlink(invalid_key_path)
    
    def test_signer_initialization_with_missing_file(self):
        """Test signer initialization with missing key file."""
        with pytest.raises(Exception):  # Should raise FileNotFoundError or similar
            CatalogSigner("/nonexistent/key.pem")
    
    @patch('eat.security.jwt.encode')
    def test_sign_catalog_success(self, mock_jwt_encode, private_key_file, sample_catalog):
        """Test successful catalog signing."""
        mock_jwt_encode.return_value = "signed.jwt.token"
        
        signer = CatalogSigner(private_key_file)
        result = signer.sign_catalog(sample_catalog)
        
        assert result == "signed.jwt.token"
        mock_jwt_encode.assert_called_once()
        
        # Check that the call included the right parameters
        call_args = mock_jwt_encode.call_args
        assert call_args[1]['algorithm'] == 'RS256'
    
    @patch('eat.security.jwt.encode')
    def test_sign_catalog_with_key_id(self, mock_jwt_encode, private_key_file, sample_catalog):
        """Test catalog signing with key ID."""
        mock_jwt_encode.return_value = "signed.jwt.token"
        
        signer = CatalogSigner(private_key_file, key_id="test-key-1")
        result = signer.sign_catalog(sample_catalog)
        
        assert result == "signed.jwt.token"
        
        # Check that headers include key ID
        call_args = mock_jwt_encode.call_args
        headers = call_args[1]['headers']
        assert headers['kid'] == 'test-key-1'
    
    def test_add_content_hashes(self, private_key_file, sample_catalog):
        """Test adding content hashes to catalog."""
        signer = CatalogSigner(private_key_file)
        catalog_with_hashes = signer._add_content_hashes(sample_catalog)
        
        # Check that hashes were added
        assert 'spec_hash' in catalog_with_hashes['tools'][0]
        assert catalog_with_hashes['tools'][0]['spec_hash'] is not None
    
    def test_compute_placeholder_hash(self, private_key_file):
        """Test placeholder hash computation."""
        signer = CatalogSigner(private_key_file)
        
        url1 = "http://example.com/spec1.yaml"
        url2 = "http://example.com/spec2.yaml"
        
        hash1 = signer._compute_placeholder_hash(url1)
        hash2 = signer._compute_placeholder_hash(url2)
        
        # Hashes should be different for different URLs
        assert hash1 != hash2
        
        # Same URL should produce same hash
        hash1_repeat = signer._compute_placeholder_hash(url1)
        assert hash1 == hash1_repeat
        
        # Hash should be 64 characters (SHA-256)
        assert len(hash1) == 64
        assert all(c in '0123456789abcdef' for c in hash1)


class TestCatalogVerifier:
    """Test cases for CatalogVerifier class."""
    
    @pytest.fixture
    def sample_signed_catalog(self):
        """Sample signed catalog JWT token."""
        # This is a mock JWT token for testing
        return "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ2ZXJzaW9uIjoiMS4wIiwidG9vbHMiOlt7Im5hbWUiOiJ0ZXN0X3Rvb2wifV19.signature"
    
    def test_verifier_initialization(self):
        """Test verifier initialization."""
        verifier = CatalogVerifier()
        assert verifier.trusted_keys == {}
        
        trusted_keys = {"key1": "public_key_content"}
        verifier_with_keys = CatalogVerifier(trusted_keys)
        assert verifier_with_keys.trusted_keys == trusted_keys
    
    @pytest.mark.asyncio
    async def test_verify_catalog_with_mock_key(self, sample_signed_catalog):
        """Test catalog verification with mocked key resolution."""
        verifier = CatalogVerifier()
        
        with patch.object(verifier, '_get_public_key') as mock_get_key:
            with patch('eat.security.jwt.decode') as mock_jwt_decode:
                mock_get_key.return_value = "mock_public_key"
                mock_jwt_decode.return_value = {"version": "1.0", "tools": []}
                
                result = await verifier.verify_catalog(sample_signed_catalog, "http://example.com/.well-known/api-catalog")
                
                assert result == {"version": "1.0", "tools": []}
                mock_jwt_decode.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verify_catalog_with_invalid_token(self, sample_signed_catalog):
        """Test catalog verification with invalid JWT token."""
        verifier = CatalogVerifier()
        
        with patch.object(verifier, '_get_public_key') as mock_get_key:
            with patch('eat.security.jwt.decode') as mock_jwt_decode:
                from jwt import InvalidTokenError
                mock_get_key.return_value = "mock_public_key"
                mock_jwt_decode.side_effect = InvalidTokenError("Invalid token")
                
                with pytest.raises(SecurityError, match="Catalog signature verification failed"):
                    await verifier.verify_catalog(sample_signed_catalog, "http://example.com/.well-known/api-catalog")
    
    @pytest.mark.asyncio
    async def test_get_public_key_from_did_web(self):
        """Test public key resolution from DID:web document."""
        verifier = CatalogVerifier()
        
        mock_did_document = {
            "verificationMethod": [
                {
                    "id": "did:web:example.com#key1",
                    "publicKeyJwk": {
                        "kty": "RSA",
                        "n": "test_modulus",
                        "e": "AQAB"
                    }
                }
            ]
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_did_document)
            
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)
            
            with patch('eat.security.jwt.algorithms.RSAAlgorithm.from_jwk') as mock_from_jwk:
                mock_from_jwk.return_value = "mock_public_key"
                
                result = await verifier._get_public_key("http://example.com/.well-known/api-catalog", "key1")
                
                assert result == "mock_public_key"
                mock_from_jwk.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_public_key_from_jwks(self):
        """Test public key resolution from JWKS endpoint."""
        verifier = CatalogVerifier()
        
        mock_jwks = {
            "keys": [
                {
                    "kid": "test-key",
                    "kty": "RSA",
                    "n": "test_modulus",
                    "e": "AQAB"
                }
            ]
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock DID:web failure, JWKS success
            responses = [
                AsyncMock(status=404),  # DID:web not found
                AsyncMock(status=200, json=AsyncMock(return_value=mock_jwks))  # JWKS found
            ]
            
            mock_get.return_value.__aenter__ = AsyncMock(side_effect=responses)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)
            
            with patch('eat.security.jwt.algorithms.RSAAlgorithm.from_jwk') as mock_from_jwk:
                mock_from_jwk.return_value = "mock_public_key"
                
                result = await verifier._get_public_key("http://example.com/.well-known/api-catalog", "test-key")
                
                assert result == "mock_public_key"
    
    @pytest.mark.asyncio
    async def test_get_public_key_failure(self):
        """Test public key resolution failure."""
        verifier = CatalogVerifier()
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            with pytest.raises(SecurityError, match="Could not retrieve public key for verification"):
                await verifier._get_public_key("http://example.com/.well-known/api-catalog", "key1")


class TestSecurityUtilities:
    """Test cases for security utility functions."""
    
    def test_compute_sha256(self):
        """Test SHA-256 hash computation."""
        test_content = b"Hello, world!"
        expected_hash = "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"
        
        result = compute_sha256(test_content)
        
        assert result == expected_hash
        assert len(result) == 64  # SHA-256 produces 64-character hex string
    
    def test_compute_sha256_empty_content(self):
        """Test SHA-256 hash computation with empty content."""
        empty_content = b""
        expected_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        
        result = compute_sha256(empty_content)
        
        assert result == expected_hash
    
    def test_compute_sha256_different_inputs(self):
        """Test that different inputs produce different hashes."""
        content1 = b"content1"
        content2 = b"content2"
        
        hash1 = compute_sha256(content1)
        hash2 = compute_sha256(content2)
        
        assert hash1 != hash2
        assert len(hash1) == len(hash2) == 64
    
    @pytest.mark.asyncio
    async def test_verify_content_integrity_success(self):
        """Test successful content integrity verification."""
        test_content = b"test content for verification"
        expected_hash = compute_sha256(test_content)
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.read = AsyncMock(return_value=test_content)
            
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await verify_content_integrity("http://example.com/content", expected_hash)
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_content_integrity_failure(self):
        """Test content integrity verification failure."""
        test_content = b"actual content"
        wrong_hash = compute_sha256(b"different content")
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.read = AsyncMock(return_value=test_content)
            
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await verify_content_integrity("http://example.com/content", wrong_hash)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_content_integrity_network_error(self):
        """Test content integrity verification with network error."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            result = await verify_content_integrity("http://example.com/content", "any_hash")
            
            assert result is False


class TestSecurityError:
    """Test cases for SecurityError exception."""
    
    def test_security_error_creation(self):
        """Test SecurityError exception creation."""
        error = SecurityError("Security violation")
        assert str(error) == "Security violation"
        assert isinstance(error, Exception)
    
    def test_security_error_inheritance(self):
        """Test that SecurityError inherits from Exception."""
        error = SecurityError("Test error")
        assert isinstance(error, Exception)


if __name__ == "__main__":
    pytest.main([__file__])