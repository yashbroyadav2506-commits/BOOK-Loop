"""
Application extensions module.
Instantiates shared Flask extensions to prevent circular imports.
"""
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

# Flask-Limiter for serverless & production
# Supports Upstash Redis / Redis URL via env var, with in-memory fallback for local development/tests
storage_backend = (
    os.environ.get('RATELIMIT_STORAGE_URI') or
    os.environ.get('UPSTASH_REDIS_URL') or
    os.environ.get('REDIS_URL') or
    'memory://'
)

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["300 per day", "100 per hour"],
    storage_uri=storage_backend,
    storage_options={}
)

# Configure login manager defaults
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'
