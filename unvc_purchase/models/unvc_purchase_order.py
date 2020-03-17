# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Idealis Consulting
#    Copyright (c) 2016 Idealis Consulting S.A. (http://www.idealisconsulting.com)
#    All Rights Reserved
#
#    WARNING: This program as such is intended to be used by professional
#    programmers who take the whole responsibility of assessing all potential
#    consequences resulting from its eventual inadequacies and bugs.
#    End users who are looking for a ready-to-use solution with commercial
#    guarantees and support are strongly advised to contact a Free Software
#    Service Company.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class UnvcPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('order_line.qty_received')
    def _get_qty_received(self):
        """
        Get the total quantity received for this PO
        """
        for po in self:
            po.qty_received = sum(po.order_line.filtered(lambda line:
                                                         line.product_id and line.product_id.type in
                                                         ('consu', 'product')).mapped('qty_received'))

    # @api.onchange('dept_manager_id')
    # def set_default_finance_manager(self):
    #     """
    #     Set default value of finance_manager_id field according to
    #     the selected dept_manager_id. The finance_manager_id by default
    #     should be the manager of the selected dept_manager
    #
    #     :return: None
    #     """
    #     for purchase in self:
    #         if not purchase.dept_manager_id:
    #             return
    #         # Retrieve the hr.employee linked to the dept_manager user
    #         related_employees = purchase.dept_manager_id.employee_ids
    #         selected_finance_manager = False
    #         # Foreach related hr.employee, in most case only one
    #         for employee in related_employees:
    #             # If the linked employee has a manager and that manager has a related user
    #             # Selected it as the default finance_manager and stop iteration
    #             if employee.parent_id and employee.parent_id.user_id:
    #                 selected_finance_manager = employee.parent_id.user_id
    #                 break
    #         purchase.finance_manager_id = selected_finance_manager
    
    # @api.onchange('finance_manager_id')
    # def set_default_director_manager(self):
    #     """
    #     Set default value of director_manager_id field => the one having the rôle
    #     :return: None
    #     """
    #     for purchase in self:
    #         if not purchase.finance_manager_id:
    #             purchase.director_manager_id = False
    #             return
    #         purchase.director_manager_id = self.env['res.users'].search(
    #             [('groups_id', 'in', [self.env.ref('purchase_tripple_approval.group_purchase_director').id])], limit=1)

    # def _get_default_dept_manager_domain(self):
    #     return [('groups_id', '=', self.env.ref('purchase_tripple_approval.group_department_manager').id)]
    #
    # def _get_default_finance_manager_domain(self):
    #     return [('groups_id', '=', self.env.ref('account.group_account_invoice').id)]
    #
    # def _get_default_director_manager_domain(self):
    #     return [('groups_id', '=', self.env.ref('purchase_tripple_approval.group_purchase_director').id)]

    def _write(self, vals):
        """
        Update order and scheduled dates after validation process
        """
        for order in self:
            if order.state in ['to approve', 'finance_approval'] and \
                    vals.get('state') in ['purchase', 'finance_approval']:
                vals['date_order'] = order.date_order = fields.Datetime.now()
                for line in order.order_line:
                    seller = line.product_id._select_seller(
                        partner_id=line.partner_id,
                        quantity=line.product_qty,
                        date=line.order_id.date_order and line.order_id.date_order[:10],
                        uom_id=line.product_uom)
                    line.date_planned = line._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return super(UnvcPurchaseOrder, self)._write(vals)

    tag_id = fields.Many2one('purchase.order.tag', required=False)
    qty_received = fields.Float(string='Quantity Received', compute='_get_qty_received', store=True)
    requester_id = fields.Many2one('hr.employee', string='Requester')
    requester_ids = fields.Many2many('stock.location', string='Requested For Project')
    
    # dept_manager_id = fields.Many2one(
    #     'res.users',
    #     string='Purchase/Department Manager',
    #     states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
    #     domain=_get_default_dept_manager_domain
    # )
    # finance_manager_id = fields.Many2one(
    #     'res.users',
    #     string='Finance Manager',
    #     states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
    #     domain=_get_default_finance_manager_domain
    # )
    # director_manager_id = fields.Many2one(
    #     'res.users',
    #     string='Director Manager',
    #     states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
    #     domain=_get_default_director_manager_domain
    # )


class UnvcPoTag(models.Model):
    _name = 'purchase.order.tag'

    name = fields.Char()
