from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        env["fl.set.set"].get_instance_configuration("003")
    except Exception:
        pass
