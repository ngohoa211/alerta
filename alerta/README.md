```
curl -XPUT http://localhost:5000/alert/d78a0723-611a-4745-829e-010182588cf0/customer \
-H 'Authorization: Key 68CiQ9BlXUzTUEsmxnZ7g86hbxPb9gtZpkwUUEZ5' \
-H 'Content-type: application/json' \
-d '{
      "customer": "vna"
    }'

```
/root/stack.yml
```
# Use root/example as user/password credentials
version: '3.1'

services:

  mongo:
    image: mongo
    restart: always
    container_name: mongo
    network_mode: "host"
    environment:
      MONGO_INITDB_ROOT_USERNAME: root
      MONGO_INITDB_ROOT_PASSWORD: example

  mongo-express:
    container_name: mongo-express
    image: mongo-express
    restart: always
    network_mode: "host"
    environment:
      ME_CONFIG_MONGODB_ADMINUSERNAME: root
      ME_CONFIG_MONGODB_ADMINPASSWORD: example
      ME_CONFIG_MONGODB_SERVER: 127.0.1.1
      ME_CONFIG_MONGODB_PORT: 27017
```


file /etc/alertad.conf
```
DEBUG = True
SECRET_KEY = 'changeme'
BASE_URL = '/api'
USE_PROXYFIX = False
LOG_HANDLERS = ['console', 'file']
LOG_FILE = '/var/log/alertad.log'
LOG_MAX_BYTES = 5*1024*1024  # 5 MB
LOG_BACKUP_COUNT = 2
LOG_FORMAT = 'verbose'
DATABASE_URL = 'mongodb://root:example@127.0.1.1:27017/?replicaSet=test&connectTimeoutMS=300000'
DATABASE_NAME = 'monitoring'
DATABASE_RAISE_ON_ERROR = False  # creating tables & indexes manually
CORS_ORIGINS = [
    'http://localhost',
    'http://localhost:8000',
    'http://192.168.28.54:8000',
    r'https?://\w*\.?local\.alerta\.io:?\d*/?.*'  # => http(s)://*.local.alerta.io:<port>
]
```
alertad run --host 0.0.0.0 --port 8080
 wget https://github.com/alerta/alerta-webui/releases/latest/download/alerta-webui.tar.gz
tar zxvf alerta-webui.tar.gz
cd dist
python3 -m http.server 8000
/root/dist/config.json
```
{"endpoint": "http://192.168.28.54:8080"}
```



Alerta Release 7.0
==================

[![Build Status](https://travis-ci.org/alerta/alerta.png)](https://travis-ci.org/alerta/alerta)
[![Gitter chat](https://badges.gitter.im/alerta/chat.png)](https://gitter.im/alerta/chat)
[![Coverage Status](https://coveralls.io/repos/github/alerta/alerta/badge.svg?branch=master)](https://coveralls.io/github/alerta/alerta?branch=master)

The Alerta monitoring tool was developed with the following aims in mind:

*   distributed and de-coupled so that it is **SCALABLE**
*   minimal **CONFIGURATION** that easily accepts alerts from any source
*   quick at-a-glance **VISUALISATION** with drill-down to detail

![webui](/docs/images/alerta-webui-v7.jpg?raw=true)

----

Python 2.7 support is EOL
-------------------------

Starting with Release 6.0 only Python 3.5+ is supported. Release 5.2 was the
last to support Python 2.7 and feature enhancements for this release ended on
August 31, 2018. Only critical bug fixes will be backported to Release 5.2.

Requirements
------------

The only mandatory dependency is MongoDB or PostgreSQL. Everything else is optional.

- Postgres version 9.5 or better
- MongoDB version 3.2 or better

Installation
------------

To install MongoDB on Debian/Ubuntu run:

    $ sudo apt-get install -y mongodb-org
    $ mongod

To install MongoDB on CentOS/RHEL run:

    $ sudo yum install -y mongodb
    $ mongod

To install the Alerta server and client run:

    $ apt-get install libpq-dev python-dev python3-dev
    $ pip3 install alerta-server alerta
    $ alertad run

To install the web console run:

    $ wget https://github.com/alerta/alerta-webui/releases/latest/download/alerta-webui.tar.gz
    $ tar zxvf alerta-webui.tar.gz
    $ cd dist
    $ python3 -m http.server 8000

    >> browse to http://localhost:8000

### Docker
Alerta and MongoDB can also run using Docker containers, see [alerta/docker-alerta](https://github.com/alerta/docker-alerta).

Configuration
-------------

To configure the ``alertad`` server override the default settings in ``/etc/alertad.conf``
or using ``ALERTA_SVR_CONF_FILE`` environment variable::

    $ ALERTA_SVR_CONF_FILE=~/.alertad.conf
    $ echo "DEBUG=True" > $ALERTA_SVR_CONF_FILE

Documentation
-------------

More information on configuration and other aspects of alerta can be found
at <http://docs.alerta.io>

Development
-----------

To run in development mode, listening on port 5000:

    $ export FLASK_APP=alerta FLASK_ENV=development
    $ pip install -e .
    $ flask run

To run in development mode, listening on port 8080, using Postgres and
reporting errors to [Sentry](https://sentry.io):

    $ export FLASK_APP=alerta FLASK_ENV=development
    $ export DATABASE_URL=postgres://localhost:5432/alerta5
    $ export SENTRY_DSN=https://8b56098250544fb78b9578d8af2a7e13:fa9d628da9c4459c922293db72a3203f@sentry.io/153768
    $ pip install -e .[postgres]
    $ flask run --debugger --port 8080 --with-threads --reload

Troubleshooting
---------------

Enable debug log output by setting `DEBUG=True` in the API server
configuration:

```
DEBUG=True

LOG_HANDLERS = ['console','file']
LOG_FORMAT = 'verbose'
LOG_FILE = '$HOME/alertad.log'
```

It can also be helpful to check the web browser developer console for
JavaScript logging, network problems and API error responses.

Tests
-----

To run the tests using a local Postgres database run:

    $ pip install -r requirements.txt
    $ pip install -e .[postgres]
    $ createdb test5
    $ ALERTA_SVR_CONF_FILE= DATABASE_URL=postgres:///test5 pytest

Cloud Deployment
----------------

Alerta can be deployed to the cloud easily using Heroku <https://github.com/alerta/heroku-api-alerta>,
AWS EC2 <https://github.com/alerta/alerta-cloudformation>, or Google Cloud Platform
<https://github.com/alerta/gcloud-api-alerta>

License
-------

    Alerta monitoring system and console
    Copyright 2012-2019 Nick Satterly

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
