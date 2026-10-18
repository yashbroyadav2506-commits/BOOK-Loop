from datetime import datetime, timezone
from app.extensions import db


class Wishlist(db.Model):
    """Student wishlist and notification subscription for specific books."""
    __tablename__ = 'wishlists'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(30), nullable=True, index=True)
    category = db.Column(db.String(80), nullable=True)
    is_notified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship('User', backref=db.backref('wishlists', lazy='dynamic', cascade='all, delete-orphan'))

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'isbn': self.isbn or '',
            'category': self.category or '',
            'is_notified': self.is_notified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f'<Wishlist {self.id}: {self.title} by User {self.user_id}>'
