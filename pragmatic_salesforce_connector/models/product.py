import json
import logging

import requests
from odoo import fields, api, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProductTemplateCust(models.Model):
    _inherit = 'product.product'

    x_salesforce_exported = fields.Boolean('Exported To Salesforce', default=False,copy=False)
    x_salesforce_id = fields.Char('Salesforce Id',copy=False)
    x_is_updated = fields.Boolean('x_is_updated', default=False,copy=False)
    x_salesforce_pbe = fields.Char('x_salesforce_pbe',copy=False)

    product_price = None

    def sendDataToSf(self, product_dict):
        # sf_config = self.env['res.users'].search([('id','=',self._uid)],limit=1).company_id
        sf_config = self.env.user.company_id

        ''' GET ACCESS TOKEN '''
        endpoint = None
        sf_access_token = None
        realmId = None
        is_create = False
        res = None
        if sf_config.sf_access_token:
            sf_access_token = sf_config.sf_access_token

        if sf_access_token:
            headers = {}
            headers['Authorization'] = 'Bearer ' + str(sf_access_token)
            headers['Content-Type'] = 'application/json'
            headers['Accept'] = 'application/json'

            endpoint = '/services/data/v40.0/sobjects/product2'

            payload = json.dumps(product_dict)
            if self.x_salesforce_id:
                ''' Try Updating it if already exported '''
                res = requests.request('PATCH', sf_config.sf_url + endpoint + '/' + self.x_salesforce_id, headers=headers, data=payload)
                if res.status_code == 204:
                    self.x_is_updated = True

                ''' Update Price as well '''
                endpoint = '/services/data/v40.0/sobjects/pricebookentry'
                payload = {
                    'UnitPrice': self.product_price
                }
                payload = json.dumps(payload)
                res_new=""
                if self.x_salesforce_pbe:
                    res_new = requests.request('PATCH', sf_config.sf_url + endpoint + '/' + self.x_salesforce_pbe, headers=headers, data=payload)
                if res.status_code == 404:
                    is_create = True
                else:
                    pass
            else:
                res = requests.request('POST', sf_config.sf_url + endpoint, headers=headers, data=payload)
                if res.status_code in [200, 201]:
                    parsed_resp = json.loads(str(res.text))
                    self.x_salesforce_exported = True
                    self.x_salesforce_id = parsed_resp.get('id')
                    return parsed_resp.get('id')
                else:
                    return False

    # @api.multi
    def exportProduct_to_sf(self):
        if len(self) > 1:
            raise UserError(_("Please Select 1 record to Export"))

        ''' PREPARE DICT FOR SENDING TO SALESFORCE '''
        product_dict = {}
        if self.name:
            product_dict['Name'] = self.name
        if self.active:
            product_dict['IsActive'] = 'true'
        else:
            product_dict['IsActive'] = 'false'
        if self.description_sale:
            product_dict['Description'] = self.description_sale
        if self.default_code:
            product_dict['ProductCode'] = self.default_code
        # if self.lst_price:
        #     self.product_price = self.lst_price
        # else:
        #     self.product_price = 0

        result = self.sendDataToSf(product_dict)
        if result:
            self.x_salesforce_exported = True
            sf_access_token = None
            #             sf_config = self.env['res.users'].search([('id','=',self._uid)],limit=1).company_id
            sf_config = self.env.user.company_id
            ''' Create a entry in pricebook in salesforce'''
            if sf_config.sf_access_token:
                sf_access_token = sf_config.sf_access_token

            if sf_access_token:
                headers = {}
                headers['Authorization'] = 'Bearer ' + str(sf_access_token)
                headers['Content-Type'] = 'application/json'
                headers['Accept'] = 'application/json'

                ''' Get Standard Pricebook Id'''
                endpoint = "/services/data/v40.0/query/?q=select Id from pricebook2 where name = '{}'".format("Standard Price Book")
                res = requests.request('GET', sf_config.sf_url + endpoint, headers=headers)
                if res.status_code == 200:
                    parsed_resp = json.loads(str(res.text))
                    if parsed_resp.get('records') and parsed_resp.get('records')[0].get('Id'):

                        payload = {
                            'IsActive': True,
                            'UnitPrice': self.list_price,
                            'UseStandardPrice': False,
                            'Product2Id': result,
                            'Pricebook2Id': parsed_resp.get('records')[0].get('Id')
                        }
                        payload = json.dumps(payload)
                        endpoint = '/services/data/v40.0/sobjects/pricebookentry'
                        res = requests.request('POST', sf_config.sf_url + endpoint, headers=headers, data=payload)
                        if res.status_code in [200, 201]:
                            resp = json.loads(str(res.text))
                            self.x_salesforce_pbe = resp.get('id')

    @api.model
    def _scheduler_export_products_to_sf(self):
        products = self.search([])
        for product in products:
            try:
                product.exportProduct_to_sf()
            except Exception as e:
                _logger.error('Oops Some error in  exporting products to SALESFORCE %s', e)
