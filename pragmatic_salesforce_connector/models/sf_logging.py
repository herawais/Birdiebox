from odoo import fields, models
from datetime import datetime, timedelta


class SfLogging(models.Model):
    _name = "sf.logging"
    _order = "id desc"
    _description = "Salesforce Logging"

    error_message = fields.Text("Log Info")
    message_log = fields.Text("SF Log Message")
    creation_date = fields.Datetime("Creation Date",
                                    default=fields.Datetime.now)
    debug_logs = fields.Boolean("Odoo Debug Logs", default=False)
    name = fields.Char("Odoo Logger")


    def create_log_message(self, error_message, message, name, is_debug=False):
        if error_message and message:
            ###### 'is_debug = True' is used for developer debugging ############
            if is_debug == True:
                res = self.create(
                    {'error_message': error_message,
                     'message_log': message,
                     'name': name,
                     'debug_logs': True})
                self._cr.commit()

            else:
                ###### Client logs ##########
                res = self.create(
                    {'error_message': error_message,
                     'message_log': message,
                     'name': name
                     })
                self._cr.commit()

            return True

    '''
        Method used for getting Client Details using the client id
    '''

    def _scheduler_delete_vital_logger(self, max_age_days=30):
        modified_date = fields.Datetime.now() + timedelta(days=-max_age_days)
        vital_log_id = self.search([('creation_date', '<', modified_date)])
        return vital_log_id.unlink()

