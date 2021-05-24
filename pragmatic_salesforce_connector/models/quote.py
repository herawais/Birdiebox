from odoo import fields, models,api, _
from odoo.exceptions import UserError
import json
import requests


class SaleOrderCust(models.Model):
    _inherit = 'sale.order'

   

    def sendQuoteDataToSf(self, quote_dict):
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

            endpoint = '/services/data/v40.0/sobjects/Quote'

            payload = json.dumps(quote_dict)
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
    def sendQuoteLineDataToSf(self, quote_line_dict,line_sf_id,line_id):
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

            endpoint = '/services/data/v40.0/sobjects/quotelineitem'

            payload = json.dumps(quote_line_dict)
            if line_sf_id:
                ''' Try Updating it if already exported '''
                res = requests.request('PATCH', sf_config.sf_url + endpoint + '/' + line_sf_id, headers=headers, data=payload)
                if res.status_code == 204:
                    quote_line=self.env['sale.order.line'].search([('id','=',line_id)])
                    quote_line.x_is_updated = True

            else:
                res = requests.request('POST', sf_config.sf_url + endpoint, headers=headers, data=payload)
                if res.status_code in [200, 201]:
                    parsed_resp = json.loads(str(res.text))
                    quote_line=self.env['sale.order.line'].search([('id','=',line_id)])
                    quote_line.x_salesforce_exported = True
                    quote_line.x_salesforce_id = parsed_resp.get('id')
                    return parsed_resp.get('id')
                else:
                    return False


    def exportQuotations_to_sf(self):
        if len(self) > 1:
            raise UserError(_("Please Select 1 record to Export"))
        if not self.contract_id:
            raise UserError(_("Please add contract"))
        if not self.opportunity_id:
            raise UserError(_("Please add Opportunity"))
        else:
            ''' PREPARE DICT FOR SENDING TO SALESFORCE '''
            sf_config = self.env.user.company_id
            quote_dict = {}
            quote_line_list=[]
            quote_line_dict ={}
            
            if self.opportunity_id and self.opportunity_id.x_salesforce_id_oppo:
                quote_dict['OpportunityId'] = str(self.opportunity_id.x_salesforce_id_oppo)
            elif self.opportunity_id and not self.opportunity_id.x_salesforce_id_oppo:
                opportunity_export = self.opportunity_id.exportOpportunity_to_sf()
                quote_dict['OpportunityId'] = str(self.opportunity_id.x_salesforce_id_oppo) 
            if self.contract_id and self.contract_id.x_salesforce_id:
                quote_dict['ContractId'] = self.contract_id.x_salesforce_id
            elif self.contract_id and not self.contract_id.x_salesforce_id:
                contract_export= self.contract_id.exportContract_to_sf()
                quote_dict['ContractId'] = self.contract_id.x_salesforce_id
            quote_dict['Status'] = 'Draft'
            ''' Create a entry in pricebook in salesforce'''
            if self.name:
                quote_dict['Name'] = self.name
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
                   quote_dict['Pricebook2Id'] = parsed_resp.get('records')[0].get('Id')
        
            result = self.sendQuoteDataToSf(quote_dict)
            line_sf_id=''
            if result:
                if self.order_line:
                    for line in self.order_line:
                        if line.x_salesforce_id:
                            if line.product_id and line.product_id.x_salesforce_id:
                                quote_line_dict={'Product2Id':line.product_id.x_salesforce_id,
                                'Quantity':line.product_uom_qty,'UnitPrice':line.price_unit,
                                'quoteId':self.x_salesforce_id,
                                }
                            elif line.product_id and not line.product_id.x_salesforce_id:
                                line.product_id.exportProduct_to_sf()
                                quote_line_dict={'Product2Id':line.product_id.x_salesforce_id,
                                'Quantity':line.product_uom_qty,'UnitPrice':line.price_unit,
                                'QuoteId':self.x_salesforce_id,
                                }
                            line_sf_id = line.x_salesforce_id
                            line_id = line.id
                        else:
                            if line.product_id and line.product_id.x_salesforce_id:
                                quote_line_dict={'Product2Id':line.product_id.x_salesforce_id,
                                'Quantity':line.product_uom_qty,'UnitPrice':line.price_unit,
                                'QuoteId':self.x_salesforce_id,
                                }
                            elif line.product_id and not line.product_id.x_salesforce_id:
                                line.product_id.exportProduct_to_sf()
                                quote_line_dict={'Product2Id':line.product_id.x_salesforce_id,
                                'Quantity':line.product_uom_qty,'UnitPrice':line.price_unit,
                                'QuoteId':self.x_salesforce_id,
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
                            quote_data = requests.request('GET',
                                                sf_config.sf_url + "/services/data/v40.0/query/?q=select Pricebook2Id from Quote where Id = '{}'".format(
                                                    self.x_salesforce_id), headers=headers)
                            if quote_data.text:
                                quote_data = json.loads(str(quote_data.text))
                                pricebook_id = quote_data.get('records')[0].get('Pricebook2Id')
                            PricebookEntryData = requests.request('GET',
                                                sf_config.sf_url + "/services/data/v40.0/query/?q=select Id,UnitPrice from PricebookEntry where  Pricebook2Id='{}'".format(
                                                    pricebook_id), headers=headers)
                            if PricebookEntryData.text:
                                pricebookentry_data = json.loads(str(PricebookEntryData.text))
                                for pricebook in pricebookentry_data.get('records'):
                                    line.product_id.x_salesforce_pbe = pricebook.get('Id')
                                quote_line_dict['PricebookEntryId']=line.product_id.x_salesforce_pbe                
                        if quote_line_dict:
                            result = self.sendQuoteLineDataToSf(quote_line_dict,line_sf_id,line_id)
                    self.x_salesforce_exported = True

    @api.model
    def _scheduler_export_quotes_to_sf(self):
        quotes = self.search([])
        for quote in quotes:
            try:
                quote.exportQuotations_to_sf()
            except Exception as e:
                _logger.error('Oops Some error in  exporting quotes to SALESFORCE %s', e)





    
