![Seedoo](doc/img/logo.png "Seedoo")

> La piattaforma software di nuova generazione per la digitalizzazione della PA.

Il software gestisce l'intero iter documentale in maniera personalizzata e integrata,
**Protocollo informatico**, **Gestione Documentale**, Analisi dei Dati, sono alcuni degli strumenti
che permettono alla nuova PA di perseguire i propri obiettivi in un'ottica di performance,
governance e trasparenza verso il cittadino.

# Installazione

Per il funzionamento dell'applicazione è necessario un ambiente GNU/Linux con database PostgreSQL.
La seguente procedura è basata sulla distribuzione GNU/Linux Ubuntu Server 16.04 amd64.

## Installazione dipendenze di sistema

Installare da utente root i seguenti pacchetti:

```bash
apt-get install wkhtmltopdf node-less inkscape pandoc texlive-fonts-recommended \
    build-essential automake autoconf libtool pkg-config python-dev python-virtualenv \
    python-pip python-setuptools libjpeg-dev libgif-dev libpng12-dev libpq-dev libxml2-dev \
    libxslt1-dev libldap2-dev libssl-dev libfreetype6-dev libwebp-dev libdotconf-dev \
    libsasl2-dev libyaml-dev libtiff5-dev postgresql postgresql-client
```
## Download del codice

Entrare in ~/git e clonare il repository

```bash
git clone https://github.com/seedoo/seedoo.git ~/seedoo
cd ~/seedoo
git submodule init
git submodule update
```

## Creazione Python virtualenv

Creare un virtualenv python ed installare le dipendenze necessarie:

```bash
cd ~/seedoo
virtualenv venv
./venv/bin/pip install -r ocb/requirements.txt 
./venv/bin/pip install -r requirements.txt
```

## Creazione utente database PostgreSQL

Creare un utente PostegreSQL dedicato per Seedoo con i diritti per la creazione di database. 

Collegarsi al database PostgreSQL come utente amministratore (utente *postgres*) è possibile effetture la creazione dell'utente *seedoo* con la seguente query:

```postgresplsql
CREATE ROLE seedoo NOSUPERUSER NOCREATEROLE CREATEDB LOGIN INHERIT NOREPLICATION ENCRYPTED PASSWORD 'seedoo';
```

## Avviare Odoo

Avviare Odoo usando il virtualenv:

```bash
cd ~/seedoo
./venv/bin/python ./ocb/openerp-server \
    --addons-path=ocb/openerp/addons,ocb/addons,core,addons/seedoo-attivita,oca/l10n-italy \
    --xmlrpc-port=8069 \
    --db_host=127.0.0.1 \
    --db_port=5432 \
    --db_user=seedoo \
    --db_password=seedoo
```
## Creazione Database Odoo

Una volta avviato Odoo collegarsi al seguente indirizzo :

http://localhost:8069

e creare un database di partenza per i moduli Seedo. 



# Bug Tracker

In caso si voglia segnalare un bug è possibile farlo su [GitHub Issues](https://github.com/seedoo/seedoo/issues).

# Credits

### Contributors

* Alessio Gerace <alessio.gerace@agilebg.com>
* Lorenzo Battistini <lorenzo.battistini@agilebg.com>
* Roberto Onnis <roberto.onnis@innoviu.com>
* Daniele Sanna <daniele.sanna@flosslab.com>
* Samuele Collu <Samuele.collu@flosslab.com>
* Saul Lai <saul.lai@flosslab.com>
* Francesco Alba <francesco.alba@flosslab.com>
* Norman Argiolas <norman.argiolas@flosslab.com>
* Andrea Peruzzu <andrea.peruzzu@flosslab.com>
* Luca Cireddu <luca.cireddu@flosslab.com>

### Maintainer

Questo software è mantenuto dalla communità Seedoo.

Seedoo è un prodotto supportato da Agilebg, Flosslab e Innoviù, aziende specializzate nella realizzazione di software
avanzati per Pubbliche Amministrazioni ed Enti Privati.

Per uteriori informazioni, visitare il sito [www.seedoo.it](www.seedoo.it).
