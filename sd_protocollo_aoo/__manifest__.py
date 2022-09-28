{
    "name": "AOO - Protocollo",
    "version": "14.0.2.0.0",
    "category": "Document Management",
    "summary": "Aggiunge la AOO al Protocollo",
    "description": """
        Gestione della Area Organizzativa Omogenea nel flusso di protocollazione
    """,
    "author": "Flosslab",
    "website": "https://www.flosslab.com",
    "license": "LGPL-3",
    "sequence": 0,
    "depends": [
        "fl_set_pa",
        "sd_protocollo_pec",
        "sd_dms_aoo"
    ],
    "data": [
        "data/inherit_fl_set_set.xml",
        "data/inherit_sd_dms_storage.xml",
        "data/inherit_sd_protocollo_registro.xml",
        "data/inherit_sd_protocollo_archivio.xml",
        "data/inherit_sd_protocollo_cartella.xml",

        "views/inherit_sd_protocollo_registro.xml",
        "views/inherit_sd_protocollo_registro_giornaliero.xml",
        "views/inherit_sd_protocollo_registro_giornaliero_configurazione.xml",
        "views/inherit_sd_protocollo_registro_emergenza.xml",
        "views/inherit_sd_protocollo_protocollo.xml",
        "views/inherit_sd_protocollo_archivio.xml",
        "views/inherit_sd_protocollo_cartella.xml",

        "wizards/inherit_sd_protocollo_crea_da_mail_view.xml",

        "templates/inherit_protocollo_dashboard_template.xml"
    ],
    "installable": True,
    "application": False,
    "auto_install": False
}
