from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        env["mail.mail"].get_instance_configuration("004")
    except Exception:
        pass
