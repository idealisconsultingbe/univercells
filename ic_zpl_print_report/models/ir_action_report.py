# -*- coding: utf-8 -*-
##############################################################################
#
# This module is developed by Idealis Consulting SPRL
# Copyright (C) 2013 Idealis Consulting SPRL (http://www.idealisconsulting.com).
# All Rights Reserved
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import unicodedata
import lxml.html
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.model
    def _get_raw(self, ids, qty=1):
        html = self.render_qweb_html(ids, self.report_name)[0]
        text = ""
        try:
            root = lxml.html.fromstring(html)
            match_klass = (
                "//div[contains(concat(' ', normalize-space(@class), ' '), "
                "' {} ')]"
            )
            for x in range(qty):
                for node in root.xpath(match_klass.format('raw')):
                    text += node.text
        except lxml.etree.XMLSyntaxError:
            pass
        text = text.replace('\n', '')
        nfkd_form = unicodedata.normalize('NFKD', text)
        text = u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
        # text = text.encode('ASCII', 'ignore')
        # text = text.decode('string_escape')
        return text

    def hw_print(self, docids, printer_id=False, qty=1):
        document = self._get_raw(docids, qty=qty)
        behaviour = self.behaviour() # [self.id]
        printer = False
        if printer_id:
            printer = self.env['printing.printer'].browse(printer_id)
        if not printer:
            printer = behaviour['printer']
        if not printer:
            raise UserError(_('No printer assigned'))
        try:
            printer.print_document(self, document.encode('utf-8'), doc_format='raw')
        except UnicodeEncodeError:
            raise
        except Exception:
            _logger.exception('Printer unavailable')
            raise UserError(_('Printer unavailable'))

