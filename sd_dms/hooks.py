from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        env["sd.dms.document"].get_instance_configuration("001")
    except Exception as e:
        pass
