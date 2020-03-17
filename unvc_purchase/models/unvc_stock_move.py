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

from odoo import api, fields, models, _


class UnvcStockMove(models.Model):
    _inherit = "stock.move"

    kit_product_details = fields.Text(string='Kit Details')

    def _prepare_procurement_values(self):
        vals = super(UnvcStockMove, self)._prepare_procurement_values()
        if self.kit_product_details:
            vals['kit_product_details'] = self.kit_product_details
        return vals

    def _prepare_phantom_move_values(self, bom_line, quantity):
        vals = super(UnvcStockMove, self)._prepare_phantom_move_values(bom_line, quantity)
        if self.sale_line_id:
            kit_quantity = quantity / bom_line.product_qty
            vals['kit_product_details'] = "%s X %s PC / %s" % (kit_quantity, bom_line.product_qty,
                                                               self.product_id.name_get()[0][1])
        return vals

    def _merge_moves_fields(self):
        res = super(UnvcStockMove, self)._merge_moves_fields()
        kit_product_details = self.mapped('kit_product_details')
        if any(kit_product_details):
            for i in range(0, len(kit_product_details)):
                if not kit_product_details[i]:
                    kit_product_details[i] = 'No kit'
            res['kit_product_details'] =  '\n'.join(kit_product_details)
        return res
