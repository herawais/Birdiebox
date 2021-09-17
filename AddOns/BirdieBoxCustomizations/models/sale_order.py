# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CustomSaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    def action_confirm(self):
        if self.x_studio_shipping_type in ['Individual', 'Bulk Freight and Individual', 'Bulk Ground and Individual'] and not self.x_studio_related_sales_order:
            self.state = 'sale'
        else:
            return super(CustomSaleOrder, self).action_confirm()

    def create_api_order(self, formatted_args):
        PARTNER = self.env['res.partner']
        SALE = self.env['sale.order']


        _logger.debug('\n\n\n Creating API Order,')


    def shopify_order(self,args):
        COUNTRY = self.env['res.country']
        STATE = self.env['res.country.state']
        PRODUCT = self.env['product.product']
        payloads = []
        orders = args.get('orders')
        for order in orders:
            shipping_details = order.get('shipping_address')
            product_details = order.get('line_items')
            order_lines = []
            partner_payload = {}
            order_payload = {}
            
            partner_payload = {
                "name": str(shipping_details.get('first_name') + ' ' + shipping_details.get('last_name')).strip(),
                "street": shipping_details.get('address1'),
                "street2": shipping_details.get('address2'),
                "city": shipping_details.get('city'),
                "zip": shipping_details.get('zip'),
                "country_id": COUNTRY.search([('code', 'ilike', shipping_details.get('country_code'))],limit=1).id,
                "state_id": STATE.search([('code', 'ilike', shipping_details.get('province_code'))],limit=1).id,
                # "email": self.email,
                "phone": shipping_details.get('phone'),
                "type": "contact",
                "property_account_receivable_id": 2,
                "property_account_payable_id": 1
            }

            for product in product_details:
                sku = product.get('sku')
                qty = product.get('quantity')
                customizations = product.get('properties')
                product_id = PRODUCT.search([('default_code', '=', sku)], limit=1)
                
                order_lines.append((0, 0, {
                    "product_id": product_id.id,
                    "name": product_id.name,
                    "x_studio_customization_detail": "",
                    "x_studio_customization_notes": "",
                    "price_unit": 0,
                    "tax_id": None,
                    "product_uom_qty": qty
                }))

                
                
            order_payload = {
                "company_id": 1,
                "warehouse_id": 1,
                "pricelist_id": 1,
                "picking_policy": 'one',
                # "partner_invoice_id": so.partner_id.id,
                # "partner_shipping_id": partner.id,
                # "partner_id": partner.id,
                # "date_order": so.date_order,
                # "team_id": so.team_id.id,
                # "carrier_id": so.carrier_id.id,
                # "commitment_date": so.commitment_date,
                # "x_studio_google_drive_link": so.x_studio_google_drive_link,
                # "x_studio_kitting": so.x_studio_kitting,
                # "x_studio_letter_content_1": so.x_studio_letter_content_1,
                # "x_studio_related_sales_order": so.id,
                # "x_studio_shipping_type": so.x_studio_shipping_type,
                # "x_studio_text_field_JLki5": so.x_studio_text_field_JLki5,
                # "x_studio_type_of_order": so.x_studio_type_of_order,
                # "x_studio_in_hand_date_flexibility": so.x_studio_in_hand_date_flexibility,
                "order_line": order_lines
            }


                

            _logger.debug('\n\n\n %s', order_payload)

class CustomSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        try:
            if self.order_id.x_studio_shipping_type in ['Individual', 'Bulk Freight and Individual', 'Bulk Ground and Individual'] and not self.order_id.x_studio_related_sales_order:
                return
        except:
            pass

        return super(CustomSaleOrderLine, self)._action_launch_stock_rule(previous_product_uom_qty)