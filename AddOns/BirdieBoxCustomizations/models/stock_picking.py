# -*- coding: utf-8 -*-
import logging
import requests
import datetime
import jwt
import time
import json

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CustomStockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super(CustomStockPicking, self).button_validate()

        if self.picking_type_id.x_require_pickings_complete:
            self.validate_kitting()

        if self.picking_type_id.x_print_shipping_label and self.carrier_id:
            self.print_shipping_label()

        if self.picking_type_id.x_validate_carrier:
            self.validate_carrier()

        return res

    def write(self, vals):
        if 'date_done' in vals and self.picking_type_id.id == 2:
            self.update_delivered_qty()

        return super(CustomStockPicking, self).write(vals)

    def validate_kitting(self):
        for record in self:
            pickings = record.sale_id.picking_ids.filtered(
                lambda x: x.picking_type_id.id not in [12, 2] and x.state
                not in ['done', 'cancel'])
            incomplete = ''
            if len(pickings) > 0:
                for picking in pickings:
                    incomplete += '\n -' + picking.name

                raise ValidationError(
                    'You cannot complete kitting until the following operations have been completed: \n'
                    + incomplete)

    
    def validate_carrier(self):
        if self.sale_id.carrier_id:
            if self.carrier_id != self.sale_id.carrier_id and self.sale_id.carrier_id.id != 4:
                    raise ValidationError(
                        'Please confirm that the shipping carrier matches the sale order.'
                    )


    def update_delivered_qty(self):
        parent_sale_order = self.sale_id.x_studio_related_sales_order

        if parent_sale_order:
            for product in parent_sale_order.order_line:
                for line in self.move_line_ids:
                    if line.product_id == product.product_id:
                        product.qty_delivered = line.qty_done + product.qty_delivered

    def print_shipping_label(self):
        self.ensure_one()
        print_service = self.env['res.printer.settings'].search([], limit=1)
        printer_pref = self.env["res.users"].search(
            [("id", "=", self.env.context.get("uid"))], limit=1)

        if not print_service:
            raise ValidationError(
                'The print service has not been configured, Please contact an administrator.'
            )

        if printer_pref.x_default_packing_printer:
            printer = printer_pref.x_default_packing_printer.name
        else:
            raise ValidationError(
                'Please set a printer in your user settings.')

        shipping_labels = self._get_shipping_label()

        payload = {"shipping_labels": shipping_labels, "printer": printer}

        exp = (datetime.datetime.now() + datetime.timedelta(minutes=15))

        encoded_jwt = jwt.encode(
            {
                "bindle": {
                    "purpose": "print shipping label",
                    "source": "Odoo"
                },
                "iat": datetime.datetime.now(),
                "exp": time.mktime(exp.timetuple())
            },
            print_service.printer_service_jwt_secret,
            algorithm="HS256")

        url = print_service.printer_service_base_url + "print/" + \
                printer + "/shipping_label"

        response = requests.post(url,
                                 timeout=10,
                                 headers={
                                     "Authorization":
                                     "Bearer " + encoded_jwt.decode("utf-8"),
                                     "Content-Type":
                                     "application/json"
                                 },
                                 data=json.dumps(payload))

    def _get_shipping_label(self):
        self.ensure_one()
        attachments = []

        for message_id in self.message_ids:
            if len(message_id.attachment_ids) > 0:
                for attachment_id in message_id.attachment_ids:
                    try:
                        attachments.append({
                            "name":
                            attachment_id.name or "",
                            "img_type":
                            attachment_id.name.split(".")[-1] or "",
                            "img":
                            attachment_id.datas.decode("utf-8") or ""
                        })
                    except Exception as e:
                        raise ValidationError(
                            'Unable To Generate Label \n- %s', e)

        return attachments