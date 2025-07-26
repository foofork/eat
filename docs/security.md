# EAT Framework Security Model

This document provides a comprehensive analysis of the EAT Framework security architecture, threat model, and security best practices for production deployment.

## 🛡️ Security Overview

The EAT Framework implements **defense-in-depth** security using multiple layers of protection:

1. **Cryptographic Integrity**: JWS signatures with DID:web key resolution
2. **Content Verification**: SHA-256 hashes for all referenced resources
3. **Transport Security**: HTTPS/TLS for all network communication
4. **Access Controls**: Authentication and authorization patterns
5. **Audit Trails**: Comprehensive logging and monitoring

## 🔐 Cryptographic Architecture

### JWS (JSON Web Signature) Implementation

#### Signature Generation Process
```
1. Canonical JSON Serialization
   ├── Sort object keys deterministically
   ├── Remove whitespace and formatting
   └── Generate reproducible byte representation

2. Content Hash Generation
   ├── SHA-256 hash of canonical catalog JSON
   └── Include hash in JWS payload

3. JWS Token Creation
   ├── Header: {"alg": "RS256", "typ": "JWT", "kid": "key-id"}
   ├── Payload: {"iss": "did:web:domain", "iat": timestamp, "exp": expiry, "catalog_hash": "sha256:..."}
   └── Signature: RS256(header.payload, private_key)

4. Publication
   ├── Signed catalog: /.well-known/api-catalog
   └── Verification key: /.well-known/did.json
```

#### Signature Verification Process
```
1. Download signed catalog and extract JWS token
2. Parse JWS header to get key identifier (kid)
3. Resolve issuer DID to get public key
4. Verify JWS signature using RS256 algorithm
5. Validate timestamp claims (iat, exp)
6. Recompute catalog hash and compare with JWS payload
7. Accept catalog only if all verifications pass
```

### DID:web Key Resolution

#### DID Document Structure
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
  ],
  "service": [
    {
      "id": "did:web:api.company.com#catalog",
      "type": "EATCatalog",
      "serviceEndpoint": "https://api.company.com/.well-known/api-catalog"
    }
  ],
  "created": "2024-01-01T00:00:00Z",
  "updated": "2024-01-20T10:30:00Z"
}
```

#### Key Resolution Algorithm
```python
def resolve_did_web_key(did_identifier, key_id):
    """
    Resolve DID:web to public key for signature verification
    """
    # Extract domain from DID
    domain = did_identifier.replace("did:web:", "")
    
    # Construct DID document URL
    did_doc_url = f"https://{domain}/.well-known/did.json"
    
    # Download and parse DID document
    response = requests.get(did_doc_url, verify=True)
    did_doc = response.json()
    
    # Find verification method
    for method in did_doc["verificationMethod"]:
        if method["id"].endswith(f"#{key_id}"):
            return method["publicKeyPem"]
    
    raise KeyNotFoundError(f"Key {key_id} not found in DID document")
```

### Content Integrity Verification

#### SHA-256 Hash Implementation
```python
import hashlib
import json

def calculate_content_hash(content: str) -> str:
    """
    Calculate SHA-256 hash of content for integrity verification
    """
    # Ensure consistent encoding
    content_bytes = content.encode('utf-8')
    
    # Calculate SHA-256
    hash_obj = hashlib.sha256(content_bytes)
    hash_hex = hash_obj.hexdigest()
    
    return f"sha256:{hash_hex}"

def verify_content_integrity(content: str, expected_hash: str) -> bool:
    """
    Verify content matches expected hash
    """
    actual_hash = calculate_content_hash(content)
    return actual_hash == expected_hash
```

#### Catalog Hash Validation
```python
def verify_catalog_integrity(catalog_json: dict, jws_payload: dict) -> bool:
    """
    Verify catalog content matches JWS payload hash
    """
    # Canonicalize catalog JSON
    canonical_json = json.dumps(catalog_json, sort_keys=True, separators=(',', ':'))
    
    # Calculate actual hash
    actual_hash = calculate_content_hash(canonical_json)
    
    # Compare with JWS payload
    expected_hash = jws_payload.get("catalog_hash")
    
    return actual_hash == expected_hash
