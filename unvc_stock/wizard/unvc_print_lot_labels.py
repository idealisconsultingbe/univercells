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


class UnvcPrintLotLabels(models.TransientModel):
    _name = 'unvc.print.lot.labels'

    def _prepare_unvc_lot_label(self, product, lot):
        """
        :param product: A product.product record
        :param lot: A stock.production.lot record
        :return: A dict for creating an unvc.lot.label
        """
        values = {
            'product_id': product.id,
            'lot_id': lot.id,
        }
        return values

    def create_unvc_lot_label(self, models):
        """
        :param models:  A record set of model, the given model should have a many2one relation toward the product.product model
                        and toward the stock.production.lot model.
        :return: Return a record set of unvc.lot.label, one for each given model.
        """
        lot_labels = self.env['unvc.lot.label']
        if models and models._name:
            models_model = self.env['ir.model'].search([('model', '=', models._name)], limit=1)
            product_field = self.env['ir.model.fields'].search([('model_id', '=', models_model.id),
                                                                ('relation', '=', 'product.product')], limit=1)
            lot_field = self.env['ir.model.fields'].search([('model_id', '=', models_model.id),
                                                            ('relation', '=', 'stock.production.lot')], limit=1)
            if product_field and lot_field:
                for model in models:
                    values = self._prepare_unvc_lot_label(model[product_field.name], model[lot_field.name])
                    lot_labels |= self.env['unvc.lot.label'].create(values)
        return lot_labels

    @api.model
    def _get_default_lot_label(self):
        """
        Get the default unvc.lot.label from the printing wizard
        :return: A record set of unvc.lot.label
        """
        default_lot_labels = self.env['unvc.lot.label']
        picking_id = self.env.context.get('active_id', False) if \
            self.env.context.get('active_model', False) == 'stock.picking' else False
        quant_ids = self.env.context.get('active_ids', False) if \
            self.env.context.get('active_model', False) == 'stock.quant' else False
        inventory_line_ids = self.env.context.get('active_ids', False) if\
            self.env.context.get('active_model', False) == 'stock.inventory.line' else False
        lot_ids = self.env.context.get('active_ids', False) if self.env.context.get('active_model', False) == 'stock.production.lot' else False
        if picking_id:
            picking = self.env['stock.picking'].browse(picking_id)
            stock_move_lines = picking.mapped('move_lines.move_line_ids')
            default_lot_labels = self.create_unvc_lot_label(stock_move_lines)
        elif quant_ids:
            quants = self.env['stock.quant'].browse(quant_ids)
            default_lot_labels = self.create_unvc_lot_label(quants)
        elif inventory_line_ids:
            inventory_lines = self.env['stock.inventory.line'].browse(inventory_line_ids)
            default_lot_labels = self.create_unvc_lot_label(inventory_lines)
        elif lot_ids:
            lots = self.env['stock.production.lot'].browse(lot_ids)
            for lot in lots:
                values = self._prepare_unvc_lot_label(lot.product_id, lot)
                default_lot_labels |= self.env['unvc.lot.label'].create(values)
        return default_lot_labels

    lot_label_ids = fields.One2many('unvc.lot.label', 'print_lot_labels_id', string='Stock Move Line',
                                    default=_get_default_lot_label)

    def do_print(self):
        self.env.ref('unvc_stock.unvc_lot_label_report').hw_print(self.id)


class UnvcLotLabel(models.TransientModel):
    _name = 'unvc.lot.label'

    product_id = fields.Many2one('product.product', string='Product', readonly=True, required=True)
    lot_id = fields.Many2one('stock.production.lot', string='Lot/Serial Number', readonly=True)
    number_of_labels = fields.Integer(string='Number Of Labels', default=1)
    print_lot_labels_id = fields.Many2one('unvc.print.lot.labels', string='Print Labels')
