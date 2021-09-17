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
            res = super(CustomSaleOrder, self).action_confirm()
            
            try:
                for picking in self.picking_ids.filtered(lambda x: x.picking_type_id.id == 12):
                    if self.carrier_id and self.carrier_id.id != 4:
                        picking.carrier_id = self.carrier_id
            except:
                pass
            
            return res

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

class CustomSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_auto_add_to_child = fields.Boolean(
        string='Auto-Add',
        default=False,
        help="If this is selected all related orders will automatically get this product added when created."
    )

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        try:
            if self.order_id.x_studio_shipping_type in ['Individual', 'Bulk Freight and Individual', 'Bulk Ground and Individual'] and not self.order_id.x_studio_related_sales_order:
                    return
        except:
            pass

        return super(CustomSaleOrderLine, self)._action_launch_stock_rule(previous_product_uom_qty)