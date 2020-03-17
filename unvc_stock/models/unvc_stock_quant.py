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

from psycopg2 import OperationalError

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from odoo.tools import config, float_compare


class UnvcStockQuant(models.Model):
    _inherit = "stock.quant"

    @api.constrains('product_id', 'quantity')
    def check_negative_qty(self):
        """
        Rewrite the standard method, this way we can have negative stock on product for which the category of the unit of measure allows it.
        """
        p = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        check_negative_qty = (
            (config['test_enable'] and
             self.env.context.get('test_stock_no_negative')) or
            not config['test_enable']
        )
        if not check_negative_qty:
            return

        for quant in self:
            ###########################################
            ########### CHANGES happens here ##########
            ###########################################
            disallowed_by_product = \
                not quant.product_id.allow_negative_stock \
                and not quant.product_id.categ_id.allow_negative_stock \
                and not quant.product_id.uom_id.category_id.allow_negative_stock
            ###########################################
            ###########################################
            disallowed_by_location = not quant.location_id.allow_negative_stock
            if (
                float_compare(quant.quantity, 0, precision_digits=p) == -1 and
                quant.product_id.type == 'product' and
                quant.location_id.usage in ['internal', 'transit'] and
                (disallowed_by_product or disallowed_by_location)
            ):
                msg_add = ''
                if quant.lot_id:
                    # Now find a quant we can compensate the negative quants
                    #  with some untracked quants.
                    untracked_qty = quant._get_available_quantity(
                        quant.product_id, quant.location_id, lot_id=False,
                        strict=True)
                    if float_compare(abs(quant.quantity),
                                     untracked_qty, precision_digits=p) < 1:
                        return True
                    msg_add = _(" lot '%s'") % quant.lot_id.display_name
                raise ValidationError(_(
                    "You cannot validate this stock operation because the "
                    "stock level of the product '%s'%s would become negative "
                    "(%s) on the stock location '%s' and negative stock is "
                    "not allowed for this product and/or location.") % (
                        quant.product_id.name, msg_add, quant.quantity,
                        quant.location_id.complete_name))

    @api.model
    def _update_available_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None,
                                   in_date=None):
        """
        Delete every negative stock quant! We don't want to keep track of them. Since negative consumption is allow only for meter
        and length it means that in reality we are at zero (negative stock only exist because of measure error on the field).
        """
        available_qty, in_date = super(UnvcStockQuant, self)._update_available_quantity(
            product_id, location_id, quantity, lot_id, package_id, owner_id, in_date)
        self = self.sudo()
        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id,
                              strict=True)
        quants = quants.filtered(lambda quant: quant.quantity < 0)
        for quant in quants:
            try:
                with self._cr.savepoint():
                    self._cr.execute("SELECT 1 FROM stock_quant WHERE id = %s FOR UPDATE NOWAIT", [quant.id],
                                     log_exceptions=False)
                    quant.unlink()
            except OperationalError as e:
                if e.pgcode == '55P03':  # could not obtain the lock
                    continue
                else:
                    raise
        return available_qty, in_date
