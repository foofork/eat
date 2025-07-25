#!/usr/bin/env python3
"""
Basic EAT Framework usage example.
Demonstrates the minimal code needed to discover and use tools.
"""

import asyncio
from eat import Catalog


async def main():
    # Discover tools
    catalog = Catalog("http://localhost:8000/.well-known/api-catalog")
    await catalog.fetch()
    await catalog.verify()
    
    # Find and use a tool
    tool = catalog.find(capability="customer")[0]
    result = await tool.call(customer_id=12345)
    
    print(f"Customer: {result['name']} ({result['email']})")


if __name__ == "__main__":
    asyncio.run(main())