```

## 🚨 Threat Model

### Assets to Protect

| Asset | Value | Impact if Compromised |
|-------|-------|----------------------|
| **Tool Catalogs** | High | Agents execute malicious tools |
| **OpenAPI Specifications** | Medium | Incorrect tool usage, data exposure |
| **Private Signing Keys** | Critical | Ability to forge catalogs |
| **Agent Credentials** | High | Unauthorized tool access |
| **Tool Execution Context** | Medium | Data leakage, privilege escalation |

### Threat Actors

| Actor | Motivation | Capabilities | Likelihood |
|-------|------------|--------------|------------|
| **External Attackers** | Financial gain, disruption | Network access, basic tools | High |
| **Malicious Insiders** | Sabotage, data theft | System access, credentials | Medium |
| **Nation-State Actors** | Espionage, disruption | Advanced persistent threats | Low |
| **Accidental Misuse** | Human error | Legitimate access | High |

### Attack Vectors

#### 1. Catalog Tampering
**Attack**: Modify catalog to redirect agents to malicious tools

**Technical Details**:
```
1. Attacker gains access to catalog hosting
2. Modifies catalog JSON to point to malicious MCP servers
3. Agents download tampered catalog
4. Agents execute malicious tools believing they're legitimate
```

**Mitigations**:
- ✅ JWS signatures prevent undetected modification
- ✅ Hash verification ensures content integrity
- ✅ HTTPS prevents man-in-the-middle attacks
- ✅ Certificate pinning for critical catalogs

#### 2. Specification Substitution
**Attack**: Replace OpenAPI specs with malicious versions

**Technical Details**:
```
1. Attacker compromises spec hosting infrastructure
2. Replaces legitimate OpenAPI specs with malicious versions
3. Agents download specs and execute based on false information
4. Results in incorrect tool usage or data exposure
```

**Mitigations**:
- ✅ SHA-256 hashes in catalog prevent undetected substitution
- ✅ Content verification before spec usage
- ✅ Immutable spec storage (content-addressed)
- ✅ Regular integrity audits

#### 3. Key Compromise
**Attack**: Obtain private signing keys to forge catalogs

**Technical Details**:
```
1. Attacker gains access to key storage
2. Uses private key to sign malicious catalogs
3. Distributes forged catalogs with valid signatures
4. Agents trust malicious catalogs due to valid signatures
```

**Mitigations**:
- ✅ Hardware Security Modules (HSMs) for key storage
- ✅ Key rotation with expiration timestamps
- ✅ Multi-signature schemes for critical catalogs
- ✅ Access logging and monitoring

#### 4. Man-in-the-Middle (MITM)
**Attack**: Intercept and modify communications

**Technical Details**:
```
1. Attacker positions between agent and catalog server
2. Intercepts catalog requests
3. Returns modified catalog or specs
4. Agent executes based on tampered information
```

**Mitigations**:
- ✅ HTTPS/TLS for all communications
- ✅ Certificate validation and pinning
- ✅ HTTP Strict Transport Security (HSTS)
- ✅ Certificate Transparency monitoring

#### 5. Replay Attacks
**Attack**: Reuse old signed catalogs to bypass updates

**Technical Details**:
```
1. Attacker captures old, validly signed catalog
2. Serves old catalog to agents instead of current version
3. Agents use outdated tools with known vulnerabilities
4. Exploitation of deprecated or insecure tools
```

**Mitigations**:
- ✅ Timestamp validation in JWS payload (iat, exp)
- ✅ Catalog versioning and sequence numbers
- ✅ Regular catalog refresh intervals
- ✅ Cache-control headers preventing stale content

### Risk Assessment Matrix

| Threat | Probability | Impact | Risk Level | Mitigation Priority |
|--------|-------------|--------|------------|-------------------|
| **Catalog Tampering** | Medium | High | 🔴 High | Critical |
| **Spec Substitution** | Medium | Medium | 🟡 Medium | High |
| **Key Compromise** | Low | Critical | 🔴 High | Critical |
| **MITM Attack** | Medium | High | 🔴 High | Critical |
| **Replay Attack** | Low | Medium | 🟡 Medium | Medium |
| **DDoS on Catalog** | High | Low | 🟡 Medium | Medium |
| **Credential Theft** | Medium | High | 🔴 High | High |

## 🔒 Security Controls

### Cryptographic Controls

#### Key Management
```yaml
Key Lifecycle:
  Generation:
    - Use RSA 2048-bit minimum (4096-bit recommended)
    - Generate in secure environment (HSM preferred)
    - Store with appropriate access controls
  
  Distribution:
    - Publish public keys via DID:web
    - Use Certificate Transparency for monitoring
    - Implement key pinning for critical clients
  
  Rotation:
    - Rotate keys every 12 months maximum
    - Emergency rotation procedures for compromise
    - Gradual rollout with overlap periods
  
  Revocation:
    - Immediate revocation for compromised keys
    - Distribute revocation via multiple channels
    - Monitor for usage of revoked keys
