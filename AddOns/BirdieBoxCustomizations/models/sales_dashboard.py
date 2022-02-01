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
                child.child_orders as child_orders,
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
            from res_partner r,
                crm_team c,
                res_users u,
                res_partner r2,
                sale_order so
            LEFT JOIN (select so2.x_studio_related_sales_order as parent,
                              spt.name as picking_type,
                              sp.state as picking_state,
                              count(sp.id) as picking_count
                    from stock_picking sp,
                         stock_picking_type spt,
                         sale_order so2
                    where sp.sale_id is not null
                    and spt.id = sp.picking_type_id
                    and sp.state != 'cancel'
                    and so2.id = sp.sale_id
                    group by so2.x_studio_related_sales_order,
                             spt.name,
                             sp.state) as pickings on pickings.parent = so.id
            LEFT JOIN (select so3.x_studio_related_sales_order as parent,
                              count(so3.id) as child_orders
                    from sale_order so3
                    where so3.x_studio_related_sales_order is not null
                    group by so3.x_studio_related_sales_order) as child on child.parent = so.id
            where r.id = so.partner_id
            and so.state != 'cancel'
            and c.id = so.team_id
            and u.id = so.user_id
            and r2.id = u.partner_id
            and exists
            (select 'x'
             from sale_order so4
             where so4.x_studio_related_sales_order = so.id)
            group by so.id,
                    so.name, 
                    r.name,
                    c.name,
                    r2.name,
                    so.commitment_date,
                    child.child_orders
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




