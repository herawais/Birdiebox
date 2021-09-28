# -*- coding: utf-8 -*-
import logging
import json
from ..controllers import shopify
from odoo.exceptions import ValidationError

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

class ShopifyOrderLog(models.Model):
    _name = 'shopify.log'
    _description = "Shopify Logs"
    
    name = fields.Char('Name')

    order_id = fields.Char('Shopify Order ID')

    shop = fields.Many2one('shopify.shop', string="Shop")

    sale_id = fields.Many2one('sale.order', string="Related Sale Order")

    success = fields.Boolean('Success')

    error = fields.Char('Error')

    body = fields.Text('Request Body')

    res = fields.Text('Response Body')

    @api.model
    def create(self, vals):
        try:
            vals['name'] = vals.get('order_id')
        except:
            pass

        return super(ShopifyOrderLog, self).create(vals)
    

    def repull_order(self):
        if not self.shop:
            raise ValidationError('Please select the corresponding shop.')
        
        try:
            brest = shopify.BirdieBox_Shopify_REST(record=self.shop.sudo())
            order = brest.get_order_details(order_id=self.order_id)            
            self.env['sale.order'].create_shopify_order(order, self.shop.shop_id)
        except Exception as e:
            raise Exception('There was an error pulling the order from Shopify: \n' + str(e))