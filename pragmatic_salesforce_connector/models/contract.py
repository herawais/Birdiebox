import json
import logging

import requests
from odoo import fields, api, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class SFContract(models.Model):
    _name = 'sf.contract'
    name = fields.Char('Name')
    contract_start_date = fields.Date('Contract Start Date')
    parent_id= fields.Many2one('res.partner','Company',domain="[('is_company', '=', True)]")
    contacr_term_month= fields.Integer('Contract Term (months)')
    state= fields.Selection([('draft', 'Draft'),('activated', 'Activated'),('approval','In Approval Process')])

    x_salesforce_exported = fields.Boolean('Exported To Salesforce', default=False,copy=False)
    x_salesforce_id = fields.Char('Salesforce Id',copy=False)
    x_is_updated = fields.Boolean('x_is_updated', default=False,copy=False)
    
    def sendDataToSf(self, contract_dict):
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

            endpoint = '/services/data/v40.0/sobjects/Contract'

            payload = json.dumps(contract_dict)
            if self.x_salesforce_id:
                ''' Try Updating it if already exported '''
                res = requests.request('PATCH', sf_config.sf_url + endpoint + '/' + self.x_salesforce_id, headers=headers, data=payload)
                if res.status_code == 204:
                    self.x_is_updated = True
                    self.env.user.company_id.export_contract_lastmodifieddate = datetime.today()


            else:
                res = requests.request('POST', sf_config.sf_url + endpoint, headers=headers, data=payload)
                if res.status_code in [200, 201]:
                    parsed_resp = json.loads(str(res.text))
                    self.x_salesforce_exported = True
                    self.x_salesforce_id = parsed_resp.get('id')
                    self.env.user.company_id.export_contract_lastmodifieddate = datetime.today()
                    return parsed_resp.get('id')
                else:
                    return False


    def exportContract_to_sf(self):
        if len(self) > 1:
            raise UserError(_("Please Select 1 record to Export"))

        ''' PREPARE DICT FOR SENDING TO SALESFORCE '''
        contract_dict = {}
        if self.contract_start_date:
            contract_dict['StartDate'] = str(self.contract_start_date)
        if self.parent_id:
            contract_dict['AccountId'] = str(self.parent_id.x_salesforce_id)
        if self.state:
            contract_dict['Status'] =  dict(self._fields['state'].selection).get(self.state) 
        if self.contacr_term_month:
            contract_dict['ContractTerm'] = self.contacr_term_month
        # if self.name:
        #     contract_dict['Contract_Name__c'] = self.name
        # if self.name:
        #     contract_dict['Contract_Type__c'] = 'Onsite Event'

        result = self.sendDataToSf(contract_dict)
        if result:
            self.x_salesforce_exported = True

    @api.model
    def _scheduler_export_contracts_to_sf(self):
        company_id = self.env.user.company_id
        if company_id:
            contracts = self.search([('write_date', '>', company_id.export_contract_lastmodifieddate)])
            for contract in contracts:
                try:
                    contract.exportContract_to_sf()
                except Exception as e:
                    _logger.error('Oops Some error in  exporting contracts to SALESFORCE %s', e)
