# Improved MCP-Odoo Documentation

## Introduction

This document describes the improvements implemented in the MCP (Model Context Protocol) for Odoo, which significantly extends the capabilities of the original repository by adding new tools, resources, and prompts for sales, purchasing, inventory, and accounting areas.

The goal of these improvements is to provide a more complete and functional integration between Odoo ERP and language models like Claude, allowing for richer and more useful interactions in business contexts.

## Architecture

The architecture of the improved MCP-Odoo follows a modular design that facilitates extension and maintenance:

```
mcp-odoo/
├── src/
│   └── odoo_mcp/
│       ├── __init__.py           # Package initialization
│       ├── server.py             # Main MCP server
│       ├── odoo_client.py        # Client for Odoo connection
│       ├── models.py             # Pydantic models for validation
│       ├── extensions.py         # Centralized extension registration
│       ├── prompts.py            # Prompts for analysis and assistance
│       ├── resources.py          # MCP resources (URIs)
│       ├── tools_sales.py        # Tools for sales
│       ├── tools_purchase.py     # Tools for purchasing
│       ├── tools_inventory.py    # Tools for inventory
│       └── tools_accountings.py  # Tools for accounting
├── pyproject.toml               # Package configuration
├── Dockerfile                   # Configuration for Docker
└── validation.py               # Validation script
```

## New Features

### 1. Tools

Tools allow language models to perform specific actions in Odoo:

#### Sales
- `search_sales_orders`: Searches for sales orders with advanced filters
- `create_sales_order`: Creates a new sales order
- `analyze_sales_performance`: Analyzes sales performance by period, product, or customer
- `get_customer_insights`: Gets detailed information about a specific customer

#### Purchases
- `search_purchase_orders`: Searches for purchase orders with advanced filters
- `create_purchase_order`: Creates a new purchase order
- `analyze_supplier_performance`: Analyzes supplier performance

#### Inventory
- `check_product_availability`: Checks stock availability for products
- `create_inventory_adjustment`: Creates an inventory adjustment
- `analyze_inventory_turnover`: Calculates and analyzes inventory turnover

#### Accounting
- `search_journal_entries`: Searches for journal entries with filters
- `create_journal_entry`: Creates a new journal entry
- `analyze_financial_ratios`: Calculates key financial ratios

### 2. Resources

Resources provide access to Odoo data via URIs:

#### Sales
- `odoo://sales/orders`: Lists sales orders
- `odoo://sales/order/{order_id}`: Gets details of a specific order
- `odoo://sales/products`: Lists sellable products
- `odoo://sales/customers`: Lists customers

#### Purchases
- `odoo://purchase/orders`: Lists purchase orders
- `odoo://purchase/order/{order_id}`: Gets details of a specific order
- `odoo://purchase/suppliers`: Lists suppliers

#### Inventory
- `odoo://inventory/products`: Lists products in inventory
- `odoo://inventory/stock/{location_id}`: Gets stock levels in a location
- `odoo://inventory/movements`: Lists inventory movements

#### Accounting
- `odoo://accounting/accounts`: Lists accounting accounts
- `odoo://accounting/journal_entries`: Lists journal entries
- `odoo://accounting/reports/{report_type}`: Gets financial reports

### 3. Prompts

Specialized prompts have been added for different areas:

- **Sales analysis**: Prompts for analyzing trends, performance, and opportunities
- **Inventory management**: Prompts for stock optimization and planning
- **Human resources planning**: Prompts for personnel and schedule management
- **Financial analysis**: Prompts for interpreting accounting and financial data

## Usage Guide

### Installation

#### Option 1: Using the Python package

```bash
# Clone the repository
git clone https://github.com/tuanle96/mcp-odoo.git
cd mcp-odoo

# Install the package
pip install -e .

# Run as a module
python -m src.odoo_mcp
```

#### Option 2: Using Docker

```bash
# Build the image
docker build -t mcp/odoo:latest -f Dockerfile .

# Run the container
docker run -i --rm \
  -e ODOO_URL=https://your-odoo-instance.com \
  -e ODOO_DB=your-database-name \
  -e ODOO_USERNAME=your-username \
  -e ODOO_PASSWORD=your-password \
  mcp/odoo
```

### Configuration

MCP-Odoo can be configured using environment variables or a configuration file:

#### Environment variables

```bash
export ODOO_URL=https://your-odoo-instance.com
export ODOO_DB=your-database-name
export ODOO_USERNAME=your-username
export ODOO_PASSWORD=your-password
```

#### Configuration file

Create a `odoo_config.json` file in the working directory:

```json
{
  "url": "https://your-odoo-instance.com",
  "db": "your-database-name",
  "username": "your-username",
  "password": "your-password"
}
```

### Integration with Claude Desktop

To use MCP-Odoo with Claude Desktop, add the following configuration to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "python",
      "args": ["-m", "src.odoo_mcp"],
      "env": {
        "ODOO_URL": "https://your-odoo-instance.com",
        "ODOO_DB": "your-database-name",
        "ODOO_USERNAME": "your-username",
        "ODOO_PASSWORD": "your-password"
      }
    }
  }
}
```

To use the Docker version:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e", "ODOO_URL",
        "-e", "ODOO_DB",
        "-e", "ODOO_USERNAME",
        "-e", "ODOO_PASSWORD",
        "mcp/odoo"
      ],
      "env": {
        "ODOO_URL": "https://your-odoo-instance.com",
        "ODOO_DB": "your-database-name",
        "ODOO_USERNAME": "your-username",
        "ODOO_PASSWORD": "your-password"
      }
    }
  }
}
```

## Usage Examples

### Example 1: Sales analysis

```
Using the Odoo MCP, analyze sales from the last quarter and show the best-selling products.
```

### Example 2: Inventory check

```
Check the stock availability for products X, Y, and Z in the main warehouse.
```

### Example 3: Financial analysis

```
Calculate the liquidity and profitability ratios for the current fiscal year and compare them with the previous year.
```

### Example 4: Creating purchase orders

```
Create a purchase order for supplier ABC with the following products: 10 units of product X and 5 units of product Y.
```

## System Extension

The system is designed to be easily extensible. To add new functionalities:

1. **New tools**: Create a new `tools_*.py` file following the existing pattern
2. **New resources**: Add new resources in `resources.py`
3. **New prompts**: Add new prompts in `prompts.py`
4. **Extension registration**: Update `extensions.py` to register the new functionalities

## Troubleshooting

### Connection problems

If you experience connection problems with Odoo:

1. Verify the credentials in the environment variables or configuration file
2. Make sure the Odoo URL is accessible from where you run the MCP
3. Verify that the user has sufficient permissions in Odoo

### Errors in tools

If a tool returns an error:

1. Review the provided parameters
2. Verify that the record IDs exist in Odoo
3. Check the user's permissions for the specific operation

## Validation

A validation script (`validation.py`) is included that can be run to verify that all functionalities are correctly implemented and compatible with your Odoo instance:

```bash
python validation.py
```

## Contribution

Contributions are welcome. To contribute:

1. Fork the repository
2. Create a branch for your feature (`git checkout -b feature/new-feature`)
3. Make your changes and add tests
4. Submit a pull request

## License

This project is distributed under the same license as the original repository.
