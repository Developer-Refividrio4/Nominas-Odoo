import logging
from odoo import api, fields, models
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def create_from_ui(self, partner):
        if 'regimen_fiscal_id' in partner:
            try:
                partner['regimen_fiscal_id'] = int(partner['regimen_fiscal_id'])
            except (ValueError, TypeError) as e:
                _logger.warning(e)
            except Exception as e:
                raise ValidationError(e) from e
        return super(ResPartner, self).create_from_ui(partner)
