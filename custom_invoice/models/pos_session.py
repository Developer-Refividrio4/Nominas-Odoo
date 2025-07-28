# -*- coding: utf-8 -*-

from odoo import models, api, _, tools, SUPERUSER_ID


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        model_names = super(PosSession, self)._pos_ui_models_to_load()
        model_names.append('catalogo.regimen.fiscal')
        return model_names

    def _loader_params_catalogo_regimen_fiscal(self):
        return {
            'search_params': {
                'domain': [],
                'fields': ['id', 'description'],
                'order': 'id',
            },
        }

    def _get_pos_ui_catalogo_regimen_fiscal(self, params):
        return self.env['catalogo.regimen.fiscal'].search_read(**params['search_params'])

    def _loader_params_res_partner(self):
        result = super()._loader_params_res_partner()
        result['search_params']['fields'].append('street2')
        result['search_params']['fields'].append('regimen_fiscal_id')
        return result
