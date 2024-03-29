# -*- coding: utf-8 -*-
import json
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CustomSaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    x_shopify_id = fields.Char('Shopify ID')
    
    x_child_order_count = fields.Integer('Child Orders', compute="_compute_child_count")

    @api.depends('name')
    def _compute_child_count(self):
        for record in self:
            record.x_child_order_count = len(
                self.env['sale.order'].search([('x_studio_related_sales_order', '=', record.id)]))
    
    def action_view_child_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _(str(self.name) + ' - Child Orders'),
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('x_studio_related_sales_order', '=', self.id)],
            'context': dict(self._context, create=False)
        }
    
    def action_confirm(self):
        if self.x_studio_shipping_type in ['Individual', 'Bulk - Parent'] and not self.x_studio_related_sales_order:
            self.state = 'sale'
        else:
            res = super(CustomSaleOrder, self).action_confirm()
            
            try:
                for line in self.order_line:
                    if not line.route_id and line.product_id.type == 'product':
                        raise Exception('Please set the route for product: ' + str(line.product_id.default_code) + '.')
            except Exception as e:
                raise ValidationError(e)

            return res
    
    def action_cancel_bulk(self):
        for order in self:
            order.with_context({'disable_cancel_warning': True}).action_cancel()

    def create_shopify_order(self,order, shop_name):
        COUNTRY = self.env['res.country']
        STATE = self.env['res.country.state']
        PRODUCT = self.env['product.product']
        PARTNER = self.env['res.partner']
        SALE = self.env['sale.order']
        SHOPIFY_LOG = self.env['shopify.log']
        
        shop = self.env['shopify.shop'].sudo().search([('shop_id', 'ilike', shop_name)],limit=1)
        parent_so = shop.parent_sales_order
        
        order_lines = []
        partner_payload = {}
        bulk_partner = False
        
        try:
            if parent_so.x_studio_shipping_type not in ['Bulk - Parent']:                
                shipping_details = order.get('shipping_address')
                if not shipping_details:
                    raise Exception('No shipping address was entered for this order in Shopify. Should the parent order be configured to be a bulk order?')
            
                country_id = COUNTRY.search([('code', 'ilike', shipping_details.get('country_code'))],limit=1)
                if not len(country_id):
                    raise Exception('Could not find the selected country for this order in Odoo.')

                state_id = STATE.search([('code', 'ilike', shipping_details.get('province_code')), ('country_id', '=', country_id.id),('create_uid', '=', 1)],limit=1)
                if not len(state_id):
                    raise Exception('Could not find the selected state for this order in Odoo.')
            
                partner_payload = {
                    "name": str(shipping_details.get('first_name') + ' ' + shipping_details.get('last_name')).strip(),
                    "street": shipping_details.get('address1'),
                    "street2": shipping_details.get('address2'),
                    "city": shipping_details.get('city'),
                    "zip": shipping_details.get('zip'),
                    "country_id": country_id.id,
                    "state_id": state_id.id,
                    "phone": 14692942500,
                    "type": "delivery",
                    "property_account_receivable_id": 2,
                    "property_account_payable_id": 1,
                    "parent_id": parent_so.partner_id.id
                }

                try:
                    partner = PARTNER.create(partner_payload)
                except Exception as e:
                    raise Exception('There was an error creating the partner for this order in Odoo.\n ' + str(e))

            else:
                shipping_lines = order.get('shipping_lines')
                if not len(shipping_lines):
                      raise Exception('No Shipping Configuration found for this bulk order.')  
                
                for shipping_line in shipping_lines:
                    for shop_coupons in shop.coupons:
                        if str(shop_coupons.code_prefix).lower() in str(shipping_line.get('code')).lower():
                            bulk_partner = shop_coupons.partner_id
                
                if not bulk_partner:
                    raise Exception('Could not find a matching partner for the specified Shopify shipping selection.')

                
                customer_details = order.get('customer')
                if not customer_details:
                    raise Exception('No customer details found for this order in Shopify.')
                
                partner_payload = {
                    "name": str(customer_details.get('first_name') + ' ' + customer_details.get('last_name')).strip(),
                    "street": bulk_partner.street,
                    "street2": bulk_partner.street2,
                    "city": bulk_partner.city,
                    "zip": bulk_partner.zip,
                    "country_id": bulk_partner.country_id.id,
                    "state_id": bulk_partner.state_id.id,
                    "phone": bulk_partner.phone,
                    "type": "delivery",
                    "property_account_receivable_id": 2,
                    "property_account_payable_id": 1,
                    "parent_id": bulk_partner.id
                }

                try:
                    partner = PARTNER.create(partner_payload)
                except Exception as e:
                    raise Exception('There was an error creating the partner for this order in Odoo.\n ' + str(e))

            product_details = order.get('line_items')
            if not product_details:
                raise Exception('No products were entered for this order in Shopify.')

            for product in product_details:
                shopify_sku = str(product.get('sku')).strip()
                qty = product.get('quantity')
                customizations = product.get('properties')
                initial_customization = ""
                logo_customization = ""
                logo_name_customization = ""
                logo_initials_customization = ""
                first_and_name_customization = ""
                full_name_customization = ""
                
                try:
                    for customization in customizations:
                        customization_key = str(customization.get('name')).lower().strip()
                        if customization_key == 'initials':
                            initial_customization = customization.get('value')
                        elif customization_key == 'logo':
                            logo_customization = customization.get('value')
                        elif customization_key == 'logo and name':
                            logo_name_customization = customization.get('value')
                        elif customization_key == 'logo and initials':
                            logo_initials_customization = customization.get('value')
                        elif customization_key == 'first letter and name' or customization_key == 'first letter and last name' or customization_key == 'last name':
                            first_and_name_customization = customization.get('value')
                        elif customization_key == 'name' or customization_key == 'full name':
                            full_name_customization = customization.get('value')
                except Exception as e:
                    raise Exception('There was an error with the customization details: \n' + str(e))
                
                for sku in shopify_sku.split('|'):
                    customization_detail = None
                    customization_notes = ""
                    route = None
                    
                    try:
                        if sku.endswith('-I'):
                            customization_detail = "Initial"
                            customization_notes = initial_customization
                            sku = sku.split('-I')[0]
                        elif sku.endswith('-L'):
                            customization_detail = "Logo"
                            customization_notes = logo_customization
                            sku = sku.split('-L')[0]
                        elif sku.endswith('-LN'):
                            customization_detail = "Logo and Name"
                            customization_notes  = logo_name_customization
                            sku = sku.split('-LN')[0]
                        elif sku.endswith('-LI'):
                            customization_detail = "Logo and Initials"
                            customization_notes  = logo_initials_customization
                            sku = sku.split('-LI')[0]
                        elif sku.endswith('-M'):
                            customization_detail = "First Letter and Name"
                            customization_notes  = first_and_name_customization
                            sku = sku.split('-M')[0]
                        elif sku.endswith('-N'):
                            customization_detail = "Full Name"
                            customization_notes = full_name_customization
                            sku = sku.split('-N')[0]


                    except Exception as e:
                        raise Exception('There was an error with the customization details: \n' + str(e))
                        
                    if customization_detail == None:
                        route = 11
                    product_id = PRODUCT.search([('default_code', '=', sku), ('active', '=', True)], limit=1)

                    if not len(product_id):
                        raise Exception('Could not find the SKU "' + sku + '" in Odoo.')

                    if len(product_id) > 1:
                        raise Exception('Found multiple matches for the SKU "' + sku + '" in Odoo.')
                    
                    if not route:
                        found_routes = product_id.get_route()
                        if len(found_routes) == 1:
                            route = found_routes[0]
                        else:
                            route = None

                    order_lines.append((0, 0, {
                        "product_id": product_id.id,
                        "name": product_id.name,
                        "x_studio_customization_detail": customization_detail,
                        "x_studio_customization_notes": customization_notes,
                        "price_unit": 0,
                        "tax_id": None,
                        "product_uom_qty": qty,
                        "route_id": route
                    }))
            
            order_partner = partner.id
            carrier_id = parent_so.carrier_id and parent_so.carrier_id.id or None
            if bulk_partner:
                order_partner = bulk_partner.id
                carrier_id = None
            
            order_payload = {
                "company_id": 1,
                "warehouse_id": 1,
                "pricelist_id": 1,
                "picking_policy": 'one',
                "x_shopify_id": order.get('id'),
                "partner_invoice_id": parent_so.partner_id and parent_so.partner_id.id or None,
                "partner_shipping_id": partner.id,
                "partner_id": order_partner,
                "date_order": parent_so.date_order,
                "team_id": parent_so.team_id and parent_so.team_id.id or None,
                "carrier_id":  carrier_id,
                "commitment_date": parent_so.commitment_date,
                "x_studio_google_drive_link": parent_so.x_studio_google_drive_link,
                "x_studio_kitting": parent_so.x_studio_kitting,
                "x_studio_letter_content_1": parent_so.x_studio_letter_content_1,
                "x_studio_related_sales_order": parent_so.id,
                "x_studio_shipping_type": parent_so.x_studio_shipping_type,
                "x_studio_text_field_JLki5": parent_so.x_studio_text_field_JLki5,
                "x_studio_type_of_order": parent_so.x_studio_type_of_order,
                "x_studio_in_hand_date_flexibility": parent_so.x_studio_in_hand_date_flexibility,
                "order_line": order_lines,
            }

            try:
                created_order = SALE.create(order_payload)
            except Exception as e:
                raise Exception('There was an error creating the sale order in Odoo\n ' + str(e))

            try:
                for line in created_order.order_line:
                    found_match = False
                    for parent_line in parent_so.order_line.filtered(lambda x: x.product_id.id == line.product_id.id):
                        found_match = True
                        parent_line.product_uom_qty = parent_line.product_uom_qty + line.product_uom_qty
                    if not found_match:
                        self.env['sale.order.line'].create(
                            {
                                "order_id": parent_so.id,
                                "product_id": line.product_id.id,
                                "name": line.product_id.name,
                                "price_unit": 0,
                                "tax_id": None,
                                "product_uom_qty": line.product_uom_qty,
                                "sequence": 1000
                            }
                        )
    
            except Exception as e:
                raise Exception('There was an error updating the parent\'s sale order quantites for this order in Odoo\n ' + str(e))
        
            SHOPIFY_LOG.create(
                {
                    "order_id": order.get('id'),
                    "shop": shop.id,
                    "sale_id": None,
                    "error": None,
                    "body": order,
                    "res": None,
                    "success": True
                }
            )

        except Exception as e:
            _logger.error(e)
            SHOPIFY_LOG.create(
                {
                    "order_id": order.get('id') or None,
                    "shop": shop.id or None,
                    "sale_id": None,
                    "error": e,
                    "body": order,
                    "res": None
                }
            )

    def confirm_shopify_orders(self):
        orders = self.search([('x_shopify_id', '!=', False), ('state', 'not in', ['cancel', 'sale', 'done'])])

        for order in orders:
            try:
                _logger.debug('\n%s', order.name)
                order.action_confirm()
            except Exception as e:
                order.env.cr.rollback()
                _logger.error('%s - %s', order.name, str(e))
                pass
            else:
                self.env.cr.commit()

    @api.model
    def create(self, vals):
        res = super(CustomSaleOrder, self).create(vals)
        if res.x_studio_related_sales_order:
            for line in res.x_studio_related_sales_order.order_line:
                already_exists = False
                if line.x_auto_add_to_child:
                    sale_order_line = {
                        "sequence": 0,
                        "product_id": line.product_id.id,
                        "order_id": res.id,
                        "name": line.name,
                        "x_studio_customization_detail": line.x_studio_customization_detail,
                        "x_studio_customization_notes": line.x_studio_customization_notes,
                        "route_id": line.route_id.id,
                        "price_unit": line.price_unit,
                        'tax_id':line.tax_id.id,
                    }
                    for created_line in res.order_line:
                        if created_line.product_id.id == line.product_id.id:
                            already_exists = True
                    
                    if not already_exists:
                        self.env['sale.order.line'].create(sale_order_line)
        return res

    def mark_parent_shipped(self):
        shipped_tags = self.env['crm.tag'].search([
            '|','|',
            ('name', '=', 'shipped'),
            ('name', '=', 'Shipped'),
            ('name', '=', 'Rolling Fulfillment')
        ])

        ship_tag = shipped_tags.filtered(lambda x: x.id == 15)
        if not ship_tag:
            return
        
        parent_orders = self.env['sale.order'].search([
            ('x_studio_related_sales_order', '=', False),
            ('picking_ids', '=', False),
            ('tag_ids', 'not in', shipped_tags.ids),
        ])
        
        for parent_order in parent_orders:
            try:
                not_completed_child_orders = self.env['stock.picking'].search([
                    ('sale_id.x_studio_related_sales_order', '=', parent_order.id),
                    ('picking_type_id', '=', 2),
                    ('state', 'not in', ['done', 'cancel'])
                ])

                completed_child_orders = self.env['stock.picking'].search([
                    ('sale_id.x_studio_related_sales_order', '=', parent_order.id),
                    ('picking_type_id', '=', 2),
                    ('state', '=', 'done')
                ])

                if len(not_completed_child_orders) > 0 or len(completed_child_orders) == 0:
                    continue
                else:
                    parent_order.tag_ids = [(4, ship_tag.id, None)]
                    self.env.cr.commit()
            except:
                pass
       
class CustomSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_auto_add_to_child = fields.Boolean(
        string='Auto-Add',
        default=False,
        help="If this is selected all related orders will automatically get this product added when created."
    )

    x_in_hand_date = fields.Datetime(
        string='In Hand Date',
        compute='_compute_in_hand',
        store=True,
        index=True
    )

    create_date = fields.Datetime(
        index=True
    )

    product_id = fields.Many2one(
        index=True
    )

    order_partner_id = fields.Many2one(
        index=True
    )

    route_id = fields.Many2one(
        index=True
    )

    @api.depends('order_id')
    def _compute_in_hand(self):
        for record in self:
            record.x_in_hand_date = record.order_id.commitment_date

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        try:
            if self.order_id.x_studio_shipping_type in ['Individual', 'Bulk - Parent'] and not self.order_id.x_studio_related_sales_order:
                return
        except:
            pass

        return super(CustomSaleOrderLine, self)._action_launch_stock_rule(previous_product_uom_qty)