# -*- coding: utf-8 -*-
import logging
import json
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ExternalSalesDashboard(models.Model):
    _name = 'external.sales.dashboard'
    _description = 'External Sales Dashboard'

    sales_data = fields.Text('Data')

    def update_sales_dashboard(self):
        sales_sql = """
           select so.id as sale_id,
				so.name as sale_order, 
                r.name as customer, 
                c.name as salesperson,
                r2.name as account_manager,
                so.commitment_date as in_hand_date, 
                count(so1.id) as child_orders,
                sum(case when pickings.picking_type in ('Pick From Stock') and pickings.picking_state != 'done' then pickings.picking_count
                        else 0
                end) as "Picked Remaining",
                sum(case when pickings.picking_type in ('Pick From Stock') and pickings.picking_state = 'done' then pickings.picking_count
                        else 0
                end) as "Picked Done",
                sum(case when pickings.picking_type in ('Etching','Embroidery','Letters','Printing') and pickings.picking_state != 'done' then pickings.picking_count
                        else 0
                end) as "Customized Remaining",
                sum(case when pickings.picking_type in ('Etching','Embroidery','Letters','Printing') and pickings.picking_state = 'done' then pickings.picking_count
                        else 0
                end) as "Customized Done",
                sum(case when pickings.picking_type in ('Kitting and Shipping','Ready to Kit') and pickings.picking_state != 'done' then pickings.picking_count
                        else 0
                end) as "Kitted Remaining",
                sum(case when pickings.picking_type in ('Kitting and Shipping','Ready to Kit') and pickings.picking_state = 'done' then pickings.picking_count
                        else 0
                end) as "Kitted Done",
                sum(case when pickings.picking_type in ('Delivery Orders') and pickings.picking_state != 'done' then pickings.picking_count
                        else 0
                end) as "Shipped Remaining",
                sum(case when pickings.picking_type in ('Delivery Orders') and pickings.picking_state = 'done' then pickings.picking_count
                        else 0
                end) as "Shipped Done"
            from sale_order so,
                res_partner r,
                crm_team c,
                res_users u,
                res_partner r2,
                sale_order so1
            LEFT JOIN (select sp.sale_id as child_id,
                            spt.name as picking_type,
                            sp.state as picking_state,
                            count(sp.id) as picking_count
                    from stock_picking sp,
                            stock_picking_type spt
                    where sp.sale_id is not null
                    and spt.id = sp.picking_type_id
                    and sp.state != 'cancel'
                    group by sp.sale_id,
                                spt.name,
                                sp.state) as pickings on pickings.child_id = so1.id
            where so.id = so1.x_studio_related_sales_order
            and r.id = so.partner_id
            and so1.state != 'cancel'
            and so.state != 'cancel'
            and c.id = so.team_id
            and u.id = so.user_id
            and r2.id = u.partner_id
            group by so.id,
					so.name, 
                    r.name,
                    c.name,
                    r2.name,
                    so.commitment_date
            order by 1,2,3
        """

        self.env.cr.execute(sales_sql)
        sales_data_raw = self.env.cr.dictfetchall()
        all_sales_data = self.search([])
        if len(all_sales_data):
            all_sales_data[0].sales_data = json.dumps(sales_data_raw, indent=4, default=str)
        else:
            self.create(
                {
                    "sales_data": json.dumps(sales_data_raw, indent=4, default=str)
                }
            )




