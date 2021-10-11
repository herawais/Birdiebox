{
    'name': 'Odoo SalesForce Connector',
    'author': 'Pragmatic TechSoft Pvt Ltd.',
    'version': '14.0.25',
    'website': 'http://www.pragtech.co.in',
    'summary': '2 way SalesForce connector Odoo SalesForce Connector odoo salesforce integration crm app',
    'depends': ['sale_management', 'product', 'crm'],
    'description': '''
2-way SalesForce Connector for Odoo
===================================
<keywords>    
Odoo SalesForce Connector
salesforce
salesforce connector
odoo salesforce integration
crm app    
''',
    'data': [
        'data/crm_stage.xml',
        'security/ir.model.access.csv',
        'wizards/message_view.xml',
        'views/res_company_view.xml',
        'views/res_partner_view.xml',
        'views/product_templ.xml',
        'views/crm_lead_view.xml',
        'views/opportunity_view.xml',
        'views/schedulers.xml',
        'views/contract_view.xml',
        'views/event_view.xml',
        'views/mail_activity_view.xml',
        'views/sale_order_view.xml',
        'views/sf_logging_views.xml'
    ],
    'images': ['static/description/animated-salesforce-connector.gif'],
    'live_test_url': 'http://www.pragtech.co.in/company/proposal-form.html?id=103&name=Odoo-Salesforce-Connector',
    'currency': 'USD',
    'license': 'OPL-1',
    'price': 450.00,
    'installable': True,
    'application': True,
    'auto_install': False,
}
