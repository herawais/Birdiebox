from odoo import fields, models,api, _
from odoo.exceptions import UserError
import json
import requests


class SaleOrderCust(models.Model):
    _inherit = 'sale.order'

    x_salesforce_id = fields.Char('Salesforce Id', copy=False)
    contract_id = fields.Many2one('sf.contract',string='Contract')
    x_salesforce_exported = fields.Boolean('Exported To Salesforce', default=False,copy=False)
    x_is_updated = fields.Boolean('x_is_updated', default=False,copy=False)
    x_salesforce_pbe = fields.Char('Salesforce pricelist', copy=False)


    @api.onchange('contract_id')
    def onchange_contract_id(self):
        if self.contract_id:
            if self.date_order.date() < self.contract_id.contract_start_date:
                raise UserError(_("Order Start Date can't be earlier than the contract's start date.: Order Start Date."))
            if self.partner_id != self.contract_id.parent_id:
                raise UserError(_("Order customer and contract customer should be same"))

    
    def sendDataToSf(self, order_dict):
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

            endpoint = '/services/data/v40.0/sobjects/Order'

            payload = json.dumps(order_dict)
            if self.x_salesforce_id:
                ''' Try Updating it if already exported '''
                res = requests.request('PATCH', sf_config.sf_url + endpoint + '/' + self.x_salesforce_id, headers=headers, data=payload)
                if res.status_code == 204:
                    self.x_is_updated = True
                    return self.x_salesforce_id

            else:
                res = requests.request('POST', sf_config.sf_url + endpoint, headers=headers, data=payload)
                if res.status_code in [200, 201]:
                    parsed_resp = json.loads(str(res.text))
                    self.x_salesforce_exported = True
                    self.x_salesforce_id = parsed_resp.get('id')
                    return parsed_resp.get('id')
                else:
                    return False
    def sendLineDataToSf(self, order_line_dict,line_sf_id,line_id):
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

            endpoint = '/services/data/v40.0/sobjects/orderitem'

            payload = json.dumps(order_line_dict)
            if line_sf_id:
                ''' Try Updating it if already exported '''
                res = requests.request('PATCH', sf_config.sf_url + endpoint + '/' + line_sf_id, headers=headers, data=payload)
                if res.status_code == 204:
                    order_line=self.env['sale.order.line'].search([('id','=',line_id)])
                    order_line.x_is_updated = True

            else:
                res = requests.request('POST', sf_config.sf_url + endpoint, headers=headers, data=payload)

                if res.status_code in [200, 201]:
                    parsed_resp = json.loads(str(res.text))
                    order_line=self.env['sale.order.line'].search([('id','=',line_id)])
                    order_line.x_salesforce_exported = True
                    order_line.x_salesforce_id = parsed_resp.get('id')
                    return parsed_resp.get('id')
                else:
                    return False


    def exportSaleOrder_to_sf(self):
        if len(self) > 1:
            raise UserError(_("Please Select 1 record to Export"))
        if not self.contract_id:
            raise UserError(_("Please add contract"))
        else:
            ''' PREPARE DICT FOR SENDING TO SALESFORCE '''
            sf_config = self.env.user.company_id
            order_dict = {}
            order_line_list=[]
            order_line_dict ={}
            if self.date_order:
                order_dict['EffectiveDate'] = str(self.date_order.date())
            if self.partner_id and self.partner_id.x_salesforce_id:
                order_dict['AccountId'] = str(self.partner_id.x_salesforce_id)
            elif self.partner_id and not self.partner_id.x_salesforce_id:
                partner_export = self.partner_id.exportPartner_to_sf()
                order_dict['AccountId'] = str(self.partner_id.x_salesforce_id) 
            if self.contract_id and self.contract_id.x_salesforce_id:
                order_dict['ContractId'] = self.contract_id.x_salesforce_id
            elif self.contract_id and not self.contract_id.x_salesforce_id:
                contract_export= self.contract_id.exportContract_to_sf()
                order_dict['ContractId'] = self.contract_id.x_salesforce_id
            order_dict['Status'] = 'Draft'
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
                    order_dict['Pricebook2Id'] = parsed_resp.get('records')[0].get('Id')
        
            result = self.sendDataToSf(order_dict)
            line_sf_id=''
            if result:
                if self.order_line:
                    for line in self.order_line:
                        if line.x_salesforce_id:
                            if line.product_id and line.product_id.x_salesforce_id:
                                order_line_dict={'Product2Id':line.product_id.x_salesforce_id,
                                'Quantity':line.product_uom_qty,'UnitPrice':line.price_unit,
                                'OrderId':self.x_salesforce_id,
                                }
                            elif line.product_id and not line.product_id.x_salesforce_id:
                                line.product_id.exportProduct_to_sf()
                                order_line_dict={'Product2Id':line.product_id.x_salesforce_id,
                                'Quantity':line.product_uom_qty,'UnitPrice':line.price_unit,
                                'OrderId':self.x_salesforce_id,
                                }
                            line_sf_id = line.x_salesforce_id
                            line_id = line.id
                        else:
                            if line.product_id and line.product_id.x_salesforce_id:
                                order_line_dict={'Product2Id':line.product_id.x_salesforce_id,
                                'Quantity':line.product_uom_qty,'UnitPrice':line.price_unit,
                                'OrderId':self.x_salesforce_id,
                                }
                            elif line.product_id and not line.product_id.x_salesforce_id:
                                line.product_id.exportProduct_to_sf()
                                order_line_dict={'Product2Id':line.product_id.x_salesforce_id,
                                'Quantity':line.product_uom_qty,'UnitPrice':line.price_unit,
                                'OrderId':self.x_salesforce_id,
                                }
                            line_id = line.id
                            ''' Create a entry in pricebook in salesforce'''
                            if sf_config.sf_access_token:
                                sf_access_token = sf_config.sf_access_token

                            if sf_access_token:
                                headers = {}
                                headers['Authorization'] = 'Bearer ' + str(sf_access_token)
                                headers['Content-Type'] = 'application/json'
                                headers['Accept'] = 'application/json'
                            salesforce_pbe =''
                            pricebook_id=''
                            order_data = requests.request('GET',
                                                sf_config.sf_url + "/services/data/v40.0/query/?q=select Pricebook2Id from Order where Id = '{}'".format(
                                                    self.x_salesforce_id), headers=headers)
                            if order_data.text:
                                order_data = json.loads(str(order_data.text))
                                pricebook_id = order_data.get('records')[0].get('Pricebook2Id')
                            PricebookEntryData = requests.request('GET',
                                                sf_config.sf_url + "/services/data/v40.0/query/?q=select Id,UnitPrice from PricebookEntry where  Pricebook2Id='{}'".format(
                                                    pricebook_id), headers=headers)
                            if PricebookEntryData.text:
                                pricebookentry_data = json.loads(str(PricebookEntryData.text))
                                for pricebook in pricebookentry_data.get('records'):
                                    line.product_id.x_salesforce_pbe = pricebook.get('Id')
                                order_line_dict['PricebookEntryId']=line.product_id.x_salesforce_pbe                
                        if order_line_dict:
                            result = self.sendLineDataToSf(order_line_dict,line_sf_id,line_id)
                    self.x_salesforce_exported = True

    @api.model
    def _scheduler_export_orders_to_sf(self):
        orders = self.search([])
        for order in orders:
            try:
                order.exportSaleOrder_to_sf()
            except Exception as e:
                _logger.error('Oops Some error in  exporting orders to SALESFORCE %s', e)
    
    def exportToSalesForce(self):
        if self.state in ['draft','sent'] :
            self.exportQuotations_to_sf()
        elif self.state in ['sale','done','cancle']:
            self.exportSaleOrder_to_sf()



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_salesforce_id = fields.Char('Salesforce Id', copy=False)
    x_salesforce_exported = fields.Boolean('Exported To Salesforce', default=False,copy=False)
    x_is_updated = fields.Boolean('x_is_updated', default=False,copy=False)

    
