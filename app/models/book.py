from datetime import datetime, timezone, timedelta
from app.extensions import db


class BookCategory:
    COMPUTER_SCIENCE = "Computer Science"
    DATA_SCIENCE = "Data Science"
    ENGINEERING = "Engineering"
    MATHEMATICS = "Mathematics"
    PHYSICS = "Physics"
    CHEMISTRY = "Chemistry"
    ELECTRONICS = "Electronics"
    COMPETITIVE_EXAMS = "Competitive Exams"
    OTHER = "Other"

    ALL = [
        COMPUTER_SCIENCE,
        DATA_SCIENCE,
        ENGINEERING,
        MATHEMATICS,
        PHYSICS,
        CHEMISTRY,
        ELECTRONICS,
        COMPETITIVE_EXAMS,
        OTHER
    ]


class BookCondition:
    LIKE_NEW = "Like New"
    GOOD = "Good"
    FAIR = "Fair"
    HEAVILY_USED = "Heavily Used"

    ALL = [LIKE_NEW, GOOD, FAIR, HEAVILY_USED]


class ExchangeStatus:
    AVAILABLE = "Available"
    EXCHANGE_REQUESTED = "Exchange Requested"
    RESERVED = "Reserved"
    EXCHANGED = "Exchanged"
    UNAVAILABLE = "Unavailable"

    ALL = [AVAILABLE, EXCHANGE_REQUESTED, RESERVED, EXCHANGED, UNAVAILABLE]


class Book(db.Model):
    """Book listing model with semester tags and moderation support."""
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    author = db.Column(db.String(150), nullable=False, index=True)
    category = db.Column(db.String(80), nullable=False, index=True)
    condition = db.Column(db.String(40), nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)
    exchange_status = db.Column(
        db.String(40),
        nullable=False,
        default=ExchangeStatus.AVAILABLE,
        index=True
    )
    description = db.Column(db.Text, nullable=True)
    isbn = db.Column(db.String(30), nullable=True, index=True)
    cover_image_url = db.Column(db.String(500), nullable=True)
    semester = db.Column(db.String(20), nullable=True)
    
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_hidden = db.Column(db.Boolean, default=False, nullable=False, index=True)  # Admin moderation flag
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    expires_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc) + timedelta(days=60),
        nullable=True,
        index=True
    )

    # Relationship to exchange requests for this book
    exchange_requests = db.relationship(
        'ExchangeRequest',
        foreign_keys='ExchangeRequest.book_id',
        backref='book',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def to_dict(self) -> dict:
        """Serialize book listing for API responses."""
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'category': self.category,
            'condition': self.condition,
            'owner_name': self.owner_name,
            'owner_id': self.owner_id,
            'exchange_status': self.exchange_status,
            'description': self.description or '',
            'isbn': self.isbn or '',
            'cover_image_url': self.cover_image_url or '',
            'semester': self.semester or '',
            'is_active': self.is_active,
            'is_hidden': self.is_hidden,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'owner_details': {
                'id': self.owner.id,
                'full_name': self.owner.full_name,
                'department': self.owner.department,
                'academic_year': self.owner.academic_year,
                'is_verified': self.owner.is_verified,
                'successful_exchanges': self.owner.successful_exchanges_count,
            } if self.owner else None
        }

    def __repr__(self) -> str:
        return f'<Book {self.id}: {self.title} by {self.author}>'
