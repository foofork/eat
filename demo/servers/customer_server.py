#!/usr/bin/env python3
"""
Customer Management MCP Server
Provides CRUD operations for customer data with authentication.
"""

import asyncio
import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import uvicorn


# Data Models
class Customer(BaseModel):
    id: Optional[int] = None
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CustomerCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None


# Database setup
DB_FILE = os.getenv('DB_FILE', '/tmp/customers.db')


def init_db():
    """Initialize the customer database."""
    conn = sqlite3.connect(DB_FILE)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            company TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert sample data
    sample_customers = [
        ("John Smith", "john.smith@example.com", "+1-555-0001", "Acme Corp"),
        ("Jane Doe", "jane.doe@example.com", "+1-555-0002", "Tech Solutions"),
        ("Bob Johnson", "bob.johnson@example.com", "+1-555-0003", "StartupXYZ"),
    ]
    
    for name, email, phone, company in sample_customers:
        try:
            conn.execute(
                "INSERT INTO customers (name, email, phone, company) VALUES (?, ?, ?, ?)",
                (name, email, phone, company)
            )
        except sqlite3.IntegrityError:
            pass  # Customer already exists
    
    conn.commit()
    conn.close()


# Authentication
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Simple token verification for demo purposes."""
    # In production, this would validate a real JWT token
    if credentials.credentials != "demo-token-12345":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    return credentials.credentials


# FastAPI app setup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="Customer Management API",
    description="MCP Server for customer CRUD operations",
    version="1.0.0",
    lifespan=lifespan
)


# Database helper functions
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "customer-server"}


@app.post("/mcp", dependencies=[Depends(verify_token)])
async def mcp_endpoint(request: Dict):
    """MCP protocol endpoint."""
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id", "unknown")
    
    try:
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "get_customer",
                            "description": "Retrieve customer information by ID",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "customer_id": {"type": "integer", "description": "Customer ID"}
                                },
                                "required": ["customer_id"]
                            }
                        },
                        {
                            "name": "create_customer",
                            "description": "Create a new customer",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string", "description": "Customer name"},
                                    "email": {"type": "string", "description": "Customer email"},
                                    "phone": {"type": "string", "description": "Customer phone"},
                                    "company": {"type": "string", "description": "Customer company"}
                                },
                                "required": ["name", "email"]
                            }
                        },
                        {
                            "name": "update_customer",
                            "description": "Update existing customer",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "customer_id": {"type": "integer", "description": "Customer ID"},
                                    "name": {"type": "string", "description": "Customer name"},
                                    "email": {"type": "string", "description": "Customer email"},
                                    "phone": {"type": "string", "description": "Customer phone"},
                                    "company": {"type": "string", "description": "Customer company"}
                                },
                                "required": ["customer_id"]
                            }
                        },
                        {
                            "name": "list_customers",
                            "description": "List all customers with optional filtering",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "limit": {"type": "integer", "description": "Maximum number of results"},
                                    "company": {"type": "string", "description": "Filter by company"}
                                }
                            }
                        }
                    ]
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name == "get_customer":
                result = await get_customer_impl(arguments.get("customer_id"))
            elif tool_name == "create_customer":
                result = await create_customer_impl(arguments)
            elif tool_name == "update_customer":
                result = await update_customer_impl(arguments)
            elif tool_name == "list_customers":
                result = await list_customers_impl(arguments)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
        
        else:
            raise ValueError(f"Unknown method: {method}")
    
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }


# Tool implementations
async def get_customer_impl(customer_id: int):
    """Get customer by ID."""
    conn = get_db()
    cursor = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise ValueError(f"Customer {customer_id} not found")
    
    return dict(row)


async def create_customer_impl(customer_data: Dict):
    """Create new customer."""
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO customers (name, email, phone, company) VALUES (?, ?, ?, ?)",
            (
                customer_data["name"],
                customer_data["email"],
                customer_data.get("phone"),
                customer_data.get("company")
            )
        )
        customer_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return await get_customer_impl(customer_id)
    
    except sqlite3.IntegrityError as e:
        conn.close()
        raise ValueError(f"Customer creation failed: {e}")


async def update_customer_impl(update_data: Dict):
    """Update existing customer."""
    customer_id = update_data.pop("customer_id")
    
    if not update_data:
        raise ValueError("No update data provided")
    
    # Build dynamic update query
    fields = []
    values = []
    for key, value in update_data.items():
        if value is not None:
            fields.append(f"{key} = ?")
            values.append(value)
    
    if not fields:
        raise ValueError("No valid update fields provided")
    
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(customer_id)
    
    conn = get_db()
    cursor = conn.execute(
        f"UPDATE customers SET {', '.join(fields)} WHERE id = ?",
        values
    )
    
    if cursor.rowcount == 0:
        conn.close()
        raise ValueError(f"Customer {customer_id} not found")
    
    conn.commit()
    conn.close()
    
    return await get_customer_impl(customer_id)


async def list_customers_impl(filters: Dict):
    """List customers with optional filtering."""
    query = "SELECT * FROM customers"
    params = []
    conditions = []
    
    # Apply filters
    if filters.get("company"):
        conditions.append("company = ?")
        params.append(filters["company"])
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY created_at DESC"
    
    # Apply limit
    limit = filters.get("limit", 100)
    query += " LIMIT ?"
    params.append(limit)
    
    conn = get_db()
    cursor = conn.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3001))
    uvicorn.run(
        "customer_server:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )