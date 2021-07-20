# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CustomStockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super(CustomStockPicking, self).button_validate()

        if self.picking_type_id.id == 12:
            self.validate_kitting()

        return res

    def write(self, vals):
        if 'date_done' in vals and self.picking_type_id.id == 2:
            self.update_delivered_qty()

        return super(CustomStockPicking, self).write(vals)

    def validate_kitting(self):
        for record in self:
            pickings = record.sale_id.picking_ids.filtered(
                lambda x: x.picking_type_id.id not in [12, 2] and x.state
                not in ['done', 'cancel'])
            incomplete = ''
            if len(pickings) > 0:
                for picking in pickings:
                    incomplete += '\n -' + picking.name

                raise ValidationError(
                    'You cannot complete kitting until the following operations have been completed: \n'
                    + incomplete)

    def update_delivered_qty(self):
        parent_sale_order = self.sale_id.x_studio_related_sales_order

        if parent_sale_order:
            for product in parent_sale_order.order_line:
                for line in self.move_line_ids:
                    if line.product_id == product.product_id:
                        product.qty_delivered = line.qty_done + product.qty_delivered