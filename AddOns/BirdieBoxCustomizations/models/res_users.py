# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CustomResUsers(models.Model):
    _name = 'res.users'
    _inherit = 'res.users'


    x_default_packing_printer = fields.Many2one(
        string="Packing Printer",
        related='partner_id.x_default_packing_printer',
        inherited=True
    )