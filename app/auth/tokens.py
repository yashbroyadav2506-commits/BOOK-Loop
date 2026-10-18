from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from flask import current_app


def get_serializer() -> URLSafeTimedSerializer:
    """Returns itsdangerous URLSafeTimedSerializer using app's SECRET_KEY."""
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


def generate_verification_token(user_id: int) -> str:
    """Generate signed, expiring email verification token."""
    serializer = get_serializer()
    return serializer.dumps(user_id, salt='email-verification-salt')


def confirm_verification_token(token: str, expiration: int = 86400) -> int | None:
    """
    Verify email confirmation token (valid for 24 hours by default).
    Returns user_id if valid, or None if invalid/expired.
    """
    serializer = get_serializer()
    try:
        user_id = serializer.loads(token, salt='email-verification-salt', max_age=expiration)
        return user_id
    except (SignatureExpired, BadTimeSignature, Exception):
        return None


def generate_reset_token(user_id: int) -> str:
    """Generate signed, expiring password reset token."""
    serializer = get_serializer()
    return serializer.dumps(user_id, salt='password-reset-salt')


def confirm_reset_token(token: str, expiration: int = 3600) -> int | None:
    """
    Verify password reset token (valid for 1 hour by default).
    Returns user_id if valid, or None if invalid/expired.
    """
    serializer = get_serializer()
    try:
        user_id = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
        return user_id
    except (SignatureExpired, BadTimeSignature, Exception):
        return None
