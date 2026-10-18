from datetime import datetime, timezone
from app.extensions import db


class AdminAuditLog(db.Model):
    """Audit trail for administrator actions."""
    __tablename__ = 'admin_audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    action = db.Column(db.String(80), nullable=False)
    target_type = db.Column(db.String(50), nullable=False)
    target_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    admin = db.relationship('User', foreign_keys=[admin_id])

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'admin_id': self.admin_id,
            'admin_name': self.admin.full_name if self.admin else 'System',
            'action': self.action,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'details': self.details or '',
            'ip_address': self.ip_address or '',
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f'<AdminAuditLog {self.id}: {self.action} on {self.target_type}>'
