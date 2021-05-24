import json
import requests
from odoo import fields, api, models, _
from odoo.exceptions import UserError


class ProductTemplateCust(models.Model):
    _inherit = 'product.template'

    x_salesforce_exported = fields.Boolean('Exported To Salesforce', default=False,copy=False)
    x_salesforce_id = fields.Char('Salesforce Id',copy=False)
    x_is_updated = fields.Boolean('x_is_updated', default=False,copy=False)

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
                res = requests.request('PATCH', sf_config.sf_url + endpoint + '/' + self.x_salesforce_id, headers=headers, data=payload)
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
