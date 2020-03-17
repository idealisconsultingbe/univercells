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
{
    'name': 'Univercells Purchase Add-ons',
    'version': '1.0',
    'author': 'Idealis Consulting',
    'summary': 'Purchase Management Add-ons For Univercells',
    'sequence': 1,
    'description': """
    """,
    'category': 'Purchase',
    'website': 'https://www.idealisconsulting.com',
    'depends': [
        'base',
        'stock',
        'purchase',
        'analytic',
        'hr'
        # 'purchase_tripple_approval',
    ],
    'data': [
        'reports/unvc_stock_picking_operation_report.xml',
        'views/unvc_stock_location_view.xml',
        'views/unvc_stock_picking_view.xml',
        'views/unvc_purchase_order_view.xml',
        'views/unvc_account_analytic_account_view.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
