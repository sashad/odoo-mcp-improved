"""
Implementation of accounting tools in MCP-Odoo
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP, Context

from .models import (
    JournalEntryFilter,
    JournalEntryCreate,
    FinancialRatioInput
)

def register_accounting_tools(mcp: FastMCP) -> None:
    """Register accounting-related tools"""
    
    @mcp.tool(description="Search accounting entries using filters")
    def search_journal_entries(
        ctx: Context,
        filters: JournalEntryFilter
    ) -> Dict[str, Any]:
        """
        Search for accounting entries based on the specified filters
        
        Args:
            filters: Filters for entry search
            
        Returns:
            Dictionary with search results
        """
        odoo = ctx.request_context.lifespan_context.odoo
        
        try:
            # Build search domain
            domain = []
            
            if filters.date_from:
                try:
                    datetime.strptime(filters.date_from, "%Y-%m-%d")
                    domain.append(("date", ">=", filters.date_from))
                except ValueError:
                    return {"success": False, "error": f"Invalid date format: {filters.date_from}. Use YYYY-MM-DD."}
                
            if filters.date_to:
                try:
                    datetime.strptime(filters.date_to, "%Y-%m-%d")
                    domain.append(("date", "<=", filters.date_to))
                except ValueError:
                    return {"success": False, "error": f"Invalid date format: {filters.date_to}. Use YYYY-MM-DD."}
                
            if filters.journal_id:
                domain.append(("journal_id", "=", filters.journal_id))
                
            if filters.state:
                domain.append(("state", "=", filters.state))
            
            # Fields to retrieve
            fields = [
                "name", "ref", "date", "journal_id", "state", 
                "amount_total", "amount_total_signed", "line_ids"
            ]
            
            # Execute search
            entries = odoo.search_read(
                "account.move", 
                domain, 
                fields=fields, 
                limit=filters.limit,
                offset=filters.offset
            )
            
            # Get the total count without limit for pagination
            total_count = odoo.execute_method("account.move", "search_count", domain)
            
            # For each entry, get summarized information from the lines
            for entry in entries:
                if entry.get("line_ids"):
                    line_ids = entry["line_ids"]
                    lines = odoo.search_read(
                        "account.move.line",
                        [("id", "in", line_ids)],
                        fields=["name", "account_id", "partner_id", "debit", "credit", "balance"]
                    )
                    entry["lines"] = lines
                    # Remove the list of IDs to reduce size
                    entry.pop("line_ids", None)
            
            return {
                "success": True, 
                "result": {
                    "count": len(entries),
                    "total_count": total_count,
                    "entries": entries
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @mcp.tool(description="Create a new accounting entry")
    def create_journal_entry(
        ctx: Context,
        entry: JournalEntryCreate
    ) -> Dict[str, Any]:
        """
        Create a new accounting entry
        
        Args:
            entry: Details of the entry to be created
            
        Returns:
            Response with the result of the operation
        """
        odoo = ctx.request_context.lifespan_context.odoo
        
        try:
            # Verify that the debit and credit are balanced
            total_debit = sum(line.debit for line in entry.lines)
            total_credit = sum(line.credit for line in entry.lines)
            
            if round(total_debit, 2) != round(total_credit, 2):
                return {
                    "success": False, 
                    "error": f"The entry is not balanced. Debit: {total_debit}, Credit: {total_credit}"
                }
            
            # Prepare values for the entry
            move_vals = {
                "journal_id": entry.journal_id,
                "line_ids": []
            }
            
            if entry.ref:
                move_vals["ref"] = entry.ref
                
            if entry.date:
                try:
                    datetime.strptime(entry.date, "%Y-%m-%d")
                    move_vals["date"] = entry.date
                except ValueError:
                    return {"success": False, "error": f"Invalid date format: {entry.date}. Use YYYY-MM-DD."}
            
            # Prepare entry lines
            for line in entry.lines:
                line_vals = [
                    0, 0, {
                        "account_id": line.account_id,
                        "name": line.name or "/",
                        "debit": line.debit,
                        "credit": line.credit
                    }
                ]
                
                if line.partner_id:
                    line_vals[2]["partner_id"] = line.partner_id
                    
                move_vals["line_ids"].append(line_vals)
            
            # Create entry
            move_id = odoo.execute_method("account.move", "create", move_vals)
            
            # Get information from the created entry
            move_info = odoo.execute_method("account.move", "read", [move_id], ["name", "state"])[0]
            
            return {
                "success": True,
                "result": {
                    "move_id": move_id,
                    "name": move_info["name"],
                    "state": move_info["state"]
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @mcp.tool(description="Calculate key financial ratios")
    def analyze_financial_ratios(
        ctx: Context,
        params: FinancialRatioInput
    ) -> Dict[str, Any]:
        """
        Calculate key financial ratios for a specific period
        
        Args:
            params: Parameters for the analysis
            
        Returns:
            Dictionary with the calculated ratios
        """
        odoo = ctx.request_context.lifespan_context.odoo
        
        try:
            # Validate dates
            try:
                datetime.strptime(params.date_from, "%Y-%m-%d")
                datetime.strptime(params.date_to, "%Y-%m-%d")
            except ValueError:
                return {"success": False, "error": "Invalid date format. Use YYYY-MM-DD."}
            
            # Check which ratios are requested
            requested_ratios = params.ratios
            
            # Initialize result
            ratios = {}
            
            # Get data from the balance sheet
            # Assets
            assets_domain = [
                ("account_id.user_type_id.internal_group", "=", "asset"),
                ("date", ">=", params.date_from),
                ("date", "<=", params.date_to),
                ("parent_state", "=", "posted")
            ]
            
            assets_data = odoo.search_read(
                "account.move.line",
                assets_domain,
                fields=["account_id", "balance"]
            )
            
            total_assets = sum(line["balance"] for line in assets_data)
            
            # Current assets
            current_assets_domain = [
                ("account_id.user_type_id.internal_group", "=", "asset"),
                ("account_id.user_type_id.type", "=", "liquidity"),
                ("date", ">=", params.date_from),
                ("date", "<=", params.date_to),
                ("parent_state", "=", "posted")
            ]
            
            current_assets_data = odoo.search_read(
                "account.move.line",
                current_assets_domain,
                fields=["account_id", "balance"]
            )
            
            current_assets = sum(line["balance"] for line in current_assets_data)
            
            # Liabilities
            liabilities_domain = [
                ("account_id.user_type_id.internal_group", "=", "liability"),
                ("date", ">=", params.date_from),
                ("date", "<=", params.date_to),
                ("parent_state", "=", "posted")
            ]
            
            liabilities_data = odoo.search_read(
                "account.move.line",
                liabilities_domain,
                fields=["account_id", "balance"]
            )
            
            total_liabilities = sum(line["balance"] for line in liabilities_data)
            
            # Current liabilities
            current_liabilities_domain = [
                ("account_id.user_type_id.internal_group", "=", "liability"),
                ("account_id.user_type_id.type", "=", "payable"),
                ("date", ">=", params.date_from),
                ("date", "<=", params.date_to),
                ("parent_state", "=", "posted")
            ]
            
            current_liabilities_data = odoo.search_read(
                "account.move.line",
                current_liabilities_domain,
                fields=["account_id", "balance"]
            )
            
            current_liabilities = sum(line["balance"] for line in current_liabilities_data)
            
            # Equity
            equity_domain = [
                ("account_id.user_type_id.internal_group", "=", "equity"),
                ("date", ">=", params.date_from),
                ("date", "<=", params.date_to),
                ("parent_state", "=", "posted")
            ]
            
            equity_data = odoo.search_read(
                "account.move.line",
                equity_domain,
                fields=["account_id", "balance"]
            )
            
            total_equity = sum(line["balance"] for line in equity_data)
            
            # Income
            income_domain = [
                ("account_id.user_type_id.internal_group", "=", "income"),
                ("date", ">=", params.date_from),
                ("date", "<=", params.date_to),
                ("parent_state", "=", "posted")
            ]
            
            income_data = odoo.search_read(
                "account.move.line",
                income_domain,
                fields=["account_id", "balance"]
            )
            
            total_income = sum(line["balance"] for line in income_data)
            
            # Expenses
            expense_domain = [
                ("account_id.user_type_id.internal_group", "=", "expense"),
                ("date", ">=", params.date_from),
                ("date", "<=", params.date_to),
                ("parent_state", "=", "posted")
            ]
            
            expense_data = odoo.search_read(
                "account.move.line",
                expense_domain,
                fields=["account_id", "balance"]
            )
            
            total_expenses = sum(line["balance"] for line in expense_data)
            
            # Calculate net income
            net_income = total_income - total_expenses
            
            # Calculate requested ratios
            if "liquidity" in requested_ratios:
                # Current liquidity ratio
                current_ratio = 0
                if current_liabilities != 0:
                    current_ratio = current_assets / abs(current_liabilities)
                
                ratios["liquidity"] = {
                    "current_ratio": current_ratio,
                    "current_assets": current_assets,
                    "current_liabilities": abs(current_liabilities)
                }
            
            if "profitability" in requested_ratios:
                # Return on assets (ROA)
                roa = 0
                if total_assets != 0:
                    roa = (net_income / total_assets) * 100
                
                # Return on equity (ROE)
                roe = 0
                if total_equity != 0:
                    roe = (net_income / total_equity) * 100
                
                # Net profit margin
                profit_margin = 0
                if total_income != 0:
                    profit_margin = (net_income / total_income) * 100
                
                ratios["profitability"] = {
                    "return_on_assets": roa,
                    "return_on_equity": roe,
                    "net_profit_margin": profit_margin,
                    "net_income": net_income,
                    "total_income": total_income
                }
            
            if "debt" in requested_ratios:
                # Debt ratio
                debt_ratio = 0
                if total_assets != 0:
                    debt_ratio = (abs(total_liabilities) / total_assets) * 100
                
                # Leverage ratio
                leverage_ratio = 0
                if total_equity != 0:
                    leverage_ratio = (abs(total_liabilities) / total_equity)
                
                ratios["debt"] = {
                    "debt_ratio": debt_ratio,
                    "leverage_ratio": leverage_ratio,
                    "total_liabilities": abs(total_liabilities),
                    "total_equity": total_equity
                }
            
            if "efficiency" in requested_ratios:
                # Asset turnover
                asset_turnover = 0
                if total_assets != 0:
                    asset_turnover = total_income / total_assets
                
                ratios["efficiency"] = {
                    "asset_turnover": asset_turnover
                }
            
            # Prepare result
            result = {
                "period": {
                    "from": params.date_from,
                    "to": params.date_to
                },
                "summary": {
                    "total_assets": total_assets,
                    "total_liabilities": abs(total_liabilities),
                    "total_equity": total_equity,
                    "total_income": total_income,
                    "total_expenses": abs(total_expenses),
                    "net_income": net_income
                },
                "ratios": ratios
            }
            
            return {"success": True, "result": result}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
