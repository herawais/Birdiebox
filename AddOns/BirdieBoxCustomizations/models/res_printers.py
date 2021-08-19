# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
import requests
import datetime
import jwt
import time
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)



class ResPrinters(models.Model):
    _name = 'res.printers'
    _description = "Printer"

    settings_id = fields.Many2one(
        comodel_name="res.printer.settings",
        string="Configuration",
        ondelete='set null'
    )

    printer_id = fields.Integer(
        "Printer ID"
    )

    type = fields.Char(
        "Type"
    )

    name = fields.Char(
        "Name"
    )

class BohmPrinterSettings(models.Model):
    _name = 'res.printer.settings'
    _description = "Printer Settings"

    name = fields.Char(
        'Name',
        default="Printer Settings"
    )

    printer_service_base_url = fields.Char(
        'Printer Service URL',
        default="https://stapi.bohmtech.com/stapi/v1/"
    )

    printer_service_jwt_secret = fields.Char(
        'Secret Key',
        default="secretkeythatlocksthejsonwebtoken"
    )

    printer_ids = fields.One2many(
        comodel_name="res.printers",
        inverse_name="settings_id",
        string="Printers",
        ondelete='set null'
    )

    def action_refresh_printers(self):
        try:
            url = self.printer_service_base_url + "printers"
            _logger.debug("**** PRINT SERVICE URL :: %s", url)

            exp = (datetime.datetime.now() + datetime.timedelta(minutes=15))

            encoded_jwt = jwt.encode({
                "bindle": {
                    "purpose": "refresh the printers",
                    "source": "Odoo"
                },
                "iat": datetime.datetime.now(),
                "exp": time.mktime(exp.timetuple())
            },
                self.printer_service_jwt_secret,
                algorithm="HS256"
            )

            response = requests.get(
                url,
                timeout=10,
                headers={
                    "Authorization": "Bearer " + encoded_jwt.decode("utf-8"),
                    "Content-Type": "application/json"
                }
            )

            if not response.status_code != 200:
                raise ValidationError('Could not connect to print server.')

            current_printers = self.env["res.printers"].search([
                ("type", "!=", False)
            ])

            for printer in current_printers:
                printer.unlink()

            for printer in response.json()["data"]:
                printer_id = self.env["res.printers"].search([
                    ("name", "=", printer["name"])
                ])

                if not printer_id:
                    self.env["res.printers"].create({
                        "name": printer["name"],
                        "type": printer["type"],
                        "printer_id": printer["id"],
                        "settings_id": self.id
                    })
                else:
                    printer_id.write({
                        "type": printer["type"],
                        "printer_id": printer["id"],
                        "settings_id": self.id
                    })

            if response.status_code != 200:
                raise Exception("Error getting printer list")
        except Exception as error:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(error).__name__, error.args)
            _logger.error(message)
