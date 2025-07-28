# -*- coding: utf-8 -*-

from collections import defaultdict

import urllib.parse
import urllib.request
from datetime import date

from odoo import models, fields, api


class ResCurrencyRateProviderMXBDM(models.Model):
    _inherit = 'res.currency.rate.provider'

    service = fields.Selection(
        selection_add=[('MX_BdM', 'Banco de Mexico USD')], ondelete={"MX_BdM": "set default"},
    )
    tipo = fields.Selection(selection=[('pago', 'Pago'),
                                       ('fix', 'Fix')], string='Tipo', default='pago')

    def _get_supported_currencies(self):
        self.ensure_one()
        if self.service != 'MX_BdM':
            return super()._get_supported_currencies()  # pragma: no cover

        # List of currencies obrained from:
        # https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip
        return ['USD']

    def _mx_bdm_provider_urlopen(self, url):
        self.ensure_one()

        parsed_url = urllib.parse.urlparse(url)
        parsed_query = urllib.parse.parse_qs(parsed_url.query)
        parsed_url = parsed_url._replace(query=urllib.parse.urlencode(
            parsed_query,
            doseq=True,
            quote_via=urllib.parse.quote,
        ))
        url = urllib.parse.urlunparse(parsed_url)

        request = urllib.request.Request(url)
        res = urllib.request.urlopen(request)
        return res.read()
    
    def rate_retrieve(self):
        """ Get currency exchange from Banxico.xml and proccess it
        TODO: Get correct data from xml instead of process string
        """
        if self.tipo == 'fix':
           url = ('http://www.banxico.org.mx/rsscb/rss?BMXC_canal=fix&BMXC_idioma=es')
        else:
           url = ('http://www.banxico.org.mx/rsscb/rss?BMXC_canal=pagos&BMXC_idioma=es')

        from xml.dom.minidom import parse
        from io import BytesIO

        
        rawfile = self._mx_bdm_provider_urlopen(url)

        dom = parse(BytesIO(rawfile))
        
        value = dom.getElementsByTagName('cb:value')[0]
        rate = value.firstChild.nodeValue

        return float(rate)
            
    def _obtain_rates(self, base_currency, currencies, date_from, date_to):
        self.ensure_one()
        if self.service != 'MX_BdM':
            return super()._obtain_rates(base_currency, currencies, date_from,
                                         date_to)
        
        if base_currency not in currencies:
            currencies.append(base_currency)
        
        content = defaultdict(dict)
        dt = date.today()

        date_content = content[dt.isoformat()]
                
        # Suported currencies
        suported = ['USD']
        # Get currency data
        main_rate = self.rate_retrieve()
        
        for curr in currencies:
            if curr in suported:
                if curr == 'USD':
                    rate = 1 / main_rate
                elif curr == 'EUR':
                    rate = 1 / main_rate
                else:
                    rate = main_rate
                
                date_content[curr] = rate
            else:
                # No other currency supported
                continue

        return content

    