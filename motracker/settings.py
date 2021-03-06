# -*- coding: utf-8 -*-
"""Application configuration.

Most configuration is set via environment variables.

For local development, use a .env file to set
environment variables.
"""
import os

from environs import Env

env = Env()
env.read_env()

ENV = env.str("FLASK_ENV", default="production")
DEBUG = ENV == "development"
SQLALCHEMY_DATABASE_URI = env.str("DATABASE_URL")
SECRET_KEY = env.str("SECRET_KEY")
BCRYPT_LOG_ROUNDS = env.int("BCRYPT_LOG_ROUNDS", default=13)
DEBUG_TB_ENABLED = DEBUG
DEBUG_TB_INTERCEPT_REDIRECTS = False
CACHE_TYPE = "simple"  # Can be "memcached", "redis", etc.
SQLALCHEMY_TRACK_MODIFICATIONS = False
WEBPACK_MANIFEST_PATH = "webpack/manifest.json"
UPLOADS_DEFAULT_DEST = os.path.abspath(os.curdir) + env.str("UPLOADS_DEFAULT_DEST")
UPLOADS_DEFAULT_URL = env.str("UPLOADS_DEFAULT_URL")
CELERY_BROKER_URL = env.str("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env.str("CELERY_RESULT_BACKEND")
MAIL_SERVER = env.str("MAIL_SERVER")
MAIL_PORT = env.str("MAIL_PORT")
MAIL_USE_TLS = env.str("MAIL_USE_TLS")
#MAIL_USE_SSL = env.str("MAIL_USE_SSL")
#MAIL_DEBUG = env.str("MAIL_DEBUG")
MAIL_USERNAME = env.str("MAIL_USERNAME")
MAIL_PASSWORD = env.str("MAIL_PASSWORD")
DEFAULT_MAIL_SENDER = env.str("DEFAULT_MAIL_SENDER")
