<?xml version="1.0" encoding="utf-8"?>
<odoo>
        <record id="view_hr_wizard" model="ir.ui.view">
            <field name="name">Pdf.generation.form</field>
            <field name="model">hr.wizard</field>
            <field name="arch" type="xml">
            <form string="generation fichier">
                <group>
                    <field name="message" />
                </group>
                <footer>
                    <button string="OK" special="cancel" class="oe_highlight"/>
                </footer>
            </form>
            </field>
        </record>
</odoo>