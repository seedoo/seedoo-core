from odoo import api, models


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        field = self._fields[field_name]
        # si prosegue con il normale flusso se almeno una delle seguenti condizioni non è verificata:
        # condizione 1: l'opzione load_only_children_onexpand è abilitata
        # condizione 2: la tipologia del campo è many2one o many2many
        # condizione 3: le voci devono essere strutturate in maniera gerarchica tramite il field del relativo parent
        condizione1 = kwargs.get("load_only_children_onexpand", False)
        condizione2 = field.type == "many2one" or field.type == "many2many"
        condizione3 = kwargs.get("hierarchize", False)
        if not condizione1 or not condizione2 or not condizione3:
            return super(Base, self).search_panel_select_range(field_name, **kwargs)
        # recupero del modello del campo many2one o many2many
        comodel = self.env[field.comodel_name]
        # recupero del'id della voce di categoria selezionata
        active_value_id = kwargs.get("active_value_id", False)
        # inizialiazzione del domain e della lista dei campi da leggere
        domain = []
        display_field_name = kwargs.get("load_only_children_onexpand_display_name", "display_name")
        field_name_list = [display_field_name]
        parent_field_name = comodel._parent_name if comodel._parent_name in comodel._fields else False
        # se non è selezionata nessuna voce allora si ricercano tutte le voci di primo livello
        if not active_value_id and parent_field_name:
            domain = [(parent_field_name, "=", False)]
            field_name_list.append(parent_field_name)
        elif active_value_id and parent_field_name:
            domain = [(parent_field_name, "=", active_value_id)]
            field_name_list.append(parent_field_name)
        search_result_list = comodel.search_read(domain, field_name_list)
        values = []
        for search_result in search_result_list:
            value = {
                "id": search_result["id"],
                "display_name": search_result[display_field_name]
            }
            if not parent_field_name:
                continue
            value[parent_field_name] = search_result[parent_field_name][0] if search_result[parent_field_name] else False
            value["children_count"] = comodel.search_count([(parent_field_name, "=", search_result["id"])])
            values.append(value)
        return {
            "parent_field": parent_field_name,
            "values": values
        }