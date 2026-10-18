from flask import request, jsonify
from flask_login import login_required, current_user
from app.api import api_bp
from app.api.schemas import ExchangeRequestCreateSchema
from app.exchanges import services as exchange_services
from app.models.exchange_request import ExchangeRequest


@api_bp.route('/exchange-requests', methods=['POST'])
@login_required
def api_create_exchange_request():
    data = request.get_json() or {}
    schema = ExchangeRequestCreateSchema()
    validated = schema.load(data)

    req = exchange_services.create_exchange_request(
        requester=current_user,
        book_id=validated['book_id'],
        message=validated.get('message'),
        offered_book_id=validated.get('offered_book_id')
    )

    return jsonify({
        'success': True,
        'message': 'Exchange request sent successfully.',
        'data': req.to_dict()
    }), 201


@api_bp.route('/exchange-requests', methods=['GET'])
@login_required
def api_list_exchange_requests():
    role = request.args.get('role', 'all')  # 'incoming', 'outgoing', 'all'
    status = request.args.get('status')

    query = ExchangeRequest.query

    if role == 'incoming':
        query = query.filter_by(owner_id=current_user.id)
    elif role == 'outgoing':
        query = query.filter_by(requester_id=current_user.id)
    else:
        query = query.filter(
            (ExchangeRequest.owner_id == current_user.id) | (ExchangeRequest.requester_id == current_user.id)
        )

    if status and status != 'All':
        query = query.filter_by(status=status)

    requests = query.order_by(ExchangeRequest.created_at.desc()).all()

    return jsonify({
        'success': True,
        'data': [r.to_dict() for r in requests]
    })


@api_bp.route('/exchange-requests/<int:request_id>', methods=['GET'])
@login_required
def api_get_exchange_request(request_id: int):
    req = db.session.get(ExchangeRequest, request_id)
    if not req:
        return jsonify({
            'success': False,
            'message': 'Exchange request not found.'
        }), 404

    # Authorization: only participants can view
    if current_user.id not in [req.owner_id, req.requester_id]:
        return jsonify({
            'success': False,
            'message': 'You are not authorized to view this exchange request.'
        }), 403

    return jsonify({
        'success': True,
        'data': req.to_dict()
    })


@api_bp.route('/exchange-requests/<int:request_id>', methods=['PATCH'])
@login_required
def api_update_exchange_request(request_id: int):
    data = request.get_json() or {}
    action = data.get('action')

    if not action:
        return jsonify({
            'success': False,
            'message': 'Missing "action" in request body (expected: accept, reject, complete).'
        }), 400

    if action == 'accept':
        updated = exchange_services.accept_exchange_request(current_user, request_id)
    elif action == 'reject':
        updated = exchange_services.reject_exchange_request(current_user, request_id)
    elif action == 'complete':
        updated = exchange_services.complete_exchange_request(current_user, request_id)
    else:
        return jsonify({
            'success': False,
            'message': f'Unsupported action "{action}". Valid actions: accept, reject, complete.'
        }), 400

    return jsonify({
        'success': True,
        'message': f'Exchange request {action}ed successfully.',
        'data': updated.to_dict()
    })


@api_bp.route('/exchange-requests/<int:request_id>/cancel', methods=['POST'])
@login_required
def api_cancel_exchange_request(request_id: int):
    cancelled = exchange_services.cancel_exchange_request(current_user, request_id)
    return jsonify({
        'success': True,
        'message': 'Exchange request cancelled successfully.',
        'data': cancelled.to_dict()
    })
