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

    # def __init__(self, pool, cr):
    #     """ Override of __init__ to add access rights.
    #         Access rights are disabled by default, but allowed
    #         on some specific fields defined in self.SELF_{READ/WRITE}ABLE_FIELDS.
    #     """
    #     readable_fields = [
    #         'x_default_packing_printer',
    #     ]
    #     init_res = super(CustomResPartner, self).__init__(pool, cr)
    #     # duplicate list to avoid modifying the original reference
    #     type(self).SELF_READABLE_FIELDS = readable_fields + type(self).SELF_READABLE_FIELDS
    #     return init_res