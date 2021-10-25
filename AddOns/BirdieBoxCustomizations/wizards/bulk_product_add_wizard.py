# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class BulkSaleProductWizard(models.Model):
    _name = 'bulk.sale.product'
    _description = 'Bulk Sale Add Product'


    product_line = fields.One2many('bulk.sale.product.line',
                                   'create_id',
                                   string='Order Lines')

    def add_all(self):
        try:
            LINE = self.env['sale.order.line']
            for active_id in self._context.get('active_ids', []):
                for line in self.product_line:
                    if not line.product_id:
                        raise Exception('Please select a product in the dropdown!')
                    if not line.route_id:
                        raise Exception('Please select a route for each product!')
                    LINE.create(
                        {
                            "sequence": 2000,
                            "product_id": line.product_id.id,
                            "order_id": active_id,
                            "name": line.name,
                            "x_studio_customization_detail": line.x_studio_customization_detail,
                            "x_studio_customization_notes": line.x_studio_customization_notes,
                            "route_id": line.route_id.id,
                            "price_unit": line.price_unit,
                            "tax_id":line.tax_id.id,
                            "product_uom_qty": line.product_uom_qty
                        }
                    )
        except Exception as e:
            raise ValidationError('There was an error adding products: ' + str(e))

class BulkSaleProductLine(models.Model):
    _name = 'bulk.sale.product.line'
    _description = 'Bulk Sale Add Product Line'

    product_id = fields.Many2one('product.product', string='Product')
    name = fields.Text(string='Description', compute="_compute_name")
    x_studio_customization_notes = fields.Char('Customization Notes')
    price_unit = fields.Float('Unit Price', digits='Product Price')
    x_studio_customization_detail = fields.Selection(
        [
         ('Logo', 'Logo'), 
         ('Initial', 'Initial'), 
         ('Full Name', 'Full Name'),
         ('Logo and Name', 'Logo and Name'),
         ('First Letter and Name', 'First Letter and Name'),
         ('Full Lid Print', 'Full Lid Print'),
         ('Full Lid Print', 'Full Lid Print'),
         ('Logo and Initials', 'Logo and Initials')
        ],
        string="Customization Detail"
    )

    price_subtotal = fields.Float(string='Subtotal',
                                  compute='_compute_amount',
                                  digits='Product Price')
    product_uom_qty = fields.Float(string='Quantity',
                                   digits='Product Unit of Measure',
                                   default=1.0)
    create_id = fields.Many2one('bulk.sale.product',
                                string='Add Reference',
                                index=True,
                                ondelete='cascade')
    tax_id = fields.Many2many(
        'account.tax',
        string='Taxes',
        domain=['|', ('active', '=', False), ('active', '=', True)])
    
    route_id = fields.Many2one('stock.location.route',
                               string='Route',
                               domain=[('sale_selectable', '=', True)],
                               ondelete='restrict',
                               check_company=True)

    @api.depends('product_uom_qty', 'price_unit')
    def _compute_amount(self):
        for line in self:
            price_subtotal = line.product_uom_qty * line.price_unit
            line.update({'price_subtotal': price_subtotal})

    @api.depends('product_id')
    def _compute_name(self):
        for record in self:
            if record.product_id:
                record.name = record.env[
                    'sale.order.line'].get_sale_order_line_multiline_description_sale(
                        record.product_id)
            else:
                record.name = ''