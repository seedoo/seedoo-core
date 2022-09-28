{
    "name": "Segnatura XML - Protocollo",
    "version": "14.0.2.0.0",
    "category": "Document Management",
    "summary": "Aggiunge le funzionalità di segnatura XML",
    "description": """
        Generazione della segnatura XML e per il parsing della segnatura XML contenuta in una mail in ingresso da protocollare
    """,
    "author": "Flosslab",
    "website": "https://www.flosslab.com",
    "license": "LGPL-3",
    "sequence": 0,
    "depends": [
        "sd_protocollo_pec",
    ],
    "external_dependencies": {
        "python": [
            "signxml",
            "pandas"
        ]
    },
    "data": [
        "data/ir_config_parameter.xml",

        "views/res_config_settings.xml",
        "views/sd_protocollo_protocollo.xml"
    ],
    "installable": True,
    "application": False,
    "auto_install": False
}
