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


class UnvcStockScrap(models.Model):
    _inherit = 'stock.scrap'

    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial Number', states={'done': [('readonly', True)]},
                             domain="[('product_id', '=', product_id)]")

    def _get_unvc_default_scrap_location_id(self):
        return False

    @api.onchange('location_id')
    def onchange_domain_scrap_location(self):
        location_same_warehouse_ids = []
        if self.location_id:
            warehouse_id = self.location_id.get_warehouse().id
            if warehouse_id:
                location_same_warehouse = self.env['stock.location'].search([])
                location_same_warehouse_ids = location_same_warehouse.filtered\
                    (lambda loc: loc.get_warehouse().id == warehouse_id).ids
        if self.location_id and self.location_id.forbid_virtual_scraping:
            domain = [('scrap_location', '=', True), ('usage', '=', 'internal'),
                      ('id', 'in', location_same_warehouse_ids)]
        else:
            domain = ['&', ('scrap_location', '=', True), '|', ('usage', '!=', 'internal'), '&',
                      ('usage', '=', 'internal'), ('id', 'in', location_same_warehouse_ids)]
        return {'domain': {'scrap_location_id': domain}}

    scrap_location_id = fields.Many2one('stock.location', 'Scrap Location', default=_get_unvc_default_scrap_location_id,
                                        domain="[('scrap_location', '=', True)]", required=True,
                                        states={'done': [('readonly', True)]})


class UnvcStockLocation(models.Model):
    _inherit = 'stock.location'

    forbid_virtual_scraping = fields.Boolean(string='Forbid Virtual Scraping', default=False)
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    postproduction_location = fields.Boolean('Is a Post Production Location?', default=False,
                                             help='Check this box to allow automatically confirm transfert'
                                                  ' of semi-finished products manufactured.')
