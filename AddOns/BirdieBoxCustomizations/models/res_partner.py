# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CustomResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    x_default_packing_printer = fields.Many2one(
        comodel_name='res.printers',
        string='Default Packing Printer',
        default=False
    )
