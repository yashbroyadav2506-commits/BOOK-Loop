from flask import jsonify, request
from flask_login import login_required, current_user
from app.api import api_bp
from app.exchanges import services as exchange_services
from app.models.book import Book
from app.models.exchange_request import ExchangeRequest


@api_bp.route('/dashboard/summary', methods=['GET'])
@login_required
def api_dashboard_summary():
    summary = exchange_services.get_user_dashboard_summary(current_user.id)
    return jsonify({
        'success': True,
        'data': summary
    })


@api_bp.route('/users/me/books', methods=['GET'])
@login_required
def api_my_books():
    books = Book.query.filter_by(owner_id=current_user.id, is_active=True).order_by(Book.created_at.desc()).all()
    return jsonify({
        'success': True,
        'data': [b.to_dict() for b in books]
    })


@api_bp.route('/users/me/exchange-requests', methods=['GET'])
@login_required
def api_my_exchange_requests():
    incoming = ExchangeRequest.query.filter_by(owner_id=current_user.id).order_by(ExchangeRequest.created_at.desc()).all()
    outgoing = ExchangeRequest.query.filter_by(requester_id=current_user.id).order_by(ExchangeRequest.created_at.desc()).all()

    return jsonify({
        'success': True,
        'data': {
            'incoming': [r.to_dict() for r in incoming],
            'outgoing': [r.to_dict() for r in outgoing]
        }
    })
