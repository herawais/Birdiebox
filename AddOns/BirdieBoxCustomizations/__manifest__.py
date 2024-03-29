# -*- coding: utf-8 -*-
{
    'name':
    "BirdieBox Customizations",
    'summary':
    """Odoo customizations from Bohm Technologies for BirdieBox""",
    'description':
    """
		Bohm Technologies Customizations
	""",
    'author':
    "Bohm Technologies - Cre Moore",
    'website':
    "https://www.bohmtechnologies.com",
    'category':
    'Uncategorized',
    'version':
    '1.0',
    'depends': ['repair', 'base', 'sale', 'delivery'],
    'data': [
        'security/ir.model.access.csv', 'views/bulk_sale.xml',
        'wizards/bulk_sale_create_wizard.xml',
        'views/report_stock_forecasted.xml',
        'views/stock_picking_type_form.xml',
        'views/printers.xml',
        'views/res_users_menu.xml',
        'views/shopify.xml',
        'views/sale_order.xml',
        'wizards/bulk_product_add_wizard.xml',
        'wizards/bulk_product_swap_wizard.xml'
    ],
    'application':
    True,
}
