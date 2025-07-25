#!/usr/bin/env python3
"""
Analytics MCP Server
Provides data aggregation and reporting capabilities.
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import uvicorn
import httpx


# Authentication
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Simple token verification for demo purposes."""
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
    yield
    # Shutdown
    pass

app = FastAPI(
    title="Analytics API",
    description="MCP Server for data aggregation and reporting",
    version="1.0.0",
    lifespan=lifespan
)

# Configuration
CUSTOMER_SERVICE_URL = os.getenv("CUSTOMER_SERVICE_URL", "http://localhost:3001")


# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "analytics-server"}


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
                            "name": "customer_analytics",
                            "description": "Generate analytics report for customers",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "customer_ids": {
                                        "type": "array",
                                        "items": {"type": "integer"},
                                        "description": "List of customer IDs to analyze"
                                    },
                                    "metrics": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Metrics to include: engagement, revenue, retention"
                                    }
                                }
                            }
                        },
                        {
                            "name": "company_analytics",
                            "description": "Generate analytics by company",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "company": {"type": "string", "description": "Company name"},
                                    "include_trends": {"type": "boolean", "description": "Include trend analysis"}
                                }
                            }
                        },
                        {
                            "name": "generate_report",
                            "description": "Generate formatted analytics report",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "template": {
                                        "type": "string",
                                        "enum": ["summary", "detailed", "executive"],
                                        "description": "Report template"
                                    },
                                    "data": {"type": "object", "description": "Analytics data"},
                                    "format": {
                                        "type": "string",
                                        "enum": ["json", "html", "pdf"],
                                        "description": "Output format"
                                    }
                                },
                                "required": ["template", "data"]
                            }
                        },
                        {
                            "name": "trend_analysis",
                            "description": "Perform trend analysis on customer data",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "period": {
                                        "type": "string",
                                        "enum": ["week", "month", "quarter"],
                                        "description": "Analysis period"
                                    },
                                    "metric": {
                                        "type": "string",
                                        "enum": ["customers", "revenue", "engagement"],
                                        "description": "Metric to analyze"
                                    }
                                },
                                "required": ["period", "metric"]
                            }
                        }
                    ]
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name == "customer_analytics":
                result = await customer_analytics_impl(arguments)
            elif tool_name == "company_analytics":
                result = await company_analytics_impl(arguments)
            elif tool_name == "generate_report":
                result = await generate_report_impl(arguments)
            elif tool_name == "trend_analysis":
                result = await trend_analysis_impl(arguments)
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
async def get_customers_data(customer_ids: List[int] = None, company: str = None):
    """Fetch customer data from customer service."""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": "Bearer demo-token-12345"}
        
        if customer_ids:
            customers = []
            for customer_id in customer_ids:
                try:
                    response = await client.post(
                        f"{CUSTOMER_SERVICE_URL}/mcp",
                        json={
                            "jsonrpc": "2.0",
                            "id": f"get_customer_{customer_id}",
                            "method": "tools/call",
                            "params": {
                                "name": "get_customer",
                                "arguments": {"customer_id": customer_id}
                            }
                        },
                        headers=headers
                    )
                    if response.status_code == 200:
                        result = response.json()
                        if "result" in result:
                            customers.append(result["result"])
                except Exception:
                    pass
            return customers
        
        elif company:
            try:
                response = await client.post(
                    f"{CUSTOMER_SERVICE_URL}/mcp",
                    json={
                        "jsonrpc": "2.0",
                        "id": "list_customers_by_company",
                        "method": "tools/call",
                        "params": {
                            "name": "list_customers",
                            "arguments": {"company": company}
                        }
                    },
                    headers=headers
                )
                if response.status_code == 200:
                    result = response.json()
                    return result.get("result", [])
            except Exception:
                pass
        
        else:
            # Get all customers
            try:
                response = await client.post(
                    f"{CUSTOMER_SERVICE_URL}/mcp",
                    json={
                        "jsonrpc": "2.0",
                        "id": "list_all_customers",
                        "method": "tools/call",
                        "params": {
                            "name": "list_customers",
                            "arguments": {"limit": 1000}
                        }
                    },
                    headers=headers
                )
                if response.status_code == 200:
                    result = response.json()
                    return result.get("result", [])
            except Exception:
                pass
        
        return []


def generate_mock_metrics(customers: List[Dict]) -> Dict:
    """Generate mock analytics metrics for demo purposes."""
    import random
    import hashlib
    
    metrics = {
        "total_customers": len(customers),
        "engagement_scores": {},
        "revenue_estimates": {},
        "retention_rates": {},
        "activity_levels": {}
    }
    
    for customer in customers:
        customer_id = customer.get("id", 0)
        email = customer.get("email", "")
        
        # Use email hash for consistent "random" values
        seed = int(hashlib.md5(email.encode()).hexdigest()[:8], 16)
        random.seed(seed)
        
        metrics["engagement_scores"][customer_id] = round(random.uniform(0.1, 1.0), 2)
        metrics["revenue_estimates"][customer_id] = round(random.uniform(100, 5000), 2)
        metrics["retention_rates"][customer_id] = round(random.uniform(0.6, 0.95), 2)
        metrics["activity_levels"][customer_id] = random.choice(["low", "medium", "high"])
    
    return metrics


