# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CustomProductProduct(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'

    barcode = fields.Char(
        string='Barcode',
        compute='_compute_barcode',
        store=True
    )

    @api.depends('default_code')
    def _compute_barcode(self):
        for record in self:
            if record.default_code:
                try:
                    record.update({
                        'barcode': record.default_code
                    })
                except Exception as e:
                    _logger.error('\n\n\n %s', e)
                