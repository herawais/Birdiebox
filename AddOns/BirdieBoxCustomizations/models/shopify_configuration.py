# -*- coding: utf-8 -*-
import logging
from ..controllers import shopify

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

class ShopifyShop(models.Model): 
    _name = 'shopify.shop'
    _description = "Shopify Shop Configuration"

    name = fields.Char('Shop Name')
    
    shop_id = fields.Char('Shop ID')

    shop_url = fields.Char('Shop URL', compute='_compute_shop_url')

    api_key = fields.Char('API key')

    secret = fields.Char('API Secret')

    shared_secret = fields.Char('Shared Secret')

    active = fields.Boolean(default=True)

    parent_sales_order = fields.Many2one('sale.order', string="Parent Sale Order")

    location_id = fields.Integer('Shopify Location ID')

    connected = fields.Boolean('Connected', default=False)

    @api.depends('shop_id')
    def _compute_shop_url(self):
        for record in self:
            record.shop_url = "https://"+ str(record.shop_id) + ".myshopify.com/"

    def shopify_connect(self):
        brest = shopify.BirdieBox_Shopify_REST(record=self.sudo())
        
        if self.connected:
            if brest.clear_webhooks():
                self.connected = False
        else:
            if brest.set_webhooks():
                self.connected = True
            else:
                self.connected = False
