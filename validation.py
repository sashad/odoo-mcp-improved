"""
Validation script to test the new functionalities of MCP-Odoo
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta

# Add the src directory to the path to be able to import odoo_mcp
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.odoo_mcp.odoo_client import get_odoo_client, OdooClient
from src.odoo_mcp.models import (
    SalesOrderFilter, 
    PurchaseOrderFilter,
    ProductAvailabilityInput,
    JournalEntryFilter,
    FinancialRatioInput
)

class ValidationContext:
    """Simulated context for testing"""
    
    class RequestContext:
        def __init__(self, odoo_client):
            self.lifespan_context = type('LifespanContext', (), {'odoo': odoo_client})
    
    def __init__(self, odoo_client):
        self.request_context = self.RequestContext(odoo_client)

def run_validation():
    """Runs validation tests for all new functionalities"""
    
    print("Starting validation of improved MCP-Odoo...")
    
    # Get Odoo client
    try:
        odoo_client = get_odoo_client()
        print("✅ Connection with Odoo established successfully")
    except Exception as e:
        print(f"❌ Error connecting to Odoo: {str(e)}")
        return False
    
    # Create simulated context
    ctx = ValidationContext(odoo_client)
    
    # Validate sales tools
    print("\n=== Validating sales tools ===")
    
    try:
        from src.odoo_mcp.tools_sales import search_sales_orders
        
        # Create test filter
        filter_params = SalesOrderFilter(
            date_from=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
            date_to=datetime.now().strftime("%Y-%m-%d"),
            limit=5
        )
        
        # Execute search
        result = search_sales_orders(ctx, filter_params)
        
        if result.get("success"):
            print(f"✅ search_sales_orders: Found {result['result']['count']} sales orders")
        else:
            print(f"❌ search_sales_orders: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Error validating search_sales_orders: {str(e)}")
    
    # Validate purchase tools
    print("\n=== Validating purchase tools ===")
    
    try:
        from src.odoo_mcp.tools_purchase import search_purchase_orders
        
        # Create test filter
        filter_params = PurchaseOrderFilter(
            date_from=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
            date_to=datetime.now().strftime("%Y-%m-%d"),
            limit=5
        )
        
        # Execute search
        result = search_purchase_orders(ctx, filter_params)
        
        if result.get("success"):
            print(f"✅ search_purchase_orders: Found {result['result']['count']} purchase orders")
        else:
            print(f"❌ search_purchase_orders: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Error validating search_purchase_orders: {str(e)}")
    
    # Validate inventory tools
    print("\n=== Validating inventory tools ===")
    
    try:
        from src.odoo_mcp.tools_inventory import check_product_availability
        
        # Get some product IDs
        products = odoo_client.search_read(
            "product.product",
            [("type", "=", "product")],
            fields=["id"],
            limit=3
        )
        
        if products:
            product_ids = [p["id"] for p in products]
            
            # Create test parameters
            params = ProductAvailabilityInput(
                product_ids=product_ids
            )
            
            # Execute check
            result = check_product_availability(ctx, params)
            
            if result.get("success"):
                print(f"✅ check_product_availability: Verified {len(result['result']['products'])} products")
            else:
                print(f"❌ check_product_availability: {result.get('error', 'Unknown error')}")
        else:
            print("⚠️ No products found to validate check_product_availability")
    except Exception as e:
        print(f"❌ Error validating check_product_availability: {str(e)}")
    
    # Validate accounting tools
    print("\n=== Validating accounting tools ===")
    
    try:
        from src.odoo_mcp.tools_accountings import search_journal_entries
        
        # Create test filter
        filter_params = JournalEntryFilter(
            date_from=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
            date_to=datetime.now().strftime("%Y-%m-%d"),
            limit=5
        )
        
        # Execute search
        result = search_journal_entries(ctx, filter_params)
        
        if result.get("success"):
            print(f"✅ search_journal_entries: Found {result['result']['count']} journal entries")
        else:
            print(f"❌ search_journal_entries: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Error validating search_journal_entries: {str(e)}")
    
    try:
        from src.odoo_mcp.tools_accountings import analyze_financial_ratios
        
        # Create test parameters
        params = FinancialRatioInput(
            date_from=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
            date_to=datetime.now().strftime("%Y-%m-%d"),
            ratios=["liquidity", "profitability", "debt"]
        )
        
        # Execute analysis
        result = analyze_financial_ratios(ctx, params)
        
        if result.get("success"):
            print(f"✅ analyze_financial_ratios: Analysis completed with {len(result['result']['ratios'])} ratios")
        else:
            print(f"❌ analyze_financial_ratios: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Error validating analyze_financial_ratios: {str(e)}")
    
    # Validate resources
    print("\n=== Validating resources ===")
    
    try:
        from src.odoo_mcp.resources import register_sales_resources
        print("✅ Sales resources imported successfully")
    except Exception as e:
        print(f"❌ Error importing sales resources: {str(e)}")
    
    try:
        from src.odoo_mcp.resources import register_purchase_resources
        print("✅ Purchase resources imported successfully")
    except Exception as e:
        print(f"❌ Error importing purchase resources: {str(e)}")
    
    try:
        from src.odoo_mcp.resources import register_inventory_resources
        print("✅ Inventory resources imported successfully")
    except Exception as e:
        print(f"❌ Error importing inventory resources: {str(e)}")
    
    try:
        from src.odoo_mcp.resources import register_accounting_resources
        print("✅ Accounting resources imported successfully")
    except Exception as e:
        print(f"❌ Error importing accounting resources: {str(e)}")
    
    # Validate prompts
    print("\n=== Validating prompts ===")
    
    try:
        from src.odoo_mcp.prompts import register_all_prompts
        print("✅ Prompts imported successfully")
    except Exception as e:
        print(f"❌ Error importing prompts: {str(e)}")
    
    # Validate full integration
    print("\n=== Validating full integration ===")
    
    try:
        from src.odoo_mcp.extensions import register_all_extensions
        print("✅ Extensions module imported successfully")
    except Exception as e:
        print(f"❌ Error importing extensions module: {str(e)}")
    
    try:
        from src.odoo_mcp.server import mcp
        print("✅ MCP server imported successfully")
    except Exception as e:
        print(f"❌ Error importing MCP server: {str(e)}")
    
    print("\nValidation completed.")
    return True

if __name__ == "__main__":
    run_validation()
