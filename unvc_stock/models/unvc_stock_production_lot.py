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
from odoo import api, models, fields


class UnvcStockProductionLot(models.Model):
    _inherit = "stock.production.lot"

    # UNVCPROD-29 - lot unicity
    _sql_constraints = [
        ('unvc_name_ref_uniq', 'unique (name)', 'Lot / Serial Number must be unique !'),
    ]

    # UNVCPROD-30 - remove default option on lot name + readonly = true
    name = fields.Char('Lot/Serial Number', default="draft", required=True, readonly=True,
                       help="Unique Lot/Serial Number")
    # UNVCPROD-30 - change internal ref number label
    ref = fields.Char('Supplier batch number',
                      help="Internal reference number in case it differs from the manufacturer's lot/serial number")
    negative_consumption_log = fields.Text(string="Negative Consumption Log",
                                           help="Keep tracks of negative concumption for security.")

    # UNVCPROD-30 - force name as the next sequence number
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('stock.lot.serial')
        return super(UnvcStockProductionLot, self).create(vals)

    def add_negative_consumption_log(self, stock_move_line, quantity):
        """
        :param stock_move_line: The stock move line that have generated a consumption in the negative stock.
        :param quantity: The quantity that have consumed in the negative stock.
        :return: A new line in the log for the negative consumption stock.
        """
        self.ensure_one()
        date = fields.Datetime.now()
        self.negative_consumption_log = "[%s] The stock move line %s have consumed %s %s from the negative stock \n%s" \
                                        % (date, stock_move_line.name_get()[0], quantity,
                                           stock_move_line.product_uom_id.name, self.negative_consumption_log or '')