```

#### Signature Validation
```python
def validate_jws_security(jws_token: str) -> bool:
    """
    Comprehensive JWS security validation
    """
    try:
        # Parse JWS components
        header, payload, signature = parse_jws(jws_token)
        
        # Validate header
        if header.get("alg") != "RS256":
            raise SecurityError("Invalid signature algorithm")
        
        if not header.get("kid"):
            raise SecurityError("Missing key identifier")
        
        # Validate payload timestamps
        now = time.time()
        iat = payload.get("iat", 0)
        exp = payload.get("exp", 0)
        
        if iat > now + 60:  # 60-second clock skew tolerance
            raise SecurityError("Token issued in future")
        
        if exp < now:
            raise SecurityError("Token expired")
        
        if exp - iat > 86400:  # Maximum 24-hour validity
            raise SecurityError("Token validity period too long")
        
        # Validate issuer
        issuer = payload.get("iss")
        if not issuer or not issuer.startswith("did:web:"):
            raise SecurityError("Invalid or missing issuer")
        
        return True
        
    except Exception as e:
        log_security_event("jws_validation_failed", {"error": str(e)})
        return False
```

### Transport Security

#### HTTPS Configuration
```nginx
# Nginx security configuration for catalog hosting
server {
    listen 443 ssl http2;
    server_name api.company.com;
    
    # SSL Configuration
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305;
    ssl_prefer_server_ciphers off;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header Content-Security-Policy "default-src 'self'";
    
    # Catalog endpoint
    location /.well-known/api-catalog {
        add_header Cache-Control "public, max-age=300";
        add_header X-Content-Type-Options nosniff;
        try_files $uri =404;
    }
    
    # DID document
    location /.well-known/did.json {
        add_header Cache-Control "public, max-age=3600";
        add_header X-Content-Type-Options nosniff;
        try_files $uri =404;
    }
}
```

#### Certificate Pinning
```python
import ssl
import certifi
from urllib3.util import ssl_

def create_secure_context(pinned_certs=None):
    """
    Create SSL context with certificate pinning
    """
    context = ssl.create_default_context(cafile=certifi.where())
    
    # Enable hostname checking
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    
    # Configure strong ciphers
    context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
    
    # Certificate pinning
    if pinned_certs:
        def cert_verifier(cert, hostname, is_verified):
            cert_der = ssl.DER_cert_to_PEM_cert(cert).encode('utf-8')
            cert_hash = hashlib.sha256(cert_der).hexdigest()
            return cert_hash in pinned_certs
        
        context.set_cert_verifier(cert_verifier)
    
    return context
```

### Access Controls

#### Authentication Patterns
```yaml
Authentication Methods:
  Bearer Tokens:
    - JWT tokens with short expiration
    - Include required scopes in token
    - Validate token on every request
  
  API Keys:
    - Long-lived keys for automated systems
    - Scope-limited permissions
    - Regular rotation and monitoring
  
  OAuth 2.0:
    - Standard flows for user authentication
    - PKCE for public clients
    - Refresh token rotation
  
  mTLS (Mutual TLS):
    - Certificate-based authentication
    - High-security environments
    - Client certificate validation
```

#### Authorization Model
```python
class ToolAuthorization:
    """
    Authorization enforcement for tool execution
    """
    
    def __init__(self, policy_engine):
        self.policy = policy_engine
    
    def authorize_tool_access(self, agent_context, tool_name, operation):
        """
        Authorize agent access to specific tool operation
        """
        # Extract agent identity and permissions
        agent_id = agent_context.get("agent_id")
        scopes = agent_context.get("scopes", [])
        
        # Check tool-specific permissions
        required_scope = f"tools:{tool_name}:{operation}"
        if required_scope not in scopes:
            raise AuthorizationError(f"Missing scope: {required_scope}")
        
        # Apply policy rules
        policy_result = self.policy.evaluate({
            "agent_id": agent_id,
            "tool": tool_name,
            "operation": operation,
            "timestamp": time.time()
        })
        
        if not policy_result.allowed:
            raise AuthorizationError(f"Policy denied: {policy_result.reason}")
        
        return True
