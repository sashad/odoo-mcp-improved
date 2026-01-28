"""
Integration of resources for MCP-Odoo
"""

from mcp.server.fastmcp import FastMCP

def register_sales_resources(mcp: FastMCP) -> None:
    """Registers sales-related resources"""
    pass

def register_purchase_resources(mcp: FastMCP) -> None:
    """Registers purchase-related resources"""
    pass

def register_inventory_resources(mcp: FastMCP) -> None:
    """Registers inventory-related resources"""
    pass

def register_accounting_resources(mcp: FastMCP) -> None:
    """Registers accounting-related resources"""
    pass

def register_all_resources(mcp: FastMCP) -> None:
    """Registers all available resources"""
    register_sales_resources(mcp)
    register_purchase_resources(mcp)
    register_inventory_resources(mcp)
    register_accounting_resources(mcp)
