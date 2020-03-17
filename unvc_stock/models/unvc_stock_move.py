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
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round, float_compare


class UnvcStockMove(models.Model):
    _inherit = "stock.move"

    negative_consumption = fields.Float(string='Negative Consumption', default=0, help='Keep track of the quantity that have been consumed in the negative part of the stock. '
                                                                                       'This value should always be positive, if its value is equal to 2 it means that 2 unit have been consumed in the negative stock.')

    # rewrite stock.account method to add analytic account while creating valuation stock accounting move
    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id, analytic_account_id=False,
                                   analytic_tag_ids=False):
        """
        Generate the account.move.line values to post to track the stock valuation difference due to the
        processing of the given quant.
        """
        self.ensure_one()

        if self._context.get('force_valuation_amount'):
            valuation_amount = self._context.get('force_valuation_amount')
        else:
            valuation_amount = cost

        if self._context.get('forced_ref'):
            ref = self._context['forced_ref']
        else:
            ref = self.picking_id.name

        # the standard_price of the product may be in another decimal precision, or not compatible with the coinage of
        # the company currency... so we need to use round() before creating the accounting entries.
        debit_value = self.company_id.currency_id.round(valuation_amount)

        # check that all data is correct
        if self.company_id.currency_id.is_zero(debit_value):
            raise UserError(_(
                "The cost of %s is currently equal to 0. Change the cost or the configuration of your product to avoid an incorrect valuation.") % (
                            self.product_id.name,))
        credit_value = debit_value

        partner_id = (self.picking_id.partner_id and self.env['res.partner']._find_accounting_partner(
            self.picking_id.partner_id).id) or False
        analytic_tag_tmp_ids = [(4, analytic_tag.id, None) for analytic_tag in
                                analytic_tag_ids] if analytic_tag_ids else []

        res = []
        # Subtract the negative consumption in order to not create Journal Item for the stock that have been consumed in the negative part.
        unprocessed_qty = abs(qty)
        debit_value_unit = debit_value / unprocessed_qty if unprocessed_qty else 0
        credit_value_unit = credit_value / unprocessed_qty if unprocessed_qty else 0
        unprocessed_qty = unprocessed_qty - self.negative_consumption
        sign = -1 if qty < 0 else 1
        no_migrated_stock = False

        migrated_stock = self.product_id.migrated_stock_ids.filtered(
            lambda x: x.warehouse_id.id == self.picking_type_id.warehouse_id.id)
        if len(migrated_stock.ids) > 1:
            raise UserError(_('Error, The product %s has muliple migrated stock line for the warehouse #%s.') % (self.product_id.name, self.warehouse_id.name))

        # Check the migrated stock in order to not impute two times the same product.
        while unprocessed_qty > 0:
            # We want to process more than what we have left from the old stock
            if migrated_stock and migrated_stock.quantity > 0 and unprocessed_qty > migrated_stock.quantity:
                qty_to_process = migrated_stock.quantity
                migrated_stock.quantity -= qty_to_process
            # We want to process less that what we have left in the old stock
            elif migrated_stock and migrated_stock.quantity > 0:
                qty_to_process = unprocessed_qty
                migrated_stock.quantity -= qty_to_process
            # the old stock is empty
            else:
                no_migrated_stock = True
                qty_to_process = unprocessed_qty
            debit_line_vals = {
                'name': self.name,
                'product_id': self.product_id.id,
                'quantity': sign * qty_to_process,
                'product_uom_id': self.product_id.uom_id.id,
                'ref': ref,
                'partner_id': partner_id,
                'debit': debit_value_unit * qty_to_process if debit_value_unit * qty_to_process > 0 else 0,
                'credit': -debit_value_unit * qty_to_process if debit_value_unit * qty_to_process < 0 else 0,
                'account_id': debit_account_id,
            }

            credit_line_vals = {
                'name': self.name,
                'product_id': self.product_id.id,
                'quantity': sign * qty_to_process,
                'product_uom_id': self.product_id.uom_id.id,
                'ref': ref,
                'partner_id': partner_id,
                'credit': credit_value_unit * qty_to_process if credit_value_unit * qty_to_process > 0 else 0,
                'debit': -credit_value_unit * qty_to_process if credit_value_unit * qty_to_process < 0 else 0,
                'account_id': credit_account_id,
            }
            if no_migrated_stock:  # old stock is empty we want to impute these lines
                debit_line_vals.update({'analytic_account_id': analytic_account_id.id if self.env[
                                                                                             'account.account'].search(
                    [('id', '=', debit_account_id)], limit=1).user_type_id.name == 'Expenses' else None,
                                        'analytic_tag_ids': analytic_tag_tmp_ids if self.env[
                                                                                        'account.account'].search(
                                            [('id', '=', debit_account_id)],
                                            limit=1).user_type_id.name == 'Expenses' else None, })
                credit_line_vals.update({'analytic_account_id': analytic_account_id.id if self.env[
                                                                                              'account.account'].search(
                    [('id', '=', credit_account_id)], limit=1).user_type_id.name == 'Expenses' else None,
                                         'analytic_tag_ids': analytic_tag_tmp_ids if self.env[
                                                                                         'account.account'].search(
                                             [('id', '=', credit_account_id)],
                                             limit=1).user_type_id.name == 'Expenses' else None, })
            unprocessed_qty -= qty_to_process
            res.append((0, 0, debit_line_vals))
            res.append((0, 0, credit_line_vals))

        if credit_value != debit_value:
            # for supplier returns of product in average costing method, in anglo saxon mode
            diff_amount = debit_value - credit_value
            price_diff_account = self.product_id.property_account_creditor_price_difference
            if not price_diff_account:
                price_diff_account = self.product_id.categ_id.property_account_creditor_price_difference_categ
            if not price_diff_account:
                raise UserError(_(
                    'Configuration error. Please configure the price difference account on the product or its category to process this operation.'))
            price_diff_line = {
                'name': self.name,
                'product_id': self.product_id.id,
                'quantity': qty,
                'product_uom_id': self.product_id.uom_id.id,
                'ref': ref,
                'partner_id': partner_id,
                'credit': diff_amount > 0 and diff_amount or 0,
                'debit': diff_amount < 0 and -diff_amount or 0,
                'account_id': price_diff_account.id,
            }
            res.append((0, 0, price_diff_line))
        return res

    # rewrite method to add analytic account in method parameter
    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, account_analytic_id=None,
                                  analytic_tag_ids=None):
        self.ensure_one()
        AccountMove = self.env['account.move']
        quantity = self.env.context.get('forced_quantity', self.product_qty)
        quantity = quantity if self._is_in() else -1 * quantity

        # Make an informative `ref` on the created account move to differentiate between classic
        # movements, vacuum and edition of past moves.
        ref = self.picking_id.name
        if self.env.context.get('force_valuation_amount'):
            if self.env.context.get('forced_quantity') == 0:
                ref = 'Revaluation of %s (negative inventory)' % ref
            elif self.env.context.get('forced_quantity') is not None:
                ref = 'Correction of %s (modification of past move)' % ref

        move_lines = self.with_context(forced_ref=ref)._prepare_account_move_line(quantity, abs(self.value),
                                                                                  credit_account_id,
                                                                                  debit_account_id,
                                                                                  account_analytic_id,
                                                                                  analytic_tag_ids)
        if move_lines:
            date = self._context.get('force_period_date', fields.Date.context_today(self))
            new_account_move = AccountMove.sudo().create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': date,
                'ref': ref,
                'stock_move_id': self.id,
            })
            new_account_move.post()

    def create_product_journal_entries(self, location, company, out=False):
        self.ensure_one()
        journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
        # UNVCPROD-33: in case of reception of a subcontracted product use subcontracted analytic account
        # UNVCPROD-31: in case of consumption on sale order, use analytic account defined in SO
        # else use analytic account defined in destination location
        account_analytic_id = False
        if self.picking_id and self.picking_id.purchase_id and self.product_id.categ_id.is_subcontracted:
            account_analytic_id = self.env['account.analytic.account'].search(
                [('subcontracted_activity_account', '=', True)], limit=1)
        elif self.picking_id and self.picking_id.sale_id and self.picking_id.sale_id.analytic_account_id:
            account_analytic_id = self.picking_id.sale_id.analytic_account_id
        elif location:
            account_analytic_id = location.account_analytic_id
        # ENDOF UNVCPROD-31&33
        if not out:
            if location and location.usage == 'customer':  # goods returned from customer
                self.with_context(force_company=company.id)._create_account_move_line(acc_dest, acc_valuation,
                                                                                      journal_id,
                                                                                      account_analytic_id,
                                                                                      location.analytic_tag_ids)
            else:
                self.with_context(force_company=company.id)._create_account_move_line(acc_src, acc_valuation,
                                                                                      journal_id,
                                                                                      account_analytic_id,
                                                                                      location.analytic_tag_ids)
        else:
            if location and location.usage == 'supplier':  # goods returned to supplier
                self.with_context(force_company=company.id)._create_account_move_line(acc_valuation, acc_src,
                                                                                      journal_id,
                                                                                      account_analytic_id,
                                                                                      location.analytic_tag_ids)
            else:
                self.with_context(force_company=company.id)._create_account_move_line(acc_valuation, acc_dest,
                                                                                      journal_id,
                                                                                      account_analytic_id,
                                                                                      location.analytic_tag_ids)

    def _account_entry_move(self):
        """ Accounting Valuation Entries """
        self.ensure_one()
        if self.product_id.type != 'product':
            # no stock valuation for consumable products
            return False
        if self.restrict_partner_id:
            # if the move isn't owned by the company, we don't make any valuation
            return False

        location_from = self.location_id.get_putaway_strategy(self.product_id) or self.location_id
        location_to = self.location_dest_id.get_putaway_strategy(self.product_id) or self.location_dest_id
        company_from = self._is_out() and self.mapped('move_line_ids.location_id.company_id') or False
        company_to = self._is_in() and self.mapped('move_line_ids.location_dest_id.company_id') or False

        # Create Journal Entry for products arriving in the company; in case of routes making the link between several
        # warehouse of the same company, the transit location belongs to this company, so we don't need to create accounting entries
        if self._is_in():
            self.create_product_journal_entries(location_from, company_to)

        # Create Journal Entry for products leaving the company
        if self._is_out():
            self.create_product_journal_entries(location_to, company_from, out=True)

        if self.company_id.anglo_saxon_accounting and self._is_dropshipped():
            # Creates an account entry from stock_input to stock_output on a dropship move. https://github.com/odoo/odoo/issues/12687
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
            self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_src, acc_dest, journal_id)


class UnvcStockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _get_default_location_id(self):
        location_id = self.env['stock.location']
        move = self.move_id
        if not move and self.env.context.get('default_move_id', False):
            move_id = int(self.env.context.get('default_move_id'))
            move = self.env['stock.move'].browse(move_id)
        if move:
            location_id = move.location_id.get_putaway_strategy(self.product_id) or move.location_id
        return location_id

    def _get_default_location_dest_id(self):
        location_dest_id = self.env['stock.location']
        move = self.move_id
        if not move and self.env.context.get('default_move_id', False):
            move_id = int(self.env.context.get('default_move_id'))
            move = self.env['stock.move'].browse(move_id)
        if move:
            location_dest_id = move.location_dest_id.get_putaway_strategy(self.product_id) or move.location_dest_id
        return location_dest_id

    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial Number')
    location_id = fields.Many2one(default=_get_default_location_id)
    location_dest_id = fields.Many2one(default=_get_default_location_dest_id)

    @api.onchange('product_id', 'move_id.location_id')
    def onchange_location_id(self):
        self.location_id = self._get_default_location_id()
        self.location_dest_id = self._get_default_location_dest_id()

    def _action_done(self):
        """
        Rewrite the standard method in order to keep track of the negative consumption that have been done.
        This tracking is mandatory because we don't want to write a journal item for the quantity that have been
        consumed in the negative part of the stock.
        """

        # First, we loop over all the move lines to do a preliminary check: `qty_done` should not
        # be negative and, according to the presence of a picking type or a linked inventory
        # adjustment, enforce some rules on the `lot_id` field. If `qty_done` is null, we unlink
        # the line. It is mandatory in order to free the reservation and correctly apply
        # `action_done` on the next move lines.
        ml_to_delete = self.env['stock.move.line']
        for ml in self:
            # Check here if `ml.qty_done` respects the rounding of `ml.product_uom_id`.
            uom_qty = float_round(ml.qty_done, precision_rounding=ml.product_uom_id.rounding, rounding_method='HALF-UP')
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            qty_done = float_round(ml.qty_done, precision_digits=precision_digits, rounding_method='HALF-UP')
            if float_compare(uom_qty, qty_done, precision_digits=precision_digits) != 0:
                raise UserError(_('The quantity done for the product "%s" doesn\'t respect the rounding precision \
                                  defined on the unit of measure "%s". Please change the quantity done or the \
                                  rounding precision of your unit of measure.') % (ml.product_id.display_name, ml.product_uom_id.name))

            qty_done_float_compared = float_compare(ml.qty_done, 0, precision_rounding=ml.product_uom_id.rounding)
            if qty_done_float_compared > 0:
                if ml.product_id.tracking != 'none':
                    picking_type_id = ml.move_id.picking_type_id
                    if picking_type_id:
                        if picking_type_id.use_create_lots:
                            # If a picking type is linked, we may have to create a production lot on
                            # the fly before assigning it to the move line if the user checked both
                            # `use_create_lots` and `use_existing_lots`.
                            if ml.lot_name and not ml.lot_id:
                                lot = self.env['stock.production.lot'].create(
                                    {'name': ml.lot_name, 'product_id': ml.product_id.id}
                                )
                                ml.write({'lot_id': lot.id})
                        elif not picking_type_id.use_create_lots and not picking_type_id.use_existing_lots:
                            # If the user disabled both `use_create_lots` and `use_existing_lots`
                            # checkboxes on the picking type, he's allowed to enter tracked
                            # products without a `lot_id`.
                            continue
                    elif ml.move_id.inventory_id:
                        # If an inventory adjustment is linked, the user is allowed to enter
                        # tracked products without a `lot_id`.
                        continue

                    if not ml.lot_id:
                        raise UserError(_('You need to supply a lot/serial number for %s.') % ml.product_id.name)
            elif qty_done_float_compared < 0:
                raise UserError(_('No negative quantities allowed'))
            else:
                ml_to_delete |= ml
        ml_to_delete.unlink()

        # Now, we can actually move the quant.
        done_ml = self.env['stock.move.line']
        for ml in self - ml_to_delete:
            if ml.product_id.type == 'product':
                Quant = self.env['stock.quant']
                rounding = ml.product_uom_id.rounding

                # if this move line is force assigned, unreserve elsewhere if needed
                if not ml.location_id.should_bypass_reservation() and float_compare(ml.qty_done, ml.product_qty, precision_rounding=rounding) > 0:
                    extra_qty = ml.qty_done - ml.product_qty
                    ml._free_reservation(ml.product_id, ml.location_id, extra_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, ml_to_ignore=done_ml)
                # unreserve what's been reserved
                if not ml.location_id.should_bypass_reservation() and ml.product_id.type == 'product' and ml.product_qty:
                    try:
                        Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                    except UserError:
                        Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)

                # move what's been actually done
                quantity = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id, rounding_method='HALF-UP')
                ####################################
                ####### CHANGES Happen Here ########
                ####################################
                qty_available_before_consumption = Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                negative_consumption = quantity - qty_available_before_consumption
                available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_id, -quantity, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                # We keep track of the negative consumption only for move that leave the stock (so that have been consumed from the stock),
                # since we delete negative stock quant the available quantity should be zero.
                if Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id) == 0 and negative_consumption > 0 and ml.move_id._is_out():
                    ml.move_id.negative_consumption += ml.product_uom_id._compute_quantity(negative_consumption, ml.move_id.product_uom)
                    lot = ml.lot_id or ml.lot_produced_id
                    if lot:
                        lot.add_negative_consumption_log(ml, negative_consumption)
                ####################################
                ####################################
                if available_qty < 0 and ml.lot_id:
                    # see if we can compensate the negative quants with some untracked quants
                    untracked_qty = Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                    if untracked_qty:
                        taken_from_untracked_qty = min(untracked_qty, abs(quantity))
                        Quant._update_available_quantity(ml.product_id, ml.location_id, -taken_from_untracked_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id)
                        Quant._update_available_quantity(ml.product_id, ml.location_id, taken_from_untracked_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                Quant._update_available_quantity(ml.product_id, ml.location_dest_id, quantity, lot_id=ml.lot_id, package_id=ml.result_package_id, owner_id=ml.owner_id, in_date=in_date)
            done_ml |= ml
        # Reset the reserved quantity as we just moved it to the destination location.
        (self - ml_to_delete).with_context(bypass_reservation_update=True).write({
            'product_uom_qty': 0.00,
            'date': fields.Datetime.now(),
        })


class UnvcStockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    def process(self):
        pick_to_backorder = self.env['stock.picking']
        pick_to_do = self.env['stock.picking']
        for picking in self.pick_ids:
            # If still in draft => confirm and assign
            if picking.state == 'draft':
                picking.action_confirm()
                if picking.state != 'assigned':
                    picking.action_assign()
                    if picking.state != 'assigned':
                        raise UserError(_("Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
            for move in picking.move_lines:
                for move_line in move.move_line_ids:
                    # FIX SOS: do note copy reserved quantity if NULL (bug for scrap process)
                    if move_line.product_uom_qty > 0:
                        move_line.qty_done = move_line.product_uom_qty
            if picking._check_backorder():
                pick_to_backorder |= picking
                continue
            pick_to_do |= picking
        # Process every picking that do not require a backorder, then return a single backorder wizard for every other ones.
        if pick_to_do:
            pick_to_do.action_done()
        if pick_to_backorder:
            return pick_to_backorder.action_generate_backorder_wizard()
        return False
