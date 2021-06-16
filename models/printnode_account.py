# Copyright 2019 VentorTech OU
# License OPL-1.0 or later.

import re
import requests

from odoo import models, fields, api


class PrintNodeAccount(models.Model):
    """ PrintNode Account entity
    """
    _name = 'printnode.account'
    _description = 'PrintNode Account'

    alias = fields.Char(
        string='Alias'
    )

    computer_ids = fields.One2many(
        'printnode.computer', 'account_id',
        string='Computers'
    )

    endpoint = fields.Char(
        string='Endpoint',
        required=True,
        readonly=True,
        default='https://api.printnode.com/'
    )

    limits = fields.Integer(
        string='Plan Page Limits',
        readonly=True,
    )

    name = fields.Char(
        string='Name',
        default="Default Account",
    )

    password = fields.Char(
        string='Password',
        required=False
    )

    printed = fields.Integer(
        string='Printed Pages',
        readonly=True,
    )

    printnode_id = fields.Integer('Printnode ID')

    status = fields.Char(
        string='Status',
        compute='_compute_account_status',
        store=True,
        readonly=True
    )

    username = fields.Char(
        string='API Key',
        required=True
    )

    _sql_constraints = [
        ('printnode_id', 'unique(printnode_id)', 'Account already exists.'),
        ('username', 'unique(username)', 'Username (token) must be unique.'),
    ]

    @api.model
    def create(self, vals):
        account = super(PrintNodeAccount, self).create(vals)
        account.import_printers()

        return account

    @api.model
    def get_limits(self):
        limits = []
        for rec in self.env['printnode.account'].search([]):
            if rec.status == 'OK':
                limits.append({
                    'account': rec.name or rec.username[:10] + '...',
                    'printed': rec.printed,
                    'limits': rec.limits,
                })
            else:
                limits.append({
                    'account': rec.name or rec.username[:10] + '...',
                    'error': rec.status,
                })
        return limits

    def import_printers(self):
        """ Re-import list of printers into OpenERP.
        """
        for printer in self._get_printnode_response('printers'):
            c = self._get_node('computer', printer['computer'], self.id)
            _ = self._get_node('printer', printer, c.id)  # NOQA

    def recheck_printer(self, printer, print_sample_report=False):
        """ Re-check particular printer status
        """
        uri = 'printers/{}'.format(printer.printnode_id)

        resp = self._get_printnode_response(uri)
        printer.write({
            'status': resp
                and resp[0]['computer']['state'] == 'connected'  # NOQA
                and resp[0]['state']  # NOQA
                or 'offline'  # NOQA
        })

        return printer.online

    def unlink(self):
        for account in self:
            account.unlink_devices()
        return super(PrintNodeAccount, self).unlink()

    def unlink_devices(self):
        """ delete computers, printers, print jobs and user rules
        """

        for computer in self.computer_ids:
            for rule in self.env['printnode.rule'].search([
                ('printer_id', 'in', computer.printer_ids.ids),
            ]):
                rule.unlink()
            for printer in computer.printer_ids:
                for job in printer.printjob_ids:
                    job.unlink()
                printer.unlink()
            computer.unlink()

    def update_limits(self):
        """
        Update limits (printed pages + total available pages) for accounts
        """
        for rec in self.env['printnode.account'].search([]):
            stats = rec._get_printnode_response('billing/statistics')
            rec.printed = stats and stats['current'].get('prints', 0)

            plan = rec._get_printnode_response('billing/plan')
            raw_limits = plan and plan['current'].get('printCurve')
            if raw_limits:
                # Parse with regex value like '("{0,5000}","{0,0}",0.0018)
                m = re.match(r'\(\"{(?P<_>\d+),(?P<limits>\d+)}\",.*\)', raw_limits)
                rec.limits = (m and m.group('limits')) or 0

        # Notify user if number of available pages too low
        company = self.env.user.company_id

        if company.printnode_notification_email and company.printnode_notification_page_limit:
            accounts_to_notify = self.env['printnode.account'].search([]).filtered(
                lambda r: r.limits > 0
                    and (r.limits - r.printed) < company.printnode_notification_page_limit)  # NOQA

            if accounts_to_notify:
                context = self.env.context.copy()
                context.update({'accounts': accounts_to_notify})

                mail_template = self.env.ref('printnode_base.reaching_limit_notification_email')
                mail_template.with_context(context).send_mail(company.id, force_send=True)

    @api.depends('endpoint', 'username', 'password')
    def _compute_account_status(self):
        """ Request PrintNode account details - whoami
        """
        for rec in self.filtered(lambda x: x.endpoint and x.username):
            rec._get_printnode_response('whoami')

    def _get_node(self, node_type, node_id, parent_id):
        """ Parse and update PrintNode nodes (printer and computers)
        """
        node = self.env['printnode.{}'.format(node_type)].search([
            ('printnode_id', '=', node_id['id']),
            '|', ('active', '=', False), ('active', '=', True)
        ], limit=1)

        if not node:
            params = {
                'printnode_id': node_id['id'],
                'name': node_id['name'],
                'status': node_id['state'],
            }
            if node_type == 'computer':
                params.update({'account_id': parent_id})
            if node_type == 'printer':
                params.update({'computer_id': parent_id})

            node = node.create(params)
        else:
            node.write({
                'status': node_id['state'],
            })

        return node

    def _get_printnode_response(self, uri):
        """ Send request with basic authentication and API key
        """

        auth = requests.auth.HTTPBasicAuth(self.username, self.password or '')
        if self.endpoint.endswith('/'):
            self.endpoint = self.endpoint[:-1]

        try:
            resp = requests.get('{}/{}'.format(self.endpoint, uri), auth=auth)
            resp.raise_for_status()

            self.status = 'OK'
            return resp.json()

        except requests.exceptions.RequestException as e:
            self.env['printnode.printer'].search([]).write({
                'status': 'offline'
            })

            self.status = e  # or resp.json().get('message')
            return []
