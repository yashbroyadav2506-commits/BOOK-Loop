from flask import request, jsonify, current_app
from flask_login import login_required, current_user
from app.api import api_bp
from app.api.schemas import BookCreateSchema, BookUpdateSchema
from app.books import services as book_services


@api_bp.route('/books', methods=['GET'])
def api_list_books():
    search = request.args.get('search')
    category = request.args.get('category')
    condition = request.args.get('condition')
    exchange_status = request.args.get('status')
    sort_by = request.args.get('sort_by', 'newest')
    
    try:
        page = max(1, int(request.args.get('page', 1)))
    except ValueError:
        page = 1

    try:
        per_page = int(request.args.get('per_page', current_app.config['BOOKS_PER_PAGE']))
        per_page = min(max(1, per_page), 50)
    except ValueError:
        per_page = current_app.config['BOOKS_PER_PAGE']

    books, total, pages = book_services.list_books(
        search=search,
        category=category,
        condition=condition,
        exchange_status=exchange_status,
        sort_by=sort_by,
        page=page,
        per_page=per_page
    )

    return jsonify({
        'success': True,
        'data': [b.to_dict() for b in books],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': pages
        }
    })


@api_bp.route('/books/<int:book_id>', methods=['GET'])
def api_get_book(book_id: int):
    book = book_services.get_book_by_id(book_id)
    if not book:
        return jsonify({
            'success': False,
            'message': 'Book not found.'
        }), 404

    return jsonify({
        'success': True,
        'data': book.to_dict()
    })


@api_bp.route('/books', methods=['POST'])
@login_required
def api_create_book():
    data = request.get_json() or {}
    schema = BookCreateSchema()
    validated = schema.load(data)

    book = book_services.create_book(owner=current_user, data=validated)

    return jsonify({
        'success': True,
        'message': 'Book listed successfully.',
        'data': book.to_dict()
    }), 201


@api_bp.route('/books/<int:book_id>', methods=['PATCH'])
@login_required
def api_update_book(book_id: int):
    book = book_services.get_book_by_id(book_id)
    if not book:
        return jsonify({
            'success': False,
            'message': 'Book not found.'
        }), 404

    data = request.get_json() or {}
    schema = BookUpdateSchema()
    validated = schema.load(data)

    updated_book = book_services.update_book(book=book, user=current_user, data=validated)

    return jsonify({
        'success': True,
        'message': 'Book listing updated successfully.',
        'data': updated_book.to_dict()
    })


@api_bp.route('/books/<int:book_id>', methods=['DELETE'])
@login_required
def api_delete_book(book_id: int):
    book = book_services.get_book_by_id(book_id)
    if not book:
        return jsonify({
            'success': False,
            'message': 'Book not found.'
        }), 404

    book_services.delete_book(book=book, user=current_user)

    return jsonify({
        'success': True,
        'message': 'Book listing deleted successfully.'
    })
