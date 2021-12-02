# -*- coding: utf-8 -*-
from odoo import http
import hmac, hashlib, base64, json, requests, time
from werkzeug.wrappers import Response

import logging
_logger = logging.getLogger(__name__)

# Manage Admin API Webhooks - REST API
# =============================
# Get webhooks - Get what webhooks are set for a shop
# Set Webhooks - Set them up for a shop
# Clear webhooks - Clear out all webhooks for a shop so you can set them again if something went wrong

# Shopify Admin API - REST API
# =============================
# Get Order Details - Get order details based on shopify id
# Get Fulfillment - Get all fulfillments for an order
# Set Fulfillment - Set either a partial fulfillment or a complete fulfillment for an order
class BirdieBox_Shopify_REST(http.Controller):
    def __init__(self, record=None):
        self.shop = record and record.shop_id or False
        self.location = record and record.location_id or False
        self.api_key = record and record.api_key or False
        self.secret = record and record.secret or False
        self.env = record and record or False
    
    def get_webhooks(self):
        shop = self.shop
        # TODO: CHANGE THIS as this needs to be queried from the database
        # based on the shop.
        # ======================================================================
        api_key = self.api_key
        secret = self.secret
        # ======================================================================

        base_path = f'https://{shop}.myshopify.com'
        wh = '/admin/api/2021-07/webhooks.json'
        hdrs = {}
        hdrs['Content-Type'] = 'application/json'
        hdrs['X-Shopify-Access-Token'] = secret

        r = requests.get(base_path + wh, headers=hdrs)
        if r.status_code == 200:
            resp = r.json()
            return resp.get('webhooks')
        else:
            # something bad happened.. probably should return better info..
            return r.status_code

    def set_webhooks(self):
        shop = self.shop
        # TODO: CHANGE THIS as this needs to be queried from the database
        # ======================================================================
        api_key = self.api_key
        secret = self.secret
        # ======================================================================
        odoo_base_path = self.env.env['ir.config_parameter'].sudo().get_param('web.base.url')

        base_path = f'https://{shop}.myshopify.com'
        wh = '/admin/api/2021-07/webhooks.json'
        hdrs = {}
        hdrs['Content-Type'] = 'application/json'
        hdrs['X-Shopify-Access-Token'] = secret

        subs = {}
        subs['orders/create'] = 'bb_shopify/orders_create'
        # Future Webhooks
        # ==========================================================
        #subs['orders/updated'] = 'bb_shopify/orders_cancelled'
        #subs['orders/cancelled'] = 'bb_shopify/orders_updated'
        #subs['customers/create'] = 'bb_shopify/customers_create'
        #subs['customers/update'] = 'bb_shopify/customers_update'

        data = []
        for item in subs.keys():
            wh_sub = {}
            wh_sub['topic'] = item
            wh_sub['address'] = odoo_base_path + '/' + subs[item]
            wh_sub['format'] = 'json'
            payload = {}
            payload['webhook'] = wh_sub
            r = requests.post(base_path + wh, data=json.dumps(payload), headers=hdrs)
            if r.status_code != 201:
                time.sleep(0.5)
                continue
            resp = r.json()
            data.append(resp.get('webhook'))
            time.sleep(0.5)

        if len(subs.keys()) != len(data):
            return False
        else:
            return True

    def clear_webhooks(self):
        shop = self.shop
        all_webhooks = self.get_webhooks()

        # TODO: CHANGE THIS as this needs to be queried from the database
        # ======================================================================
        api_key = self.api_key
        secret = self.secret
        # ======================================================================
        base_path = f'https://{shop}.myshopify.com'
        hdrs = {}
        hdrs['Content-Type'] = 'application/json'
        hdrs['X-Shopify-Access-Token'] = secret

        data = []
        for item in all_webhooks:
            wh_id = str(item.get('id'))
            wh_del = f'/admin/api/2021-07/webhooks/{wh_id}.json'
            r = requests.delete(base_path + wh_del, headers=hdrs )
            if r.status_code == 200:
                data.append("OK")
            else:
                time.sleep(0.5)
                continue
            time.sleep(0.5)

        if len(all_webhooks) != len(data):
            return False
        else:
            return True

    def get_order_details(self, order_id=None):
        shop = self.shop
        # TODO: CHANGE THIS as this needs to be queried from the database
        # ======================================================================
        api_key = self.api_key
        secret = self.secret
        # ======================================================================

        base_path = f'https://{shop}.myshopify.com'
        orders = f'/admin/api/2021-07/orders/{str(order_id)}.json'
        hdrs = {}
        hdrs['Content-Type'] = 'application/json'
        hdrs['X-Shopify-Access-Token'] = secret
        r = requests.get(base_path + orders, headers=hdrs)
        if r.status_code != 200:
            return False, "No Order found for that id, or something is wrong with Shopify"
        else:
            resp = r.json()
            return resp.get('order')

    def get_sh_location(self):
        shop = self.shop
        # TODO: CHANGE THIS as this needs to be queried from the database
        # ======================================================================
        api_key = self.api_key
        secret = self.secret
        # ======================================================================
        base_path = f'https://{shop}.myshopify.com'
        loc = f'/admin/api/2021-07/locations.json'
        hdrs = {}
        hdrs['Content-Type'] = 'application/json'
        hdrs['X-Shopify-Access-Token'] = secret
        r = requests.get(base_path + loc, headers=hdrs)
        if r.status_code != 200:
            return False
        else:
            
            resp = r.json()
            locations = resp.get('locations')

            active_locations = []
            for item in locations:
                if item.get('active'):
                    active_locations.append(item)
                else:
                    continue

            first_loc = active_locations[0]
            self.location = first_loc.get('id')
            return first_loc.get('id')

    def get_location(self):
        # Query Shopify for the location id of this shop and set it in the class
        if self.location == 0:
            return self.get_sh_location()
        else:
            return self.location

    def get_fulfillments(self, order_id=None):
        shop = self.shop
        # TODO: CHANGE THIS as this needs to be queried from the database
        # ======================================================================
        api_key = self.api_key
        secret = self.secret
        # ======================================================================
        base_path = f'https://{shop}.myshopify.com'
        fil = f'/admin/api/2021-07/orders/{str(order_id)}/fulfillments.json'
        hdrs = {}
        hdrs['Content-Type'] = 'application/json'
        hdrs['X-Shopify-Access-Token'] = secret
        r = requests.get(base_path + fil, headers=hdrs)
        if r.status_code != 200:
            return False, "No Order found for that id, or something is wrong with Shopify"
        else:
            resp = r.json()
            return resp.get('fulfillments')

    def set_fulfillments_and_close(self, order_id=None, tracking_numbers=None, notify_customer=False):
        # ======================================================================
        # This will set the tracking number to the order and close it out.  if
        # you need to leave it open because it's not complete use set_fulfillments.
        # ======================================================================
        shop = self.shop
        location = self.get_location()
        # TODO: CHANGE THIS as this needs to be queried from the database
        # based on the shop.
        # ======================================================================
        api_key = self.api_key
        secret = self.secret
        # ======================================================================

        base_path = f'https://{shop}.myshopify.com'
        fil = f'/admin/api/2021-07/orders/{str(order_id)}/fulfillments.json'
        hdrs = {}
        hdrs['Content-Type'] = 'application/json'
        hdrs['X-Shopify-Access-Token'] = secret

        payload = {}
        fp = {}
        fp["location_id"] = location
        if notify_customer:
            fp["notify_customer"] = True
        else:
            fp["notify_customer"] = False

        if isinstance(tracking_numbers, list):
            fp["tracking_numbers"] = tracking_numbers
        else:
            fp["tracking_numbers"] = str(tracking_numbers)
        payload["fulfillment"] = fp

        r = requests.post(base_path + fil, data=json.dumps(payload), headers=hdrs)
        if r.status_code != 201:
            return None
        else:
            resp = r.json()
            resp_f = resp.get('fulfillment')
            return resp_f.get('id')

    def set_fulfillments(self, order_id=None, line_item_ids=[], tracking_numbers=[]):
        # future scaffold
        pass

    def update_fulfillments(self, order_id=None, fulfillment_id=None, tracking_numbers=[]):
        # Future scaffold
        pass

