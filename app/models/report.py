from datetime import datetime, timezone
from app.extensions import db


class ReportStatus:
    PENDING = 'Pending'
    REVIEWED = 'Reviewed'
    DISMISSED = 'Dismissed'
    ALL = [PENDING, REVIEWED, DISMISSED]


class ListingReport(db.Model):
    """User reports against suspicious, inappropriate, or sold listings."""
    __tablename__ = 'listing_reports'

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id', ondelete='CASCADE'), nullable=False, index=True)
    reason = db.Column(db.String(80), nullable=False)
    note = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default=ReportStatus.PENDING, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    reporter = db.relationship('User', foreign_keys=[reporter_id], backref=db.backref('reports_submitted', lazy='dynamic'))
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id])
    book = db.relationship('Book', backref=db.backref('reports', lazy='dynamic', cascade='all, delete-orphan'))

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'book_id': self.book_id,
            'book_title': self.book.title if self.book else None,
            'reporter_id': self.reporter_id,
            'reporter_name': self.reporter.full_name if self.reporter else None,
            'reason': self.reason,
            'note': self.note or '',
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
        }

    def __repr__(self) -> str:
        return f'<ListingReport {self.id}: Book {self.book_id} Status {self.status}>'
