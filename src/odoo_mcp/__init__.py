"""
Update of the __init__.py file to include all modules
"""

from . import odoo_client
from . import server
from . import models
from . import prompts
from . import tools_sales
from . import tools_purchase
from . import tools_inventory
from . import tools_accountings
from . import resources
from . import extensions

__all__ = [
    'odoo_client',
    'server',
    'models',
    'prompts',
    'tools_sales',
    'tools_purchase',
    'tools_inventory',
    'tools_accountings',
    'resources',
    'extensions'
]
