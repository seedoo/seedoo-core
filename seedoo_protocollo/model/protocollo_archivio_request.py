# -*- coding: utf-8 -*-
# This file is part of Seedoo.  The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

import os
import logging
from openerp.osv import orm, fields
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class protocollo_archivio_request(orm.Model):
    _name = 'protocollo.archivio.request'

    _columns = {
        'archivio_id': fields.many2one('protocollo.archivio', 'Archivio', ondelete='cascade', readonly=True),
        'aoo_id': fields.many2one('protocollo.aoo', 'AOO', readonly=True),
        'interval_type': fields.selection([
            ('date', 'Intervallo per data'),
            ('number', 'Intervallo per numero')
        ], 'Tipo di intervallo', readonly=True),
        'date_start': fields.datetime('Data Inizio', readonly=True),
        'date_end': fields.datetime('Data Fine', readonly=True),
        'year_start': fields.char('Anno Inizio', readonly=True),
        'year_end': fields.char('Anno Fine', readonly=True),
        'protocol_start': fields.char('Protocollo Inizio', readonly=True),
        'protocol_end': fields.char('Protocollo Fine', readonly=True),
        'state': fields.selection([
            ('waiting', 'In Attesa'),
            ('running', 'In Esecuzione'),
            ('error', 'Errore'),
            ('completed', 'Concluso'),
        ], 'Stato', readonly=True),
        'running_start': fields.datetime('Inizio Esecuzione', readonly=True),
        'running_end': fields.datetime('Fine Esecuzione', readonly=True),
        'archived_protocol_count': fields.integer('Protocolli Archiviati', readonly=True),
        'error': fields.text('Errore', readonly=True),
    }

    def run(self, cr, uid, ids, context=None):
        protocollo_obj = self.pool.get('protocollo.protocollo')
        archivio_obj = self.pool.get('protocollo.archivio')
        archivio_request_obj = self.pool.get('protocollo.archivio.request')
        archivio_corrente_id = archivio_obj._get_archivio_ids(cr, uid, True)[0]

        # si controlla che non ci siano archivazioni in esecuzione
        archivio_request_ids = archivio_request_obj.search(cr, uid, [('state', '=', 'running')], order='id ASC')
        if archivio_request_ids:
            return

        # per ogni richiesta in attesa si esegue la procedura di archiviazione
        for archivio_request_id in ids:
            archivio_request = archivio_request_obj.browse(cr, uid, archivio_request_id)
            if archivio_request.state in ['running', 'completed']:
                return

            archivio_request_obj.write(cr, uid, archivio_request_id, {
                'state': 'running',
                'running_start': fields.datetime.now()
            })

            archivio_corrente_id = archivio_obj._get_archivio_ids(cr, uid, True)[0]
            archivio_id = archivio_request.archivio_id.id
            interval_type = archivio_request.interval_type
            aoo_id = archivio_request.aoo_id.id
            date_start = archivio_request.date_start
            date_end = archivio_request.date_end
            year_start = archivio_request.year_start
            protocol_start = archivio_request.protocol_start
            year_end = archivio_request.year_end
            protocol_end = archivio_request.protocol_end

            newpid = os.fork()
            # se il nuovo pid è uguale a 0 allora è il processo figlio, se è maggiore di 0 è il processo padre
            if newpid == 0:
                # il processo figlio deve eseguire lo smaltimento delle richieste di creazione archivio
                _logger.debug("PID PROCESSO FIGLIO %d", (os.getpid()))
                archivio_obj.archive(
                    cr, uid,
                    archivio_request_id,
                    archivio_corrente_id, archivio_id, aoo_id,
                    interval_type,
                    date_start, date_end,
                    year_start, protocol_start, year_end, protocol_end
                )
                os._exit(0)
            else:
                _logger.debug("PID PROCESSO PADRE %d", (os.getpid()))