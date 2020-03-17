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
from odoo import api, models, fields, _


class UnvcProductMigratedStock(models.Model):
    _inherit = "product.product"

    migrated_stock_ids = fields.One2many('unvc.migrated.stock', 'product_id', string="Migrated Stock")

    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state', 'stock_move_ids.remaining_value',
                 'product_tmpl_id.cost_method', 'product_tmpl_id.standard_price', 'product_tmpl_id.property_valuation',
                 'product_tmpl_id.categ_id.property_valuation')
    def _compute_stock_value(self):
        """
        Overwrite the standard method, build the inventory valuation report based on stock move if cost method is fifo.
        """
        StockMove = self.env['stock.move']
        to_date = self.env.context.get('to_date')

        real_time_product_ids = [product.id for product in self if product.product_tmpl_id.valuation == 'real_time']
        if real_time_product_ids:
            self.env['account.move.line'].check_access_rights('read')
            fifo_automated_values = {}
            query = """SELECT aml.product_id, aml.account_id, sum(aml.debit) - sum(aml.credit), sum(quantity), array_agg(aml.id)
                             FROM account_move_line AS aml
                            WHERE aml.product_id IN %%s AND aml.company_id=%%s %s
                         GROUP BY aml.product_id, aml.account_id"""
            params = (tuple(real_time_product_ids), self.env.user.company_id.id)
            if to_date:
                query = query % ('AND aml.date <= %s',)
                params = params + (to_date,)
            else:
                query = query % ('',)
            self.env.cr.execute(query, params=params)

            res = self.env.cr.fetchall()
            for row in res:
                fifo_automated_values[(row[0], row[1])] = (row[2], row[3], list(row[4]))

        product_values = {product.id: 0 for product in self}
        product_move_ids = {product.id: [] for product in self}

        if to_date:
            domain = [('product_id', 'in', self.ids), ('date', '<=', to_date)] + StockMove._get_all_base_domain()
            value_field_name = 'value'
        else:
            domain = [('product_id', 'in', self.ids)] + StockMove._get_all_base_domain()
            value_field_name = 'remaining_value'

        StockMove.check_access_rights('read')
        query = StockMove._where_calc(domain)
        StockMove._apply_ir_rules(query, 'read')
        from_clause, where_clause, params = query.get_sql()
        query_str = """
                SELECT stock_move.product_id, SUM(COALESCE(stock_move.{}, 0.0)), ARRAY_AGG(stock_move.id)
                FROM {}
                WHERE {}
                GROUP BY stock_move.product_id
            """.format(value_field_name, from_clause, where_clause)
        self.env.cr.execute(query_str, params)
        for product_id, value, move_ids in self.env.cr.fetchall():
            product_values[product_id] = value
            product_move_ids[product_id] = move_ids

        for product in self:
            if product.cost_method in ['standard', 'average']:
                qty_available = product.with_context(company_owned=True, owner_id=False).qty_available
                price_used = product.standard_price
                if to_date:
                    price_used = product.get_history_price(
                        self.env.user.company_id.id,
                        date=to_date,
                    )
                product.stock_value = price_used * qty_available
                product.qty_at_date = qty_available
            elif product.cost_method == 'fifo':
                #################################################
                ############ CHANGES HAPPENS HERE################
                #################################################
                if to_date:
                    product.stock_value = product_values[product.id]
                    product.qty_at_date = product.with_context(company_owned=True, owner_id=False).qty_available
                    product.stock_fifo_manual_move_ids = StockMove.browse(product_move_ids[product.id])
                ################################################
                else:
                    product.stock_value = product_values[product.id]
                    product.qty_at_date = product.with_context(company_owned=True, owner_id=False).qty_available
                    if product.product_tmpl_id.valuation == 'manual_periodic':
                        product.stock_fifo_manual_move_ids = StockMove.browse(product_move_ids[product.id])
                    elif product.product_tmpl_id.valuation == 'real_time':
                        valuation_account_id = product.categ_id.property_stock_valuation_account_id.id
                        value, quantity, aml_ids = fifo_automated_values.get((product.id, valuation_account_id)) or (
                        0, 0, [])
                        product.stock_fifo_real_time_aml_ids = self.env['account.move.line'].browse(aml_ids)

    def action_valuation_at_date_details(self):
        """
        Overwrite standard method.
        Always display stock move details and not account move line
        """
        self.ensure_one()
        to_date = self.env.context.get('to_date')
        action = {'name': _('Valuation at date'),
                  'type': 'ir.actions.act_window',
                  'view_mode': 'tree,form',
                  'context': self.env.context,
                  'res_model': 'stock.move',
                  'domain': [('id', 'in', self.with_context(to_date=to_date).stock_fifo_manual_move_ids.ids)]}
        #################################################
        ############ CHANGES HAPPENS HERE################
        #################################################
        tree_view_ref = self.env.ref('stock_account.view_move_tree_valuation_at_date')
        form_view_ref = self.env.ref('stock.view_move_form')
        action['views'] = [(tree_view_ref.id, 'tree'), (form_view_ref.id, 'form')]
        #################################################
        return action


class UnvcProductCategory(models.Model):
    _inherit = "product.category"

    #UNVCPROD-33 add subcontracted products flag
    is_subcontracted = fields.Boolean('Subcontracted products', default=False,
                              help='Check this box to identify subcontracted products. '
                                   'Impact on analytic account determination')


class UnvcProductUom(models.Model):
    _inherit = "uom.category"

    allow_negative_stock = fields.Boolean(string='Allow Negative Stock', default=False,
                                          help="Product of this kind of unit of measure will be allow to have negative stock.")
