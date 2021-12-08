# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class BulkSale(models.Model):
    _name = 'bulk.sale'
    _description = 'Bulk Sales Import'

    name = fields.Char(string="Name", required=True)
    street = fields.Char(string="Street", required=True)
    street2 = fields.Char(string="Street 2")
    zip = fields.Char(string="Zip", required=True)
    city = fields.Char(string="City", required=True)
    state = fields.Char(string="State", required=True)
    country = fields.Char(string="Country", required=True)
    email = fields.Char(string="E-Mail")
    phone = fields.Char(string="Phone")
    initials = fields.Char(string="Initials")
    box_name = fields.Char(string="Box Name")
    monogram = fields.Char(string="Monogram")
    parent_sale_order = fields.Char(string="Parent Sale Order", required=True)
    sale_order_created = fields.Boolean(string="Sale Order Created?",
                                        readonly=True)
    created_sale_order = fields.Many2one('sale.order',
                                         string="Created Sale Order",
                                         ondelete='set null',
                                         readonly=True)
    state_id = fields.Many2one("res.country.state",
                               string='State ID',
                               ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]",
                               readonly=True)
    country_id = fields.Many2one('res.country',
                                 string='Country ID',
                                 ondelete='restrict',
                                 readonly=True)
    parent_sale_order_id = fields.Many2one('sale.order',
                                           string="Parent Sale Order ID",
                                           ondelete='restrict',
                                           readonly=True)

    def create_partner(self):
        COUNTRY = self.env['res.country']
        STATE = self.env['res.country.state']
        PARTNER = self.env['res.partner']

        search_partner = PARTNER.search([('name', '=', self.name),
                                         ('street', '=', self.street),
                                         ('zip', '=', self.zip)],
                                        limit=1)
        if search_partner:
            partner = search_partner
        else:
            if self.country.upper() in ['US', 'USA']:
                self.country = 'United States'
            country = COUNTRY.search([
                '|', ('name', 'ilike', self.country),
                ('code', 'ilike', self.country)
            ],
                                     limit=1)
            #
            if not country:
                raise ValidationError(
                    'The entered country could not be found for ' + self.name +
                    '.')
            else:
                self.country_id = country

            if self.state.upper() == 'VIRGINIA':
                self.state = 'VA'

            state = STATE.search([
                '|', ('name', '=', self.state), ('code', '=', self.state),
                ('country_id', '=', country.id),('create_uid', '=', 1)
            ])

            if len(state) > 1:
                raise ValidationError(
                    'Found multiple matches for state for ' + self.name +
                    '. Try using the the state code instead. EX: TX, FL, NY')

            if not state:
                raise ValidationError(
                    'The entered state could not be found for ' + self.name +
                    '.')
            else:
                self.state_id = state

            partner_body = {
                "name": self.name,
                "street": self.street,
                "street2": self.street2,
                "city": self.city,
                "zip": self.zip,
                "country_id": country.id,
                "state_id": state.id,
                "email": self.email,
                "phone": self.phone,
                "type": "delivery",
                "parent_id": self.parent_sale_order_id.partner_id.id,
                "property_account_receivable_id": 2,
                "property_account_payable_id": 1
            }

            partner = PARTNER.create(partner_body)

        return partner

    def create_child_sale_order(self, create_order_lines=False):
        SALE = self.env['sale.order']
        for record in self:
            has_intials = False
            has_box_name = False
            has_monogram = False
            if record.created_sale_order:
                return

            if not record.parent_sale_order_id:
                parent_order = SALE.search(
                    [('name', 'ilike', record.parent_sale_order)], limit=1)
                if not parent_order:
                    raise ValidationError(
                        'The parent sales order could not be found for ' +
                        record.name + '.')
                else:
                    record.parent_sale_order_id = parent_order

            for line in create_order_lines:
                if not line.x_studio_customization_notes:
                    if line.x_studio_customization_detail == 'Initial':
                        if not record.initials:
                            raise ValidationError(
                                line.x_studio_customization_detail +
                                ' selected but no "Initials" were imported for '
                                + record.name + '.')
                        else:
                            has_intials = True
                            line.x_studio_customization_notes = record.initials
                    elif line.x_studio_customization_detail in [
                            'Full Name', 'Logo and Name'
                    ]:
                        if not record.box_name:
                            raise ValidationError(
                                line.x_studio_customization_detail +
                                ' selected but no "Box Name" imported for ' +
                                record.name + '.')
                        else:
                            has_box_name = True
                            line.x_studio_customization_notes = record.box_name
                    elif line.x_studio_customization_detail == 'First Letter and Name':
                        if not record.monogram:
                            raise ValidationError(
                                line.x_studio_customization_detail +
                                ' selected but no "Monogram" imported for ' +
                                record.name + '.')
                        else:
                            has_monogram = True
                            line.x_studio_customization_notes = record.monogram

            partner = record.create_partner()
            so = record.parent_sale_order_id
            order_lines = []

            if create_order_lines:
                for line in create_order_lines:
                    order_lines.append((0, 0, {
                        "product_id": line.product_id.id,
                        "name": line.name,
                        "x_studio_customization_detail":
                        line.x_studio_customization_detail,
                        "x_studio_customization_notes":
                        line.x_studio_customization_notes,
                        "price_unit": line.price_unit,
                        "route_id": line.route_id.id,
                        "tax_id": line.tax_id.id,
                        "product_uom_qty": line.product_uom_qty
                    }))

            else:
                for line in so.order_line:
                    order_lines.append((0, 0, {
                        "product_id": line.product_id.id,
                        "name": line.name,
                        "x_studio_customization_detail":
                        line.x_studio_customization_detail,
                        "x_studio_customization_notes":
                        line.x_studio_customization_notes,
                        "price_unit": line.price_unit,
                        "tax_id": line.tax_id,
                        "product_uom_qty": 1.0
                    }))

            sale_order_body = {
                "company_id": so.company_id.id,
                "warehouse_id": so.warehouse_id.id,
                "pricelist_id": so.pricelist_id.id,
                "picking_policy": so.picking_policy,
                "partner_invoice_id": so.partner_id.id,
                "partner_shipping_id": partner.id,
                "partner_id": partner.id,
                "date_order": so.date_order,
                "team_id": so.team_id.id,
                "carrier_id": so.carrier_id.id,
                "commitment_date": so.commitment_date,
                "x_studio_google_drive_link": so.x_studio_google_drive_link,
                "x_studio_kitting": so.x_studio_kitting,
                "x_studio_letter_content_1": so.x_studio_letter_content_1,
                "x_studio_related_sales_order": so.id,
                "x_studio_shipping_type": so.x_studio_shipping_type,
                "x_studio_text_field_JLki5": so.x_studio_text_field_JLki5,
                "x_studio_type_of_order": so.x_studio_type_of_order,
                "x_studio_in_hand_date_flexibility": so.x_studio_in_hand_date_flexibility,
                "order_line": order_lines
            }

            created_sale = SALE.create(sale_order_body)

            record.created_sale_order = created_sale

            created_sale.action_confirm()

            record.sale_order_created = True

            for line in create_order_lines:
                if line.x_studio_customization_detail == 'Initial' and has_intials:
                    line.x_studio_customization_notes = False
                elif line.x_studio_customization_detail in [
                    'Full Name', 'Logo and Name'
                ] and has_box_name:
                    line.x_studio_customization_notes = False
                elif line.x_studio_customization_detail == 'First Letter and Name' and has_monogram:
                    line.x_studio_customization_notes = False