"""Notification model class."""
from typing import List, Optional
from flask_backend.models.base import BaseModel
from flask_backend.utils.constants import NotificationType
from flask_backend.extensions import db

class Notification(BaseModel):
    """Notification model."""
    __tablename__ = 'notifications'

    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), nullable=False, default=NotificationType.INFO)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    action_url = db.Column(db.String(512))
    action_text = db.Column(db.String(100))
    data = db.Column(db.JSON)
    expires_at = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        """Initialize notification model."""
        super().__init__(**kwargs)
        if not self.type:
            self.type = NotificationType.INFO

    def mark_as_read(self) -> None:
        """Mark notification as read."""
        self.read = True
        self.read_at = get_current_time()
        self.save()

    def mark_as_unread(self) -> None:
        """Mark notification as unread."""
        self.read = False
        self.read_at = None
        self.save()

    def set_action(self, url: str, text: str) -> None:
        """Set notification action."""
        self.action_url = url
        self.action_text = text
        self.save()

    def set_expiry(self, days: int = 30) -> None:
        """Set notification expiry."""
        from datetime import datetime, timedelta
        self.expires_at = datetime.utcnow() + timedelta(days=days)
        self.save()

    @property
    def is_expired(self) -> bool:
        """Check if notification is expired."""
        if not self.expires_at:
            return False
        return get_current_time() > self.expires_at

    @property
    def time_ago(self) -> str:
        """Get time ago string."""
        from datetime import datetime, timedelta
        now = get_current_time()
        diff = now - self.created_at

        if diff < timedelta(minutes=1):
            return 'just now'
        elif diff < timedelta(hours=1):
            minutes = diff.seconds // 60
            return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
        elif diff < timedelta(days=1):
            hours = diff.seconds // 3600
            return f'{hours} hour{"s" if hours != 1 else ""} ago'
        elif diff < timedelta(days=30):
            days = diff.days
            return f'{days} day{"s" if days != 1 else ""} ago'
        elif diff < timedelta(days=365):
            months = diff.days // 30
            return f'{months} month{"s" if months != 1 else ""} ago'
        else:
            years = diff.days // 365
            return f'{years} year{"s" if years != 1 else ""} ago'

    @classmethod
    def get_by_user(cls, user_id: int) -> List['Notification']:
        """Get notifications by user."""
        return cls.query.filter_by(user_id=user_id).order_by(cls.created_at.desc()).all()

    @classmethod
    def get_unread_by_user(cls, user_id: int) -> List['Notification']:
        """Get unread notifications by user."""
        return cls.query.filter_by(
            user_id=user_id,
            read=False
        ).order_by(cls.created_at.desc()).all()

    @classmethod
    def get_read_by_user(cls, user_id: int) -> List['Notification']:
        """Get read notifications by user."""
        return cls.query.filter_by(
            user_id=user_id,
            read=True
        ).order_by(cls.created_at.desc()).all()

    @classmethod
    def get_by_type(cls, type: str) -> List['Notification']:
        """Get notifications by type."""
        return cls.query.filter_by(type=type).all()

    @classmethod
    def get_recent_notifications(cls, limit: int = 10) -> List['Notification']:
        """Get recent notifications."""
        return cls.query.order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_expired_notifications(cls) -> List['Notification']:
        """Get expired notifications."""
        return cls.query.filter(
            cls.expires_at < get_current_time()
        ).all()

    @classmethod
    def mark_all_as_read(cls, user_id: int) -> None:
        """Mark all user notifications as read."""
        cls.query.filter_by(
            user_id=user_id,
            read=False
        ).update({
            'read': True,
            'read_at': get_current_time()
        })
        db.session.commit()

    @classmethod
    def delete_expired(cls) -> None:
        """Delete expired notifications."""
        cls.query.filter(
            cls.expires_at < get_current_time()
        ).delete()
        db.session.commit()

    def to_dict(self) -> dict:
        """Convert notification to dictionary."""
        data = super().to_dict()
        data['time_ago'] = self.time_ago
        data['is_expired'] = self.is_expired
        return data 