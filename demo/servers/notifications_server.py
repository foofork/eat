#!/usr/bin/env python3
"""
Notifications MCP Server
Provides email, Slack, and webhook notification capabilities.
"""

import asyncio
import json
import os
from datetime import datetime
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
    title="Notifications API",
    description="MCP Server for email, Slack, and webhook notifications",
    version="1.0.0",
    lifespan=lifespan
)

# Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", 1025))

# In-memory storage for demo purposes
notification_log = []


# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "notifications-server"}


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
                            "name": "send_email",
                            "description": "Send email notification",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "to": {"type": "string", "description": "Recipient email address"},
                                    "subject": {"type": "string", "description": "Email subject"},
                                    "body": {"type": "string", "description": "Email body (HTML or text)"},
                                    "from": {"type": "string", "description": "Sender email address"},
                                    "cc": {"type": "array", "items": {"type": "string"}, "description": "CC recipients"},
                                    "bcc": {"type": "array", "items": {"type": "string"}, "description": "BCC recipients"}
                                },
                                "required": ["to", "subject", "body"]
                            }
                        },
                        {
                            "name": "send_slack_message",
                            "description": "Send message to Slack channel or user",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "channel": {"type": "string", "description": "Slack channel or user ID"},
                                    "message": {"type": "string", "description": "Message content"},
                                    "username": {"type": "string", "description": "Bot username"},
                                    "emoji": {"type": "string", "description": "Bot emoji"},
                                    "attachments": {"type": "array", "description": "Message attachments"}
                                },
                                "required": ["channel", "message"]
                            }
                        },
                        {
                            "name": "send_webhook",
                            "description": "Send webhook notification",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "url": {"type": "string", "description": "Webhook URL"},
                                    "payload": {"type": "object", "description": "Webhook payload"},
                                    "headers": {"type": "object", "description": "Custom headers"},
                                    "method": {
                                        "type": "string",
                                        "enum": ["POST", "PUT", "PATCH"],
                                        "description": "HTTP method"
                                    }
                                },
                                "required": ["url", "payload"]
                            }
                        },
                        {
                            "name": "send_bulk_notifications",
                            "description": "Send notifications to multiple recipients",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "notifications": {
                                        "type": "array",
                                        "description": "List of notifications to send",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "type": {"type": "string", "enum": ["email", "slack", "webhook"]},
                                                "config": {"type": "object", "description": "Type-specific configuration"}
                                            }
                                        }
                                    },
                                    "batch_size": {"type": "integer", "description": "Batch processing size"},
                                    "delay_ms": {"type": "integer", "description": "Delay between batches in milliseconds"}
                                },
                                "required": ["notifications"]
                            }
                        },
                        {
                            "name": "get_notification_status",
                            "description": "Get status of sent notifications",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "notification_id": {"type": "string", "description": "Specific notification ID"},
                                    "limit": {"type": "integer", "description": "Number of recent notifications to return"}
                                }
                            }
                        }
                    ]
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name == "send_email":
                result = await send_email_impl(arguments)
            elif tool_name == "send_slack_message":
                result = await send_slack_message_impl(arguments)
            elif tool_name == "send_webhook":
                result = await send_webhook_impl(arguments)
            elif tool_name == "send_bulk_notifications":
                result = await send_bulk_notifications_impl(arguments)
            elif tool_name == "get_notification_status":
                result = await get_notification_status_impl(arguments)
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


# Utility functions
def generate_notification_id() -> str:
    """Generate unique notification ID."""
    import uuid
    return str(uuid.uuid4())


def log_notification(notification_type: str, config: Dict, status: str, error: str = None):
    """Log notification attempt."""
    log_entry = {
        "id": generate_notification_id(),
        "type": notification_type,
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "config": config,
        "error": error
    }
    notification_log.append(log_entry)
    
    # Keep only last 1000 entries
    if len(notification_log) > 1000:
        notification_log.pop(0)
    
    return log_entry["id"]


# Tool implementations
async def send_email_impl(arguments: Dict):
    """Send email notification (mock implementation for demo)."""
    to = arguments["to"]
    subject = arguments["subject"]
    body = arguments["body"]
    from_addr = arguments.get("from", "noreply@example.com")
    cc = arguments.get("cc", [])
    bcc = arguments.get("bcc", [])
    
    # Mock email sending for demo
    notification_id = log_notification("email", {
        "to": to,
        "from": from_addr,
        "subject": subject,
        "cc": cc,
        "bcc": bcc
    }, "sent")
    
    # In a real implementation, you would:
    # 1. Connect to SMTP server
    # 2. Compose email with proper headers
    # 3. Send email
    # 4. Handle delivery status
    
    return {
        "notification_id": notification_id,
        "status": "sent",
        "recipients": [to] + cc + bcc,
        "sent_at": datetime.now().isoformat(),
        "provider": "demo-smtp",
        "message": f"Email sent to {to} with subject '{subject}'"
    }


