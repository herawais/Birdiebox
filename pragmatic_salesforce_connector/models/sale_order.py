from odoo import fields, models, api, _
from odoo.exceptions import UserError
import json
import requests
import logging

_logger = logging.getLogger(__name__)


class SaleOrderCust(models.Model):
    _inherit = 'sale.order'

    x_salesforce_id = fields.Char('Salesforce Id', copy=False)
    contract_id = fields.Many2one('sf.contract', string='Contract')
    x_salesforce_exported = fields.Boolean('Exported To Salesforce', default=False, copy=False)
    x_is_updated = fields.Boolean('x_is_updated', default=False, copy=False)
    x_salesforce_pbe = fields.Char('Salesforce pricelist', copy=False)

    custom_so_salesforce_id = fields.Char('Custom SO Salesforce Id', copy=False)
    custom_so_salesforce_exported = fields.Boolean('Custom SO Exported To Salesforce', default=False, copy=False)
    custom_so_is_updated = fields.Boolean('custom_so_is_updated', default=False, copy=False)
    custom_so_salesforce_pbe = fields.Char('Custom SO Salesforce pricelist', copy=False)

    package_salesforce_id = fields.Char('Package Salesforce Id', copy=False)
    package_salesforce_exported = fields.Boolean('Package Exported To Salesforce', default=False, copy=False)
    package_is_updated = fields.Boolean('package_is_updated', default=False, copy=False)

    @api.onchange('contract_id')
    def onchange_contract_id(self):
        if self.contract_id:
            if self.date_order.date() < self.contract_id.contract_start_date:
                raise UserError(
                    _("Order Start Date can't be earlier than the contract's start date.: Order Start Date."))
            if self.partner_id != self.contract_id.parent_id:
                raise UserError(_("Order customer and contract customer should be same"))

    def sendDataToSf(self, order_dict):
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

            endpoint = '/services/data/v40.0/sobjects/Order'

            payload = json.dumps(order_dict)
            if self.x_salesforce_id:
                ''' Try Updating it if already exported '''
                res = requests.request('PATCH', sf_config.sf_url + endpoint + '/' + self.x_salesforce_id,
                                       headers=headers, data=payload)
                if res.status_code in [200, 201, 204]:
                    self.x_is_updated = True
                    return self.x_salesforce_id

            else:
                res = requests.request('POST', sf_config.sf_url + endpoint, headers=headers, data=payload)
                if res.status_code in [200, 201, 204]:
                    parsed_resp = json.loads(str(res.text))
                    self.x_salesforce_exported = True
                    self.x_salesforce_id = parsed_resp.get('id')
                    return parsed_resp.get('id')
                else:
                    return False

    @api.model
    def _scheduler_export_orders_to_sf(self):
        orders = self.search([])
        for order in orders:
            try:
                order.exportSaleOrder_to_sf()
            except Exception as e:
                _logger.error('Oops Some error in  exporting orders to SALESFORCE %s', e)

    def exportToSalesForce(self):
        if self.state in ['draft', 'sent']:
            self.exportQuotations_to_sf()
        elif self.state in ['sale', 'done', 'cancel']:
            self.exportSaleOrder_to_sf()

    @api.model
    def _scheduler_export_custom_orders_to_sf(self):
        orders = self.sudo().search([])
        for order in orders:
            try:
                if order.state in ['sale', 'done', 'cancel', 'draft', 'sent']:
                    order.exportCustomSaleOrder_to_sf()
            except Exception as e:
                _logger.error('Oops Some error in  exporting custom orders to SALESFORCE %s', e)

    def exportCustomSaleOrder_to_sf(self):
        # print("\nIn exportCustomSaleOrder_to_sf Method")
        if len(self) > 1:
            raise UserError(_("Please Select 1 record to Export"))

        ''' PREPARE DICT FOR SENDING TO SALESFORCE '''
        sf_config = self.env.user.company_id
        order_dict = {}
        if not self.x_studio_related_sales_order and self.partner_id.is_company and self.partner_id.x_salesforce_id:
            order_dict['Account__c'] = str(self.partner_id.x_salesforce_id)
            if self.partner_invoice_id and self.partner_invoice_id.x_salesforce_id and not self.partner_invoice_id.is_company:
                order_dict['Contact__c'] = str(self.partner_invoice_id.x_salesforce_id)
            # if self.contract_id and self.contract_id.x_salesforce_id:
            #     order_dict['Contract__c'] = self.contract_id.x_salesforce_id
            # elif self.contract_id and not self.contract_id.x_salesforce_id:
            #     contract_export = self.contract_id.exportContract_to_sf()
            #     order_dict['Contract__c'] = self.contract_id.x_salesforce_id

            if self.name:
                order_dict['Odoo_Order_Number__c'] = self.name

            if self.x_studio_sample_order_type:
                order_dict['Sample_Order_Type__c'] = self.x_studio_sample_order_type

            if self.x_studio_type_of_order:
                order_dict['Type_of_Order__c'] = self.x_studio_type_of_order
            if self.commitment_date:
                order_dict['Date_In_Hand__c'] = str(self.commitment_date.date())
            if self.x_studio_letter_content_1:
                order_dict['Letter_Contents__c'] = self.x_studio_letter_content_1
            if self.x_studio_text_field_JLki5:
                order_dict['Notes__c'] = self.x_studio_text_field_JLki5
            for line in self.order_line:
                if line.product_id.type == 'service':
                    order_dict['Shipping_Price__c'] = line.price_unit
                    break

            ''' Create a entry in pricebook in salesforce'''
            result_so = self.sendCustomOrderDataToSf(order_dict)
            result_package = self.create_package_sf(self, result_so)
            result_so_line = self.create_send_orderitem_sf(result_package, result_so)

    def sendCustomOrderDataToSf(self, order_dict):
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

            endpoint = '/services/data/v40.0/sobjects/Order__c'

            if self.custom_so_salesforce_id:
                # print("\nOrder__c In if self.custom_so_salesforce_id ")
                ''' Try Updating it if already exported '''
                if order_dict.get('Account__c'):
                    del order_dict['Account__c']

                payload = json.dumps(order_dict)
                # print("\nIn update sendCustomOrderDataToSf self.x_salesforce_id: ", self.custom_so_salesforce_id,
                #       "\npayload: ", payload, "\nsf_config.sf_url + endpoint: ", sf_config.sf_url + endpoint,
                #       "\nheaders: ", headers)

                res = requests.request('PATCH', sf_config.sf_url + endpoint + '/' + self.custom_so_salesforce_id,
                                       headers=headers, data=payload)
                # print("\nUpdate res.text: ", res.text, "\nUpdate res.status_code: ", res.status_code)
                if res.status_code in [200, 201, 204]:
                    self.custom_so_is_updated = True
                    return self.custom_so_salesforce_id
                else:

                    log_message = self.env['sf.logging'].create_log_message(self,
                                                                            'Export Sale Order => ' + payload,
                                                                            res.text)

            else:
                # print("\nOrder__c  elseelse  if sf id not exists")
                payload = json.dumps(order_dict)

                res = requests.request('POST', sf_config.sf_url + endpoint, headers=headers, data=payload)

                if res.status_code in [200, 201, 204]:
                    parsed_resp = json.loads(str(res.text))
                    # print("\nOrder__c Create parsed_resp: ", parsed_resp)
                    self.custom_so_salesforce_exported = True
                    self.custom_so_salesforce_id = parsed_resp.get('id')
                    return parsed_resp.get('id')
                else:
                    log_message = self.env['sf.logging'].create_log_message(self,
                                                                            'Export Create Sale Order => ' + payload,
                                                                            res.text)

                    return False

    def create_package_sf(self, so_id, result):
        package_dict = {}
        # package_dict['Name'] = 'p-' + so_id.name
        if result:
            package_dict['Order__c'] = result
        package_dict['Number_Of_Boxes__c'] = 1
        package_dict['Box_Type__c'] = 'No Box'
        sf_config = self.env.user.company_id
        endpoint = None
        sf_access_token = None
        if sf_config.sf_access_token:
            sf_access_token = sf_config.sf_access_token
        if sf_access_token:
            headers = {}
            headers['Authorization'] = 'Bearer ' + str(sf_access_token)
            headers['Content-Type'] = 'application/json'
            headers['Accept'] = 'application/json'
            endpoint = '/services/data/v40.0/sobjects/Package__c'
            payload = json.dumps(package_dict)
            # print("\nIn create package self.package_salesforce_id: ", self.package_salesforce_id, "\npayload: ",
            #       payload, "\nsf_config.sf_url + endpoint: ", sf_config.sf_url + endpoint, "\nheaders: ", headers)
            if self.package_salesforce_id:

                return self.package_salesforce_id
            else:
                # print("\nPackage__c In if package sf id not exists")
                res = requests.request('POST', sf_config.sf_url + endpoint, headers=headers, data=payload)
                # print("\nPackage__c Create package res.text: ", res.text, "\nCreate package res.status_code: ",
                #       res.status_code)
                if res.status_code in [200, 201, 204]:
                    parsed_resp = json.loads(str(res.text))
                    # print("\nPackage__c Create package parsed_resp: ", parsed_resp)
                    self.package_salesforce_exported = True
                    self.package_salesforce_id = parsed_resp.get('id')
                    return parsed_resp.get('id')
                else:
                    log_message = self.env['sf.logging'].create_log_message(self,
                                                                            'Export Create Package__c => ' + payload,
                                                                            res.text)
                    return False

    def create_send_orderitem_sf(self, sf_package_id, sf_order_id):
        if self.order_line:
            i = 0

            for line in self.order_line:
                order_item_dict = {}
                line_sf_id = ''
                i = i + 1
                if line.custom_soline_salesforce_id or line.sale_order_line_updated:
                    if line.product_id and line.product_id.x_salesforce_id and line.product_id.type != 'service':
                        line.sale_order_line_updated = False
                        sf_config = self.env.user.company_id
                        endpoint = None
                        sf_access_token = None
                        if sf_config.sf_access_token:
                            sf_access_token = sf_config.sf_access_token
                        if sf_access_token:
                            headers = {}
                            payload = {}
                            headers['Authorization'] = 'Bearer ' + str(sf_access_token)
                            headers['Content-Type'] = 'application/json'
                            headers['Accept'] = 'application/json'
                            endpoint = '/services/data/v40.0/sobjects/Product2'
                            if line.product_id.x_salesforce_id:
                                ''' Try Updating it if already exported '''
                                prod_line_dict={'Price__c':line.price_unit}
                                payload = json.dumps(prod_line_dict)

                                res = requests.request('PATCH', sf_config.sf_url + endpoint + '/' + line.product_id.x_salesforce_id,
                                                       headers=headers,
                                                       data=payload)
                                if res.status_code in [200, 201, 204]:
                                    order_item_dict.update({'Product__c': line.product_id.x_salesforce_id,
                                                            'Quantity__c': line.product_uom_qty,
                                                            'Price__c': line.price_unit,
                                                            'Customization_Details__c': line.x_studio_customization_detail,
                                                            'Item_Notes__c': line.x_studio_customization_notes,
                                                            })
                                else:
                                    order_item_dict.update({'Product__c': line.product_id.x_salesforce_id,
                                                            'Quantity__c': line.product_uom_qty,
                                                            'Price__c': line.price_unit,
                                                            'Customization_Details__c': line.x_studio_customization_detail,
                                                            'Item_Notes__c': line.x_studio_customization_notes,
                                                            })
                        else:
                            order_item_dict.update({'Product__c': line.product_id.x_salesforce_id,
                                                    'Quantity__c': line.product_uom_qty,
                                                    'Price__c': line.price_unit,
                                                    'Customization_Details__c': line.x_studio_customization_detail,
                                                    'Item_Notes__c': line.x_studio_customization_notes,
                                                    })


                    elif line.product_id and not line.product_id.x_salesforce_id and line.product_id.type != 'service':
                        line.sale_order_line_updated = False
                        line.product_id.exportProduct_to_sf()
                        sf_config = self.env.user.company_id
                        endpoint = None
                        sf_access_token = None
                        if sf_config.sf_access_token:
                            sf_access_token = sf_config.sf_access_token
                        if sf_access_token:
                            headers = {}
                            payload = {}
                            headers['Authorization'] = 'Bearer ' + str(sf_access_token)
                            headers['Content-Type'] = 'application/json'
                            headers['Accept'] = 'application/json'
                            endpoint = '/services/data/v40.0/sobjects/Product2'
                            if line.product_id.x_salesforce_id:
                                ''' Try Updating it if already exported '''
                                prod_line_dict = {'Price__c': line.price_unit}
                                payload = json.dumps(prod_line_dict)

                                res = requests.request('PATCH',
                                                       sf_config.sf_url + endpoint + '/' + line.product_id.x_salesforce_id,
                                                       headers=headers,
                                                       data=payload)
                                if res.status_code in [200, 201, 204]:
                                    order_item_dict.update({'Product__c': line.product_id.x_salesforce_id,
                                                            'Quantity__c': line.product_uom_qty,
                                                            'Price__c': line.price_unit,
                                                            'Customization_Details__c': line.x_studio_customization_detail,
                                                            'Item_Notes__c': line.x_studio_customization_notes,
                                                            })
                                else:
                                    order_item_dict.update({'Product__c': line.product_id.x_salesforce_id,
                                                            'Quantity__c': line.product_uom_qty,
                                                            'Price__c': line.price_unit,
                                                            'Customization_Details__c': line.x_studio_customization_detail,
                                                            'Item_Notes__c': line.x_studio_customization_notes,
                                                            })
                        else:
                            order_item_dict.update({'Product__c': line.product_id.x_salesforce_id,
                                                    'Quantity__c': line.product_uom_qty,
                                                    'Price__c': line.price_unit,
                                                    'Customization_Details__c': line.x_studio_customization_detail,
                                                    'Item_Notes__c': line.x_studio_customization_notes,
                                                    })
                        # order_item_dict.update({'Product__c': line.product_id.x_salesforce_id,
                        #                         'Quantity__c': line.product_uom_qty, 'Price__c': line.price_unit,
                        #                         'Customization_Details__c': line.x_studio_customization_detail,
                        #                         'Item_Notes__c': line.x_studio_customization_notes,
                        #                         })
                    line_sf_id = line.custom_soline_salesforce_id
                    line_id = line.id

                else:
                    if line.product_id and line.product_id.x_salesforce_id and line.product_id.type != 'service':
                        # order_item_dict.update({'Product__c': line.product_id.x_salesforce_id,
                        #                         'Quantity__c': line.product_uom_qty, 'Price__c': line.price_unit,
                        #                         'Customization_Details__c': line.x_studio_customization_detail,
                        #                         'Item_Notes__c': line.x_studio_customization_notes,
                        #                         })
                        sf_config = self.env.user.company_id
                        endpoint = None
                        sf_access_token = None
                        if sf_config.sf_access_token:
                            sf_access_token = sf_config.sf_access_token
                        if sf_access_token:
                            headers = {}
                            payload = {}
                            headers['Authorization'] = 'Bearer ' + str(sf_access_token)
                            headers['Content-Type'] = 'application/json'
                            headers['Accept'] = 'application/json'
                            endpoint = '/services/data/v40.0/sobjects/Product2'
                            if line.product_id.x_salesforce_id:
                                ''' Try Updating it if already exported '''
                                prod_line_dict = {'Price__c': line.price_unit}
                                payload = json.dumps(prod_line_dict)

                                res = requests.request('PATCH',
                                                       sf_config.sf_url + endpoint + '/' + line.product_id.x_salesforce_id,
                                                       headers=headers,
                                                       data=payload)
                                if res.status_code in [200, 201, 204]:
                                    order_item_dict.update({'Product__c': line.product_id.x_salesforce_id,
                                                            'Quantity__c': line.product_uom_qty,
                                                            'Price__c': line.price_unit,
                                                            'Customization_Details__c': line.x_studio_customization_detail,
                                                            'Item_Notes__c': line.x_studio_customization_notes,
                                                            })
                                else:
                                    order_item_dict.update({'Product__c': line.product_id.x_salesforce_id,
                                                            'Quantity__c': line.product_uom_qty,
                                                            'Price__c': line.price_unit,
                                                            'Customization_Details__c': line.x_studio_customization_detail,
                                                            'Item_Notes__c': line.x_studio_customization_notes,
                                                            })
                        else:
                            order_item_dict.update({'Product__c': line.product_id.x_salesforce_id,
                                                    'Quantity__c': line.product_uom_qty,
                                                    'Price__c': line.price_unit,
                                                    'Customization_Details__c': line.x_studio_customization_detail,
                                                    'Item_Notes__c': line.x_studio_customization_notes,
                                                    })
                    elif line.product_id and not line.product_id.x_salesforce_id and line.product_id.type != 'service':
                        line.product_id.exportProduct_to_sf()
                        sf_config = self.env.user.company_id
                        endpoint = None
                        sf_access_token = None
                        if sf_config.sf_access_token:
                            sf_access_token = sf_config.sf_access_token
                        if sf_access_token:
                            headers = {}
                            payload = {}
                            headers['Authorization'] = 'Bearer ' + str(sf_access_token)
                            headers['Content-Type'] = 'application/json'
                            headers['Accept'] = 'application/json'
                            endpoint = '/services/data/v40.0/sobjects/Product2'
                            if line.product_id.x_salesforce_id:
                                ''' Try Updating it if already exported '''
                                prod_line_dict = {'Price__c': line.price_unit}
                                payload = json.dumps(prod_line_dict)

                                res = requests.request('PATCH',
                                                       sf_config.sf_url + endpoint + '/' + line.product_id.x_salesforce_id,
                                                       headers=headers,
                                                       data=payload)
                                if res.status_code in [200, 201, 204]:
                                    order_item_dict.update({'Product__c': line.product_id.x_salesforce_id,
                                                            'Quantity__c': line.product_uom_qty,
                                                            'Price__c': line.price_unit,
                                                            'Customization_Details__c': line.x_studio_customization_detail,
                                                            'Item_Notes__c': line.x_studio_customization_notes,
                                                            })
                                else:
                                    order_item_dict.update({'Product__c': line.product_id.x_salesforce_id,
                                                            'Quantity__c': line.product_uom_qty,
                                                            'Price__c': line.price_unit,
                                                            'Customization_Details__c': line.x_studio_customization_detail,
                                                            'Item_Notes__c': line.x_studio_customization_notes,
                                                            })
                        else:
                            order_item_dict.update({'Product__c': line.product_id.x_salesforce_id,
                                                    'Quantity__c': line.product_uom_qty,
                                                    'Price__c': line.price_unit,
                                                    'Customization_Details__c': line.x_studio_customization_detail,
                                                    'Item_Notes__c': line.x_studio_customization_notes,
                                                    })
                        #
                        # order_item_dict.update({'Product__c': line.product_id.x_salesforce_id,
                        #                         'Quantity__c': line.product_uom_qty, 'Price__c': line.price_unit,
                        #                         'Customization_Details__c': line.x_studio_customization_detail,
                        #                         'Item_Notes__c': line.x_studio_customization_notes,
                        #                         })
                    line_id = line.id

                if order_item_dict:
                    order_item_dict['Package__c'] = sf_package_id
                    order_item_dict['Place_Order_Without_Inventory__c'] = True
                    sf_order_item_id = self.send_orderitem_sf(order_item_dict, line_sf_id, line_id)

    def send_orderitem_sf(self, order_line_dict, line_sf_id, line_id):
        sf_config = self.env.user.company_id
        endpoint = None
        sf_access_token = None
        if sf_config.sf_access_token:
            sf_access_token = sf_config.sf_access_token
        if sf_access_token:
            headers = {}
            payload = {}
            headers['Authorization'] = 'Bearer ' + str(sf_access_token)
            headers['Content-Type'] = 'application/json'
            headers['Accept'] = 'application/json'
            endpoint = '/services/data/v40.0/sobjects/Order_Item__c'
            if line_sf_id:
                ''' Try Updating it if already exported '''
                if order_line_dict.get('Package__c'):
                    del order_line_dict['Package__c']
                payload = json.dumps(order_line_dict)

                res = requests.request('PATCH', sf_config.sf_url + endpoint + '/' + line_sf_id, headers=headers,
                                       data=payload)
                if res.status_code in [200, 201, 204]:
                    order_line = self.env['sale.order.line'].search([('id', '=', line_id)])
                    order_line.custom_soline_is_updated = True
                else:
                    log_message = self.env['sf.logging'].create_log_message(str(line_id) + ' = ' + line_sf_id,
                                                                            'Export Update OrderItem => ' + payload,
                                                                            res.text)

            else:
                payload = json.dumps(order_line_dict)

                res = requests.request('POST', sf_config.sf_url + endpoint, headers=headers, data=payload)

                if res.status_code in [200, 201, 204]:
                    parsed_resp = json.loads(str(res.text))
                    order_line = self.env['sale.order.line'].search([('id', '=', line_id)])
                    order_line.custom_soline_salesforce_exported = True
                    order_line.custom_soline_salesforce_id = parsed_resp.get('id')
                    return parsed_resp.get('id')
                else:
                    log_message = self.env['sf.logging'].create_log_message(line_id,
                                                                            'Export Create OrderItem => ' + payload,
                                                                            res.text)
                    return False


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_salesforce_id = fields.Char('Salesforce Id', copy=False)
    x_salesforce_exported = fields.Boolean('Exported To Salesforce', default=False, copy=False)
    x_is_updated = fields.Boolean('x_is_updated', default=False, copy=False)

    custom_soline_salesforce_id = fields.Char('Custom SO Salesforce Id', copy=False)
    custom_soline_salesforce_exported = fields.Boolean('Custom SO Exported To Salesforce', default=False, copy=False)
    custom_soline_is_updated = fields.Boolean('custom_so_is_updated', default=False, copy=False)
    sale_order_line_updated = fields.Boolean('Sale order is updated', default=False)

    def write(self, vals):
        if self.custom_soline_salesforce_id:
            vals['sale_order_line_updated'] = True
        return super(SaleOrderLine, self).write(vals)

    def unlink(self):
        sf_config = self.env.user.company_id
        if sf_config.sf_access_token:
            sf_access_token = sf_config.sf_access_token

            if sf_access_token:
                headers = {}
                headers['Authorization'] = 'Bearer ' + str(sf_access_token)
                headers['Content-Type'] = 'application/json'
                headers['Accept'] = 'application/json'

            for record in self:
                if (record.x_salesforce_id or record.custom_soline_salesforce_id):

                    endpoint = "/services/data/v52.0/sobjects/Order_Item__c/" + str(
                        record.custom_soline_salesforce_id)
                    res = requests.request('DELETE', sf_config.sf_url + endpoint, headers=headers)
                    if res.status_code == 200 or res.status_code == 201 or res.status_code == 204:
                        _logger.info('Order Line is deleted from SALESFORCE===========================')
        return super(SaleOrderLine, self).unlink()
