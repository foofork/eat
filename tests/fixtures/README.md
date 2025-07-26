# Test Fixtures

This directory contains static test fixtures for integration testing and development purposes.

## Structure

```
fixtures/
├── README.md              # This file
├── catalogs/              # Sample EAT catalogs
│   ├── valid_catalog.json      # Valid catalog for testing
│   └── invalid_catalog.json    # Invalid catalog for error testing
├── specs/                 # Sample OpenAPI specifications
│   ├── simple_api.yaml         # Basic API with x-mcp-tool
│   └── complex_api.yaml        # Full-featured API example
└── keys/                  # Test cryptographic keys
    ├── test_private_key.pem    # RSA private key (TEST ONLY)
    └── test_public_key.pem     # RSA public key (TEST ONLY)
```

## Usage

### In Unit Tests

Unit tests typically create their own temporary fixtures using `conftest.py`:

```python
def test_catalog_loading(sample_catalog):
    # Uses fixture from conftest.py
    assert sample_catalog["version"] == "1.0"
```

### In Integration Tests

Integration tests can use these static files:

```python
import json
from pathlib import Path

def test_real_catalog_file():
    fixtures_dir = Path(__file__).parent / "fixtures"
    catalog_file = fixtures_dir / "catalogs" / "valid_catalog.json"
    
    with open(catalog_file) as f:
        catalog = json.load(f)
    
    # Test with actual file
    assert catalog["version"] == "1.0"
```

### In Development

Use these files for manual testing and development:

```bash
# Test catalog parsing
python -c "
import json
with open('tests/fixtures/catalogs/valid_catalog.json') as f:
    catalog = json.load(f)
    print(f'Tools: {len(catalog[\"tools\"])}')
"

# Test OpenAPI spec parsing
python -c "
import yaml
with open('tests/fixtures/specs/simple_api.yaml') as f:
    spec = yaml.safe_load(f)
    print(f'Paths: {list(spec[\"paths\"].keys())}')
"
```

## Security Note

The keys in `keys/` are for testing only and contain dummy/example data. They should never be used in production.

## Adding New Fixtures

When adding new test fixtures:

1. **Catalogs**: Add to `catalogs/` directory
2. **OpenAPI Specs**: Add to `specs/` directory  
3. **Keys**: Add to `keys/` directory (test data only)
4. **Update this README** with descriptions of new fixtures

## Relationship to conftest.py

The `conftest.py` file provides programmatic fixtures that create temporary test data. Use those for most unit tests. Use these static files for:

- Integration tests that need persistent files
- Development and debugging
- Complex test scenarios that need pre-built data
- Performance testing with realistic data sizes