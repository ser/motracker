# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located in app.py."""
from flask_bcrypt import Bcrypt
from flask_caching import Cache
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import UploadSet
from flask_webpack import Webpack
from flask_wtf.csrf import CSRFProtect

bcrypt = Bcrypt()
cache = Cache()
csrf_protect = CSRFProtect()
db = SQLAlchemy()
debug_toolbar = DebugToolbarExtension()
filez = UploadSet(name='filez', extensions=('gpx', 'GPX'), default_dest=lambda x: 'filez')
login_manager = LoginManager()
migrate = Migrate()
webpack = Webpack()
