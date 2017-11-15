#!/bin/bash

Xvfb :10 &

export DISPLAY=":10"

./venv/bin/python ./ocb/openerp-server \
    --addons-path=ocb/openerp/addons,ocb/addons,seedoo-core,l10n-italy \
    --xmlrpc-port=8069 \
    --db_host=127.0.0.1 \
    --db_port=5432 \
    --db_user=seedoo \
    --db_password=seedoo \
    --logfile=$HOME/seedoo.log &
