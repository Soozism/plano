"""AuditLog model class."""
from typing import List, Optional, Dict, Any
from flask_backend.models.base import BaseModel
from flask_backend.extensions import db

class AuditLog(BaseModel):
    """AuditLog model."""
    __tablename__ = 'audit_logs'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(50), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer)
    old_values = db.Column(db.JSON)
    new_values = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(200))
    status = db.Column(db.String(20), default='success')  # success, failure, error
    error_message = db.Column(db.Text)
    metadata = db.Column(db.JSON)

    def __init__(self, **kwargs):
        """Initialize audit log model."""
        super().__init__(**kwargs)
        if not self.metadata:
            self.metadata = {}

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to audit log."""
        self.metadata[key] = value
        self.save()

    def set_error(self, message: str) -> None:
        """Set error status and message."""
        self.status = 'error'
        self.error_message = message
        self.save()

    def set_failure(self, message: str) -> None:
        """Set failure status and message."""
        self.status = 'failure'
        self.error_message = message
        self.save()

    @classmethod
    def get_by_user(cls, user_id: int) -> List['AuditLog']:
        """Get audit logs by user."""
        return cls.query.filter_by(user_id=user_id).order_by(cls.created_at.desc()).all()

    @classmethod
    def get_by_action(cls, action: str) -> List['AuditLog']:
        """Get audit logs by action."""
        return cls.query.filter_by(action=action).order_by(cls.created_at.desc()).all()

    @classmethod
    def get_by_entity(cls, entity_type: str, entity_id: int) -> List['AuditLog']:
        """Get audit logs by entity."""
        return cls.query.filter_by(
            entity_type=entity_type,
            entity_id=entity_id
        ).order_by(cls.created_at.desc()).all()

    @classmethod
    def get_by_status(cls, status: str) -> List['AuditLog']:
        """Get audit logs by status."""
        return cls.query.filter_by(status=status).order_by(cls.created_at.desc()).all()

    @classmethod
    def get_by_date_range(cls, start_date: datetime, end_date: datetime) -> List['AuditLog']:
        """Get audit logs within date range."""
        return cls.query.filter(
            cls.created_at >= start_date,
            cls.created_at <= end_date
        ).order_by(cls.created_at.desc()).all()

    @classmethod
    def get_errors(cls) -> List['AuditLog']:
        """Get error audit logs."""
        return cls.query.filter_by(status='error').order_by(cls.created_at.desc()).all()

    @classmethod
    def get_failures(cls) -> List['AuditLog']:
        """Get failure audit logs."""
        return cls.query.filter_by(status='failure').order_by(cls.created_at.desc()).all()

    @classmethod
    def get_recent_logs(cls, limit: int = 100) -> List['AuditLog']:
        """Get recent audit logs."""
        return cls.query.order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def log_event(
        cls,
        user_id: Optional[int],
        action: str,
        entity_type: str,
        entity_id: Optional[int] = None,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> 'AuditLog':
        """Create a new audit log entry."""
        log = cls(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )
        log.save()
        return log

    @classmethod
    def log_error(
        cls,
        user_id: Optional[int],
        action: str,
        error_message: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> 'AuditLog':
        """Create a new error audit log entry."""
        log = cls(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {},
            status='error',
            error_message=error_message
        )
        log.save()
        return log

    @classmethod
    def log_failure(
        cls,
        user_id: Optional[int],
        action: str,
        failure_message: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> 'AuditLog':
        """Create a new failure audit log entry."""
        log = cls(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {},
            status='failure',
            error_message=failure_message
        )
        log.save()
        return log

    @classmethod
    def cleanup_old_logs(cls, days: int = 90) -> None:
        """Delete audit logs older than specified days."""
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        cls.query.filter(cls.created_at < cutoff_date).delete()
        db.session.commit()

    def to_dict(self) -> dict:
        """Convert audit log to dictionary."""
        data = super().to_dict()
        data['ip_address'] = self.ip_address
        data['user_agent'] = self.user_agent
        data['error_message'] = self.error_message
        data['metadata'] = self.metadata
        return data 