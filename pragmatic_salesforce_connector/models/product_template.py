import json
import requests
from datetime import datetime, timedelta
from odoo import fields, api, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class ProductTemplateCust(models.Model):
    _inherit = 'product.template'

    x_salesforce_exported = fields.Boolean('Exported To Salesforce', default=False, copy=False)
    x_salesforce_id = fields.Char('Salesforce Id', copy=False)
    x_is_updated = fields.Boolean('x_is_updated', default=False, copy=False)

    def sendDataToSf(self, product_dict):
        #         sf_config = self.env['res.users'].search([('id','=',self._uid)],limit=1).company_id
        sf_config = self.env.user.company_id

        ''' GET ACCESS TOKEN '''
        endpoint = None
        sf_access_token = None
        # realmId = None
        res = None
        if sf_config.sf_access_token:
            sf_access_token = sf_config.sf_access_token

        if sf_access_token:
            headers = {}
            headers['Authorization'] = 'Bearer ' + str(sf_access_token)
            headers['Content-Type'] = 'application/json'
            headers['Accept'] = 'application/json'

            endpoint = '/services/data/v39.0/sobjects/product2'

            payload = json.dumps(product_dict)
            if self.x_salesforce_id:
                ''' Try Updating it if already exported '''
                res = requests.request('PATCH', sf_config.sf_url + endpoint + '/' + self.x_salesforce_id,
                                       headers=headers, data=payload)
                if res.status_code == 204:
                    self.x_is_updated = True
                else:
                    pass
            else:
                res = requests.request('POST', sf_config.sf_url + endpoint, headers=headers, data=payload)
                if res.status_code in [200, 201]:
                    parsed_resp = json.loads(str(res.text))
                    self.x_salesforce_exported = True
                    self.x_salesforce_id = parsed_resp.get('id')
                else:
                    pass

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

        result = self.sendDataToSf(product_dict)
        if result:
            self.x_salesforce_exported = True

    # @api.multi
    def exportProductTemplate_to_sf(self):
        for prod_temp in self:
            for product in prod_temp.product_variant_ids:
                product.exportProduct_to_sf()

    def send_product_temp_DataToSf(self, product_dict):
        _logger.info("send_product_temp_DataToSf")

        sf_config = self.env.user.company_id

        ''' GET ACCESS TOKEN '''
        endpoint = None
        sf_access_token = None
        # realmId = None
        res = None
        if sf_config.sf_access_token:
            sf_access_token = sf_config.sf_access_token

        if sf_access_token:
            headers = {}
            headers['Authorization'] = 'Bearer ' + str(sf_access_token)
            headers['Content-Type'] = 'application/json'
            headers['Accept'] = 'application/json'
            exsting_res = ''
            if 'SKU__c' in product_dict and not self.x_salesforce_id:
                _logger.info("In if sku found")

                exsiting_endpoint = "/services/data/v40.0/query/?q=select Id from product2 where sku__c = '{}'".format(
                    product_dict['SKU__c'])
                exsting_res = requests.request('GET', sf_config.sf_url + exsiting_endpoint, headers=headers)
                exsting_res_dict = json.loads(exsting_res.text)
                endpoint = '/services/data/v39.0/sobjects/product2'
                _logger.info("==== exsiting%s in sku", exsting_res.text)
                if exsting_res_dict['totalSize'] > 0:
                    if exsting_res.status_code == 200:
                        parsed_resp = json.loads(str(exsting_res.text))
                        if parsed_resp.get('records') and parsed_resp.get('records')[0].get('Id'):
                            self.x_salesforce_exported = True
                            self.x_salesforce_id = parsed_resp.get('records')[0].get('Id')
                            for prod_temp in self:
                                for product in prod_temp.product_variant_ids:
                                    product.x_salesforce_id = self.x_salesforce_id
                                    product.x_salesforce_exported = True
                            payload = json.dumps(product_dict)

                            res = requests.request('PATCH', sf_config.sf_url + endpoint + '/' + self.x_salesforce_id,
                                                   headers=headers,
                                                   data=payload)
                            if res.status_code == 204:
                                _logger.info("SKU wise updated product sucessfully")
                                self.env.user.company_id.export_product_template_lastmodifieddate = datetime.today()


                        else:
                            pass

                elif 'Name' in product_dict and not self.x_salesforce_id:
                    _logger.info("In if name found")

                    exsiting_endpoint = "/services/data/v40.0/query/?q=select Id from product2 where name = '{}'".format(
                        product_dict['Name'])
                    exsting_res = requests.request('GET', sf_config.sf_url + exsiting_endpoint, headers=headers)
                    exsting_res_dict = json.loads(exsting_res.text)
                    endpoint = '/services/data/v39.0/sobjects/product2'
                    _logger.info("==== exsiting name%s", exsting_res)
                    if exsting_res_dict['totalSize'] > 0:
                        if exsting_res.status_code == 200:
                            parsed_resp = json.loads(str(exsting_res.text))
                            if parsed_resp.get('records') and parsed_resp.get('records')[0].get('Id'):
                                self.x_salesforce_exported = True
                                self.x_salesforce_id = parsed_resp.get('records')[0].get('Id')
                                for prod_temp in self:
                                    for product in prod_temp.product_variant_ids:
                                        product.x_salesforce_id = self.x_salesforce_id
                                        product.x_salesforce_exported = True
                                payload = json.dumps(product_dict)
                                res = requests.request('PATCH',
                                                       sf_config.sf_url + endpoint + '/' + self.x_salesforce_id,
                                                       headers=headers,
                                                       data=payload)
                                if res.status_code == 204:
                                    _logger.info("Name wise updated product sucessfully")
                                    self.env.user.company_id.export_product_template_lastmodifieddate = datetime.today()

                            else:
                                pass
                    else:
                        _logger.info("In else name=========")

                        payload = json.dumps(product_dict)
                        res = requests.request('POST', sf_config.sf_url + endpoint, headers=headers, data=payload)
                        _logger.info("==== new res %s", res)
                        if res.status_code in [200, 201]:
                            parsed_resp = json.loads(str(res.text))
                            self.x_salesforce_exported = True
                            self.x_salesforce_id = parsed_resp.get('id')
                            for prod_temp in self:
                                for product in prod_temp.product_variant_ids:
                                    product.x_salesforce_id = self.x_salesforce_id
                                    product.x_salesforce_exported = True
                                    self.env.user.company_id.export_product_template_lastmodifieddate = datetime.today()




            elif 'Name' in product_dict and not self.x_salesforce_id:
                _logger.info("In if name found")

                exsiting_endpoint = "/services/data/v40.0/query/?q=select Id from product2 where name = '{}'".format(
                    product_dict['Name'])
                exsting_res = requests.request('GET', sf_config.sf_url + exsiting_endpoint, headers=headers)
                exsting_res_dict = json.loads(exsting_res.text)
                endpoint = '/services/data/v39.0/sobjects/product2'
                _logger.info("==== exsiting name%s", exsting_res)
                if exsting_res_dict['totalSize'] >= 1:
                    if exsting_res.status_code == 200:
                        parsed_resp = json.loads(str(exsting_res.text))
                        if parsed_resp.get('records') and parsed_resp.get('records')[0].get('Id'):
                            self.x_salesforce_exported = True
                            self.x_salesforce_id = parsed_resp.get('records')[0].get('Id')
                            for prod_temp in self:
                                for product in prod_temp.product_variant_ids:
                                    product.x_salesforce_id = self.x_salesforce_id
                                    product.x_salesforce_exported = True
                            payload = json.dumps(product_dict)
                            res = requests.request('PATCH', sf_config.sf_url + endpoint + '/' + self.x_salesforce_id,
                                                   headers=headers,
                                                   data=payload)
                            if res.status_code == 204:
                                _logger.info("Name wise updated product sucessfully")
                                self.env.user.company_id.export_product_template_lastmodifieddate = datetime.today()

                        else:
                            pass
                else:
                    _logger.info("In else name=========")

                    payload = json.dumps(product_dict)
                    res = requests.request('POST', sf_config.sf_url + endpoint, headers=headers, data=payload)
                    _logger.info("==== new res %s", res)
                    if res.status_code in [200, 201]:
                        parsed_resp = json.loads(str(res.text))
                        self.x_salesforce_exported = True
                        self.x_salesforce_id = parsed_resp.get('id')
                        for prod_temp in self:
                            for product in prod_temp.product_variant_ids:
                                product.x_salesforce_id = self.x_salesforce_id
                                product.x_salesforce_exported = True
                                self.env.user.company_id.export_product_template_lastmodifieddate = datetime.today()


            elif self.x_salesforce_id:
                _logger.info("In elif x_salesforce_id exists")

                endpoint = '/services/data/v39.0/sobjects/product2'
                payload = json.dumps(product_dict)
                res = requests.request('PATCH', sf_config.sf_url + endpoint + '/' + self.x_salesforce_id,
                                       headers=headers,
                                       data=payload)
                if res.status_code == 204:
                    _logger.info("Updated product sucessfully")
                    self.env.user.company_id.export_product_template_lastmodifieddate = datetime.today()

    def exportProduct_Template_to_sf(self):
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

        if self.description:
            product_dict['Description'] = self.description

        if self.default_code:
            product_dict['SKU__c'] = self.default_code

        if self.x_studio_brand:
            product_dict['Brand__c'] = self.x_studio_brand

        if self.x_studio_branding_fee:
            product_dict['Branding_Fees__c'] = self.x_studio_branding_fee

        # if self.qty_available:
        #     product_dict['Quantity_In_Warehouse__c'] = self.qty_available
        sf_product_variant = self.env['product.product'].search(
            [('name', '=', self.name), ('default_code', '=', self.default_code), ], limit=1)
        if sf_product_variant:
            product_dict['Quantity_In_Warehouse__c'] = sf_product_variant.free_qty
        if self.virtual_available:
            product_dict['Forecasted_Quantity__c'] = self.virtual_available

        if self.list_price:
            product_dict['Price__c'] = self.list_price

        if self.standard_price:
            product_dict['Cost__c'] = self.standard_price

        product_dict['Can_Be_Purchased__c'] = self.purchase_ok

        product_dict['Can_Be_Sold__c'] = self.sale_ok

        if self.categ_id.name:
            product_dict['Category__c'] = self.categ_id.name

        if self.x_studio_domestic_intl:
            product_dict['Dom_Int_l__c'] = self.x_studio_domestic_intl

        if self.x_studio_customization_available:
            product_dict['Customization_Available__c'] = self.x_studio_customization_available
        _logger.info("exportProduct_Template_to_sf ===== product dict1111111111111 === %s", product_dict)

        result = self.send_product_temp_DataToSf(product_dict)
        if result:
            self.x_salesforce_exported = True
            for prod_temp in self:
                for product in prod_temp.product_variant_ids:
                    product.x_salesforce_exported = True

    @api.model
    def _scheduler_export_products_temp_to_sf(self):
        company_id = self.env.user.company_id
        if company_id:
            products = self.search([('write_date', '>', company_id.export_product_template_lastmodifieddate)])
            for product in products:
                try:
                    product.exportProduct_Template_to_sf()
                except Exception as e:
                    _logger.error('Oops Some error in  exporting products to SALESFORCE %s', e)
