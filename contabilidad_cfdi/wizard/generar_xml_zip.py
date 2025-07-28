
from odoo import api, models, fields,_
import requests
from odoo.exceptions import UserError
from datetime import datetime
import base64
import json
import logging
from lxml import etree as ET
_logger = logging.getLogger(__name__)

class ContaXMLZIPDownload(models.TransientModel):
    _name = 'conta.xml.zip.download'
    
    xml_data = fields.Binary("XML File")
    zip_data = fields.Binary("Zip File")

    def download_xml_zip_file(self):
        if self._context.get('file_type','')=='zip':
            field_name = 'zip_data'
            filename = '%s.zip'%self._context.get('conta_name')
        else:
            field_name = 'xml_data'
            filename = '%s.xml'%self._context.get('conta_name')
        return {
                'type' : 'ir.actions.act_url',
                'url': "/web/content/?model="+self._name+"&id=" + str(self.id) + "&field="+field_name+"&download=true&filename="+filename,
                'target':'self',
                }   

