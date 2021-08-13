# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CustomResUsers(models.Model):
    _name = 'res.users'
    _inherit = 'res.users'

    # x_default_packing_printer = fields.Many2one(
    #     related='partner_id.x_default_packing_printer',
    #     inherited=True
    # )


    # def __init__(self, pool, cr):
    #     """ Override of __init__ to add access rights.
    #         Access rights are disabled by default, but allowed
    #         on some specific fields defined in self.SELF_{READ/WRITE}ABLE_FIELDS.
    #     """
    #     readable_fields = [
    #         'x_default_packing_printer',
    #     ]
    #     init_res = super(CustomResUsers, self).__init__(pool, cr)
    #     # duplicate list to avoid modifying the original reference
    #     type(self).SELF_READABLE_FIELDS = readable_fields + type(self).SELF_READABLE_FIELDS
    #     return init_res