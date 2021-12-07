import json
import logging

import requests
from odoo import fields, api, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
_logger = logging.getLogger(__name__)


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    x_salesforce_exported = fields.Boolean('Exported To Salesforce', default=False,copy=False)
    x_salesforce_id = fields.Char('Salesforce Id',copy=False)
    x_is_updated = fields.Boolean('x_is_updated', default=False,copy=False)
    sf_status = fields.Selection([('open','Open - Not Contacted'),('working','Working - Contacted'),
                                  ('closed1','Closed - Converted'),('closed2','Closed - Not Converted')      ])

    def sendDataToSf(self, lead_dict):
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

            endpoint = '/services/data/v40.0/sobjects/Lead'

            payload = json.dumps(lead_dict)
            if self.x_salesforce_id:
                ''' Try Updating it if already exported '''
                res = requests.request('PATCH', sf_config.sf_url + endpoint + '/' + self.x_salesforce_id, headers=headers, data=payload)
                if res.status_code == 204:
                    self.x_is_updated = True
                    self.env.user.company_id.export_lead_lastmodifieddate = datetime.today()
            else:
                res = requests.request('POST', sf_config.sf_url + endpoint, headers=headers, data=payload)
                if res.status_code in [200, 201]:
                    parsed_resp = json.loads(str(res.text))
                    self.x_salesforce_exported = True
                    self.x_salesforce_id = parsed_resp.get('id')
                    self.env.user.company_id.export_lead_lastmodifieddate = datetime.today()
                    return parsed_resp.get('id')
                else:
                    return False


    def exportLead_to_sf(self):
        if len(self) > 1:
            raise UserError(_("Please Select 1 record to Export"))
        if not self.partner_name:
            raise UserError(_("Please add Company name"))
        if not self.contact_name or not self.title:
            raise UserError(_("Please add contact name and title"))
        if not self.sf_status:
            raise UserError(_("Please add SF Status"))
        ''' PREPARE DICT FOR SENDING TO SALESFORCE '''
        lead_dict = {}
        if self.name:
            lead_dict['LastName'] = self.name
        if self.partner_name:
            lead_dict['Company'] = self.partner_name
        if self.sf_status:
            lead_dict['Status'] =  dict(self._fields['sf_status'].selection).get(self.sf_status)
        if self.title:
            lead_dict['Salutation'] = self.title.name
        if self.name:
            lead_dict['LastName'] = self.name
        if self.phone:
            lead_dict['Phone'] = self.phone
        if self.mobile:
            lead_dict['MobilePhone'] = self.mobile
        if self.email_from:
            lead_dict['Email'] = self.email_from
        if self.website:
            lead_dict['Website'] = self.website
        if self.description:
            lead_dict['Description'] = self.description
        if self.street:
            lead_dict['Street'] = self.street
        if self.city:
            lead_dict['City'] = self.city
        if self.zip:
            lead_dict['PostalCode'] = self.zip
        if self.country_id:
            lead_dict['Country'] = self.country_id.name

        result = self.sendDataToSf(lead_dict)
        if result:
            self.x_salesforce_exported = True

    def exportLeadDatatosaleforce(self):
        if self.type == 'lead':
            self.exportLead_to_sf()
        elif self.type == 'opportunity':
            self.exportOpportunity_to_sf()

    @api.model
    def _scheduler_export_leads_to_sf(self):
        company_id = self.env.user.company_id
        if company_id:
            leads = self.search([('write_date', '>', company_id.export_lead_lastmodifieddate)])
            for lead in leads:
                try:
                    lead.exportLead_to_sf()
                except Exception as e:
                    _logger.error('Oops Some error in  exporting leads to SALESFORCE %s', e)
