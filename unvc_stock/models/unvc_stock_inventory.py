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


class UnvcStockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    def _get_default_location_id(self):
        location_id = self.env['stock.location']
        if self.inventory_id:
            location_id = self.inventory_id.location_id.get_putaway_strategy(self.product_id) or\
                          self.inventory_id.location_id
        return location_id

    @api.onchange('product_id', 'inventory_id.location_id')
    def onchange_location_id(self):
        self.location_id = self._get_default_location_id()

    location_id = fields.Many2one(default=_get_default_location_id)
