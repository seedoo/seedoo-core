{
    "name": "Disable child of search panel",
    "version": "14.0.2.0.0",
    "category": "Security",
    "summary": "Disable 'child_of' domain on expand event of item in search panel",
    "description": """
        To enable the feature set option disable_childof_domain_onexpand to true in the options attribute of field added in search panel.
    """,

    "author": "Flosslab",
    "website": "https://www.flosslab.com",
    "license": "LGPL-3",
    "sequence": 0,
    "depends": [
        "fl_m2m_search_panel"
    ],
    "data": [
        "templates/assets.xml",
    ],
    'qweb': [
        "static/src/xml/search_panel.xml"
    ],
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "installable": True,
    "application": False,
    "auto_install": False
}
