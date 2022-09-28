import datetime
import logging
import string
import re

_logger = logging.getLogger(__name__)
try:
    import vatnumber
except ImportError:
    _logger.warning("VAT validation partially unavailable because the `vatnumber` Python library cannot be found. "
                    "Install it to support more countries, for example with `easy_install vatnumber`.")
    vatnumber = None

try:
    import stdnum
except ImportError:
    stdnum = None

from odoo import api, models, tools, _
from odoo.tools.misc import ustr
from odoo.exceptions import ValidationError, UserError
from stdnum.at.uid import compact as compact_at
from stdnum.be.vat import compact as compact_be
from stdnum.bg.vat import compact as compact_bg
from stdnum.ch.vat import compact as compact_ch, format as format_ch
from stdnum.cy.vat import compact as compact_cy
from stdnum.cz.dic import compact as compact_cz
from stdnum.de.vat import compact as compact_de
from stdnum.ee.kmkr import compact as compact_ee
# el not in stdnum
from stdnum.es.nif import compact as compact_es
from stdnum.fi.alv import compact as compact_fi
from stdnum.fr.tva import compact as compact_fr
from stdnum.gb.vat import compact as compact_gb
from stdnum.gr.vat import compact as compact_gr
from stdnum.hu.anum import compact as compact_hu
from stdnum.hr.oib import compact as compact_hr
from stdnum.ie.vat import compact as compact_ie
from stdnum.it.iva import compact as compact_it
from stdnum.lt.pvm import compact as compact_lt
from stdnum.lu.tva import compact as compact_lu
from stdnum.lv.pvn import compact as compact_lv
from stdnum.mt.vat import compact as compact_mt
from stdnum.mx.rfc import compact as compact_mx
from stdnum.nl.btw import compact as compact_nl
from stdnum.no.mva import compact as compact_no
# pe is not in stdnum
from stdnum.pl.nip import compact as compact_pl
from stdnum.pt.nif import compact as compact_pt
from stdnum.ro.cf import compact as compact_ro
from stdnum.se.vat import compact as compact_se
from stdnum.si.ddv import compact as compact_si
from stdnum.sk.dph import compact as compact_sk
from stdnum.ar.cuit import compact as compact_ar

# tr compact vat is not in stdnum


_eu_country_vat = {
    'GR': 'EL'
}

_eu_country_vat_inverse = {v: k for k, v in _eu_country_vat.items()}

