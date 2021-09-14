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


class CustomSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        try:
            if self.order_id.x_studio_shipping_type in ['Individual', 'Bulk Freight and Individual', 'Bulk Ground and Individual'] and not self.order_id.x_studio_related_sales_order:
                    return
        except:
            pass

        return super(CustomSaleOrderLine, self)._action_launch_stock_rule(previous_product_uom_qty)