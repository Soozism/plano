"""User model class."""
from typing import List, Optional
from flask_backend.models.base import BaseModel
from flask_backend.utils.constants import UserRole
from flask_backend.utils.helpers import generate_password_hash, check_password_hash
from flask_backend.extensions import db

class User(BaseModel):
    """User model."""
    __tablename__ = 'users'

    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=UserRole.MEMBER)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(100), unique=True)
    password_reset_token = db.Column(db.String(100), unique=True)
    password_reset_expires = db.Column(db.DateTime)

    # Relationships
    tasks = db.relationship('Task', backref='assigned_to', lazy='dynamic')
    created_tasks = db.relationship('Task', backref='created_by', lazy='dynamic')
    comments = db.relationship('Comment', backref='user', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')

    def __init__(self, **kwargs):
        """Initialize user model."""
        if 'password' in kwargs:
            kwargs['password_hash'] = generate_password_hash(kwargs.pop('password'))
        super().__init__(**kwargs)

    def check_password(self, password: str) -> bool:
        """Check if password matches hash."""
        return check_password_hash(self.password_hash, password)

    def set_password(self, password: str) -> None:
        """Set password hash."""
        self.password_hash = generate_password_hash(password)

    def verify_email(self) -> None:
        """Mark email as verified."""
        self.email_verified = True
        self.email_verification_token = None
        self.save()

    def set_password_reset_token(self, token: str, expires_in: int = 3600) -> None:
        """Set password reset token."""
        from datetime import datetime, timedelta
        self.password_reset_token = token
        self.password_reset_expires = datetime.utcnow() + timedelta(seconds=expires_in)
        self.save()

    def clear_password_reset_token(self) -> None:
        """Clear password reset token."""
        self.password_reset_token = None
        self.password_reset_expires = None
        self.save()

    def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login = get_current_time()
        self.save()

    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.OWNER

    @property
    def is_manager(self) -> bool:
        """Check if user is manager."""
        return self.role in [UserRole.OWNER, UserRole.MANAGER]

    @property
    def task_count(self) -> int:
        """Get total task count."""
        return self.tasks.count()

    @property
    def completed_task_count(self) -> int:
        """Get completed task count."""
        return self.tasks.filter_by(status='DONE').count()

    @property
    def pending_task_count(self) -> int:
        """Get pending task count."""
        return self.tasks.filter_by(status='TODO').count()

    @property
    def in_progress_task_count(self) -> int:
        """Get in-progress task count."""
        return self.tasks.filter_by(status='IN_PROGRESS').count()

    @property
    def unread_notification_count(self) -> int:
        """Get unread notification count."""
        return self.notifications.filter_by(read=False).count()

    def to_dict(self) -> dict:
        """Convert user to dictionary."""
        data = super().to_dict()
        data.pop('password_hash', None)
        data.pop('email_verification_token', None)
        data.pop('password_reset_token', None)
        data.pop('password_reset_expires', None)
        return data

    @classmethod
    def get_by_email(cls, email: str) -> Optional['User']:
        """Get user by email."""
        return cls.query.filter_by(email=email).first()

    @classmethod
    def get_by_username(cls, username: str) -> Optional['User']:
        """Get user by username."""
        return cls.query.filter_by(username=username).first()

    @classmethod
    def get_by_verification_token(cls, token: str) -> Optional['User']:
        """Get user by email verification token."""
        return cls.query.filter_by(email_verification_token=token).first()

    @classmethod
    def get_by_reset_token(cls, token: str) -> Optional['User']:
        """Get user by password reset token."""
        return cls.query.filter_by(password_reset_token=token).first()

    @classmethod
    def get_active_users(cls) -> List['User']:
        """Get all active users."""
        return cls.query.filter_by(is_active=True).all()

    @classmethod
    def get_admins(cls) -> List['User']:
        """Get all admin users."""
        return cls.query.filter_by(role=UserRole.OWNER).all()

    @classmethod
    def get_managers(cls) -> List['User']:
        """Get all manager users."""
        return cls.query.filter(User.role.in_([UserRole.OWNER, UserRole.MANAGER])).all()

    @classmethod
    def get_members(cls) -> List['User']:
        """Get all member users."""
        return cls.query.filter_by(role=UserRole.MEMBER).all() 