from lxml import etree

from odoo import models, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class UtilityXml(models.AbstractModel):
    _name = "fl.utility.xml"
    _description = "Utility for XML manipulation"

    @api.model
    def parse(self, string: str) -> etree._Element:
        if not string:
            raise ValidationError(_("XML String not valid"))

        root_element = etree.fromstring(string.encode())
        return root_element

    @api.model
    def serialize(
            self,
            element: etree._Element,
            method: str = "xml",
            xml_declaration: bool = False,
            pretty: bool = False
    ) -> str:
        if element is None:
            raise ValidationError(_("XML Element not valid"))

        kwargs = {
            "xml_declaration": xml_declaration,
            "pretty_print": pretty,
            "standalone": True,
            "method": method
        }

        if method in ["xml"]:
            kwargs["encoding"] = "UTF-8"

        xml_bytes = etree.tostring(element, **kwargs)

        string: str = xml_bytes.decode()
        return string

    @api.model
    def pretty(self, xml_data: str = "") -> str:
        xml = self.parse(xml_data)
        xml_string = self.serialize(xml, pretty=True)
        return xml_string

    @api.model
    def find_elements(self, element: etree._Element, xpath: str):
        if element is None:
            raise ValidationError(_("XML Element not valid"))

        if not xpath:
            raise ValidationError(_("XML X-Path not valid"))

        elements = element.xpath(xpath)
        if not elements:
            raise ValidationError(_("No elements found using given XPath"))

        return elements

    @api.model
    def find_first_element(self, element: etree._Element, xpath: str) -> etree._Element:
        elements = self.find_elements(element, xpath)
        element = elements[0]
        return element

    @api.model
    def create_root_element(self, name: str = "", attribs: dict = None) -> etree._Element:
        if not name or not name.strip():
            raise ValidationError(_("XML Element name not valid"))

        if not attribs:
            attribs = {}

        element_name = name.strip()
        element = etree.Element(element_name)

        self._add_attribs(element, attribs)

        return element

    @api.model
    def create_child_element(self,
                             parent: etree._Element,
                             name: str,
                             text: str = "",
                             attribs: dict = None) -> etree._Element:
        if parent is None:
            raise ValidationError(_("XML Parent Element not valid"))

        if not name or not name.strip():
            raise ValidationError(_("XML Element name not valid"))

        if attribs is None:
            attribs = {}

        sub_element = etree.SubElement(parent, name)

        self._add_attribs(sub_element, attribs)

        if text:
            sub_element.text = text

        return sub_element

    @api.model
    def create_children_elements(self, parent: etree._Element, children: dict = None):
        if parent is None:
            raise ValidationError(_("XML Parent Element not valid"))

        if children is None:
            children = {}

        for child_name, child_text in children.items():
            self.create_child_element(parent, child_name, child_text)

    @staticmethod
    def _add_attribs(element, attribs: dict):
        if attribs:
            for attrib_name, attrib_value in attribs.items():
                if attrib_name and attrib_name.strip():
                    element.attrib[attrib_name.strip()] = attrib_value
