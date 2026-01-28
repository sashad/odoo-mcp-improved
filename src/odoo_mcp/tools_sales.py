"""
Implementation of tools for sales in MCP-Odoo
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP, Context

from .models import (
    SalesOrderFilter,
    SalesOrderCreate,
    SalesPerformanceInput
)

def register_sales_tools(mcp: FastMCP) -> None:
    """Registers sales-related tools"""
    
    @mcp.tool(description="Search for sales orders with advanced filters")
    def search_sales_orders(
        ctx: Context,
        filters: SalesOrderFilter
    ) -> Dict[str, Any]:
        """
        Searches for sales orders based on the specified filters
        
        Args:
            filters: Filters for the order search
            
        Returns:
            Dictionary with search results
        """
        odoo = ctx.request_context.lifespan_context.odoo
        
        try:
            # Build search domain
            domain = []
            
            if filters.partner_id:
                domain.append(("partner_id", "=", filters.partner_id))
                
            if filters.date_from:
                try:
                    datetime.strptime(filters.date_from, "%Y-%m-%d")
                    domain.append(("date_order", ">=", filters.date_from))
                except ValueError:
                    return {"success": False, "error": f"Invalid date format: {filters.date_from}. Use YYYY-MM-DD."}
                
            if filters.date_to:
                try:
                    datetime.strptime(filters.date_to, "%Y-%m-%d")
                    domain.append(("date_order", "<=", filters.date_to))
                except ValueError:
                    return {"success": False, "error": f"Invalid date format: {filters.date_to}. Use YYYY-MM-DD."}
                
            if filters.state:
                domain.append(("state", "=", filters.state))
            
            # Fields to retrieve
            fields = [
                "name", "partner_id", "date_order", "amount_total", 
                "state", "invoice_status", "user_id", "order_line"
            ]
            
            # Execute search
            orders = odoo.search_read(
                "sale.order", 
                domain, 
                fields=fields, 
                limit=filters.limit,
                offset=filters.offset,
                order=filters.order
            )
            
            # Get the total count without limit for pagination
            total_count = odoo.execute_method("sale.order", "search_count", domain)
            
            return {
                "success": True, 
                "result": {
                    "count": len(orders),
                    "total_count": total_count,
                    "orders": orders
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @mcp.tool(description="Create a new sales order")
    def create_sales_order(
        ctx: Context,
        order: SalesOrderCreate
    ) -> Dict[str, Any]:
        """
        Creates a new sales order
        
        Args:
            order: Data of the order to be created
            
        Returns:
            Response with the result of the operation
        """
        odoo = ctx.request_context.lifespan_context.odoo
        
        try:
            # Prepare values for the order
            order_vals = {
                "partner_id": order.partner_id,
                "order_line": []
            }
            
            if order.date_order:
                try:
                    datetime.strptime(order.date_order, "%Y-%m-%d")
                    order_vals["date_order"] = order.date_order
                except ValueError:
                    return {"success": False, "error": f"Invalid date format: {order.date_order}. Use YYYY-MM-DD."}
            
            # Prepare order lines
            for line in order.order_lines:
                line_vals = [
                    0, 0, {
                        "product_id": line.product_id,
                        "product_uom_qty": line.product_uom_qty
                    }
                ]
                
                if line.price_unit is not None:
                    line_vals[2]["price_unit"] = line.price_unit
                    
                order_vals["order_line"].append(line_vals)
            
            # Create order
            order_id = odoo.execute_method("sale.order", "create", order_vals)
            
            # Get information of the created order
            order_info = odoo.execute_method("sale.order", "read", [order_id], ["name"])[0]
            
            return {
                "success": True,
                "result": {
                    "order_id": order_id,
                    "order_name": order_info["name"]
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @mcp.tool(description="Analyzes sales performance over a period")
    def analyze_sales_performance(
        ctx: Context,
        params: SalesPerformanceInput
    ) -> Dict[str, Any]:
        """
        Analyzes sales performance over a specific period
        
        Args:
            params: Parameters for the analysis
            
        Returns:
            Dictionary with analysis results
        """
        odoo = ctx.request_context.lifespan_context.odoo
        
        try:
            # Validate dates
            try:
                datetime.strptime(params.date_from, "%Y-%m-%d")
                datetime.strptime(params.date_to, "%Y-%m-%d")
            except ValueError:
                return {"success": False, "error": "Invalid date format. Use YYYY-MM-DD."}
            
            # Build domain for confirmed orders
            domain = [
                ("date_order", ">=", params.date_from),
                ("date_order", "<=", params.date_to),
                ("state", "in", ["sale", "done"])
            ]
            
            # Get sales data
            sales_data = odoo.search_read(
                "sale.order",
                domain,
                fields=["name", "partner_id", "date_order", "amount_total", "user_id"]
            )
            
            # Calculate previous period for comparison
            date_from = datetime.strptime(params.date_from, "%Y-%m-%d")
            date_to = datetime.strptime(params.date_to, "%Y-%m-%d")
            delta = date_to - date_from
            
            prev_date_to = date_from - timedelta(days=1)
            prev_date_from = prev_date_to - delta
            
            prev_domain = [
                ("date_order", ">=", prev_date_from.strftime("%Y-%m-%d")),
                ("date_order", "<=", prev_date_to.strftime("%Y-%m-%d")),
                ("state", "in", ["sale", "done"])
            ]
            
            prev_sales_data = odoo.search_read(
                "sale.order",
                prev_domain,
                fields=["amount_total"]
            )
            
            # Calculate totals
            current_total = sum(order["amount_total"] for order in sales_data)
            previous_total = sum(order["amount_total"] for order in prev_sales_data)
            
            # Calculate percentage change
            percent_change = 0
            if previous_total > 0:
                percent_change = ((current_total - previous_total) / previous_total) * 100
            
            # Group according to the group_by parameter
            grouped_data = {}
            if params.group_by:
                if params.group_by == "product":
                    # Get order lines to analyze products
                    order_ids = [order["id"] for order in sales_data]
                    if order_ids:
                        order_lines = odoo.search_read(
                            "sale.order.line",
                            [("order_id", "in", order_ids)],
                            fields=["product_id", "product_uom_qty", "price_subtotal"]
                        )
                        
                        # Group by product
                        product_data = {}
                        for line in order_lines:
                            product_id = line["product_id"][0] if line["product_id"] else 0
                            product_name = line["product_id"][1] if line["product_id"] else "Unknown"
                            
                            if product_id not in product_data:
                                product_data[product_id] = {
                                    "name": product_name,
                                    "quantity": 0,
                                    "amount": 0
                                }
                            
                            product_data[product_id]["quantity"] += line["product_uom_qty"]
                            product_data[product_id]["amount"] += line["price_subtotal"]
                        
                        # Sort by amount
                        top_products = sorted(
                            product_data.items(),
                            key=lambda x: x[1]["amount"],
                            reverse=True
                        )
                        
                        grouped_data["products"] = [
                            {"id": k, **v} for k, v in top_products[:10]
                        ]
                
                elif params.group_by == "customer":
                    # Group by customer
                    customer_data = {}
                    for order in sales_data:
                        customer_id = order["partner_id"][0] if order["partner_id"] else 0
                        customer_name = order["partner_id"][1] if order["partner_id"] else "Unknown"
                        
                        if customer_id not in customer_data:
                            customer_data[customer_id] = {
                                "name": customer_name,
                                "order_count": 0,
                                "amount": 0
                            }
                        
                        customer_data[customer_id]["order_count"] += 1
                        customer_data[customer_id]["amount"] += order["amount_total"]
                    
                    # Sort by amount
                    top_customers = sorted(
                        customer_data.items(),
                        key=lambda x: x[1]["amount"],
                        reverse=True
                    )
                    
                    grouped_data["customers"] = [
                        {"id": k, **v} for k, v in top_customers[:10]
                    ]
                
                elif params.group_by == "salesperson":
                    # Group by salesperson
                    salesperson_data = {}
                    for order in sales_data:
                        salesperson_id = order["user_id"][0] if order["user_id"] else 0
                        salesperson_name = order["user_id"][1] if order["user_id"] else "Unknown"
                        
                        if salesperson_id not in salesperson_data:
                            salesperson_data[salesperson_id] = {
                                "name": salesperson_name,
                                "order_count": 0,
                                "amount": 0
                            }
                        
                        salesperson_data[salesperson_id]["order_count"] += 1
                        salesperson_data[salesperson_id]["amount"] += order["amount_total"]
                    
                    # Sort by amount
                    top_salespersons = sorted(
                        salesperson_data.items(),
                        key=lambda x: x[1]["amount"],
                        reverse=True
                    )
                    
                    grouped_data["salespersons"] = [
                        {"id": k, **v} for k, v in top_salespersons
                    ]
            
            # Prepare result
            result = {
                "period": {
                    "from": params.date_from,
                    "to": params.date_to
                },
                "summary": {
                    "order_count": len(sales_data),
                    "total_amount": current_total,
                    "previous_period": {
                        "from": prev_date_from.strftime("%Y-%m-%d"),
                        "to": prev_date_to.strftime("%Y-%m-%d"),
                        "order_count": len(prev_sales_data),
                        "total_amount": previous_total
                    },
                    "percent_change": round(percent_change, 2)
                }
            }
            
            # Add grouped data if it exists
            if grouped_data:
                result["grouped_data"] = grouped_data
            
            return {"success": True, "result": result}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
