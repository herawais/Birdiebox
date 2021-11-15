# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class BulkSaleProductSwapWizard(models.Model):
    _name = 'bulk.sale.product.swap'
    _description = 'Bulk Sale Product Swap'

    def _default_swappable_products_domain(self):
        active_orders = self.env['sale.order'].browse(
            self._context.get('active_ids', []))

        products = []
        for index, order in enumerate(active_orders):
            if index == 0:
                for line in order.order_line:
                    products.append(line.product_id.id)
            else:
                found_products = [
                    product.product_id.id for product in order.order_line
                ]
                for product in products:
                    if product not in found_products:
                        products.remove(product)

        return [('id', 'in', products)]

    product_to_replace = fields.Many2one(
        'product.product',
        string='Product to Replace',
        help=
        "This product will be set to 0 on the sale order and all pickings that have not been completed.",
        domain=lambda self: self._default_swappable_products_domain())

    product_line = fields.One2many('bulk.sale.product.swap.line',
                                   'create_id',
                                   string='Order Lines')
    
    
    def do_swap(self):
        try:
            active_orders = self.env['sale.order'].browse(
                self._context.get('active_ids', []))
            
            if not self.product_to_replace:
                raise ValidationError('Please enter a product to replace.')
            
            for order in active_orders.sudo():
                sale_line_to_zero = order.order_line.filtered(
                    lambda x: x.product_id.id == self.product_to_replace.id)
                for line in sale_line_to_zero:
                    line.product_uom_qty = 0

                pickings = order.picking_ids.filtered(
                    lambda x: x.state not in ['done', 'cancel'])

                moves = order.env['stock.move'].search([
                    ('picking_id', 'in', pickings.ids),
                    ('product_id', '=', self.product_to_replace.id),
                    ('state', 'not in', ['done', 'cancel'])
                ])
                for line in moves:
                    line._do_unreserve()
                    line.product_uom_qty = 0

                move_lines = order.env['stock.move.line'].search([
                    ('picking_id', 'in', pickings.ids),
                    ('product_id', '=', self.product_to_replace.id),
                    ('state', 'not in', ['done', 'cancel'])
                ])
                for line in move_lines:
                    line.unlink()
                
                if len(self.product_line):
                    for line in self.product_line:
                        if not line.product_id:
                            raise ValidationError('Please enter a product to swap.')
                        if not line.route_id:
                            raise ValidationError('A route is required for every product.')
                        if line.product_uom_qty < 1:
                            raise ValidationError('Please enter a quantity greater than 0.')

                        swap_body = {
                            "order_id": order.id,
                            "product_id": line.product_id.id,
                            "name": line.product_id.name,
                            "x_studio_customization_detail": line.x_studio_customization_detail,
                            "x_studio_customization_notes": line.x_studio_customization_notes,
                            "price_unit": line.price_unit,
                            "tax_id": None,
                            "product_uom_qty": line.product_uom_qty,
                            "route_id": line.route_id.id
                        }
                        order.env['sale.order.line'].create(swap_body)
                    
                    for picking in pickings:
                        moves_with_qty = order.env['stock.move'].search([
                            ('picking_id', '=', picking.id),
                            ('product_uom_qty', '>', 0),
                            ('state', 'not in', ['done', 'cancel'])
                        ])
                        if not len(moves_with_qty):
                            picking.action_cancel()

                else:
                    raise ValidationError('Please enter product(s) to be added.')
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_('There was an error swapping these products: %s', str(e)))


class BulkSaleProductSwapLine(models.Model):
    _name = 'bulk.sale.product.swap.line'
    _description = 'Bulk Sale Swap Product Line'

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
    create_id = fields.Many2one('bulk.sale.product.swap',
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