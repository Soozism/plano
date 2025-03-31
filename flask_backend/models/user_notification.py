"""UserNotification model class."""
from typing import Optional, Dict, Any
from datetime import datetime
from flask_backend.models.base import BaseModel
from flask_backend.extensions import db

class UserNotification(BaseModel):
    """UserNotification model."""
    __tablename__ = 'user_notifications'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # task, sprint, comment, system, etc.
    priority = db.Column(db.String(20), default='normal')  # low, normal, high
    status = db.Column(db.String(20), default='unread')  # unread, read, archived
    read_at = db.Column(db.DateTime)
    action_url = db.Column(db.String(500))  # URL to navigate to when clicked
    metadata = db.Column(db.JSON)  # Additional data specific to notification type
    expires_at = db.Column(db.DateTime)  # When the notification expires
    is_sticky = db.Column(db.Boolean, default=False)  # Whether notification stays at top
    is_silent = db.Column(db.Boolean, default=False)  # Whether to show without sound
    is_persistent = db.Column(db.Boolean, default=False)  # Whether to keep after read
    category = db.Column(db.String(50))  # Category for grouping notifications
    tags = db.Column(db.JSON)  # List of tags for filtering
    related_models = db.Column(db.JSON)  # References to related models (e.g., task_id, sprint_id)

    def __init__(self, **kwargs):
        """Initialize user notification model."""
        super().__init__(**kwargs)
        if not self.metadata:
            self.metadata = {}
        if not self.tags:
            self.tags = []
        if not self.related_models:
            self.related_models = {}

    def mark_as_read(self) -> None:
        """Mark notification as read."""
        if self.status == 'unread':
            self.status = 'read'
            self.read_at = datetime.utcnow()
            self.save()

    def mark_as_unread(self) -> None:
        """Mark notification as unread."""
        if self.status == 'read':
            self.status = 'unread'
            self.read_at = None
            self.save()

    def archive(self) -> None:
        """Archive the notification."""
        self.status = 'archived'
        self.save()

    def unarchive(self) -> None:
        """Unarchive the notification."""
        self.status = 'read'
        self.save()

    def toggle_sticky(self) -> None:
        """Toggle sticky status."""
        self.is_sticky = not self.is_sticky
        self.save()

    def toggle_silent(self) -> None:
        """Toggle silent status."""
        self.is_silent = not self.is_silent
        self.save()

    def toggle_persistent(self) -> None:
        """Toggle persistent status."""
        self.is_persistent = not self.is_persistent
        self.save()

    def add_tag(self, tag: str) -> None:
        """Add a tag to the notification."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.save()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the notification."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.save()

    def add_related_model(self, model_type: str, model_id: int) -> None:
        """Add a related model reference."""
        self.related_models[model_type] = model_id
        self.save()

    def remove_related_model(self, model_type: str) -> None:
        """Remove a related model reference."""
        if model_type in self.related_models:
            del self.related_models[model_type]
            self.save()

    def update_metadata(self, key: str, value: Any) -> None:
        """Update metadata."""
        self.metadata[key] = value
        self.save()

    def remove_metadata(self, key: str) -> None:
        """Remove metadata."""
        if key in self.metadata:
            del self.metadata[key]
            self.save()

    @property
    def is_expired(self) -> bool:
        """Check if notification is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def age(self) -> int:
        """Get notification age in seconds."""
        return int((datetime.utcnow() - self.created_at).total_seconds())

    @classmethod
    def get_by_user(
        cls,
        user_id: int,
        status: Optional[str] = None,
        type: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        unread_only: bool = False,
        sticky_only: bool = False,
        persistent_only: bool = False,
        expired_only: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list:
        """Get notifications by user with optional filters."""
        query = cls.query.filter_by(user_id=user_id)

        if status:
            query = query.filter_by(status=status)
        if type:
            query = query.filter_by(type=type)
        if priority:
            query = query.filter_by(priority=priority)
        if category:
            query = query.filter_by(category=category)
        if tag:
            query = query.filter(cls.tags.contains([tag]))
        if unread_only:
            query = query.filter_by(status='unread')
        if sticky_only:
            query = query.filter_by(is_sticky=True)
        if persistent_only:
            query = query.filter_by(is_persistent=True)
        if expired_only:
            query = query.filter(cls.expires_at < datetime.utcnow())

        # Order by sticky first, then created_at
        query = query.order_by(cls.is_sticky.desc(), cls.created_at.desc())

        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)

        return query.all()

    @classmethod
    def get_unread_count(cls, user_id: int) -> int:
        """Get count of unread notifications."""
        return cls.query.filter_by(user_id=user_id, status='unread').count()

    @classmethod
    def mark_all_as_read(cls, user_id: int) -> None:
        """Mark all notifications as read for a user."""
        notifications = cls.query.filter_by(user_id=user_id, status='unread').all()
        for notification in notifications:
            notification.mark_as_read()

    @classmethod
    def archive_all(cls, user_id: int) -> None:
        """Archive all notifications for a user."""
        notifications = cls.query.filter_by(user_id=user_id).all()
        for notification in notifications:
            notification.archive()

    def to_dict(self) -> dict:
        """Convert notification to dictionary."""
        data = super().to_dict()
        data['metadata'] = self.metadata
        data['tags'] = self.tags
        data['related_models'] = self.related_models
        data['is_expired'] = self.is_expired
        data['age'] = self.age
        return data 