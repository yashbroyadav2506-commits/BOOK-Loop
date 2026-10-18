import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the application
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file if it exists
load_dotenv(BASE_DIR / '.env')


def normalize_database_url(url: str | None) -> str:
    """
    Ensure PostgreSQL URLs use the appropriate psycopg driver format for SQLAlchemy 2.x.
    Fixes legacy 'postgres://' URLs provided by Heroku/Render/Vercel/Neon.
    """
    if not url:
        if os.environ.get('VERCEL'):
            return "sqlite:////tmp/pallotti_bookloop.db"
        return f"sqlite:///{BASE_DIR / 'pallotti_bookloop.db'}"
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://") and "+psycopg" not in url:
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


class Config:
    """Base configuration with sensible defaults."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-pallotti-bookloop-fallback-secret-key-3.14')
    
    # Database
    SQLALCHEMY_DATABASE_URI = normalize_database_url(os.environ.get('DATABASE_URL'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # Session Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1', 't')
    
    # Application Business Configuration
    BOOKS_PER_PAGE = int(os.environ.get('BOOKS_PER_PAGE', 9))
    
    # Configurable College Email Restriction
    # Example: "stvincentngp.edu.in,pallottine.org"
    # When empty, any valid email address is accepted.
    _domains = os.environ.get('ALLOWED_EMAIL_DOMAINS', '').strip()
    ALLOWED_EMAIL_DOMAINS = [d.strip().lower() for d in _domains.split(',') if d.strip()]


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration with isolated test database."""
    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
