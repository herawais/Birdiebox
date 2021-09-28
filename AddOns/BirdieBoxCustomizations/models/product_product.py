# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.misc import split_every

_logger = logging.getLogger(__name__)


class CustomProductProduct(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'

    barcode = fields.Char(string='Barcode',
                          compute='_compute_barcode',
                          store=True)

    @api.depends('default_code')
    def _compute_barcode(self):
        for record in self:
            if record.default_code:
                try:
                    record.update({'barcode': record.default_code})
                except:
                    pass

    def get_route(self):
        route = None
        for route_id in self.route_ids.ids:
            if route_id in [9, 11, 8, 10]:
                route = route_id
                break

        return route
    
    def add_reordering_rule(self):
        active_reordering = self.env['stock.warehouse.orderpoint'].search([
            ('active', '=', True), ('trigger', '=', 'auto')
        ])
        products = self.search([
            ('active', '=', True),
            ('id', 'not in',
             [x['product_id']['id'] for x in active_reordering])
        ])

        for product in products:
            product.action_add_reordering_rule()


    @api.model
    def create(self, vals):
        res = super(CustomProductProduct, self).create(vals)
        res.action_add_reordering_rule()

        return res

    def action_add_reordering_rule(self):
        Reorder = self.env['stock.warehouse.orderpoint']
        rule = self.env['stock.rule'].search([('name', 'ilike', 'scheduler')])

        if not rule:
            raise ValidationError(
                'Please set up the stock rule with the name scheduler')

        for record in self:
            if not Reorder.search([('product_id', '=', record.id),
                                   ('location_id', '=', 8)]):
                body = {
                    'trigger': 'auto',
                    'warehouse_id': 1,
                    'location_id': 8,
                    'product_id': record.id,
                    'product_category_id': record.categ_id.id,
                    'product_min_qty': 0.0,
                    'product_max_qty': 0.0,
                    'qty_multiple': 1.0,
                    'company_id': 1,
                    'rule_ids': rule.ids,
                }

                Reorder.create(body)