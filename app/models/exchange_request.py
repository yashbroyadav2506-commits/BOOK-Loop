from datetime import datetime, timezone
from app.extensions import db


class RequestStatus:
    PENDING = "Pending"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"

    ALL = [PENDING, ACCEPTED, REJECTED, CANCELLED, COMPLETED]


class ExchangeRequest(db.Model):
    """Exchange request model between a requester student and a book owner."""
    __tablename__ = 'exchange_requests'

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id', ondelete='CASCADE'), nullable=False, index=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    message = db.Column(db.Text, nullable=True)
    offered_book_id = db.Column(db.Integer, db.ForeignKey('books.id', ondelete='SET NULL'), nullable=True)
    
    status = db.Column(
        db.String(30),
        nullable=False,
        default=RequestStatus.PENDING,
        index=True
    )
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationship to offered book
    offered_book = db.relationship('Book', foreign_keys=[offered_book_id])

    def to_dict(self) -> dict:
        """Serialize exchange request safely."""
        return {
            'id': self.id,
            'book_id': self.book_id,
            'book_title': self.book.title if self.book else None,
            'book_author': self.book.author if self.book else None,
            'book_cover': self.book.cover_image_url if self.book else None,
            'requester_id': self.requester_id,
            'requester_name': self.requester.full_name if self.requester else None,
            'requester_department': self.requester.department if self.requester else None,
            'requester_email': self.requester.college_email if self.requester else None,
            'requester_phone': self.requester.phone_number if self.requester else None,
            'owner_id': self.owner_id,
            'owner_name': self.owner.full_name if self.owner else None,
            'owner_department': self.owner.department if self.owner else None,
            'owner_email': self.owner.college_email if self.owner else None,
            'owner_phone': self.owner.phone_number if self.owner else None,
            'offered_book_id': self.offered_book_id,
            'offered_book_title': self.offered_book.title if self.offered_book else None,
            'message': self.message or '',
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f'<ExchangeRequest {self.id}: Book {self.book_id} Status {self.status}>'