async def send_slack_message_impl(arguments: Dict):
    """Send Slack message (mock implementation for demo)."""
    channel = arguments["channel"]
    message = arguments["message"]
    username = arguments.get("username", "EAT Bot")
    emoji = arguments.get("emoji", ":robot_face:")
    attachments = arguments.get("attachments", [])
    
    # Mock Slack API call for demo
    notification_id = log_notification("slack", {
        "channel": channel,
        "username": username,
        "emoji": emoji
    }, "sent")
    
    # In a real implementation, you would:
    # 1. Make HTTP request to Slack Web API
    # 2. Handle authentication with bot token
    # 3. Process response and handle errors
    # 4. Return message timestamp and other metadata
    
    return {
        "notification_id": notification_id,
        "status": "sent",
        "channel": channel,
        "message_ts": str(datetime.now().timestamp()),
        "sent_at": datetime.now().isoformat(),
        "bot_id": "demo-bot",
        "message": f"Slack message sent to {channel}"
    }


async def send_webhook_impl(arguments: Dict):
    """Send webhook notification."""
    url = arguments["url"]
    payload = arguments["payload"]
    headers = arguments.get("headers", {})
    method = arguments.get("method", "POST")
    
    notification_id = generate_notification_id()
    
    try:
        # Set default headers
        default_headers = {
            "Content-Type": "application/json",
            "User-Agent": "EAT-Framework/1.0"
        }
        default_headers.update(headers)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                json=payload,
                headers=default_headers
            )
            
            log_notification("webhook", {
                "url": url,
                "method": method,
                "status_code": response.status_code
            }, "sent" if response.status_code < 400 else "error")
            
            return {
                "notification_id": notification_id,
                "status": "sent" if response.status_code < 400 else "error",
                "status_code": response.status_code,
                "sent_at": datetime.now().isoformat(),
                "response_headers": dict(response.headers),
                "url": url,
                "message": f"Webhook {method} to {url} returned {response.status_code}"
            }
    
    except Exception as e:
        log_notification("webhook", {
            "url": url,
            "method": method
        }, "error", str(e))
        
        return {
            "notification_id": notification_id,
            "status": "error",
            "error": str(e),
            "sent_at": datetime.now().isoformat(),
            "url": url,
            "message": f"Webhook {method} to {url} failed: {e}"
        }


async def send_bulk_notifications_impl(arguments: Dict):
    """Send bulk notifications with batching."""
    notifications = arguments["notifications"]
    batch_size = arguments.get("batch_size", 10)
    delay_ms = arguments.get("delay_ms", 100)
    
    results = []
    
    # Process in batches
    for i in range(0, len(notifications), batch_size):
        batch = notifications[i:i + batch_size]
        batch_results = []
        
        # Process batch concurrently
        for notification in batch:
            notification_type = notification["type"]
            config = notification["config"]
            
            try:
                if notification_type == "email":
                    result = await send_email_impl(config)
                elif notification_type == "slack":
                    result = await send_slack_message_impl(config)
                elif notification_type == "webhook":
                    result = await send_webhook_impl(config)
                else:
                    result = {
                        "status": "error",
                        "error": f"Unknown notification type: {notification_type}"
                    }
                
                batch_results.append(result)
                
            except Exception as e:
                batch_results.append({
                    "status": "error",
                    "error": str(e),
                    "type": notification_type
                })
        
        results.extend(batch_results)
        
        # Delay between batches
        if delay_ms > 0 and i + batch_size < len(notifications):
            await asyncio.sleep(delay_ms / 1000)
    
    # Calculate summary statistics
    sent_count = sum(1 for r in results if r.get("status") == "sent")
    error_count = len(results) - sent_count
    
    return {
        "total_notifications": len(notifications),
        "sent_count": sent_count,
        "error_count": error_count,
        "success_rate": round((sent_count / len(results)) * 100, 1) if results else 0,
        "processed_at": datetime.now().isoformat(),
        "results": results
    }


async def get_notification_status_impl(arguments: Dict):
    """Get notification status and history."""
    notification_id = arguments.get("notification_id")
    limit = arguments.get("limit", 50)
    
    if notification_id:
        # Get specific notification
        for entry in reversed(notification_log):
            if entry["id"] == notification_id:
                return entry
        
        raise ValueError(f"Notification {notification_id} not found")
    
    else:
        # Get recent notifications
        recent_notifications = notification_log[-limit:] if notification_log else []
        
        # Calculate summary statistics
        total = len(notification_log)
        sent = sum(1 for entry in notification_log if entry["status"] == "sent")
        errors = total - sent
        
        return {
            "total_notifications": total,
            "sent_count": sent,
            "error_count": errors,
            "success_rate": round((sent / total) * 100, 1) if total > 0 else 0,
            "recent_notifications": list(reversed(recent_notifications)),
            "retrieved_at": datetime.now().isoformat()
        }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3003))
    uvicorn.run(
        "notifications_server:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )