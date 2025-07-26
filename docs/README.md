# EAT Framework Documentation

Welcome to the comprehensive documentation for the **Ephemeral Agent Toolkit (EAT)** - one-hop tool discovery for AI agents using signed .well-known catalogs.

## 📚 Documentation Overview

This documentation provides detailed technical guidance for implementing, deploying, and using the EAT Framework in production environments.

### 🚀 Getting Started

| Document | Description | Audience |
|----------|-------------|----------|
| **[../README.md](../README.md)** | Project overview and quick start | Everyone |
| **[../QUICKSTART.md](../QUICKSTART.md)** | 10-minute implementation tutorial | Developers |
| **[../INSTALL.md](../INSTALL.md)** | Installation guide with troubleshooting | Developers |

### 🏗️ Architecture & Design

| Document | Description | Audience |
|----------|-------------|----------|
| **[architecture.md](architecture.md)** | System architecture and design patterns | Architects, Engineers |
| **[comparison.md](comparison.md)** | Comparison with other tool discovery approaches | Decision makers |
| **[extensions.md](extensions.md)** | x-mcp-tool OpenAPI extension specification | Spec authors |

### 🔒 Security & Operations

| Document | Description | Audience |
|----------|-------------|----------|
| **[security.md](security.md)** | Security model, threats, and mitigations | Security teams |
| **[deployment.md](deployment.md)** | Production deployment patterns | DevOps, SRE |
| **[enterprise.md](enterprise.md)** | Enterprise deployment and governance | IT leadership |

### 🛠️ Development & Reference

| Document | Description | Audience |
|----------|-------------|----------|
| **[api-reference.md](api-reference.md)** | Complete Python API documentation | Developers |
| **[troubleshooting.md](troubleshooting.md)** | Common issues and solutions | Support teams |
| **[../PROTOCOL.md](../PROTOCOL.md)** | Complete EAT protocol specification | Protocol implementers |
| **[../IMPLEMENTATION.md](../IMPLEMENTATION.md)** | Language-agnostic implementation guide | Developers |

## 🎯 Use Case Documentation

### For Different Audiences

**🤖 AI Agent Developers:**
- Start with [../QUICKSTART.md](../QUICKSTART.md) for immediate implementation
- Review [api-reference.md](api-reference.md) for Python library usage
- Check [troubleshooting.md](troubleshooting.md) for common integration issues

**🏢 Enterprise Teams:**
- Read [enterprise.md](enterprise.md) for governance and deployment patterns
- Review [security.md](security.md) for compliance and risk assessment
- See [deployment.md](deployment.md) for production architecture

**🔧 Tool Publishers:**
- Study [extensions.md](extensions.md) for x-mcp-tool specification
- Follow [../IMPLEMENTATION.md](../IMPLEMENTATION.md) for catalog creation
- Use [troubleshooting.md](troubleshooting.md) for catalog validation

**⚖️ Decision Makers:**
- Review [comparison.md](comparison.md) for technology evaluation
- Read [architecture.md](architecture.md) for technical understanding
- Check [enterprise.md](enterprise.md) for business considerations

## 🔍 Key Concepts

### Core Architecture
EAT uses a three-stage process:
1. **Discovery**: Single HTTP GET to `/.well-known/api-catalog`
2. **Validation**: JWS signature and SHA-256 hash verification
3. **Execution**: MCP protocol tool invocation

### Design Principles
- **One-hop discovery**: No registries or complex handshakes
- **Standards-based**: RFC 8615, OpenAPI 3.0, JWS, MCP
- **Zero infrastructure**: Plain HTTPS and static files
- **Human + AI friendly**: Same specs readable by browsers and agents

### Security Model
- **Cryptographic integrity**: JWS signatures with DID:web
- **Content verification**: SHA-256 hashes for all resources
- **Distributed trust**: No central PKI required
- **Tamper evidence**: Detect any catalog modifications

## 📁 Documentation Structure

```
docs/
├── README.md              # This overview (start here)
├── architecture.md        # System design and patterns
├── comparison.md         # Technology comparison
├── security.md           # Security model and threats
├── deployment.md         # Production deployment
├── api-reference.md      # Python API documentation
├── troubleshooting.md    # Common issues and solutions
├── extensions.md         # OpenAPI extension specification
├── enterprise.md         # Enterprise patterns
└── assets/              # Diagrams and visual aids
    ├── architecture.svg
    ├── sequence-diagrams/
    └── deployment-patterns/
```

## 🚀 Quick Navigation

**Need to implement EAT quickly?**
→ [../QUICKSTART.md](../QUICKSTART.md) (10 minutes)

**Want to understand the architecture?**
→ [architecture.md](architecture.md)

**Evaluating EAT vs alternatives?**
→ [comparison.md](comparison.md)

**Planning production deployment?**
→ [deployment.md](deployment.md)

**Need security review information?**
→ [security.md](security.md)

**Looking for API reference?**
→ [api-reference.md](api-reference.md)

## 🤝 Contributing to Documentation

We welcome improvements to the documentation! Here's how to contribute:

### Documentation Standards

1. **Audience-focused**: Write for specific user personas
2. **Example-driven**: Include working code examples
3. **Progressive disclosure**: Simple concepts first, advanced later
4. **Cross-referenced**: Link related concepts and documents

### Content Guidelines

- Use clear, concise language
- Include practical examples and use cases
- Provide troubleshooting guidance
- Keep technical accuracy high
- Update examples when code changes

### Updating Documentation

1. **Local testing**: Test all code examples
2. **Consistency check**: Ensure terminology matches
3. **Link validation**: Verify all internal and external links
4. **Review process**: Submit PR for documentation changes

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/foofork/eat/issues)
- **Discussions**: Technical questions and community support
- **Documentation**: This directory contains comprehensive guides
- **Examples**: [../examples/](../examples/) directory has working code

---

## 📋 Documentation Checklist

When reading the documentation, you should be able to:

- [ ] Understand what EAT is and why it exists
- [ ] Implement basic tool discovery in under 10 minutes
- [ ] Deploy a production catalog with proper security
- [ ] Troubleshoot common integration issues
- [ ] Compare EAT with alternative approaches
- [ ] Design enterprise-scale deployments
- [ ] Contribute to the project effectively

**Questions or missing information?** Please [create an issue](https://github.com/foofork/eat/issues) to help us improve this documentation.