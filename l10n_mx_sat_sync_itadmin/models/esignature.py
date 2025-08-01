# -*- coding: utf-8 -*-

import base64
import logging
import ssl
import subprocess
import tempfile
from datetime import datetime

_logger = logging.getLogger(__name__)

try:
    from OpenSSL import crypto
except ImportError:
    _logger.warning('OpenSSL library not found. If you plan to use l10n_mx_edi, please install the library from https://pypi.python.org/pypi/pyOpenSSL')

from pytz import timezone
import pytz

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError, UserError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT


KEY_TO_PEM_CMD = 'openssl pkcs8 -in %s -inform der -outform pem -out %s -passin file:%s'


def convert_key_cer_to_pem(key, password):
    # TODO compute it from a python way
    with tempfile.NamedTemporaryFile('wb', suffix='.key', prefix='edi.mx.tmp.') as key_file, \
            tempfile.NamedTemporaryFile('wb', suffix='.txt', prefix='edi.mx.tmp.') as pwd_file, \
            tempfile.NamedTemporaryFile('rb', suffix='.key', prefix='edi.mx.tmp.') as keypem_file:
        key_file.write(key)
        key_file.flush()
        pwd_file.write(password)
        pwd_file.flush()
        subprocess.call((KEY_TO_PEM_CMD % (key_file.name, keypem_file.name, pwd_file.name)).split())
        key_pem = keypem_file.read()
    return key_pem


def str_to_datetime(dt_str, tz=timezone('America/Mexico_City')):
    return tz.localize(fields.Datetime.from_string(dt_str))


class Certificate(models.Model):
    _name = 'l10n.mx.esignature.certificate'
    _description = 'MX E-signature'

    content = fields.Binary(
        string='Certificado Cer',
        help='Archivo Cer',
        required=True,)
    key = fields.Binary(
        string='Certificado Key',
        help='Archivo Key',
        required=True,)
    password = fields.Char(
        string='Contraseña del Certificado',
        help='Contraseña del Certificado',
        required=True,)
    holder = fields.Char(
        string='Titular',
        help='Titular del certificado',
        required=False,)
    holder_vat = fields.Char(
        string="RFC",
        help="RFC del certificado",
        required=False,)
    serial_number = fields.Char(
        string='Numero de serie',
        help='The serial number to add to electronic documents',
        readonly=True,
        index=True)
    date_start = fields.Datetime(
        string='Fecha inicio',
        help='The date on which the certificate starts to be valid',
        readonly=True)
    date_end = fields.Datetime(
        string='Fecha expiración',
        help='The date on which the certificate expires',
        readonly=True)

    @tools.ormcache('content')
    def get_pem_cer(self, content):
        '''Get the current content in PEM format
        '''
        self.ensure_one()
        return ssl.DER_cert_to_PEM_cert(base64.decodebytes(content)).encode('UTF-8')

    @tools.ormcache('key', 'password')
    def get_pem_key(self, key, password):
        '''Get the current key in PEM format
        '''
        self.ensure_one()
        return convert_key_cer_to_pem(base64.decodebytes(key), password.encode('UTF-8'))

    def get_data(self):
        '''Return the content (b64 encoded) and the certificate decrypted
        '''
        self.ensure_one()
        cer_pem = self.get_pem_cer(self.content)
        certificate = crypto.load_certificate(crypto.FILETYPE_PEM, cer_pem)
        for to_del in ['\n', ssl.PEM_HEADER, ssl.PEM_FOOTER]:
            cer_pem = cer_pem.replace(to_del.encode('UTF-8'), b'')
        return cer_pem, certificate

    def get_mx_current_datetime(self):
        '''Get the current datetime with the Mexican timezone.
        '''
        mexican_tz = timezone('America/Mexico_City')
        return datetime.now(mexican_tz)
#         return fields.Datetime.context_timestamp(
#             self.with_context(tz='America/Mexico_City'), fields.Datetime.now())

    def get_valid_certificate(self):
        '''Search for a valid certificate that is available and not expired.
        '''
        mexican_dt = self.get_mx_current_datetime()
        for record in self:
            timezone = self._context.get('tz')
            if not timezone:
               timezone = self.env.user.partner_id.tz or 'America/Mexico_City'

            local = pytz.timezone(timezone)
            date_start = record.date_start.replace(tzinfo=pytz.UTC).astimezone(local)
            date_end = record.date_end.replace(tzinfo=pytz.UTC).astimezone(local)

            if date_start <= mexican_dt <= date_end:
                return record
        return None

    def get_encrypted_cadena(self, cadena):
        '''Encrypt the cadena using the private key.
        '''
        self.ensure_one()
        key_pem = self.get_pem_key(self.key, self.password)
        private_key = crypto.load_privatekey(crypto.FILETYPE_PEM, key_pem)
        encrypt = 'sha256WithRSAEncryption'
        cadena_crypted = crypto.sign(private_key, cadena, encrypt)
        return base64.b64encode(cadena_crypted)

    @api.constrains('content', 'key', 'password')
    def _check_credentials(self):
        '''Check the validity of content/key/password and fill the fields
        with the certificate values.
        '''
        mexican_tz = timezone('America/Mexico_City')
        mexican_dt = self.get_mx_current_datetime()
        date_format = '%Y%m%d%H%M%SZ'
        for record in self:
            # Try to decrypt the certificate
            try:
                cer_pem, certificate = record.get_data()
                before = mexican_tz.localize(
                    datetime.strptime(certificate.get_notBefore().decode("utf-8"), date_format))
                after = mexican_tz.localize(
                    datetime.strptime(certificate.get_notAfter().decode("utf-8"), date_format))
                serial_number = certificate.get_serial_number()
                subject = certificate.get_subject()
                holder = subject.CN
                holder_vat = certificate.get_subject().x500UniqueIdentifier.split(' ')[0]
            except Exception as e:
                raise ValidationError(_('The certificate content is invalid.'))
            # Assign extracted values from the certificate
            record.holder = holder
            record.holder_vat = holder_vat
            record.serial_number = ('%x' % serial_number)[1::2]
            record.date_start = before.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            record.date_end = after.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            if mexican_dt > after:
                raise ValidationError(_('The certificate is expired since %s') % record.date_end)
            # Check the pair key/password
            try:
                key_pem = self.get_pem_key(self.key, self.password)
                crypto.load_privatekey(crypto.FILETYPE_PEM, key_pem)
            except Exception:
                raise ValidationError(_('The certificate key and/or password is/are invalid.'))

    @api.model_create_multi
    def create(self, vals_list):
        res = super(Certificate, self).create(vals_list)
        self.clear_caches()
        return res

    def write(self, data):
        res = super(Certificate, self).write(data)
        self.clear_caches()
        return res

    def unlink(self):
#        if self.env['account.move'].search(
#                [('l10n_mx_edi_cfdi_certificate_id', 'in', self.ids)]):
#            raise UserError(_(
#                'You cannot remove a certificate that has already been used '
#                'to sign an invoice. Expired Certificates will not be used '
#                'as Odoo uses the latest valid certificate.'))
        res = super(Certificate, self).unlink()
        self.clear_caches()
        return res
