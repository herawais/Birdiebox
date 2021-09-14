# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CustomSaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    def action_confirm(self):
        if self.x_studio_shipping_type in ['Individual', 'Bulk Freight and Individual', 'Bulk Ground and Individual'] and not self.x_studio_related_sales_order:
            self.state = 'sale'
        else:
            return super(CustomSaleOrder, self).action_confirm()

    def create_api_order(self, formatted_args):

        _logger.debug('\n\n\n Creating API Order,')


    def format_shopify_order(self):
        orders =  [{
                'admin_graphql_api_id':
                'gid://shopify/Order/4048145907899',
                'app_id':
                580111,
                'billing_address': {
                    'address1': '1801 Tennyson Drive',
                    'address2': '',
                    'city': 'Arlington',
                    'company': None,
                    'country': 'United States',
                    'country_code': 'US',
                    'first_name': 'David',
                    'last_name': 'Bodine',
                    'latitude': 32.7289019,
                    'longitude': -97.1338765,
                    'name': 'David Bodine',
                    'phone': None,
                    'province': 'Texas',
                    'province_code': 'TX',
                    'zip': '76013'
                },
                'browser_ip':
                '75.13.231.163',
                'buyer_accepts_marketing':
                False,
                'cancel_reason':
                None,
                'cancelled_at':
                None,
                'cart_token':
                '6000200028afc320fda5d4e0d3050081',
                'checkout_id':
                22156509511867,
                'checkout_token':
                '3cba773be9e134bcae0754bcd219eed4',
                'client_details': {
                    'accept_language':
                    'en-US,en;q=0.9',
                    'browser_height':
                    722,
                    'browser_ip':
                    '75.13.231.163',
                    'browser_width':
                    1492,
                    'session_hash':
                    None,
                    'user_agent':
                    'Mozilla/5.0 (X11; Linux x86_64) '
                    'AppleWebKit/537.36 (KHTML, like '
                    'Gecko) Chrome/93.0.4577.63 '
                    'Safari/537.36'
                },
                'closed_at':
                None,
                'confirmed':
                True,
                'contact_email':
                None,
                'created_at':
                '2021-09-09T15:25:34-05:00',
                'currency':
                'USD',
                'current_subtotal_price':
                '0.00',
                'current_subtotal_price_set': {
                    'presentment_money': {
                        'amount': '0.00',
                        'currency_code': 'USD'
                    },
                    'shop_money': {
                        'amount': '0.00',
                        'currency_code': 'USD'
                    }
                },
                'current_total_discounts':
                '0.00',
                'current_total_discounts_set': {
                    'presentment_money': {
                        'amount': '0.00',
                        'currency_code': 'USD'
                    },
                    'shop_money': {
                        'amount': '0.00',
                        'currency_code': 'USD'
                    }
                },
                'current_total_duties_set':
                None,
                'current_total_price':
                '19.90',
                'current_total_price_set': {
                    'presentment_money': {
                        'amount': '19.90',
                        'currency_code': 'USD'
                    },
                    'shop_money': {
                        'amount': '19.90',
                        'currency_code': 'USD'
                    }
                },
                'current_total_tax':
                '0.00',
                'current_total_tax_set': {
                    'presentment_money': {
                        'amount': '0.00',
                        'currency_code': 'USD'
                    },
                    'shop_money': {
                        'amount': '0.00',
                        'currency_code': 'USD'
                    }
                },
                'customer': {
                    'accepts_marketing': False,
                    'accepts_marketing_updated_at':
                    '2021-09-09T15:25:35-05:00',
                    'admin_graphql_api_id':
                    'gid://shopify/Customer/5477453889723',
                    'created_at': '2021-09-09T15:23:52-05:00',
                    'currency': 'USD',
                    'default_address': {
                        'address1': '1801 Tennyson Drive',
                        'address2': '',
                        'city': 'Arlington',
                        'company': None,
                        'country': 'United States',
                        'country_code': 'US',
                        'country_name': 'United States',
                        'customer_id': 5477453889723,
                        'default': True,
                        'first_name': 'David',
                        'id': 6670286258363,
                        'last_name': 'Bodine',
                        'name': 'David Bodine',
                        'phone': None,
                        'province': 'Texas',
                        'province_code': 'TX',
                        'zip': '76013'
                    },
                    'email': None,
                    'first_name': 'David',
                    'id': 5477453889723,
                    'last_name': 'Bodine',
                    'last_order_id': None,
                    'last_order_name': None,
                    'marketing_opt_in_level': None,
                    'multipass_identifier': None,
                    'note': None,
                    'orders_count': 0,
                    'phone': '+19726462550',
                    'state': 'disabled',
                    'tags': '',
                    'tax_exempt': False,
                    'tax_exemptions': [],
                    'total_spent': '0.00',
                    'updated_at': '2021-09-09T15:25:35-05:00',
                    'verified_email': True
                },
                'customer_locale':
                'en',
                'device_id':
                None,
                'discount_applications': [],
                'discount_codes': [],
                'email':
                '',
                'estimated_taxes':
                False,
                'financial_status':
                'paid',
                'fulfillment_status':
                None,
                'fulfillments': [],
                'gateway':
                'bogus',
                'id':
                4048145907899,
                'landing_site':
                '/?_ab=0&_fd=0&_sc=1&key=25d3d0024f3f28b5c6a488c9ca1d9494b42904b04e004cd92da4829869581352',
                'landing_site_ref':
                None,
                'line_items': [{
                    'admin_graphql_api_id':
                    'gid://shopify/LineItem/10375213252795',
                    'discount_allocations': [],
                    'duties': [],
                    'fulfillable_quantity':
                    1,
                    'fulfillment_service':
                    'manual',
                    'fulfillment_status':
                    None,
                    'gift_card':
                    False,
                    'grams':
                    2722,
                    'id':
                    10375213252795,
                    'name':
                    '(TEST) Boxy Set 1 (TEST)',
                    'origin_location': {
                        'address1': '401 Gerault Road',
                        'address2': '',
                        'city': 'Flower Mound',
                        'country_code': 'US',
                        'id': 3073882325179,
                        'name': 'happyboxes1',
                        'province_code': 'TX',
                        'zip': '75028'
                    },
                    'price':
                    '0.00',
                    'price_set': {
                        'presentment_money': {
                            'amount': '0.00',
                            'currency_code': 'USD'
                        },
                        'shop_money': {
                            'amount': '0.00',
                            'currency_code': 'USD'
                        }
                    },
                    'product_exists':
                    True,
                    'product_id':
                    7106382987451,
                    'properties': [{
                        'name': 'Initials',
                        'value': 'AB'
                    }, {
                        'name': 'Custom Text',
                        'value': 'This is a\r\ntest'
                    }, {
                        'name':
                        'Preview',
                        'value':
                        'https://cdn.shopify.com/s/files/1/0601/5582/2267/uploads/30d2af663f513384f874a4d70f9b33f5.jpeg'
                    }, {
                        'name':
                        'Preview1',
                        'value':
                        'https://cdn.shopify.com/s/files/1/0601/5582/2267/uploads/c6dee3333a650301a2f1c7df6bae154f.jpeg'
                    }, {
                        'name':
                        'Custom Image',
                        'value':
                        'https://cdn.shopify.com/s/files/1/0601/5582/2267/uploads/14617d5fb1cf26d016b8c550e5e10b6f.jpeg'
                    }, {
                        'name': '_pplr_preview',
                        'value': 'Preview'
                    }],
                    'quantity':
                    1,
                    'requires_shipping':
                    True,
                    'sku':
                    'Blargy111',
                    'tax_lines': [],
                    'taxable':
                    True,
                    'title':
                    '(TEST) Boxy Set 1 (TEST)',
                    'total_discount':
                    '0.00',
                    'total_discount_set': {
                        'presentment_money': {
                            'amount': '0.00',
                            'currency_code': 'USD'
                        },
                        'shop_money': {
                            'amount': '0.00',
                            'currency_code': 'USD'
                        }
                    },
                    'variant_id':
                    41639148224699,
                    'variant_inventory_management':
                    None,
                    'variant_title':
                    '',
                    'vendor':
                    'happyboxes1'
                }],
                'location_id':
                None,
                'name':
                '#1001',
                'note':
                None,
                'note_attributes': [],
                'number':
                1,
                'order_number':
                1001,
                'order_status_url':
                'https://happyboxes1.myshopify.com/60155822267/orders/be53d6b54e137f3210bd821e7263e9bb/authenticate?key=3eb4ee8dab474998225c6f5a72b853c8',
                'original_total_duties_set':
                None,
                'payment_details': {
                    'avs_result_code': None,
                    'credit_card_bin': '1',
                    'credit_card_company': 'Bogus',
                    'credit_card_number': '•••• •••• •••• 1',
                    'cvv_result_code': None
                },
                'payment_gateway_names': ['bogus'],
                'phone':
                '+19726462550',
                'presentment_currency':
                'USD',
                'processed_at':
                '2021-09-09T15:25:34-05:00',
                'processing_method':
                'direct',
                'reference':
                None,
                'referring_site':
                '',
                'refunds': [],
                'shipping_address': {
                    'address1': '1801 Tennyson Drive',
                    'address2': '',
                    'city': 'Arlington',
                    'company': None,
                    'country': 'United States',
                    'country_code': 'US',
                    'first_name': 'David',
                    'last_name': 'Bodine',
                    'latitude': 32.7289019,
                    'longitude': -97.1338765,
                    'name': 'David Bodine',
                    'phone': None,
                    'province': 'Texas',
                    'province_code': 'TX',
                    'zip': '76013'
                },
                'shipping_lines': [{
                    'carrier_identifier': None,
                    'code': 'Economy',
                    'delivery_category': None,
                    'discount_allocations': [],
                    'discounted_price': '19.90',
                    'discounted_price_set': {
                        'presentment_money': {
                            'amount': '19.90',
                            'currency_code': 'USD'
                        },
                        'shop_money': {
                            'amount': '19.90',
                            'currency_code': 'USD'
                        }
                    },
                    'id': 3393966244027,
                    'phone': None,
                    'price': '19.90',
                    'price_set': {
                        'presentment_money': {
                            'amount': '19.90',
                            'currency_code': 'USD'
                        },
                        'shop_money': {
                            'amount': '19.90',
                            'currency_code': 'USD'
                        }
                    },
                    'requested_fulfillment_service_id': None,
                    'source': 'shopify',
                    'tax_lines': [],
                    'title': 'Economy'
                }],
                'source_identifier':
                None,
                'source_name':
                'web',
                'source_url':
                None,
                'subtotal_price':
                '0.00',
                'subtotal_price_set': {
                    'presentment_money': {
                        'amount': '0.00',
                        'currency_code': 'USD'
                    },
                    'shop_money': {
                        'amount': '0.00',
                        'currency_code': 'USD'
                    }
                },
                'tags':
                '',
                'tax_lines': [],
                'taxes_included':
                False,
                'test':
                True,
                'token':
                'be53d6b54e137f3210bd821e7263e9bb',
                'total_discounts':
                '0.00',
                'total_discounts_set': {
                    'presentment_money': {
                        'amount': '0.00',
                        'currency_code': 'USD'
                    },
                    'shop_money': {
                        'amount': '0.00',
                        'currency_code': 'USD'
                    }
                },
                'total_line_items_price':
                '0.00',
                'total_line_items_price_set': {
                    'presentment_money': {
                        'amount': '0.00',
                        'currency_code': 'USD'
                    },
                    'shop_money': {
                        'amount': '0.00',
                        'currency_code': 'USD'
                    }
                },
                'total_outstanding':
                '0.00',
                'total_price':
                '19.90',
                'total_price_set': {
                    'presentment_money': {
                        'amount': '19.90',
                        'currency_code': 'USD'
                    },
                    'shop_money': {
                        'amount': '19.90',
                        'currency_code': 'USD'
                    }
                },
                'total_price_usd':
                '19.90',
                'total_shipping_price_set': {
                    'presentment_money': {
                        'amount': '19.90',
                        'currency_code': 'USD'
                    },
                    'shop_money': {
                        'amount': '19.90',
                        'currency_code': 'USD'
                    }
                },
                'total_tax':
                '0.00',
                'total_tax_set': {
                    'presentment_money': {
                        'amount': '0.00',
                        'currency_code': 'USD'
                    },
                    'shop_money': {
                        'amount': '0.00',
                        'currency_code': 'USD'
                    }
                },
                'total_tip_received':
                '0.00',
                'total_weight':
                2721,
                'updated_at':
                '2021-09-09T15:25:35-05:00',
                'user_id':
                None
            }]
       

        _logger.debug('Args')

class CustomSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        try:
            if self.order_id.x_studio_shipping_type in ['Individual', 'Bulk Freight and Individual', 'Bulk Ground and Individual'] and not self.order_id.x_studio_related_sales_order:
                return
        except:
            pass

        return super(CustomSaleOrderLine, self)._action_launch_stock_rule(previous_product_uom_qty)