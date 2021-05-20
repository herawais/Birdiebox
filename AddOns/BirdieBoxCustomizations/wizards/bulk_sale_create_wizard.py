# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class BulkSaleCreateWizard(models.Model):
    _name = 'bulk.sale.create'
    _description = 'Bulk Sales Create Wizard'

    @api.model
    def _unique_entered_sales_orders(self):
        active_orders = self.env['bulk.sale'].browse(
            self._context.get('active_ids', []))

        return len(
            set(val.parent_sale_order for dic in active_orders for val in dic))

    @api.model
    def _unique_found_sales_orders(self):
        active_orders = self.env['bulk.sale'].browse(
            self._context.get('active_ids', []))
        unique_orders = list(
            set(val.parent_sale_order for dic in active_orders for val in dic))

        sale_orders = self.env['sale.order'].search([('name', 'in',
                                                      unique_orders)])
        return len(sale_orders)

    @api.model
    def _parent_sale_order_id(self):
        active_order = self.env['bulk.sale'].browse(
            self._context.get('active_ids', []))
        sale_order = self.env['sale.order'].search([
            ('name', '=', active_order[0].parent_sale_order)
        ])

        return sale_order

    parent_sale_order_id = fields.Many2one('sale.order',
                                           string="Parent Sale Order ID",
                                           ondelete='restrict',
                                           default=_parent_sale_order_id)

    unique_entered_sales_orders = fields.Integer(
        default=_unique_entered_sales_orders,
        string='Unique Entered Order Count')

    unique_found_sales_orders = fields.Integer(
        default=_unique_found_sales_orders, string='Unique Found Order Count')

    product_line = fields.One2many('bulk.sale.create.line',
                                   'create_id',
                                   string='Order Lines')

    def create_many(self):
        active_orders = self.env['bulk.sale'].browse(
            self._context.get('active_ids', []))

        for order in active_orders:
            order.create_child_sale_order(self.product_line)


class BulkSaleCreateLine(models.Model):
    _name = 'bulk.sale.create.line'
    _description = 'Bulk Sale Create Line'

    product_id = fields.Many2one('product.product', string='Product')
    name = fields.Text(string='Description', compute="_compute_name")
    x_studio_customization_notes = fields.Char('Customization Notes')
    price_unit = fields.Float('Unit Price', digits='Product Price')
    x_studio_customization_detail = fields.Selection(
        [('Logo', 'Logo'), ('Initial', 'Initial'), ('Full Name', 'Full Name'),
         ('Logo and Name', 'Logo and Name'),
         ('First Letter and Name', 'First Letter and Name'),
         ('Full Lid Print', 'Full Lid Print')],
        string="Customization Detail")

    price_subtotal = fields.Float(string='Subtotal',
                                  compute='_compute_amount',
                                  digits='Product Price')
    product_uom_qty = fields.Float(string='Quantity',
                                   digits='Product Unit of Measure',
                                   default=1.0)
    create_id = fields.Many2one('bulk.sale.create',
                                string='Create Reference',
                                index=True,
                                ondelete='cascade')
    tax_id = fields.Many2many(
        'account.tax',
        string='Taxes',
        domain=['|', ('active', '=', False), ('active', '=', True)])

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
