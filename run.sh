#!/bin/bash

./venv/bin/python ./OCB/openerp-server \
    --addons-path=OCB/openerp/addons,OCB/addons,web,seedoo-core,l10n-italy,server-tools \
    --xmlrpc-port=8069 \
    --db_host=127.0.0.1 \
    --db_port=5432 \
    --db_user=seedoo \
    --db_password=seedoo \
    --data-dir=~/seedoo/data \
    --logfile=~/seedoo/log/seedoo.log &
    
