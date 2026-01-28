"""
Implementation of tools for inventory in MCP-Odoo
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP, Context

from .models import (
    ProductAvailabilityInput,
    InventoryAdjustmentCreate,
    InventoryTurnoverInput
)

def register_inventory_tools(mcp: FastMCP) -> None:
    """Registers inventory-related tools"""
    
    @mcp.tool(description="Checks the stock availability for one or more products")
    def check_product_availability(
        ctx: Context,
        params: ProductAvailabilityInput
    ) -> Dict[str, Any]:
        """
        Checks the stock availability for one or more products
        
        Args:
            params: Parameters with product IDs and optional location
            
        Returns:
            Dictionary with availability information
        """
        odoo = ctx.request_context.lifespan_context.odoo
        
        try:
            # Check if products exist
            products = odoo.search_read(
                "product.product",
                [("id", "in", params.product_ids)],
                fields=["name", "default_code", "type", "uom_id"]
            )
            
            if not products:
                return {"success": False, "error": "No products found with the provided IDs"}
            
            # Map IDs to names for reference
            product_names = {p["id"]: p["name"] for p in products}
            
            # Get availability
            availability = {}
            
            for product_id in params.product_ids:
                # Build context for the query
                context = {}
                if params.location_id:
                    context["location"] = params.location_id
                
                # Get available quantity using the qty_available method
                try:
                    product_data = odoo.execute_method(
                        "product.product", 
                        "read", 
                        [product_id], 
                        ["qty_available", "virtual_available", "incoming_qty", "outgoing_qty"],
                        context
                    )
                    
                    if product_data:
                        product_info = product_data[0]
                        availability[product_id] = {
                            "name": product_names.get(product_id, f"Product {product_id}"),
                            "qty_available": product_info["qty_available"],
                            "virtual_available": product_info["virtual_available"],
                            "incoming_qty": product_info["incoming_qty"],
                            "outgoing_qty": product_info["outgoing_qty"]
                        }
                    else:
                        availability[product_id] = {
                            "name": product_names.get(product_id, f"Product {product_id}"),
                            "error": "Product not found"
                        }
                except Exception as e:
                    availability[product_id] = {
                        "name": product_names.get(product_id, f"Product {product_id}"),
                        "error": str(e)
                    }
            
            # Get location information if specified
            location_info = None
            if params.location_id:
                try:
                    location_data = odoo.search_read(
                        "stock.location",
                        [("id", "=", params.location_id)],
                        fields=["name", "complete_name"]
                    )
                    if location_data:
                        location_info = location_data[0]
                except Exception:
                    location_info = {"id": params.location_id, "name": "Unknown location"}
            
            return {
                "success": True,
                "result": {
                    "products": availability,
                    "location": location_info
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @mcp.tool(description="Creates an inventory adjustment to correct stock")
    def create_inventory_adjustment(
        ctx: Context,
        adjustment: InventoryAdjustmentCreate
    ) -> Dict[str, Any]:
        """
        Creates an inventory adjustment to correct stock
        
        Args:
            adjustment: Data of the adjustment to be created
            
        Returns:
            Response with the result of the operation
        """
        odoo = ctx.request_context.lifespan_context.odoo
        
        try:
            # Check Odoo version to determine the correct model
            # In Odoo 13.0+, 'stock.inventory' is used
            # In Odoo 15.0+, 'stock.quant' is used directly
            
            # Try to get the stock.inventory model
            inventory_model_exists = odoo.execute_method(
                "ir.model",
                "search_count",
                [("model", "=", "stock.inventory")]
            ) > 0
            
            if inventory_model_exists:
                # Use the stock.inventory flow (Odoo 13.0, 14.0)
                # Create the inventory
                inventory_vals = {
                    "name": adjustment.name,
                    "line_ids": []
                }
                
                if adjustment.date:
                    try:
                        datetime.strptime(adjustment.date, "%Y-%m-%d")
                        inventory_vals["date"] = adjustment.date
                    except ValueError:
                        return {"success": False, "error": f"Invalid date format: {adjustment.date}. Use YYYY-MM-DD."}
                
                # Create the inventory
                inventory_id = odoo.execute_method("stock.inventory", "create", inventory_vals)
                
                # Add lines to the inventory
                for line in adjustment.adjustment_lines:
                    line_vals = {
                        "inventory_id": inventory_id,
                        "product_id": line.product_id,
                        "location_id": line.location_id,
                        "product_qty": line.product_qty
                    }
                    
                    odoo.execute_method("stock.inventory.line", "create", line_vals)
                
                # Confirm the inventory
                odoo.execute_method("stock.inventory", "action_validate", [inventory_id])
                
                return {
                    "success": True,
                    "result": {
                        "inventory_id": inventory_id,
                        "name": adjustment.name
                    }
                }
            else:
                # Use the stock.quant flow (Odoo 15.0+)
                result_ids = []
                
                for line in adjustment.adjustment_lines:
                    # Search for the existing quant
                    quant_domain = [
                        ("product_id", "=", line.product_id),
                        ("location_id", "=", line.location_id)
                    ]
                    
                    quants = odoo.search_read(
                        "stock.quant",
                        quant_domain,
                        fields=["id", "quantity"]
                    )
                    
                    if quants:
                        # Update existing quant
                        quant_id = quants[0]["id"]
                        odoo.execute_method(
                            "stock.quant",
                            "write",
                            [quant_id],
                            {"inventory_quantity": line.product_qty}
                        )
                        result_ids.append(quant_id)
                    else:
                        # Create new quant
                        quant_vals = {
                            "product_id": line.product_id,
                            "location_id": line.location_id,
                            "inventory_quantity": line.product_qty
                        }
                        quant_id = odoo.execute_method("stock.quant", "create", quant_vals)
                        result_ids.append(quant_id)
                
                # Apply the inventory
                odoo.execute_method("stock.quant", "action_apply_inventory", result_ids)
                
                return {
                    "success": True,
                    "result": {
                        "quant_ids": result_ids,
                        "name": adjustment.name
                    }
                }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @mcp.tool(description="Calculates and analyzes inventory turnover")
    def analyze_inventory_turnover(
        ctx: Context,
        params: InventoryTurnoverInput
    ) -> Dict[str, Any]:
        """
        Calculates and analyzes inventory turnover
        
        Args:
            params: Parameters for the analysis
            
        Returns:
            Dictionary with analysis results
        """
        odoo = ctx.request_context.lifespan_context.odoo
        
        try:
            # Validate dates
            try:
                date_from = datetime.strptime(params.date_from, "%Y-%m-%d")
                date_to = datetime.strptime(params.date_to, "%Y-%m-%d")
            except ValueError:
                return {"success": False, "error": "Invalid date format. Use YYYY-MM-DD."}
            
            # Build domain for products
            product_domain = [("type", "=", "product")]  # Only storable products
            
            if params.product_ids:
                product_domain.append(("id", "in", params.product_ids))
                
            if params.category_id:
                product_domain.append(("categ_id", "=", params.category_id))
            
            # Get products
            products = odoo.search_read(
                "product.product",
                product_domain,
                fields=["name", "default_code", "categ_id", "standard_price"]
            )
            
            if not products:
                return {"success": False, "error": "No products found with the specified criteria"}
            
            # Calculate turnover for each product
            product_turnover = {}
            
            for product in products:
                product_id = product["id"]
                
                # 1. Get outgoing moves (sales) in the period
                outgoing_domain = [
                    ("product_id", "=", product_id),
                    ("date", ">=", params.date_from),
                    ("date", "<=", params.date_to),
                    ("location_dest_id.usage", "=", "customer")  # Destination: customer
                ]
                
                outgoing_moves = odoo.search_read(
                    "stock.move",
                    outgoing_domain,
                    fields=["product_uom_qty", "price_unit"]
                )
                
                # Calculate cost of goods sold
                cogs = sum(move["product_uom_qty"] * (move.get("price_unit") or product["standard_price"]) for move in outgoing_moves)
                
                # 2. Get average inventory value
                # Try to get inventory valuation at the beginning and end of the period
                
                # Method 1: Use valuation reports if available
                try:
                    # Valuation at the beginning of the period
                    context_start = {
                        "to_date": params.date_from
                    }
                    
                    valuation_start = odoo.execute_method(
                        "product.product",
                        "read",
                        [product_id],
                        ["stock_value"],
                        context_start
                    )
                    
                    # Valuation at the end of the period
                    context_end = {
                        "to_date": params.date_to
                    }
                    
                    valuation_end = odoo.execute_method(
                        "product.product",
                        "read",
                        [product_id],
                        ["stock_value"],
                        context_end
                    )
                    
                    start_value = valuation_start[0]["stock_value"] if valuation_start else 0
                    end_value = valuation_end[0]["stock_value"] if valuation_end else 0
                    
                    avg_inventory_value = (start_value + end_value) / 2
                    
                except Exception:
                    # Method 2: Estimation based on standard price and quantity
                    # Get quantity at the beginning
                    context_start = {
                        "to_date": params.date_from
                    }
                    
                    qty_start = odoo.execute_method(
                        "product.product",
                        "read",
                        [product_id],
                        ["qty_available"],
                        context_start
                    )
                    
                    # Get quantity at the end
                    context_end = {
                        "to_date": params.date_to
                    }
                    
                    qty_end = odoo.execute_method(
                        "product.product",
                        "read",
                        [product_id],
                        ["qty_available"],
                        context_end
                    )
                    
                    start_qty = qty_start[0]["qty_available"] if qty_start else 0
                    end_qty = qty_end[0]["qty_available"] if qty_end else 0
                    
                    avg_qty = (start_qty + end_qty) / 2
                    avg_inventory_value = avg_qty * product["standard_price"]
                
                # 3. Calculate turnover metrics
                turnover_ratio = 0
                days_inventory = 0
                
                if avg_inventory_value > 0:
                    turnover_ratio = cogs / avg_inventory_value
                    
                    # Days of inventory (based on the analyzed period)
                    days_in_period = (date_to - date_from).days + 1
                    if turnover_ratio > 0:
                        days_inventory = days_in_period / turnover_ratio
                
                # Save results
                product_turnover[product_id] = {
                    "name": product["name"],
                    "default_code": product["default_code"],
                    "category": product["categ_id"][1] if product["categ_id"] else "Uncategorized",
                    "cogs": cogs,
                    "avg_inventory_value": avg_inventory_value,
                    "turnover_ratio": turnover_ratio,
                    "days_inventory": days_inventory
                }
            
            # Sort products by turnover (from highest to lowest)
            sorted_products = sorted(
                product_turnover.items(),
                key=lambda x: x[1]["turnover_ratio"],
                reverse=True
            )
            
            # Calculate overall averages
            total_cogs = sum(data["cogs"] for _, data in product_turnover.items())
            total_avg_value = sum(data["avg_inventory_value"] for _, data in product_turnover.items())
            
            overall_turnover = 0
            overall_days = 0
            
            if total_avg_value > 0:
                overall_turnover = total_cogs / total_avg_value
                days_in_period = (date_to - date_from).days + 1
                if overall_turnover > 0:
                    overall_days = days_in_period / overall_turnover
            
            # Prepare result
            result = {
                "period": {
                    "from": params.date_from,
                    "to": params.date_to,
                    "days": (date_to - date_from).days + 1
                },
                "summary": {
                    "product_count": len(products),
                    "total_cogs": total_cogs,
                    "total_avg_inventory_value": total_avg_value,
                    "overall_turnover_ratio": overall_turnover,
                    "overall_days_inventory": overall_days
                },
                "products": [
                    {"id": k, **v} for k, v in sorted_products
                ]
            }
            
            return {"success": True, "result": result}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
