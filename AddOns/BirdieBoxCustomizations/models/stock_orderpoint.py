# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from collections import defaultdict
from odoo import _, api, fields, models
from odoo.addons.stock.models.stock_rule import ProcurementException
from odoo.tools import frozendict

_logger = logging.getLogger(__name__)


class CustomStockWarehouseOrderpoint(models.Model):
    """ Defines Minimum stock rules. """
    _name = "stock.warehouse.orderpoint"
    _inherit = "stock.warehouse.orderpoint"
    _description = "Minimum Inventory Rule"

    @api.depends('product_id', 'location_id', 'product_id.stock_move_ids',
                 'product_id.stock_move_ids.state',
                 'product_id.stock_move_ids.product_uom_qty')
    def _compute_qty(self):
        orderpoints_contexts = defaultdict(
            lambda: self.env['stock.warehouse.orderpoint'])
        for orderpoint in self:
            if not orderpoint.product_id or not orderpoint.location_id:
                orderpoint.qty_on_hand = False
                orderpoint.qty_forecast = False
                continue
            orderpoint_context = orderpoint._get_product_context()
            product_context = frozendict({
                **self.env.context,
                **orderpoint_context
            })
            orderpoints_contexts[product_context] |= orderpoint
        for orderpoint_context, orderpoints_by_context in orderpoints_contexts.items(
        ):
            products_qty = orderpoints_by_context.product_id.with_context(
                prefetch_fields=False)._product_available()
            
            products_qty_in_progress = orderpoints_by_context._quantity_in_progress(
            )
            for orderpoint in orderpoints_by_context:
                orderpoint.qty_on_hand = products_qty[
                    orderpoint.product_id.id]['qty_available']
                orderpoint.qty_forecast = products_qty[
                    orderpoint.product_id.
                    id]['virtual_available'] + products_qty_in_progress[
                        orderpoint.id]