_ref_vat = {
    'at': 'ATU12345675',
    'be': 'BE0477472701',
    'bg': 'BG1234567892',
    'ch': 'CHE-123.456.788 TVA or CH TVA 123456',  # Swiss by Yannick Vaucher @ Camptocamp
    'cl': 'CL76086428-5',
    'co': 'CO213123432-1 or CO213.123.432-1',
    'cy': 'CY12345678F',
    'cz': 'CZ12345679',
    'de': 'DE123456788',
    'dk': 'DK12345674',
    'ee': 'EE123456780',
    'el': 'EL12345670',
    'es': 'ESA12345674',
    'fi': 'FI12345671',
    'fr': 'FR32123456789',
    'gb': 'GB123456782',
    'gr': 'GR12345670',
    'hu': 'HU12345676',
    'hr': 'HR01234567896',  # Croatia, contributed by Milan Tribuson
    'ie': 'IE1234567FA',
    'it': 'IT12345670017',
    'lt': 'LT123456715',
    'lu': 'LU12345613',
    'lv': 'LV41234567891',
    'mt': 'MT12345634',
    'mx': 'ABC123456T1B',
    'nl': 'NL123456782B90',
    'no': 'NO123456785',
    'pe': '10XXXXXXXXY or 20XXXXXXXXY or 15XXXXXXXXY or 16XXXXXXXXY or 17XXXXXXXXY',
    'pl': 'PL1234567883',
    'pt': 'PT123456789',
    'ro': 'RO1234567897',
    'se': 'SE123456789701',
    'si': 'SI12345679',
    'sk': 'SK0012345675',
    'tr': 'TR1234567890 (VERGINO) veya TR12345678901 (TCKIMLIKNO)'  # Levent Karakas @ Eska Yazilim A.S.
}


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _split_vat(self, vat):
        vat_country, vat_number = vat[:2].lower(), vat[2:].replace(' ', '')
        return vat_country, vat_number

    @api.model
    def simple_vat_check(self, country_code, vat_number):
        '''
        Check the VAT number depending of the country.
        http://sima-pc.com/nif.php
        '''
        if not ustr(country_code).encode('utf-8').isalpha():
            return False
        check_func_name = 'check_vat_' + country_code
        check_func = getattr(self, check_func_name, None) or getattr(vatnumber, check_func_name, None)
        if not check_func:
            # No VAT validation available, default to check that the country code exists
            if country_code.upper() == 'EU':
                # Foreign companies that trade with non-enterprises in the EU
                # may have a VATIN starting with "EU" instead of a country code.
                return True
            country_code = _eu_country_vat_inverse.get(country_code, country_code)
            return bool(self.env['res.country'].search([('code', '=ilike', country_code)]))
        return check_func(vat_number)

    @api.model
    def fix_eu_vat_number(self, country_id, vat):
        europe = self.env.ref('base.europe')
        country = self.env["res.country"].browse(country_id)
        if not europe:
            europe = self.env["res.country.group"].search([('name', '=', 'Europe')], limit=1)
        if europe and country and country.id in europe.country_ids.ids:
            vat = re.sub('[^A-Za-z0-9]', '', vat).upper()
            country_code = _eu_country_vat.get(country.code, country.code).upper()
            if vat[:2] != country_code:
                vat = country_code + vat
        return vat

    @api.constrains('vat', 'country_id')
    def check_vat(self):
        check_func = self.simple_vat_check
        for partner in self:
            if not partner.vat:
                continue
            # check with country code as prefix of the TIN
            vat_country, vat_number = self._split_vat(partner.vat)
            if not check_func(vat_country, vat_number):
                # if fails, check with country code from country
                country_code = partner.commercial_partner_id.country_id.code
                if country_code:
                    if not check_func(country_code.lower(), partner.vat):
                        msg = partner._construct_constraint_msg(country_code.lower())
                        raise ValidationError(msg)

    def _construct_constraint_msg(self, country_code):
        self.ensure_one()
        vat_no = "'CC##' (CC=Country Code, ##=VAT Number)"
        vat_no = _ref_vat.get(country_code) or vat_no
        return '\n' + _(
            'The VAT number [%s] for partner [%s] does not seem to be valid. \nNote: the expected format is %s') % (
                   self.vat, self.name, vat_no)

    def default_compact(self, vat):
        return vat

    def _fix_vat_number(self, vat, country_id):
        code = self.env['res.country'].browse(country_id).code if country_id else False
        vat_country, vat_number = self._split_vat(vat)
        if code and code.lower() != vat_country:
            return vat
        check_func_name = 'compact_' + vat_country
        check_func = globals().get(check_func_name) or getattr(self, 'default_compact')
        vat_number = check_func(vat_number)
        format_func = globals().get('format_' + vat_country)
        return format_func(vat_country.upper() + vat_number) if format_func else vat_country.upper() + vat_number

    @api.model
    def create(self, values):
        if values.get('vat'):
            country_id = values.get('country_id')
            values['vat'] = self._fix_vat_number(values['vat'], country_id)
        error, values = self.check_vat_number(values)
        if error:
            raise UserError(error)
        return super(ResPartner, self).create(values)

    def write(self, values):
        for rec in self:
            ir_config_parameter = self.env["ir.config_parameter"].sudo()
            res_partner = self.env["res.partner"].sudo()

            if values.get('vat') and len(self.mapped('country_id')) == 1:
                country_id = values.get('country_id', self.country_id.id)
                values['vat'] = rec._fix_vat_number(values['vat'], country_id)

            if ir_config_parameter.get_param("fl_partner_vat.vat_unique"):
                if rec.company_type == "company":
                    if values.get('vat', False) and res_partner.search_count([('vat', '=', values.get('vat'))]) > 0:
                        error, values = self.check_vat_number(values)
                        if error:
                            raise UserError(error)
        return super(ResPartner, self).write(values)

    def check_vat_number(self,values):
        ir_config_parameter = self.env["ir.config_parameter"].sudo()
        res_partner = self.env["res.partner"].sudo()
        error = False
        if ir_config_parameter.get_param("fl_partner_vat.vat_mandatory"):
            if values.get('company_type', None) == "company" and not values.get('vat', False):
                error = _('You have not entered the VAT number')
                return error,values

        if ir_config_parameter.get_param("fl_partner_vat.vat_unique"):
            if res_partner.search_count([('vat', '=', values.get('vat'))]) > 0 and \
                    not (values.get("parent_id") or values.get("parent_personal_id") or values.get("parent_company_id"))\
                    and values.get('vat'):
                error = _('You have entered a VAT number already used')
                return error, values
        return error,values