import os
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from sqlalchemy import text
from marshmallow import ValidationError
from app.extensions import db
from app.books.services import BookServiceError, expire_stale_books
from app.exchanges.services import ExchangeServiceError

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')


@api_bp.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({
        'success': False,
        'message': 'Validation failed',
        'errors': e.messages
    }), 400


@api_bp.errorhandler(BookServiceError)
def handle_book_service_error(e):
    return jsonify({
        'success': False,
        'message': e.message
    }), e.status_code


@api_bp.errorhandler(ExchangeServiceError)
def handle_exchange_service_error(e):
    return jsonify({
        'success': False,
        'message': e.message
    }), e.status_code


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint that verifies database connectivity."""
    db_status = "connected"
    try:
        db.session.execute(text('SELECT 1'))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        return jsonify({
            'status': 'unhealthy',
            'database': db_status,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 503

    return jsonify({
        'status': 'healthy',
        'service': 'Pallotti BookLoop API',
        'database': db_status,
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


@api_bp.route('/cron/expire-stale-books', methods=['GET', 'POST'])
def cron_expire_books():
    """
    Vercel Cron endpoint to automatically expire listings older than 60 days.
    Protected by CRON_SECRET if configured.
    """
    cron_secret = os.environ.get('CRON_SECRET')
    if cron_secret:
        auth_header = request.headers.get('Authorization', '')
        query_key = request.args.get('key', '')
        expected_token = f"Bearer {cron_secret}"
        if auth_header != expected_token and query_key != cron_secret:
            return jsonify({'success': False, 'message': 'Unauthorized cron invocation'}), 401

    expired_count = expire_stale_books()
    return jsonify({
        'success': True,
        'expired_count': expired_count,
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


# Import sub-routes to register on api_bp
from app.api import auth_routes, book_routes, exchange_routes, dashboard_routes
