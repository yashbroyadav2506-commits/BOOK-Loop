import os
import logging
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify
from flask_login import current_user
from app.config import config_by_name
from app.extensions import db, migrate, login_manager, csrf, limiter
from app.models.user import User


def create_app(config_name: str | None = None) -> Flask:
    """Application factory for Pallotti BookLoop."""
    if not config_name:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Optional Sentry Error Tracking integration (Phase G.1)
    sentry_dsn = os.environ.get('SENTRY_DSN')
    if sentry_dsn and not app.testing:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.flask import FlaskIntegration
            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[FlaskIntegration()],
                traces_sample_rate=0.2,
                profiles_sample_rate=0.2,
            )
            app.logger.info("Sentry error tracking initialized.")
        except ImportError:
            app.logger.warning("sentry-sdk not installed. Skipping Sentry initialization.")

    # Logging setup
    if not app.debug and not app.testing:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        app.logger.setLevel(logging.INFO)
        app.logger.info('Pallotti BookLoop application startup')

    # Configure user loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register Blueprints
    from app.main import main_bp
    from app.auth import auth_bp
    from app.books import books_bp
    from app.exchanges import exchanges_bp
    from app.dashboard import dashboard_bp
    from app.admin import admin_bp
    from app.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(exchanges_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Context processors for all Jinja templates
    @app.context_processor
    def inject_global_template_vars():
        unread_count = 0
        if current_user.is_authenticated:
            from app.models.notification import Notification
            try:
                unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
            except Exception:
                unread_count = 0

        return {
            'app_name': 'Pallotti BookLoop',
            'college_name': 'St. Vincent Pallotti College of Engineering & Technology',
            'tagline': 'Your Next Book Is Already Here.',
            'current_year': datetime.now(timezone.utc).year,
            'unread_notifications_count': unread_count,
        }

    # Security Headers (Phase A.5)
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # CSP allowing Bootstrap CDN, Google Fonts, Bootstrap Icons, Unsplash, Cloudinary, and OpenLibrary
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
            "img-src 'self' data: blob: https://images.unsplash.com https://res.cloudinary.com https://covers.openlibrary.org; "
            "connect-src 'self' https://openlibrary.org; "
            "frame-ancestors 'none';"
        )
        response.headers['Content-Security-Policy'] = csp
        return response

    # Centralized error handlers
    def is_api_request():
        return request.path.startswith('/api/') or request.is_json

    @app.errorhandler(400)
    def bad_request(error):
        if is_api_request():
            return jsonify({'success': False, 'message': 'Bad request', 'error': str(error)}), 400
        return render_template('errors/400.html', title='Bad Request - Pallotti BookLoop'), 400

    @app.errorhandler(403)
    def forbidden(error):
        if is_api_request():
            return jsonify({'success': False, 'message': 'Access forbidden'}), 403
        return render_template('errors/403.html', title='Access Forbidden - Pallotti BookLoop'), 403

    @app.errorhandler(404)
    def page_not_found(error):
        if is_api_request():
            return jsonify({'success': False, 'message': 'Resource not found'}), 404
        return render_template('errors/404.html', title='Page Not Found - Pallotti BookLoop'), 404

    @app.errorhandler(429)
    def ratelimit_handler(e):
        if is_api_request():
            return jsonify({'success': False, 'message': 'Rate limit exceeded. Please try again later.'}), 429
        return render_template(
            'errors/400.html',
            title='Rate Limit Exceeded',
            error_message='Too many requests. Please slow down and try again shortly.'
        ), 429

    @app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()
        if is_api_request():
            return jsonify({'success': False, 'message': 'Internal server error'}), 500
        return render_template('errors/500.html', title='Internal Server Error - Pallotti BookLoop'), 500

    return app
