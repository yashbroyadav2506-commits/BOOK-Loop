from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db


class User(UserMixin, db.Model):
    """Student user account model with trust & security fields."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    college_email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    academic_year = db.Column(db.String(30), nullable=False)
    phone_number = db.Column(db.String(25), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Security & Verification
    is_verified = db.Column(db.Boolean, default=False, nullable=False, index=True)
    email_verified_at = db.Column(db.DateTime, nullable=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False, index=True)
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)
    password_changed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Contact preferences for privacy-conscious exchange coordination
    preferred_contact_method = db.Column(db.String(30), default='WhatsApp', nullable=False)
    preferred_meeting_spot = db.Column(db.String(120), default='Central Library Entrance', nullable=True)

    # Relationships
    books = db.relationship(
        'Book',
        backref='owner',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    exchange_requests_made = db.relationship(
        'ExchangeRequest',
        foreign_keys='ExchangeRequest.requester_id',
        backref='requester',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    exchange_requests_received = db.relationship(
        'ExchangeRequest',
        foreign_keys='ExchangeRequest.owner_id',
        backref='owner',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def set_password(self, password: str) -> None:
        """Hash and set user password and update password_changed_at."""
        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.now(timezone.utc)

    def check_password(self, password: str) -> bool:
        """Verify user password against stored hash."""
        return check_password_hash(self.password_hash, password)

    def is_account_locked(self) -> bool:
        """Check if user account is currently temporarily locked."""
        if not self.locked_until:
            return False
        # Normalize timezone
        locked_time = self.locked_until
        if locked_time.tzinfo is None:
            locked_time = locked_time.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) < locked_time

    def record_failed_login(self, max_attempts: int = 5, lock_duration_minutes: int = 15) -> bool:
        """Increment failed attempts and lock if exceeded. Returns True if locked."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=lock_duration_minutes)
            return True
        return False

    def reset_failed_logins(self) -> None:
        """Reset failed login count and unlock."""
        self.failed_login_attempts = 0
        self.locked_until = None

    @property
    def successful_exchanges_count(self) -> int:
        """Count of completed exchanges as either owner or requester."""
        from app.models.exchange_request import ExchangeRequest, RequestStatus
        return ExchangeRequest.query.filter(
            db.or_(ExchangeRequest.owner_id == self.id, ExchangeRequest.requester_id == self.id),
            ExchangeRequest.status == RequestStatus.COMPLETED
        ).count()

    @property
    def average_rating(self) -> float | None:
        """Calculate average peer exchange rating."""
        from app.models.rating import ExchangeRating
        ratings = ExchangeRating.query.filter_by(rated_user_id=self.id).all()
        if not ratings:
            return None
        return round(sum(r.rating for r in ratings) / len(ratings), 1)

    def to_dict(self, include_private: bool = False) -> dict:
        """
        Serialize user details safely without leaking password_hash.
        Public serialization exposes only public profile info for marketplace listings.
        """
        data = {
            'id': self.id,
            'full_name': self.full_name,
            'department': self.department,
            'academic_year': self.academic_year,
            'is_verified': self.is_verified,
            'successful_exchanges': self.successful_exchanges_count,
            'average_rating': self.average_rating,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_private:
            data.update({
                'college_email': self.college_email,
                'phone_number': self.phone_number,
                'preferred_contact_method': self.preferred_contact_method,
                'preferred_meeting_spot': self.preferred_meeting_spot,
                'is_active': self.is_active,
                'is_admin': self.is_admin,
            })
        return data

    def __repr__(self) -> str:
        return f'<User {self.id}: {self.college_email}>'