```

### Audit and Monitoring

#### Security Event Logging
```python
import json
import time
from datetime import datetime

class SecurityLogger:
    """
    Structured security event logging
    """
    
    def log_catalog_access(self, agent_id, catalog_url, signature_valid, tools_accessed):
        """
        Log catalog discovery and tool access
        """
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "catalog_access",
            "agent_id": agent_id,
            "catalog_url": catalog_url,
            "signature_valid": signature_valid,
            "tools_accessed": tools_accessed,
            "client_ip": self.get_client_ip(),
            "user_agent": self.get_user_agent()
        }
        
        self.write_audit_log(event)
    
    def log_tool_execution(self, agent_id, tool_name, success, duration_ms, error=None):
        """
        Log tool execution attempts
        """
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "tool_execution",
            "agent_id": agent_id,
            "tool_name": tool_name,
            "success": success,
            "duration_ms": duration_ms,
            "error": error,
            "client_ip": self.get_client_ip()
        }
        
        self.write_audit_log(event)
    
    def log_security_violation(self, violation_type, details):
        """
        Log security violations for investigation
        """
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "security_violation",
            "violation_type": violation_type,
            "severity": "HIGH",
            "details": details,
            "client_ip": self.get_client_ip(),
            "requires_investigation": True
        }
        
        self.write_audit_log(event)
        self.alert_security_team(event)
```

#### Monitoring and Alerting
```yaml
Security Monitoring:
  Metrics:
    - catalog_signature_failures
    - invalid_token_attempts
    - unauthorized_tool_access
    - catalog_fetch_anomalies
    - certificate_validation_failures
  
  Alerts:
    - Multiple signature failures from same IP
    - Sudden spike in catalog access
    - Access to high-privilege tools
    - Certificate expiration warnings
    - Key rotation due dates
  
  Dashboards:
    - Security event timeline
    - Agent access patterns
    - Tool usage statistics
    - Certificate status overview
    - Threat detection summary
```

## 🛡️ Security Best Practices

### Deployment Security

#### Production Hardening Checklist
```yaml
Infrastructure:
  - [ ] HTTPS-only catalog hosting
  - [ ] HTTP Strict Transport Security enabled
  - [ ] Certificate Transparency monitoring
  - [ ] DDoS protection configured
  - [ ] Web Application Firewall deployed
  - [ ] Rate limiting implemented

Key Management:
  - [ ] Private keys stored in HSM
  - [ ] Key rotation schedule defined
  - [ ] Emergency key revocation procedures
  - [ ] Multi-person key ceremonies
  - [ ] Key backup and recovery tested

Monitoring:
  - [ ] Security event logging enabled
  - [ ] Real-time threat detection
  - [ ] Anomaly detection for access patterns
  - [ ] Certificate expiration monitoring
  - [ ] Audit trail retention policy

Access Control:
  - [ ] Principle of least privilege
  - [ ] Regular access reviews
  - [ ] Strong authentication required
  - [ ] Session management implemented
  - [ ] Authorization policies defined