async def customer_analytics_impl(arguments: Dict):
    """Generate analytics for specific customers."""
    customer_ids = arguments.get("customer_ids", [])
    requested_metrics = arguments.get("metrics", ["engagement", "revenue", "retention"])
    
    customers = await get_customers_data(customer_ids=customer_ids)
    if not customers:
        raise ValueError("No customer data available")
    
    metrics = generate_mock_metrics(customers)
    
    # Filter metrics based on request
    result = {
        "customer_count": len(customers),
        "timestamp": datetime.now().isoformat(),
        "metrics": {}
    }
    
    if "engagement" in requested_metrics:
        result["metrics"]["engagement"] = {
            "average": round(sum(metrics["engagement_scores"].values()) / len(metrics["engagement_scores"]), 2),
            "individual": metrics["engagement_scores"]
        }
    
    if "revenue" in requested_metrics:
        result["metrics"]["revenue"] = {
            "total": round(sum(metrics["revenue_estimates"].values()), 2),
            "average": round(sum(metrics["revenue_estimates"].values()) / len(metrics["revenue_estimates"]), 2),
            "individual": metrics["revenue_estimates"]
        }
    
    if "retention" in requested_metrics:
        result["metrics"]["retention"] = {
            "average": round(sum(metrics["retention_rates"].values()) / len(metrics["retention_rates"]), 2),
            "individual": metrics["retention_rates"]
        }
    
    return result


async def company_analytics_impl(arguments: Dict):
    """Generate analytics for a specific company."""
    company = arguments.get("company")
    include_trends = arguments.get("include_trends", False)
    
    if not company:
        raise ValueError("Company name required")
    
    customers = await get_customers_data(company=company)
    if not customers:
        raise ValueError(f"No customers found for company: {company}")
    
    metrics = generate_mock_metrics(customers)
    
    result = {
        "company": company,
        "customer_count": len(customers),
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_estimated_revenue": round(sum(metrics["revenue_estimates"].values()), 2),
            "average_engagement": round(sum(metrics["engagement_scores"].values()) / len(metrics["engagement_scores"]), 2),
            "average_retention": round(sum(metrics["retention_rates"].values()) / len(metrics["retention_rates"]), 2)
        }
    }
    
    if include_trends:
        # Mock trend data
        result["trends"] = {
            "customer_growth": [
                {"month": "2024-01", "count": max(1, len(customers) - 3)},
                {"month": "2024-02", "count": max(1, len(customers) - 2)},
                {"month": "2024-03", "count": max(1, len(customers) - 1)},
                {"month": "2024-04", "count": len(customers)}
            ],
            "engagement_trend": "increasing",
            "revenue_trend": "stable"
        }
    
    return result


async def generate_report_impl(arguments: Dict):
    """Generate formatted analytics report."""
    template = arguments.get("template", "summary")
    data = arguments.get("data", {})
    format_type = arguments.get("format", "json")
    
    if not data:
        raise ValueError("Analytics data required")
    
    if format_type == "json":
        return {
            "report_type": template,
            "generated_at": datetime.now().isoformat(),
            "format": "json",
            "content": data
        }
    
    elif format_type == "html":
        html_content = generate_html_report(template, data)
        return {
            "report_type": template,
            "generated_at": datetime.now().isoformat(),
            "format": "html",
            "content": html_content
        }
    
    elif format_type == "pdf":
        return {
            "report_type": template,
            "generated_at": datetime.now().isoformat(),
            "format": "pdf",
            "content": "PDF generation not implemented in demo",
            "download_url": "https://example.com/reports/analytics.pdf"
        }
    
    else:
        raise ValueError(f"Unsupported format: {format_type}")


def generate_html_report(template: str, data: Dict) -> str:
    """Generate HTML report content."""
    title = f"{template.title()} Analytics Report"
    
    html = f"""
    <html>
    <head>
        <title>{title}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; }}
            .metric {{ margin: 10px 0; padding: 10px; border-left: 3px solid #007cba; }}
            .summary {{ background: #e7f3ff; padding: 15px; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{title}</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="summary">
            <h2>Summary</h2>
            <pre>{json.dumps(data, indent=2)}</pre>
        </div>
    </body>
    </html>
    """
    
    return html


async def trend_analysis_impl(arguments: Dict):
    """Perform trend analysis on customer data."""
    period = arguments.get("period", "month")
    metric = arguments.get("metric", "customers")
    
    # Mock trend data for demo
    current_date = datetime.now()
    
    if period == "week":
        periods = [(current_date - timedelta(weeks=i)).strftime("%Y-W%U") for i in range(4, 0, -1)]
    elif period == "month":
        periods = [(current_date - timedelta(days=30*i)).strftime("%Y-%m") for i in range(4, 0, -1)]
    elif period == "quarter":
        periods = [f"{current_date.year}-Q{((current_date.month-1)//3 + 1 - i) % 4 + 1}" for i in range(4, 0, -1)]
    else:
        raise ValueError(f"Unsupported period: {period}")
    
    # Generate mock trend data
    import random
    base_value = {"customers": 100, "revenue": 10000, "engagement": 0.7}[metric]
    
    trend_data = []
    for i, period_label in enumerate(periods):
        # Simulate realistic growth/decline
        multiplier = 1 + (i * 0.1) + random.uniform(-0.05, 0.15)
        value = round(base_value * multiplier, 2)
        
        trend_data.append({
            "period": period_label,
            "value": value
        })
    
    # Calculate trend direction
    if len(trend_data) >= 2:
        first_value = trend_data[0]["value"]
        last_value = trend_data[-1]["value"]
        change_percent = ((last_value - first_value) / first_value) * 100
        
        if change_percent > 5:
            trend_direction = "increasing"
        elif change_percent < -5:
            trend_direction = "decreasing"
        else:
            trend_direction = "stable"
    else:
        trend_direction = "insufficient_data"
    
    return {
        "metric": metric,
        "period": period,
        "trend_direction": trend_direction,
        "change_percent": round(change_percent, 1) if len(trend_data) >= 2 else 0,
        "data_points": trend_data,
        "analysis_date": current_date.isoformat()
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3002))
    uvicorn.run(
        "analytics_server:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )