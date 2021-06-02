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
