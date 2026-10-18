from flask import request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from flask_wtf.csrf import generate_csrf
from app.extensions import db
from app.models.user import User
from app.api import api_bp
from app.api.schemas import UserRegisterSchema, UserLoginSchema


@api_bp.route('/auth/csrf-token', methods=['GET'])
def get_csrf_token():
    """Returns a fresh CSRF token for API consumers and Fetch clients."""
    token = generate_csrf()
    return jsonify({
        'success': True,
        'csrf_token': token
    })


@api_bp.route('/auth/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    schema = UserRegisterSchema()
    validated = schema.load(data)

    if validated['password'] != validated['confirm_password']:
        return jsonify({
            'success': False,
            'message': 'Passwords do not match.',
            'errors': {'confirm_password': ['Passwords do not match.']}
        }), 400

    existing_user = User.query.filter_by(college_email=validated['college_email'].strip().lower()).first()
    if existing_user:
        return jsonify({
            'success': False,
            'message': 'An account with this college email already exists.',
            'errors': {'college_email': ['Email already registered.']}
        }), 409

    user = User(
        full_name=validated['full_name'].strip(),
        college_email=validated['college_email'].strip().lower(),
        department=validated['department'].strip(),
        academic_year=validated['academic_year'],
        phone_number=validated.get('phone_number', '').strip() or None,
        is_active=True
    )
    user.set_password(validated['password'])

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Database error during registration: {str(e)}'
        }), 500

    login_user(user)

    return jsonify({
        'success': True,
        'message': 'Registration successful.',
        'user': user.to_dict(include_private=True)
    }), 201


@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    schema = UserLoginSchema()
    validated = schema.load(data)

    user = User.query.filter_by(college_email=validated['college_email'].strip().lower()).first()
    if not user or not user.check_password(validated['password']):
        return jsonify({
            'success': False,
            'message': 'Invalid email or password.'
        }), 401

    if not user.is_active:
        return jsonify({
            'success': False,
            'message': 'This account has been deactivated.'
        }), 403

    login_user(user)

    return jsonify({
        'success': True,
        'message': 'Login successful.',
        'user': user.to_dict(include_private=True)
    })


@api_bp.route('/auth/logout', methods=['POST'])
@login_required
def api_logout():
    logout_user()
    return jsonify({
        'success': True,
        'message': 'Successfully logged out.'
    })


@api_bp.route('/auth/me', methods=['GET'])
@login_required
def api_get_current_user():
    return jsonify({
        'success': True,
        'user': current_user.to_dict(include_private=True)
    })
