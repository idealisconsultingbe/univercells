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


class UnvcPurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.onchange('product_id')
    def set_default_account_analytic(self):
        """
        Set default value of account_analytic_id field depending of the product type
        if the product is type of 'product' (stockable):
            set default analytic account with 'generic_stock_account' flag
        No default analytic account otherwise

        :return: None

        !!! If logic changes, please update def _prepare_purchase_order_line as well (used for
        PO created based on min-max or MTO rules"
        """
        for order_line in self:
            analytic_account = None
            if order_line.product_id.type == 'product' and \
                    order_line.product_id.categ_id.property_valuation == 'real_time':
                analytic_account = self.env['account.analytic.account'].search([('generic_stock_account', '=', True)],
                                                                               limit=1)
            elif order_line.product_id.type == 'product' and \
                    order_line.product_id.categ_id.property_valuation == 'manual_periodic':
                analytic_account = self.env['account.analytic.account'].search(
                    [('generic_stock_allocated_account', '=', True)], limit=1)
            elif order_line.product_id.type == 'service':
                analytic_account = order_line.product_id.account_analytic_id

            order_line.account_analytic_id = analytic_account if analytic_account else False
        return

        # Add required field to inherited account_analytic_id field
    account_analytic_id = fields.Many2one('account.analytic.account', required=True)


