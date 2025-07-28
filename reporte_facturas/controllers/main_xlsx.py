# -*- coding: utf-8 -*-
from odoo.http import route
from odoo.addons.web.controllers import report

class ReportControllerInherit(report.ReportController):

    def report_routes(self, reportname, docids=None, converter=None, **data):
        if converter == "xlsx":
            if data['context'] and data['context'].partition('?options'):
                data['context'] = data['context'].partition('?options')[0]
        return super(ReportControllerInherit, self).report_routes(reportname=reportname, docids=docids, converter=converter, **data)
