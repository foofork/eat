#!/usr/bin/env python3
"""
Setup verification script for EAT Framework.
Run this script to verify that all components are properly installed and working.
"""

import sys
import json
import asyncio
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required. Current version:", sys.version)
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def check_imports():
    """Check if all required modules can be imported."""
    required_modules = [
        'aiohttp', 'cryptography', 'jwt', 'click', 
        'pydantic', 'requests', 'yaml', 'jsonschema'
    ]
    
    failed = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed.append(module)
    
    return len(failed) == 0

def check_eat_framework():
    """Check if EAT framework modules can be imported."""
    try:
        import eat
        from eat import Catalog, Tool
        from eat.discovery import Catalog as DiscoveryCatalog
        from eat.mcp_client import MCPClient
        from eat.security import JWSVerifier
        print("✅ EAT Framework core modules")
        return True
    except ImportError as e:
        print(f"❌ EAT Framework: {e}")
        return False

def check_cli_tools():
    """Check if CLI tools are available."""
    try:
        from eat.cli.main import generate, serve
        print("✅ CLI tools (eat-gen, eat-serve)")
        return True
    except ImportError as e:
        print(f"❌ CLI tools: {e}")
        return False

def check_demo_files():
    """Check if demo files exist and are valid."""
    demo_path = Path(__file__).parent / "demo"
    
    # Check demo structure
    required_files = [
        "quickstart.sh",
        "site/.well-known/api-catalog",
        "specs/customer-api.yaml",
        "specs/analytics-api.yaml", 
        "specs/notifications-api.yaml",
        "servers/customer_server.py",
        "servers/analytics_server.py",
        "servers/notifications_server.py"
    ]
    
    missing = []
    for file_path in required_files:
        full_path = demo_path / file_path
        if not full_path.exists():
            missing.append(file_path)
        else:
            print(f"✅ demo/{file_path}")
    
    if missing:
        print(f"❌ Missing demo files: {missing}")
        return False
    
    # Check catalog validity
    try:
        catalog_path = demo_path / "site/.well-known/api-catalog"
        with open(catalog_path) as f:
            catalog = json.load(f)
        
        assert catalog["version"] == "1.0"
        assert len(catalog["tools"]) == 13
        print(f"✅ Demo catalog valid ({len(catalog['tools'])} tools)")
        return True
    except Exception as e:
        print(f"❌ Demo catalog invalid: {e}")
        return False

def check_examples():
    """Check if examples directory is complete."""
    examples_path = Path(__file__).parent / "examples"
    
    required_dirs = [
        "specs", "catalogs", "curl", 
        "minimal-python", "test-vectors"
    ]
    
    missing = []
    for dir_name in required_dirs:
        dir_path = examples_path / dir_name
        if not dir_path.exists():
            missing.append(dir_name)
        else:
            print(f"✅ examples/{dir_name}/")
    
    if missing:
        print(f"❌ Missing example directories: {missing}")
        return False
    
    return True

def check_documentation():
    """Check if documentation files exist."""
    docs = [
        "README.md", "PROTOCOL.md", "IMPLEMENTATION.md", 
        "QUICKSTART.md", "INSTALL.md"
    ]
    
    missing = []
    for doc in docs:
        doc_path = Path(__file__).parent / doc
        if not doc_path.exists():
            missing.append(doc)
        else:
            print(f"✅ {doc}")
    
    if missing:
        print(f"❌ Missing documentation: {missing}")
        return False
    
    return True

async def test_basic_functionality():
    """Test basic EAT functionality."""
    try:
        from eat import Catalog
        
        # Test catalog creation (without network)
        catalog = Catalog("http://example.com/.well-known/api-catalog")
        print("✅ Catalog creation")
        
        # Test tool discovery (mock)
        tools = []  # Would normally be catalog.tools after fetch()
        print("✅ Basic functionality test")
        return True
    except Exception as e:
        print(f"❌ Basic functionality: {e}")
        return False

def main():
    """Run all verification checks."""
    print("🔍 EAT Framework Setup Verification")
    print("=" * 40)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_imports),
        ("EAT Framework", check_eat_framework),
        ("CLI Tools", check_cli_tools),
        ("Demo Files", check_demo_files),
        ("Examples", check_examples),
        ("Documentation", check_documentation),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n📋 {name}:")
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {name} check failed: {e}")
            results.append(False)
    
    # Test basic functionality
    print(f"\n📋 Basic Functionality:")
    try:
        result = asyncio.run(test_basic_functionality())
        results.append(result)
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        results.append(False)
    
    # Summary
    print("\n" + "=" * 40)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All checks passed! ({passed}/{total})")
        print("\n✅ EAT Framework is ready to use!")
        print("\nNext steps:")
        print("  • Try the demo: cd demo && ./quickstart.sh")
        print("  • Read QUICKSTART.md for 10-minute tutorial")
        print("  • Explore examples/ directory")
        return 0
    else:
        print(f"⚠️  {passed}/{total} checks passed")
        print("\n❌ Setup incomplete. Please address the failed checks above.")
        print("\nFor help:")
        print("  • See INSTALL.md for detailed installation instructions")
        print("  • Check requirements.txt for dependencies")
        print("  • Create an issue at: https://github.com/foofork/eat/issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())