# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Idealis Consulting
#    Copyright (c) 2020 Idealis Consulting S.A. (http://www.idealisconsulting.com)
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
{
    'name': 'Univercells Stock Add-ons',
    'version': '1.0',
    'author': 'Idealis Consulting',
    'summary': 'Stock Management Add-ons For Univercells',
    'sequence': 1,
    'description': """
    """,
    'category': 'Stock',
    'website': 'https://www.idealisconsulting.com',
    'depends': ['base', 'stock', 'unvc_purchase', 'stock_account'],
# , 'stock_mts_mto_rule', 'ic_zpl_print_report'
    'data': [
        'security/ir.model.access.csv',
        'reports/unvc_lot_labels_report.xml',
        'views/unvc_stock_picking_view.xml',
        'views/unvc_stock_move_view.xml',
        'views/unvc_stock_picking_type_view.xml',
        'views/unvc_stock_location_view.xml',
        'views/unvc_product_product_view.xml',
        'views/unvc_res_partner_view.xml',
        'views/unvc_stock_inventory_view.xml',
        'views/unvc_stock_production_lot_view.xml',
        'wizard/unvc_print_lot_labels_view.xml',
        'wizard/unvc_stock_quantity_history_view.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