# Endpoints for webhooks - REST ENDPOINTS USED by Shopify
# =============================
# orders/create
# orders/cancelled
# orders/updated
# customers/create
# customers/update
class BirdieBox_Shopify_WH(http.Controller):
    def __init__(self):
        super().__init__()
    
    def verify_webhook(self, sh_shared_secret, data, hmac_header):
        digest = hmac.new(sh_shared_secret.encode('UTF-8'), data.encode('UTF-8'), hashlib.sha256).digest()
        computed_hmac = base64.b64encode(digest)
        return hmac.compare_digest(computed_hmac, hmac_header.encode('UTF-8'))

    @http.route('/bb_shopify/orders_create', type='json', methods=['POST'], auth='public', csrf=False)
    def orders_create(self, **kw):
        
        req = http.request.httprequest
        raw_shopify_data = req.get_data().decode('UTF-8')
        headers = req.headers
        sh_shop_domain = headers.get('X-Shopify-Shop-Domain')
        shop_name = sh_shop_domain.split('.')[0]

        hmac_header = headers.get('X-Shopify-Hmac-Sha256')
        # ============================================================================
        # Confirm the Webhook is coming from Shopify with the shared secret..
        # ============================================================================
        # Get Shared Secret from the database.
        # sh_shared_secret = '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'
        sh_shared_secret = http.request.env['shopify.shop'].sudo().search([('shop_id', 'ilike', shop_name)],limit=1).shared_secret
        # ============================================================================
        sh_validator = self.verify_webhook(sh_shared_secret, raw_shopify_data, hmac_header)
        # Validate the request coming from BirdieBox
        if not sh_validator:
            resp = Response("Not Found", status=404)
            resp.headers['X-MP-Odoo-JSON'] = "TRUE"
            return resp

        
        

        # ======================================================================
        # Order Create -- queue_job is incompatible with odoo.sh, and will
        # violate terms if used so, it's either cron
        # ======================================================================
        http.request.env['sale.order'].sudo().create_shopify_order(json.loads(raw_shopify_data), shop_name)
        # ======================================================================

        # See the __init__.py for the monkey patch code
        resp = Response("OK", status=200)
        resp.headers['X-MP-Odoo-JSON'] = "TRUE"
        return resp

    @http.route('/bb_shopify/orders_cancelled', type='json', methods=['POST'], auth='public', csrf=False)
    def orders_cancelled(self, **kw):
        # ============================================================================
        # Confirm the Webhook is coming from Shopify with the shared secret..
        # ============================================================================
        # Get Shared Secret from the database.
        sh_shared_secret = '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'
        # ============================================================================
        req = http.request.httprequest
        raw_shopify_data = req.get_data().decode('UTF-8')
        headers = req.headers
        hmac_header = headers.get('X-Shopify-Hmac-Sha256')
        sh_validator = self.verify_webhook(sh_shared_secret, raw_shopify_data, hmac_header)
        # Validate the request coming from BirdieBox
        if not sh_validator:
            resp = Response("Not Found", status=404)
            resp.headers['X-MP-Odoo-JSON'] = "TRUE"
            return resp

        sh_shop_domain = headers.get('X-Shopify-Shop-Domain')
        shop_name = sh_shop_domain.split('.')[0]

        # ======================================================================
        # Orders Cancelled -- queue_job is incompatible with odoo.sh, and will
        # violate terms if used so, it's either cron
        # ======================================================================

        # ======================================================================


        # See the __init__.py for the monkey patch code
        resp = Response("OK", status=200)
        resp.headers['X-MP-Odoo-JSON'] = "TRUE"
        return resp


    @http.route('/bb_shopify/orders_updated', type='json', methods=['POST'], auth='public', csrf=False)
    def orders_updated(self, **kw):
        # ============================================================================
        # Confirm the Webhook is coming from Shopify with the shared secret..
        # ============================================================================
        # Get Shared Secret from the database.
        sh_shared_secret = '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'
        # ============================================================================
        req = http.request.httprequest
        raw_shopify_data = req.get_data().decode('UTF-8')
        headers = req.headers
        hmac_header = headers.get('X-Shopify-Hmac-Sha256')
        sh_validator = self.verify_webhook(sh_shared_secret, raw_shopify_data, hmac_header)
        # Validate the request coming from BirdieBox
        if not sh_validator:
            resp = Response("Not Found", status=404)
            resp.headers['X-MP-Odoo-JSON'] = "TRUE"
            return resp

        sh_shop_domain = headers.get('X-Shopify-Shop-Domain')
        shop_name = sh_shop_domain.split('.')[0]

        # ======================================================================
        # Orders Updated -- queue_job is incompatible with odoo.sh, and will
        # violate terms if used so, it's either cron
        # ======================================================================

        # ======================================================================

        # See the __init__.py for the monkey patch code
        resp = Response("OK", status=200)
        resp.headers['X-MP-Odoo-JSON'] = "TRUE"
        return resp


    @http.route('/bb_shopify/customers_create', type='json', methods=['POST'], auth='public', csrf=False)
    def customers_create(self, **kw):
        # ============================================================================
        # Confirm the Webhook is coming from Shopify with the shared secret..
        # ============================================================================
        # Get Shared Secret from the database.
        sh_shared_secret = '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'
        # ============================================================================
        req = http.request.httprequest
        raw_shopify_data = req.get_data().decode('UTF-8')
        headers = req.headers
        hmac_header = headers.get('X-Shopify-Hmac-Sha256')
        sh_validator = self.verify_webhook(sh_shared_secret, raw_shopify_data, hmac_header)
        # Validate the request coming from BirdieBox
        if not sh_validator:
            resp = Response("Not Found", status=404)
            resp.headers['X-MP-Odoo-JSON'] = "TRUE"
            return resp

        sh_shop_domain = headers.get('X-Shopify-Shop-Domain')
        shop_name = sh_shop_domain.split('.')[0]

        # ======================================================================
        # Customers Create -- queue_job is incompatible with odoo.sh, and will
        # violate terms if used so, it's either cron
        # ======================================================================

        # ======================================================================

        # See the __init__.py for the monkey patch code
        resp = Response("OK", status=200)
        resp.headers['X-MP-Odoo-JSON'] = "TRUE"
        return resp

    @http.route('/bb_shopify/customers_update', type='json', methods=['POST'], auth='public', csrf=False)
    def customers_update(self, **kw):
        # ============================================================================
        # Confirm the Webhook is coming from Shopify with the shared secret..
        # ============================================================================
        # Get Shared Secret from the database.
        sh_shared_secret = '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'
        # ============================================================================
        req = http.request.httprequest
        raw_shopify_data = req.get_data().decode('UTF-8')
        headers = req.headers
        hmac_header = headers.get('X-Shopify-Hmac-Sha256')
        sh_validator = self.verify_webhook(sh_shared_secret, raw_shopify_data, hmac_header)
        # Validate the request coming from BirdieBox
        if not sh_validator:
            resp = Response("Not Found", status=404)
            resp.headers['X-MP-Odoo-JSON'] = "TRUE"
            return resp

        sh_shop_domain = headers.get('X-Shopify-Shop-Domain')
        shop_name = sh_shop_domain.split('.')[0]

        # ======================================================================
        # Customers Update -- queue_job is incompatible with odoo.sh, and will
        # violate terms if used so, it's either cron
        # ======================================================================

        # ======================================================================

        # See the __init__.py for the monkey patch code
        resp = Response("OK", status=200)
        resp.headers['X-MP-Odoo-JSON'] = "TRUE"
        return resp
