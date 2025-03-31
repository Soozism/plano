"""UserSession model class."""
from typing import List, Optional, Dict, Any
from flask_backend.models.base import BaseModel
from flask_backend.extensions import db
from datetime import datetime

class UserSession(BaseModel):
    """UserSession model."""
    __tablename__ = 'user_sessions'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(100), nullable=False, unique=True)
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.String(500))  # Browser/device info
    location = db.Column(db.String(200))  # Geographic location
    device_type = db.Column(db.String(50))  # desktop, mobile, tablet
    browser = db.Column(db.String(100))  # Chrome, Firefox, Safari, etc.
    os = db.Column(db.String(100))  # Windows, macOS, Linux, iOS, Android
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    is_remembered = db.Column(db.Boolean, default=False)
    metadata = db.Column(db.JSON)  # Additional session data
    security_info = db.Column(db.JSON)  # Security-related information
    activity_count = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    last_error = db.Column(db.Text)
    last_error_at = db.Column(db.DateTime)
    tags = db.Column(db.JSON)  # List of tags for categorization

    def __init__(self, **kwargs):
        """Initialize user session model."""
        super().__init__(**kwargs)
        if not self.metadata:
            self.metadata = {}
        if not self.security_info:
            self.security_info = {}
        if not self.tags:
            self.tags = []

    def update_last_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
        self.activity_count += 1
        self.save()

    def record_error(self, error_message: str) -> None:
        """Record an error for this session."""
        self.error_count += 1
        self.last_error = error_message
        self.last_error_at = datetime.utcnow()
        self.save()

    def deactivate(self) -> None:
        """Deactivate the session."""
        self.is_active = False
        self.save()

    def reactivate(self) -> None:
        """Reactivate the session."""
        self.is_active = True
        self.save()

    def extend_expiry(self, days: int = 30) -> None:
        """Extend session expiry."""
        self.expires_at = datetime.utcnow() + timedelta(days=days)
        self.save()

    def add_tag(self, tag: str) -> None:
        """Add a tag to the session."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.save()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the session."""
        if tag in self.tags:
            self.tags.remove(tag)
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

    def update_security_info(self, key: str, value: Any) -> None:
        """Update security information."""
        self.security_info[key] = value
        self.save()

    def remove_security_info(self, key: str) -> None:
        """Remove security information."""
        if key in self.security_info:
            del self.security_info[key]
            self.save()

    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def duration(self) -> int:
        """Get session duration in seconds."""
        return int((datetime.utcnow() - self.created_at).total_seconds())

    @property
    def inactivity_duration(self) -> int:
        """Get duration since last activity in seconds."""
        return int((datetime.utcnow() - self.last_activity).total_seconds())

    @classmethod
    def get_by_session_id(cls, session_id: str) -> Optional['UserSession']:
        """Get session by session ID."""
        return cls.query.filter_by(session_id=session_id).first()

    @classmethod
    def get_by_user(
        cls,
        user_id: int,
        active_only: bool = False,
        device_type: Optional[str] = None,
        browser: Optional[str] = None,
        os: Optional[str] = None,
        tag: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list:
        """Get sessions by user with optional filters."""
        query = cls.query.filter_by(user_id=user_id)

        if active_only:
            query = query.filter_by(is_active=True)
        if device_type:
            query = query.filter_by(device_type=device_type)
        if browser:
            query = query.filter_by(browser=browser)
        if os:
            query = query.filter_by(os=os)
        if tag:
            query = query.filter(cls.tags.contains([tag]))

        # Order by last activity descending
        query = query.order_by(cls.last_activity.desc())

        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)

        return query.all()

    @classmethod
    def get_active_sessions(
        cls,
        user_id: Optional[int] = None,
        device_type: Optional[str] = None,
        browser: Optional[str] = None,
        os: Optional[str] = None,
        tag: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list:
        """Get active sessions with optional filters."""
        query = cls.query.filter_by(is_active=True)

        if user_id:
            query = query.filter_by(user_id=user_id)
        if device_type:
            query = query.filter_by(device_type=device_type)
        if browser:
            query = query.filter_by(browser=browser)
        if os:
            query = query.filter_by(os=os)
        if tag:
            query = query.filter(cls.tags.contains([tag]))

        # Order by last activity descending
        query = query.order_by(cls.last_activity.desc())

        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)

        return query.all()

    @classmethod
    def deactivate_all_user_sessions(cls, user_id: int) -> None:
        """Deactivate all sessions for a user."""
        sessions = cls.query.filter_by(user_id=user_id, is_active=True).all()
        for session in sessions:
            session.deactivate()

    @classmethod
    def cleanup_expired_sessions(cls) -> None:
        """Deactivate all expired sessions."""
        sessions = cls.query.filter(
            cls.is_active == True,
            cls.expires_at < datetime.utcnow()
        ).all()
        for session in sessions:
            session.deactivate()

    def to_dict(self) -> dict:
        """Convert session to dictionary."""
        data = super().to_dict()
        data['metadata'] = self.metadata
        data['security_info'] = self.security_info
        data['tags'] = self.tags
        data['is_expired'] = self.is_expired
        data['duration'] = self.duration
        data['inactivity_duration'] = self.inactivity_duration
        return data 