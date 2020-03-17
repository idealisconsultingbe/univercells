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
from datetime import datetime, timedelta


class UnvcStockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def create(self, vals):
        tmp = False
        if vals.get('move_lines'):
            tmp = vals.pop('move_lines')
        res = super(UnvcStockPicking, self).create(vals)
        if tmp:
            super(UnvcStockPicking, res).write({'move_lines': tmp})
        return res

    def get_tomorrow_request_date(self):
        """
        Utility function to compute tomorrow request date

        :return: datetime corresponding to tomorrow
        """
        return (datetime.today() + timedelta(days=1)).date()

    def _check_backorder(self):
        """
        Overwrite the standard method. We do not take into account scrap move in the to do quantity.
        Scrap quantities are compare only between them self.
        """
        quantity_todo = {}
        quantity_done = {}
        ######## Change happens here ##################
        for move_not_scrap in self.mapped('move_lines').filtered(lambda x: not x.location_dest_id.scrap_location):
            quantity_todo.setdefault(move_not_scrap.product_id.id, 0)
            quantity_todo[move_not_scrap.product_id.id] += move_not_scrap.product_uom_qty
        for move in self.mapped('move_lines'):
            quantity_done.setdefault(move.product_id.id, 0)
            quantity_done[move.product_id.id] += move.quantity_done
        ################################################
        for ops in self.mapped('move_line_ids').filtered(lambda x: x.package_id and not x.product_id and not x.move_id):
            for quant in ops.package_id.quant_ids:
                quantity_done.setdefault(quant.product_id.id, 0)
                quantity_done[quant.product_id.id] += quant.qty
        for pack in self.mapped('move_line_ids').filtered(lambda x: x.product_id and not x.move_id):
            quantity_done.setdefault(pack.product_id.id, 0)
            quantity_done[pack.product_id.id] += pack.product_uom_id._compute_quantity(pack.qty_done, pack.product_id.uom_id)
        return any(quantity_done[x] < quantity_todo.get(x, 0) for x in quantity_done)

    @api.onchange('request_date')
    def _check_request_date_constraint(self):
        """
        Check 'request_date' minimum value is tomorrow
        If not, set the field to tomorrow value

        :return None
        """
        for picking in self:
            if self.picking_type_id.picking_request:
                min_date = picking.get_tomorrow_request_date()
                current_date = fields.Date.from_string(picking.request_date) or min_date
                if current_date < min_date:
                    picking.request_date = min_date
                    return {
                        'warning': {
                            'title': "Warning",
                            'message': "Requested Date should be at least tomorrow"}
                    }

    @api.onchange('picking_type_id', 'partner_id')
    def onchange_picking_type(self):
        """
        Override StockPicking.onchange_picking_type() method to avoid 'location_dest_id' to be set
        according to the default value

        Call super() and override location_dest_id if it contains a value

        :return: None
        """
        super(UnvcStockPicking, self).onchange_picking_type()
        if self.picking_type_id.picking_request:
            self.location_dest_id = False

        #UNVCPROD-33 for subcontracting activities, the delivery orders destination location
        # must be the one related to the subcontractor (to ensure correct analytic account select)
        elif self.partner_id and self.picking_type_id.code == 'outgoing':
            self.location_dest_id = self.partner_id.property_stock_customer

    @api.onchange('picking_type_id')
    def apply_domain_on_location(self):
        """
        Apply dynamic domain  on field 'location_dest_id' depending on the flag 'picking_request'
        of stock.picking.type having the same warehouse between stock.picking.type and stock.location

        :return: domain filtering location by project_location flag if 'picking_request' flag is True
        and an empty domain otherwise
        """
        if self.is_picking_request:
            picking_type_warehouse = self.picking_type_id.warehouse_id
            locations = self.env['stock.location'].search([('project_location', '=', 'True')])
            warehouse_locations = locations.filtered(lambda location: location.get_warehouse().id == picking_type_warehouse.id or location.usage == 'customer').mapped('id')
            return {
                'domain': {
                    'location_dest_id': [('id', 'in', warehouse_locations)]
                }
            }
        else:
            return {
                'domain': {
                    'location_dest_id': []
                }
            }

    request_date = fields.Date(string='Requested Date', default=datetime.today() + timedelta(days=1))

    is_picking_request = fields.Boolean(string='Is Picking Request', related='picking_type_id.picking_request')
