#!/usr/bin/env python3
"""
Advanced EAT agent demonstrating multi-tool workflows with error handling.
This example shows how to chain multiple tools together for complex tasks.
"""

import asyncio
import sys
import os
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from eat import Catalog


async def generate_customer_report(customer_ids: List[int]) -> Dict[str, Any]:
    """
    Generate a comprehensive customer report using multiple tools.
    
    Workflow:
    1. Fetch customer data for each ID
    2. Generate analytics for the customers
    3. Create a formatted report
    4. Send notification about the report
    """
    print("📊 Starting Multi-Tool Customer Report Generation")
    print("=" * 50)
    
    try:
        # Initialize catalog
        print("🔍 Loading tool catalog...")
        catalog = Catalog("http://localhost:8000/.well-known/api-catalog", verify_signatures=False)
        await catalog.fetch()
        
        print(f"✅ Catalog loaded with {len(catalog.tools)} tools")
        
        # Get required tools
        print("🔧 Identifying required tools...")
        
        customer_tool = catalog.get_tool("get_customer")
        analytics_tool = catalog.get_tool("customer_analytics") 
        report_tool = catalog.get_tool("generate_report")
        notification_tool = catalog.get_tool("send_email")
        
        tools_found = {
            "customer": customer_tool is not None,
            "analytics": analytics_tool is not None,
            "report": report_tool is not None,
            "notification": notification_tool is not None
        }
        
        print("🔍 Tool availability:")
        for tool_name, available in tools_found.items():
            status = "✅" if available else "❌"
            print(f"   {status} {tool_name}")
        
        if not all(tools_found.values()):
            print("⚠️  Some required tools are missing. Continuing with available tools...")
        
        # Step 1: Fetch customer data
        print(f"\n👥 Step 1: Fetching data for {len(customer_ids)} customers...")
        customers = []
        
        for customer_id in customer_ids:
            if customer_tool:
                try:
                    customer = await customer_tool.call(customer_id=customer_id)
                    customers.append(customer)
                    print(f"   ✅ Retrieved customer {customer_id}: {customer.get('name', 'Unknown')}")
                except Exception as e:
                    print(f"   ❌ Failed to get customer {customer_id}: {e}")
            else:
                print(f"   ⚠️  Customer tool not available, using mock data for {customer_id}")
                customers.append({
                    "id": customer_id,
                    "name": f"Customer {customer_id}",
                    "email": f"customer{customer_id}@example.com",
                    "company": "Demo Company"
                })
        
        print(f"📊 Successfully retrieved {len(customers)} customer records")
        
        # Step 2: Generate analytics
        print(f"\n📈 Step 2: Generating analytics...")
        analytics_result = None
        
        if analytics_tool and customers:
            try:
                analytics_result = await analytics_tool.call(
                    customer_ids=[c["id"] for c in customers],
                    metrics=["engagement", "revenue", "retention"]
                )
                print("   ✅ Analytics generated successfully")
                print(f"   📊 Analyzed {analytics_result.get('customer_count', 0)} customers")
                
                # Display key metrics
                metrics = analytics_result.get('metrics', {})
                if 'revenue' in metrics:
                    total_revenue = metrics['revenue'].get('total', 0)
                    print(f"   💰 Total estimated revenue: ${total_revenue:,.2f}")
                
                if 'engagement' in metrics:
                    avg_engagement = metrics['engagement'].get('average', 0)
                    print(f"   📊 Average engagement score: {avg_engagement:.2f}")
                
            except Exception as e:
                print(f"   ❌ Analytics failed: {e}")
                # Create mock analytics data
                analytics_result = {
                    "customer_count": len(customers),
                    "metrics": {
                        "revenue": {"total": len(customers) * 1500, "average": 1500},
                        "engagement": {"average": 0.75}
                    }
                }
                print("   📊 Using mock analytics data")
        else:
            print("   ⚠️  Analytics tool not available, creating summary from customer data")
            analytics_result = {
                "customer_count": len(customers),
                "summary": "Basic customer count analysis"
            }
        
        # Step 3: Generate formatted report
        print(f"\n📋 Step 3: Generating formatted report...")
        report_result = None
        
        if report_tool and analytics_result:
            try:
                report_result = await report_tool.call(
                    template="executive",
                    data=analytics_result,
                    format="html"
                )
                print("   ✅ Report generated successfully")
                print(f"   📄 Format: {report_result.get('format', 'unknown')}")
                
            except Exception as e:
                print(f"   ❌ Report generation failed: {e}")
                report_result = {
                    "report_type": "executive",
                    "format": "text",
                    "content": f"Customer Report Summary:\\n- Customers analyzed: {len(customers)}\\n- Total estimated revenue: ${analytics_result.get('metrics', {}).get('revenue', {}).get('total', 0):,.2f}"
                }
                print("   📋 Generated basic text report")
        else:
            print("   ⚠️  Report tool not available, creating summary")
            report_result = {
                "summary": f"Customer analysis complete for {len(customers)} customers"
            }
        
        # Step 4: Send notification
        print(f"\n📧 Step 4: Sending completion notification...")
        notification_result = None
        
        if notification_tool and report_result:
            try:
                notification_result = await notification_tool.call(
                    to="manager@example.com",
                    subject=f"Customer Report Generated - {len(customers)} Customers Analyzed",
                    body=f"""
                    <h2>Customer Report Complete</h2>
                    <p>A new customer analysis report has been generated.</p>
                    <ul>
                        <li><strong>Customers Analyzed:</strong> {len(customers)}</li>
                        <li><strong>Report Type:</strong> {report_result.get('report_type', 'Summary')}</li>
                        <li><strong>Generated:</strong> {analytics_result.get('timestamp', 'Unknown')}</li>
                    </ul>
                    <p>The detailed report is available in the system.</p>
                    """,
                    from_addr="reports@example.com"
                )
                print("   ✅ Notification sent successfully")
                print(f"   📧 Sent to: {notification_result.get('recipients', ['Unknown'])}")
                
            except Exception as e:
                print(f"   ❌ Notification failed: {e}")
                notification_result = {"status": "simulated", "message": "Would send email notification"}
                print("   📧 Notification simulated (MCP server not available)")
        else:
            print("   ⚠️  Notification tool not available")
            notification_result = {"status": "skipped"}
        
        # Final summary
        print(f"\n🎉 Multi-Tool Workflow Complete!")
        print("=" * 50)
        
        final_result = {
            "workflow_status": "completed",
            "customers_processed": len(customers),
            "analytics_available": analytics_result is not None,
            "report_generated": report_result is not None,
            "notification_sent": notification_result is not None,
            "summary": {
                "customers": [{"id": c["id"], "name": c["name"]} for c in customers],
                "analytics": analytics_result,
                "report": report_result,
                "notification": notification_result
            }
        }
        
        return final_result
        
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        return {"workflow_status": "failed", "error": str(e)}


async def main():
    """Main function to run the multi-tool agent demo."""
    # Example customer IDs to analyze
    customer_ids = [1, 2, 3]
    
    result = await generate_customer_report(customer_ids)
    
    print(f"\n📊 Final Result Summary:")
    print(f"   Status: {result.get('workflow_status', 'unknown')}")
    print(f"   Customers: {result.get('customers_processed', 0)}")
    
    if result.get('workflow_status') == 'failed':
        print(f"   Error: {result.get('error', 'Unknown error')}")
        print(f"\n🔧 Troubleshooting:")
        print(f"   1. Start the demo environment: cd demo && ./quickstart.sh")
        print(f"   2. Verify catalog is accessible: curl http://localhost:8000/.well-known/api-catalog")
        print(f"   3. Check MCP server logs: docker-compose logs")
    else:
        print(f"   ✅ Workflow completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())