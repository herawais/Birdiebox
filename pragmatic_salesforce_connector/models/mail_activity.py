import json
import logging

import requests
from odoo import fields, api, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    x_salesforce_exported = fields.Boolean('Exported To Salesforce', default=False,copy=False)
    x_salesforce_id = fields.Char('Salesforce Id',copy=False)
    x_is_updated = fields.Boolean('x_is_updated', default=False,copy=False)
    sf_status = fields.Selection([('not_started','Not Started'),('in_progress','In Progress'),
                                  ('completed','Completed'),('waiting','Waiting for someone else'),('deferred','Deferred')])
    priority = fields.Selection([('high','High'),('normal','Normal'),
                                  ('low','Low'),])
    parent_id= fields.Many2one('res.partner','Company',domain="[('is_company', '=', True)]")


    def sendDataToSf(self, activity_dict):
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
            endpoint = '/services/data/v40.0/sobjects/Task'
            payload = json.dumps(activity_dict)
            if self.x_salesforce_id:
                ''' Try Updating it if already exported '''
                res = requests.request('PATCH', sf_config.sf_url + endpoint + '/' + self.x_salesforce_id, headers=headers, data=payload)
                if res.status_code == 204:
                    self.x_is_updated = True
                    self.env.user.company_id.export_task_lastmodifieddate = datetime.today()
            else:
                res = requests.request('POST', sf_config.sf_url + endpoint, headers=headers, data=payload)
                if res.status_code in [200, 201]:
                    parsed_resp = json.loads(str(res.text))
                    self.x_salesforce_exported = True
                    self.x_salesforce_id = parsed_resp.get('id')
                    self.env.user.company_id.export_task_lastmodifieddate = datetime.today()
                    return parsed_resp.get('id')
                else:
                    return False


    def exportActivity_to_sf(self):
        if len(self) > 1:
            raise UserError(_("Please Select 1 record to Export"))

        ''' PREPARE DICT FOR SENDING TO SALESFORCE '''
        activity_dict = {}
        if self.request_partner_id:
            activity_dict['WhoId'] = self.request_partner_id.x_salesforce_id
        if self.parent_id:
            activity_dict['WhatId'] = self.parent_id.x_salesforce_id
        if self.summary:
            activity_dict['Subject'] = self.summary
        if self.sf_status:
            activity_dict['Status'] =  dict(self._fields['sf_status'].selection).get(self.sf_status) 
        if self.sf_status:
            activity_dict['Priority'] =  dict(self._fields['priority'].selection).get(self.priority) 
        if self.date_deadline:
            activity_dict['ActivityDate'] = str(self.date_deadline)
        activity_dict['Priority'] = 'Normal'
        result = self.sendDataToSf(activity_dict)
        if result:
            self.x_salesforce_exported = True

    @api.model
    def _scheduler_export_activity_to_sf(self):
        company_id = self.env.user.company_id
        if company_id:
            activities = self.search([('write_date', '>', company_id.export_task_lastmodifieddate)])
            for activity in activities:
                try:
                    activity.exportActivity_to_sf()
                except Exception as e:
                    _logger.error('Oops Some error in  exporting Activity to SALESFORCE %s', e)
