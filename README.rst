===============================
moTracker
===============================

Location, Location, Location!


Quickstart
----------

Run the following commands to bootstrap your environment ::

    git clone https://github.com/ser/motracker
    cd motracker
    pip install -r requirements/dev.txt
    cp .env.example .env
    npm install
    npm start  # run the webpack dev server and flask server using concurrently

You will see a pretty welcome screen.

Create your postgres database, let's assume 'gnss' and add postgis features ::

    $ sudo -u postgres psql gnss
    gnss=# CREATE EXTENSION postgis;
    gnss=# CREATE EXTENSION address_standardizer;
    gnss=# CREATE EXTENSION fuzzystrmatch;
    gnss=# CREATE EXTENSION postgis_topology;

Once you have installed your DBMS, run the following to create your app's
database tables and perform the initial migration ::

    flask db init
    flask db migrate

Now, before you proceed, you must update alembic scripts. Alembic does not try
to determine and render all imports for custom types in the migration scripts.
Edit the generated script to include ``from geoalchemy2.types import Geometry`` and
change the column def to just use ``Geometry``. And later ::

    flask db upgrade
    npm start


Deployment
----------

To deploy::

    export FLASK_ENV=production
    export FLASK_DEBUG=0
    export DATABASE_URL="<YOUR DATABASE URL>"
    npm run build   # build assets with webpack
    flask run       # start the flask server

In your production environment, make sure the ``FLASK_DEBUG`` environment
variable is unset or is set to ``0``.

Setting admin user
------------------

After creation a user via web, you can set that username as admin ::

    flask users --makeadmin username

If you want to unset admin rights ::

    flask users --removeadmin username

Shell
-----

To open the interactive shell, run ::

    flask shell

By default, you will have access to the flask ``app``.


Running Tests/Linter
--------------------

To run all tests, run ::

    flask test

To run the linter, run ::

    flask lint

The ``lint`` command will attempt to fix any linting/style errors in the code. If you only want to know if the code will pass CI and do not wish for the linter to make changes, add the ``--check`` argument.

Migrations
----------

Whenever a database migration needs to be made. Run the following commands ::

    flask db migrate

This will generate a new migration script. Then run ::

    flask db upgrade

To apply the migration.

For a full migration command reference, run ``flask db --help``.

Asset Management
----------------

Files placed inside the ``assets`` directory and its subdirectories
(excluding ``js`` and ``css``) will be copied by webpack's
``file-loader`` into the ``static/build`` directory, with hashes of
their contents appended to their names.  For instance, if you have the
file ``assets/img/favicon.ico``, this will get copied into something
like
``static/build/img/favicon.fec40b1d14528bf9179da3b6b78079ad.ico``.
You can then put this line into your header::

    <link rel="shortcut icon" href="{{asset_url_for('img/favicon.ico') }}">

to refer to it inside your HTML page.  If all of your static files are
managed this way, then their filenames will change whenever their
contents do, and you can ask Flask to tell web browsers that they
should cache all your assets forever by including the following line
in your ``settings.py``::

    SEND_FILE_MAX_AGE_DEFAULT = 31556926  # one year
