from datetime import datetime, timezone
from app.extensions import db


class ExchangeRating(db.Model):
    """Post-exchange student rating and review."""
    __tablename__ = 'exchange_ratings'

    id = db.Column(db.Integer, primary_key=True)
    exchange_request_id = db.Column(db.Integer, db.ForeignKey('exchange_requests.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    rater_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    rated_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    rating = db.Column(db.Integer, nullable=False)  # 1 to 5
    comment = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    exchange_request = db.relationship('ExchangeRequest', backref=db.backref('rating', uselist=False))
    rater = db.relationship('User', foreign_keys=[rater_id], backref=db.backref('ratings_given', lazy='dynamic'))
    rated_user = db.relationship('User', foreign_keys=[rated_user_id], backref=db.backref('ratings_received', lazy='dynamic'))

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'exchange_request_id': self.exchange_request_id,
            'rater_id': self.rater_id,
            'rater_name': self.rater.full_name if self.rater else None,
            'rated_user_id': self.rated_user_id,
            'rating': self.rating,
            'comment': self.comment or '',
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f'<ExchangeRating {self.id}: {self.rating} stars for User {self.rated_user_id}>'