```

#### Security Configuration Templates

**High-Security Environment**:
```yaml
security_profile: high
signature_verification: required
certificate_pinning: enabled
token_lifetime: 300  # 5 minutes
key_rotation_interval: 30  # days
monitoring_level: verbose
audit_retention: 2555  # 7 years
```

**Standard Environment**:
```yaml
security_profile: standard
signature_verification: required
certificate_pinning: optional
token_lifetime: 3600  # 1 hour
key_rotation_interval: 90  # days
monitoring_level: standard
audit_retention: 1095  # 3 years
```

**Development Environment**:
```yaml
security_profile: development
signature_verification: optional
certificate_pinning: disabled
token_lifetime: 86400  # 24 hours
key_rotation_interval: 365  # days
monitoring_level: basic
audit_retention: 30  # days
```

### Agent Security

#### Secure Agent Implementation
```python
class SecureEATAgent:
    """
    Security-focused EAT agent implementation
    """
    
    def __init__(self, catalog_url, security_config):
        self.catalog_url = catalog_url
        self.config = security_config
        self.session = self.create_secure_session()
        self.audit_logger = SecurityLogger()
    
    def create_secure_session(self):
        """
        Create HTTP session with security controls
        """
        session = requests.Session()
        
        # Configure timeouts
        session.timeout = (5, 30)  # (connect, read)
        
        # Set security headers
        session.headers.update({
            'User-Agent': f'EATAgent/1.0 (Security-Profile: {self.config.profile})',
            'Accept': 'application/json',
            'Cache-Control': 'no-cache'
        })
        
        # Configure SSL verification
        if self.config.certificate_pinning:
            session.verify = self.create_secure_context()
        
        return session
    
    async def discover_tools_securely(self):
        """
        Secure tool discovery with comprehensive validation
        """
        try:
            # Download catalog with security headers
            response = self.session.get(
                self.catalog_url,
                headers={'Accept': 'application/json'},
                timeout=10
            )
            response.raise_for_status()
            
            # Validate content type
            if response.headers.get('content-type') != 'application/json':
                raise SecurityError("Invalid content type")
            
            # Parse and validate catalog
            catalog = response.json()
            
            # Verify JWS signature if required
            if self.config.signature_verification:
                if not self.verify_catalog_signature(catalog):
                    raise SecurityError("Catalog signature verification failed")
            
            # Log successful discovery
            self.audit_logger.log_catalog_access(
                agent_id=self.agent_id,
                catalog_url=self.catalog_url,
                signature_valid=True,
                tools_accessed=[tool['name'] for tool in catalog['tools']]
            )
            
            return catalog
            
        except Exception as e:
            self.audit_logger.log_security_violation(
                "catalog_discovery_failed",
                {"error": str(e), "catalog_url": self.catalog_url}
            )
            raise
```

## 📊 Security Metrics

### Key Performance Indicators (KPIs)

| Metric | Target | Measurement | Frequency |
|--------|--------|-------------|-----------|
| **Signature Verification Success Rate** | >99.9% | Valid signatures / Total verifications | Real-time |
| **Certificate Validation Success Rate** | >99.9% | Valid certificates / Total validations | Real-time |
| **Security Event Response Time** | <5 minutes | Alert to response time | Per incident |
| **Key Rotation Compliance** | 100% | On-time rotations / Scheduled rotations | Monthly |
| **Audit Log Coverage** | 100% | Logged events / Total security events | Daily |

### Security Dashboard Metrics
```yaml
Real-time Metrics:
  - Active agents with valid tokens
  - Catalog access rate and patterns
  - Tool execution success/failure rates
  - Security violations per hour
  - Certificate expiration countdown

Daily Metrics:
  - New agent registrations
  - Tool usage by category
  - Failed authentication attempts
  - Geographic access patterns
  - Average session duration

Monthly Metrics:
  - Security trend analysis
  - Compliance audit results
  - Key rotation completion
  - Vulnerability assessment summary
  - Incident response metrics
```

## 🚨 Incident Response

### Security Incident Classification

| Level | Criteria | Response Time | Escalation |
|-------|----------|---------------|------------|
| **P0 - Critical** | Key compromise, mass exploitation | <15 minutes | CISO, CTO |
| **P1 - High** | Authentication bypass, data exposure | <1 hour | Security team lead |
| **P2 - Medium** | Failed access attempts, policy violations | <4 hours | On-call engineer |
| **P3 - Low** | Configuration issues, monitoring alerts | <24 hours | Standard process |

### Response Procedures

#### Key Compromise Response
```yaml
Immediate Actions (0-15 minutes):
  1. Revoke compromised key from DID document
  2. Generate new signing key pair
  3. Update catalog with new signature
  4. Alert all agent operators
  5. Enable enhanced monitoring

Short-term Actions (15 minutes - 4 hours):
  1. Investigate compromise scope
  2. Audit all recent catalog accesses
  3. Validate integrity of all published catalogs
  4. Update emergency contacts
  5. Document incident timeline

Long-term Actions (4+ hours):
  1. Conduct post-incident review
  2. Update key management procedures
  3. Enhance monitoring based on lessons learned
  4. Update incident response playbook
  5. Implement additional controls if needed
```

---

This comprehensive security model ensures that EAT Framework deployments maintain the highest standards of security while enabling the flexibility and performance benefits of one-hop tool discovery.