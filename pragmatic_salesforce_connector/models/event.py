import json
import logging

import requests
from odoo import fields, api, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    x_salesforce_exported = fields.Boolean('Exported To Salesforce', default=False,copy=False)
    x_salesforce_id = fields.Char('Salesforce Id',copy=False)
    x_is_updated = fields.Boolean('x_is_updated', default=False,copy=False)
    
    def sendDataToSf(self, event_dict):
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
            endpoint = '/services/data/v40.0/sobjects/Event__c'
            payload = json.dumps(event_dict)
            if self.x_salesforce_id:
                ''' Try Updating it if already exported '''
                res = requests.request('PATCH', sf_config.sf_url + endpoint + '/' + self.x_salesforce_id, headers=headers, data=payload)
                if res.status_code == 204:
                    self.x_is_updated = True

            else:
                res = requests.request('POST', sf_config.sf_url + endpoint, headers=headers, data=payload)
                if res.status_code in [200, 201]:
                    parsed_resp = json.loads(str(res.text))
                    self.x_salesforce_exported = True
                    self.x_salesforce_id = parsed_resp.get('id')
                    return parsed_resp.get('id')
                else:
                    return False


    def exportCalendarEvent_to_sf(self):
        if len(self) > 1:
            raise UserError(_("Please Select 1 record to Export"))

        ''' PREPARE DICT FOR SENDING TO SALESFORCE '''
        event_dict = {}
        if self.name:
            event_dict['Name'] = self.name
        if self.start:
            event_dict['Event_Start_Date__c'] = str(self.start.date())
        result = self.sendDataToSf(event_dict)
        if result:
            self.x_salesforce_exported = True

    @api.model
    def _scheduler_export_event_to_sf(self):
        events = self.search([])
        for event in events:
            try:
                event.exportCalendarEvent_to_sf()
            except Exception as e:
                _logger.error('Oops Some error in  exporting events to SALESFORCE %s', e)
