# -*- coding: utf-8 -*-
import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)

class CustomStockPickingType(models.Model):
    _name = 'stock.picking.type'
    _inherit = 'stock.picking.type'

    x_require_pickings_complete = fields.Boolean(
        string='Require All Orders to Be Complete Before Validating',
        default=False
    )

    x_print_shipping_label = fields.Boolean(
        string='Auto Print Shipping Label',
        default=False
    )

    x_validate_carrier = fields.Boolean(
        string='Validate Carrier Matches Sale Order',
        default=False
    )