"""
Pydantic models implementation for MCP-Odoo
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

# Sales Models
class SalesOrderLineCreate(BaseModel):
    """Sales order line for creation"""
    product_id: int = Field(description="ID of the product")
    product_uom_qty: float = Field(description="Quantity")
    price_unit: Optional[float] = Field(None, description="Unit price (optional, Odoo can calculate it)")

class SalesOrderCreate(BaseModel):
    """Data to create a sales order"""
    partner_id: int = Field(description="ID of the customer")
    order_lines: List[SalesOrderLineCreate] = Field(description="Order lines")
    date_order: Optional[str] = Field(None, description="Order date (YYYY-MM-DD)")

class SalesOrderFilter(BaseModel):
    """Filters for sales order search"""
    partner_id: Optional[int] = Field(None, description="Filter by customer ID")
    date_from: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    state: Optional[str] = Field(None, description="Order state (e.g., 'sale', 'draft', 'done')")
    limit: Optional[int] = Field(20, description="Limit of results")
    offset: Optional[int] = Field(0, description="Offset for pagination")
    order: Optional[str] = Field(None, description="Sort criteria (e.g., 'date_order DESC')")

class SalesPerformanceInput(BaseModel):
    """Parameters for sales performance analysis"""
    date_from: str = Field(description="Start date (YYYY-MM-DD)")
    date_to: str = Field(description="End date (YYYY-MM-DD)")
    group_by: Optional[str] = Field(None, description="Group by ('product', 'customer', 'salesperson')")

# Purchase Models
class PurchaseOrderLineCreate(BaseModel):
    """Purchase order line for creation"""
    product_id: int = Field(description="ID of the product")
    product_qty: float = Field(description="Quantity")
    price_unit: Optional[float] = Field(None, description="Unit price (optional)")

class PurchaseOrderCreate(BaseModel):
    """Data to create a purchase order"""
    partner_id: int = Field(description="ID of the supplier")
    order_lines: List[PurchaseOrderLineCreate] = Field(description="Order lines")
    date_order: Optional[str] = Field(None, description="Order date (YYYY-MM-DD)")

class PurchaseOrderFilter(BaseModel):
    """Filters for purchase order search"""
    partner_id: Optional[int] = Field(None, description="Filter by supplier ID")
    date_from: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    state: Optional[str] = Field(None, description="Order state (e.g., 'purchase', 'draft', 'done')")
    limit: Optional[int] = Field(20, description="Limit of results")
    offset: Optional[int] = Field(0, description="Offset for pagination")
    order: Optional[str] = Field(None, description="Sort criteria (e.g., 'date_order DESC')")

class SupplierPerformanceInput(BaseModel):
    """Parameters for supplier performance analysis"""
    date_from: str = Field(description="Start date (YYYY-MM-DD)")
    date_to: str = Field(description="End date (YYYY-MM-DD)")
    supplier_ids: Optional[List[int]] = Field(None, description="List of supplier IDs (optional)")

# Inventory Models
class ProductAvailabilityInput(BaseModel):
    """Parameters to check product availability"""
    product_ids: List[int] = Field(description="List of product IDs")
    location_id: Optional[int] = Field(None, description="ID of the specific location (optional)")

class InventoryLineAdjustment(BaseModel):
    """Inventory adjustment line"""
    product_id: int = Field(description="ID of the product")
    location_id: int = Field(description="ID of the location")
    product_qty: float = Field(description="Actual counted quantity")

class InventoryAdjustmentCreate(BaseModel):
    """Data to create an inventory adjustment"""
    name: str = Field(description="Name or description of the adjustment")
    adjustment_lines: List[InventoryLineAdjustment] = Field(description="Adjustment lines")
    date: Optional[str] = Field(None, description="Date of the adjustment (YYYY-MM-DD)")

class InventoryTurnoverInput(BaseModel):
    """Parameters for inventory turnover analysis"""
    date_from: str = Field(description="Start date (YYYY-MM-DD)")
    date_to: str = Field(description="End date (YYYY-MM-DD)")
    product_ids: Optional[List[int]] = Field(None, description="List of product IDs (optional)")
    category_id: Optional[int] = Field(None, description="Product category ID (optional)")

# Accounting Models
class JournalEntryLineCreate(BaseModel):
    """Journal entry line for creation"""
    account_id: int = Field(description="ID of the account")
    partner_id: Optional[int] = Field(None, description="ID of the partner (optional)")
    name: Optional[str] = Field(None, description="Line description")
    debit: float = Field(0.0, description="Debit amount")
    credit: float = Field(0.0, description="Credit amount")

class JournalEntryCreate(BaseModel):
    """Data to create a journal entry"""
    ref: Optional[str] = Field(None, description="Reference of the entry")
    journal_id: int = Field(description="ID of the journal")
    date: Optional[str] = Field(None, description="Date of the entry (YYYY-MM-DD)")
    lines: List[JournalEntryLineCreate] = Field(description="Entry lines (debit and credit must match)")

class JournalEntryFilter(BaseModel):
    """Filters for journal entry search"""
    date_from: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    journal_id: Optional[int] = Field(None, description="Filter by journal ID")
    state: Optional[str] = Field(None, description="Entry state (e.g., 'posted', 'draft')")
    limit: Optional[int] = Field(20, description="Limit of results")
    offset: Optional[int] = Field(0, description="Offset for pagination")

class FinancialRatioInput(BaseModel):
    """Parameters for calculating financial ratios"""
    date_from: str = Field(description="Start date (YYYY-MM-DD)")
    date_to: str = Field(description="End date (YYYY-MM-DD)")
    ratios: List[str] = Field(description="List of ratios to calculate (e.g., ['liquidity', 'profitability', 'debt'])")
