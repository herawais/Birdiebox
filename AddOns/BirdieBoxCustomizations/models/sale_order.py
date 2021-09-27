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
    
    def action_confirm(self):
        if self.x_studio_shipping_type in ['Individual', 'Bulk Freight and Individual', 'Bulk Ground and Individual'] and not self.x_studio_related_sales_order:
            self.state = 'sale'
        else:
            return super(CustomSaleOrder, self).action_confirm()

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
        
        try:
            shipping_details = order.get('shipping_address')
            if not shipping_details:
                raise Exception('No shipping address was entered for this order in Shopify.')
            
            product_details = order.get('line_items')
            if not product_details:
                raise Exception('No products were entered for this order in Shopify.')
            
            country_id = COUNTRY.search([('code', 'ilike', shipping_details.get('country_code'))],limit=1)
            if not len(country_id):
                raise Exception('Could not find the selected country for this order in Odoo.')

            state_id = STATE.search([('code', 'ilike', shipping_details.get('province_code')), ('country_id', '=', country_id.id)],limit=1)
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
                "phone": shipping_details.get('phone'),
                "type": "delivery",
                "property_account_receivable_id": 2,
                "property_account_payable_id": 1,
                "parent_id": parent_so.partner_id.id
            }

            try:
                partner = PARTNER.create(partner_payload)
            except Exception as e:
                raise Exception('There was an error creating the partner for this order in Odoo.\n ' + str(e))

            for product in product_details:
                shopify_sku = str(product.get('sku'))
                qty = product.get('quantity')
                customizations = product.get('properties')
                initial_customization = ""
                logo_customization = ""
                logo_name_customization = ""
                logo_initials_customzation = ""
                
                try:
                    for customization in customizations:
                        customization_key = str(customization.get('name')).lower()
                        if customization_key == 'initials':
                            initial_customization = customization.get('value')
                        elif customization_key == 'logo':
                            logo_customization = customization.get('value')
                        elif customization_key == 'logo and name':
                            logo_name_customization = customization.get('value')
                        elif customization_key == 'logo and initials':
                            logo_initials_customzation = customization.get('value')
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
                            customization_notes  = logo_initials_customzation
                            sku = sku.split('-LI')[0]
                    except Exception as e:
                        raise Exception('There was an error with the customization details: \n' + str(e))
                        
                    if customization_detail == None:
                        route = 11
                    product_id = PRODUCT.search([('default_code', '=', sku), ('active', '=', True)], limit=1)

                    if not len(product_id):
                        raise Exception('Could not find the SKU "' + sku + '" in Odoo.')

                    if len(product_id) > 1:
                        raise Exception('Found multiple matches for the SKU "' + sku + '" in Odoo.')
                    
                    order_lines.append((0, 0, {
                        "product_id": product_id.id,
                        "name": product_id.name,
                        "x_studio_customization_detail": customization_detail,
                        "x_studio_customization_notes": customization_notes,
                        "price_unit": 0,
                        "tax_id": None,
                        "route_id": route,
                        "product_uom_qty": qty
                    }))
            
            order_payload = {
                "company_id": 1,
                "warehouse_id": 1,
                "pricelist_id": 1,
                "picking_policy": 'one',
                "x_shopify_id": order.get('id'),
                "partner_invoice_id": parent_so.partner_id and parent_so.partner_id.id or None,
                "partner_shipping_id": partner.id,
                "partner_id": partner.id,
                "date_order": parent_so.date_order,
                "team_id": parent_so.team_id and parent_so.team_id.id or None,
                "carrier_id":  parent_so.carrier_id and parent_so.carrier_id.id or None,
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

    def confirm_shopify_orders(self):
        orders = self.search([('x_shopify_id', '!=', False), ('state', 'not in', ['cancel', 'sale', 'done'])])

        for order in orders:
            order.action_confirm()
            self.env.cr.commit()

class CustomSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        try:
            if self.order_id.x_studio_shipping_type in ['Individual', 'Bulk Freight and Individual', 'Bulk Ground and Individual'] and not self.order_id.x_studio_related_sales_order:
                return
        except:
            pass

        return super(CustomSaleOrderLine, self)._action_launch_stock_rule(previous_product_uom_qty)