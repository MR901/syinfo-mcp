#!/usr/bin/env python3
"""
E-commerce MCP Server Example

This example shows how to adapt the template for an e-commerce domain.
It demonstrates:
- Custom configuration for e-commerce
- Domain-specific tools for inventory, orders, customers
- Resources for product catalogs, sales data
- Prompts for customer service and analytics

Run with: python examples/ecommerce_server.py
"""

import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import json
from datetime import datetime

from src.template_server import TemplateMCPServer, ServerCapabilities
from src.common.template_config import EcommerceServerConfig, TemplateConfigManager


# Custom e-commerce capabilities registration
def register_ecommerce_capabilities(mcp_server, http_client, config):
    """Register e-commerce specific capabilities."""
    
    # Sample e-commerce data (in real app, this would come from database)
    sample_products = [
        {"id": "1", "name": "Laptop", "price": 999.99, "stock": 15},
        {"id": "2", "name": "Mouse", "price": 29.99, "stock": 50},
        {"id": "3", "name": "Keyboard", "price": 79.99, "stock": 30},
    ]
    
    sample_orders = [
        {"id": "1001", "customer": "john@example.com", "total": 1029.98, "status": "shipped"},
        {"id": "1002", "customer": "jane@example.com", "total": 79.99, "status": "processing"},
    ]
    
    # ============================================================================
    # E-COMMERCE TOOLS
    # ============================================================================
    
    @mcp_server.tool()
    def get_product_inventory(product_id: str = "") -> Dict[str, Any]:
        """Get current inventory levels for products.
        
        Args:
            product_id: Specific product ID, or empty for all products
            
        Returns:
            Product inventory information with stock levels
        """
        try:
            if product_id:
                # Find specific product
                product = next((p for p in sample_products if p["id"] == product_id), None)
                if not product:
                    return {"error": f"Product {product_id} not found", "status": "not_found"}
                return {"product": product, "status": "success"}
            else:
                # Return all products
                return {"products": sample_products, "total_products": len(sample_products), "status": "success"}
                
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    @mcp_server.tool()
    def update_product_stock(product_id: str, new_stock: int) -> Dict[str, Any]:
        """Update stock level for a product.
        
        Args:
            product_id: Product ID to update
            new_stock: New stock quantity
            
        Returns:
            Updated product information
        """
        if not config.get("allow_write_access", False):
            return {"error": "Write access not allowed", "status": "permission_denied"}
            
        try:
            # Find and update product
            for product in sample_products:
                if product["id"] == product_id:
                    old_stock = product["stock"]
                    product["stock"] = max(0, new_stock)  # Don't allow negative stock
                    return {
                        "product_id": product_id,
                        "old_stock": old_stock,
                        "new_stock": product["stock"],
                        "updated_at": datetime.now().isoformat(),
                        "status": "success"
                    }
            
            return {"error": f"Product {product_id} not found", "status": "not_found"}
            
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    @mcp_server.tool()
    def search_orders(customer_email: str = "", status: str = "", limit: int = 10) -> Dict[str, Any]:
        """Search orders by customer or status.
        
        Args:
            customer_email: Filter by customer email
            status: Filter by order status (processing, shipped, delivered, cancelled)
            limit: Maximum number of orders to return
            
        Returns:
            List of matching orders
        """
        try:
            filtered_orders = sample_orders.copy()
            
            # Apply filters
            if customer_email:
                filtered_orders = [o for o in filtered_orders if customer_email.lower() in o["customer"].lower()]
            
            if status:
                filtered_orders = [o for o in filtered_orders if o["status"].lower() == status.lower()]
            
            # Apply limit
            filtered_orders = filtered_orders[:limit]
            
            return {
                "orders": filtered_orders,
                "total_found": len(filtered_orders),
                "filters_applied": {"customer_email": customer_email, "status": status},
                "status": "success"
            }
            
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    @mcp_server.tool()
    def calculate_sales_metrics(days: int = 30) -> Dict[str, Any]:
        """Calculate sales metrics for the specified period.
        
        Args:
            days: Number of days to analyze (default: 30)
            
        Returns:
            Sales analytics and metrics
        """
        try:
            # Simple calculation with sample data
            total_orders = len(sample_orders)
            total_revenue = sum(order["total"] for order in sample_orders)
            average_order_value = total_revenue / total_orders if total_orders > 0 else 0
            
            # Product performance
            product_sales = {}
            for order in sample_orders:
                # Simplified - in real app would have order items
                product_sales["misc_products"] = product_sales.get("misc_products", 0) + 1
            
            return {
                "period_days": days,
                "total_orders": total_orders,
                "total_revenue": round(total_revenue, 2),
                "average_order_value": round(average_order_value, 2),
                "product_performance": product_sales,
                "calculated_at": datetime.now().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    # ============================================================================
    # E-COMMERCE RESOURCES
    # ============================================================================
    
    @mcp_server.resource("resource://ecommerce/catalog")
    def get_product_catalog() -> str:
        """Get the complete product catalog with current pricing and availability."""
        
        catalog_md = "# Product Catalog\n\n"
        catalog_md += f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        catalog_md += f"**Total Products:** {len(sample_products)}\n\n"
        
        for product in sample_products:
            catalog_md += f"## {product['name']} (ID: {product['id']})\n\n"
            catalog_md += f"- **Price:** ${product['price']:.2f}\n"
            catalog_md += f"- **In Stock:** {product['stock']} units\n"
            catalog_md += f"- **Availability:** {'Available' if product['stock'] > 0 else 'Out of Stock'}\n\n"
        
        return catalog_md
    
    @mcp_server.resource("resource://ecommerce/orders/recent")
    def get_recent_orders() -> str:
        """Get recent order activity and status."""
        
        orders_md = "# Recent Orders\n\n"
        orders_md += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        orders_md += f"**Total Orders:** {len(sample_orders)}\n\n"
        
        for order in sample_orders:
            orders_md += f"## Order #{order['id']}\n\n"
            orders_md += f"- **Customer:** {order['customer']}\n"
            orders_md += f"- **Total:** ${order['total']:.2f}\n"
            orders_md += f"- **Status:** {order['status'].title()}\n\n"
        
        return orders_md
    
    @mcp_server.resource("resource://ecommerce/analytics/dashboard")
    def get_analytics_dashboard() -> str:
        """Get e-commerce analytics dashboard data."""
        
        # Calculate metrics
        total_revenue = sum(order["total"] for order in sample_orders)
        avg_order_value = total_revenue / len(sample_orders) if sample_orders else 0
        total_inventory_value = sum(p["price"] * p["stock"] for p in sample_products)
        
        dashboard_md = "# E-commerce Analytics Dashboard\n\n"
        dashboard_md += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        dashboard_md += "## Key Metrics\n\n"
        dashboard_md += f"- **Total Revenue:** ${total_revenue:.2f}\n"
        dashboard_md += f"- **Average Order Value:** ${avg_order_value:.2f}\n"
        dashboard_md += f"- **Total Orders:** {len(sample_orders)}\n"
        dashboard_md += f"- **Inventory Value:** ${total_inventory_value:.2f}\n\n"
        
        dashboard_md += "## Stock Alerts\n\n"
        low_stock_products = [p for p in sample_products if p["stock"] < 20]
        if low_stock_products:
            for product in low_stock_products:
                dashboard_md += f"- ⚠️ **{product['name']}**: Only {product['stock']} units remaining\n"
        else:
            dashboard_md += "- ✅ All products have adequate stock levels\n"
        
        dashboard_md += "\n## Order Status Distribution\n\n"
        status_counts = {}
        for order in sample_orders:
            status_counts[order["status"]] = status_counts.get(order["status"], 0) + 1
        
        for status, count in status_counts.items():
            dashboard_md += f"- **{status.title()}:** {count} orders\n"
        
        return dashboard_md
    
    # ============================================================================
    # E-COMMERCE PROMPTS
    # ============================================================================
    
    @mcp_server.prompt()
    def get_customer_service_prompt() -> str:
        """Get prompt for customer service interactions."""
        return """You are a helpful e-commerce customer service AI assistant.

You have access to:
- Product inventory and catalog information
- Order status and history
- Customer order details
- Sales analytics and metrics

## Your Capabilities:
- Check product availability and pricing
- Look up order status and details
- Help with inventory questions
- Provide sales and analytics insights
- Answer general e-commerce questions

## Guidelines:
1. Always be helpful and professional
2. Use actual data from the tools when possible
3. For order issues, get specific order numbers
4. For product questions, check current inventory
5. Escalate complex issues appropriately

## Example Interactions:
- "What's the status of order #1001?"
- "Do you have laptops in stock?"
- "Show me recent sales metrics"
- "Which products are running low on inventory?"

Please ask how you can help the customer today.
"""
    
    @mcp_server.prompt()
    def get_inventory_management_prompt() -> str:
        """Get prompt for inventory management tasks."""
        return """You are an inventory management AI assistant for an e-commerce business.

## Your Role:
You help manage product inventory, track stock levels, and provide insights for purchasing decisions.

## Available Data:
- Real-time product inventory levels
- Sales velocity and trends
- Stock alerts and recommendations
- Product performance metrics

## Key Tasks:
1. **Stock Monitoring**: Track inventory levels and identify low stock
2. **Reorder Recommendations**: Suggest when to reorder products
3. **Performance Analysis**: Analyze product sales and inventory turnover
4. **Alert Management**: Flag urgent inventory issues

## Usage Examples:
- "Check current inventory levels"
- "Which products need reordering?"
- "Show me low stock alerts"
- "Calculate inventory turnover for laptops"
- "Update stock levels after receiving shipment"

Focus on maintaining optimal inventory levels while minimizing stockouts and overstock situations.
"""
    
    @mcp_server.prompt()
    def get_sales_analysis_prompt() -> str:
        """Get prompt for sales analysis and reporting."""
        return """You are a sales analysis AI assistant for e-commerce operations.

## Your Expertise:
You analyze sales data, identify trends, and provide actionable insights for business growth.

## Analysis Capabilities:
- Sales performance metrics and KPIs
- Product performance analysis
- Customer behavior insights
- Revenue trend analysis
- Seasonal pattern identification

## Key Metrics You Track:
- Total revenue and growth rates
- Average order value (AOV)
- Conversion rates and sales velocity
- Product mix and category performance
- Customer lifetime value indicators

## Reporting Focus:
1. **Performance Dashboards**: Real-time sales metrics
2. **Trend Analysis**: Identify growth patterns and opportunities
3. **Product Insights**: Best/worst performing products
4. **Recommendations**: Data-driven suggestions for improvement

## Example Queries:
- "Generate monthly sales report"
- "Which products are top performers?"
- "Show revenue trends for the last quarter"
- "Calculate average order value by customer segment"

Provide actionable insights that drive business decisions and growth.
"""


def main():
    """Run the e-commerce MCP server example."""
    
    # Custom e-commerce configuration
    config = {
        "server_name": "E-commerce MCP Server",
        "server_description": "MCP server for e-commerce operations, inventory management, and customer analytics",
        "allow_read_access": True,
        "allow_write_access": True,  # Enable for inventory updates
        "allow_delete_access": False,
        "store_api_host": "api.mystore.com",
        "enable_inventory_tracking": True,
        "enable_order_management": True,
        "enable_customer_analytics": True
    }
    
    print("🛒 Starting E-commerce MCP Server...")
    print(f"📊 Server: {config['server_name']}")
    print(f"🔧 Features: Inventory tracking, Order management, Customer analytics")
    print("=" * 60)
    
    # Create server with custom capabilities
    server = TemplateMCPServer(
        server_name=config["server_name"],
        server_description=config["server_description"],
        host=os.getenv("MCP_HOST", "0.0.0.0"),
        port=int(os.getenv("MCP_PORT", "8000")),
        debug=os.getenv("MCP_DEBUG", "false").lower() == "true",
        capabilities_config=config,
        capabilities=ServerCapabilities.empty(),  # Use custom registration
        custom_registration_fn=register_ecommerce_capabilities
    )
    
    # Setup and run
    server.setup_mcp_server_and_capabilities()
    server.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 E-commerce server stopped by user")
    except Exception as e:
        print(f"❌ E-commerce server error: {e}")
        sys.exit(1)
