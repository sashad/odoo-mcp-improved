"""
Implementation of prompts for MCP-Odoo
"""

from mcp.server.fastmcp import FastMCP

def register_sales_prompts(mcp: FastMCP) -> None:
    """Registers sales-related prompts"""
    
    @mcp.prompt(
        name="sales_analysis",
        description="Analyzes sales for a specific period and provides key insights"
    )
    def sales_analysis_prompt() -> str:
        return """
        Analyze sales for the last {period} (e.g., 'month', 'quarter', 'year') and provide insights on:
        - Top selling products (top 5)
        - Main customers (top 5)
        - Sales trends (comparison with the previous period if possible)
        - Performance by salesperson (if applicable)
        - Actionable recommendations to improve sales.
        
        Use the available tools like 'search_sales_orders' and 'execute_method' to get the necessary data from Odoo.
        """

def register_purchase_prompts(mcp: FastMCP) -> None:
    """Registers purchase-related prompts"""
    
    @mcp.prompt(
        name="purchase_analysis",
        description="Analyzes purchase orders and supplier performance"
    )
    def purchase_analysis_prompt() -> str:
        return """
        Analyze purchases made in the last {period} (e.g., 'month', 'quarter', 'year') and provide insights on:
        - Most purchased products (top 5)
        - Main suppliers (top 5 by volume/value)
        - Purchase trends
        - Average delivery times per supplier
        - Recommendations for optimizing purchases or negotiating with suppliers.
        
        Use the available tools like 'search_purchase_orders' to get the necessary data from Odoo.
        """

def register_inventory_prompts(mcp: FastMCP) -> None:
    """Registers inventory-related prompts"""
    
    @mcp.prompt(
        name="inventory_management",
        description="Analyzes inventory status and provides recommendations"
    )
    def inventory_management_prompt() -> str:
        return """
        Analyze the current inventory status and provide information on:
        - Products with low stock (below the minimum if configured)
        - Products with excess stock (above the maximum or without movement)
        - Current inventory valuation
        - Inventory turnover for key products
        - Recommendations for adjustments, replenishment, or stock liquidation.
        
        Use the available tools like 'check_product_availability' and 'analyze_inventory_turnover' to get the necessary data from Odoo.
        """

def register_accounting_prompts(mcp: FastMCP) -> None:
    """Registers accounting-related prompts"""
    
    @mcp.prompt(
        name="financial_analysis",
        description="Performs a basic financial analysis"
    )
    def financial_analysis_prompt() -> str:
        return """
        Perform a financial analysis for the {period} (e.g., 'last_month', 'last_quarter', 'year_to_date') and provide:
        - Summary of the income statement (revenue, expenses, profit)
        - Summary of the balance sheet (assets, liabilities, equity)
        - Key financial ratios (e.g., liquidity, profitability)
        - Comparison with the previous period if possible
        - Important observations or alerts.
        
        Use the available tools like 'search_journal_entries' and 'analyze_financial_ratios' to get the necessary data from Odoo.
        """

def register_all_prompts(mcp: FastMCP) -> None:
    """Registers all available prompts"""
    register_sales_prompts(mcp)
    register_purchase_prompts(mcp)
    register_inventory_prompts(mcp)
    register_accounting_prompts(mcp)
