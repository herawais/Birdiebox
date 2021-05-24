import json
import logging

import requests
from odoo import fields, api, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CRMOpportunity(models.Model):
    _inherit = 'crm.lead'

    x_salesforce_exported_oppo = fields.Boolean('Exported To Salesforce', default=False,copy=False)
    x_salesforce_id_oppo = fields.Char('Salesforce Id',copy=False)
    x_is_updated_oppo = fields.Boolean('x_is_updated', default=False,copy=False)
    sf_status_oppo = fields.Selection([('open','Open - Not Contacted'),('working','Working - Contacted'),
                                  ('closed1','Closed - Converted'),('closed2','Closed - Not Converted')      ])

    def sendOpportunityDataToSf(self, opportunity_dict):
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
            endpoint = '/services/data/v40.0/sobjects/Opportunity'
            payload = json.dumps(opportunity_dict)
            if self.x_salesforce_id_oppo:
                ''' Try Updating it if already exported '''
                res = requests.request('PATCH', sf_config.sf_url + endpoint + '/' + self.x_salesforce_id_oppo, headers=headers, data=payload)
                if res.status_code == 204:
                    self.x_is_updated_oppo = True
            else:
                res = requests.request('POST', sf_config.sf_url + endpoint, headers=headers, data=payload)
                if res.status_code in [200, 201]:
                    parsed_resp = json.loads(str(res.text))
                    self.x_salesforce_exported_oppo = True
                    self.x_salesforce_id_oppo = parsed_resp.get('id')
                    return parsed_resp.get('id')
                else:
                    return False


    def exportOpportunity_to_sf(self):
        if len(self) > 1:
            raise UserError(_("Please Select 1 record to Export"))
        if not self.date_deadline:
            raise UserError(_("Please add Expected Closing date"))
        ''' PREPARE DICT FOR SENDING TO SALESFORCE '''
        opportunity_dict = {}
        if self.name:
            opportunity_dict['Name'] = self.name
        if self.date_deadline:
            opportunity_dict['CloseDate'] = str(self.date_deadline)
        if self.stage_id:
            opportunity_dict['StageName'] =  self.stage_id.name
        result = self.sendOpportunityDataToSf(opportunity_dict)
        if result:
            self.x_salesforce_exported_oppo = True

    @api.model
    def _scheduler_export_opportunity_to_sf(self):
        opportunities = self.search([])
        for opportunity in opportunities:
            try:
                opportunity.exportOpportunity_to_sf()
            except Exception as e:
                _logger.error('Oops Some error in  exporting Opportunity to SALESFORCE %s', e)
