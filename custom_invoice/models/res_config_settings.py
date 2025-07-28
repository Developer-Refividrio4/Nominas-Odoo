# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    fg_nc_create = fields.Boolean(string='Crear notas de crédito de devoluciones')
    fg_code = fields.Boolean(string='Utilizar código de ticket en FG')
    fg_client = fields.Boolean(string='No cambiar cliente del recibo al hacer factura global')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param_obj = self.env['ir.config_parameter'].sudo()
        res.update(
            fg_nc_create = param_obj.get_param('custom_invoice.fg_nc_create'),
            fg_code = param_obj.get_param('custom_invoice.fg_code'),
            fg_client = param_obj.get_param('custom_invoice.fg_client'),
        )
        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        param_obj = self.env['ir.config_parameter'].sudo()
        param_obj.set_param('custom_invoice.fg_nc_create', self.fg_nc_create)
        param_obj.set_param('custom_invoice.fg_code', self.fg_code)
        param_obj.set_param('custom_invoice.fg_client', self.fg_client)
        return res
