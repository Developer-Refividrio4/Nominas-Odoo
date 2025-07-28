# -*- coding: utf-8 -*-
from odoo import fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    tipo_proveedor = fields.Selection(
        selection=[('04', _('04 - Proveedor nacional')),
                   ('05', _('05 - Proveedor extranjero')),
                   ('15', _('15 - Proveedor global')),],
        string=_('Tipo de tercero'),
    )

    tipo_operacion = fields.Selection(
        selection=[
                   ('02', _('02 - Enajenación de bienes')),
                   ('03', _('03 - Prestación de servicio profesionales')),
                   ('06', _('06 - Uso o goce temporal de bienes')),
                   ('07', _('07 - Importación de bienes o servicios')),
                   ('08', _('08 - Importación por transferencia virtual')),
                   ('85', _('85 - Otros')),
                   ('87', _('87 - Operaciones globales')),],
        string=_('Tipo de operación'),
    )

    pais_diot = fields.Many2one('catalogos.pais_diot', string='Pais')

    tipo_frontera = fields.Selection(
        selection=[('01', _('Norte')),
                   ('02', _('Sur')),],
        string=_('Proveedor de frontera'),
    )
