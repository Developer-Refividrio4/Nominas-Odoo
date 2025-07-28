from odoo import models, fields, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ks_enable_ledger_in_bal = fields.Boolean('Enable Ledger Initial Balance',
                                             config_parameter='ks_enable_ledger_in_bal')
    ks_disable_trial_en_bal = fields.Boolean('Disable Trial Initial Balance',
                                             config_parameter='ks_disable_trial_en_bal')
    ks_disable_bs_sign = fields.Boolean('Disable Balance Sheet Sign',
                                        config_parameter='ks_disable_bs_sign')
    ks_enable_net_tax = fields.Boolean('Enable Net Tax',
                                             config_parameter='ks_enable_net_tax')

