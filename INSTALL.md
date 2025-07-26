# Installation Guide

## Quick Install (Recommended)

### Option 1: From Source (Development)

```bash
# Clone the repository
git clone https://github.com/foofork/eat.git
cd eat

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Verify installation
python -c "import eat; print('✅ EAT Framework installed successfully!')"
```

### Option 2: Demo Only (No Installation)

```bash
# Clone and run demo without installing
git clone https://github.com/foofork/eat.git
cd eat/demo
./quickstart.sh

# Visit http://localhost:8000 to explore tools
```

## Development Setup

### Prerequisites

- Python 3.8+ 
- pip or pipx for package management
- Virtual environment (strongly recommended)

### Full Development Environment

```bash
# Clone repository
git clone https://github.com/foofork/eat.git
cd eat

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt
pip install -e .

# Run tests to verify setup
python -m pytest tests/ -v

# Run linting and formatting
black .
flake8 .
mypy eat/
```

### Available Commands After Installation

```bash
# Generate catalog from OpenAPI specs
eat-gen specs/ --output catalog.json

# Serve catalog locally
eat-serve --port 8000

# Run demo environment
cd demo && ./quickstart.sh

# Run tests
python -m pytest tests/

# CLI help
python -m eat.cli.main --help
```

## Dependencies

### Core Runtime Dependencies

- `aiohttp>=3.8.0` - Async HTTP client/server
- `cryptography>=3.4.0` - JWS signing and verification
- `pyjwt[crypto]>=2.0.0` - JWT token handling
- `click>=8.0.0` - CLI framework
- `pydantic>=1.8.0` - Data validation
- `requests>=2.25.0` - HTTP client
- `pyyaml>=5.4.0` - YAML parsing
- `jsonschema>=3.2.0` - JSON schema validation

### Development Dependencies

- `pytest>=6.0.0` - Testing framework
- `pytest-asyncio>=0.18.0` - Async test support
- `pytest-cov>=2.12.0` - Coverage reporting
- `black>=21.0.0` - Code formatting
- `flake8>=3.9.0` - Linting
- `mypy>=0.910` - Type checking

## Troubleshooting

### Common Issues

**1. ModuleNotFoundError: No module named 'aiohttp'**
```bash
# Install dependencies first
pip install -r requirements.txt
```

**2. externally-managed-environment error**
```bash
# Use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -e .

# Or use --user flag (not recommended)
pip install --user -e .
```

**3. Demo servers won't start**
```bash
# Ensure you're in the demo directory
cd demo
./quickstart.sh

# Check if ports 3001-3003 and 8000 are available
lsof -i :3001
```

**4. Tests failing**
```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run with verbose output
python -m pytest tests/ -v -s
```

### Verify Installation

```bash
# Quick verification script
python -c "
import eat
from eat import Catalog, Tool
from eat.cli.main import generate, serve
print('✅ All core modules imported successfully')
print(f'📦 EAT Framework version: {eat.__version__}')
"
```

### Platform-Specific Notes

**macOS with Homebrew Python:**
- Use virtual environments to avoid system package conflicts
- May need to install additional build tools: `xcode-select --install`

**Windows:**
- Use `python` instead of `python3`
- Activate venv with: `venv\Scripts\activate`
- May need Visual Studio Build Tools for cryptography

**Linux:**
- Install development headers: `apt-get install python3-dev libffi-dev libssl-dev`
- Use system package manager for system-wide install (not recommended)

## Next Steps

After successful installation:

1. **Try the demo**: `cd demo && ./quickstart.sh`
2. **Read the quickstart**: [QUICKSTART.md](QUICKSTART.md)
3. **Explore examples**: [examples/](examples/)
4. **Read the protocol**: [PROTOCOL.md](PROTOCOL.md)
5. **Build your implementation**: [IMPLEMENTATION.md](IMPLEMENTATION.md)

## Support

- **Documentation**: [Repository docs](/)
- **Issues**: [GitHub Issues](https://github.com/foofork/eat/issues)
- **Examples**: [examples/](examples/) directory
- **Demo**: [demo/README.md](demo/README.md)