"""UserActivity model class."""
from typing import Optional, Dict, Any
from datetime import datetime
from flask_backend.models.base import BaseModel
from flask_backend.extensions import db

class UserActivity(BaseModel):
    """UserActivity model."""
    __tablename__ = 'user_activities'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # create, update, delete, view, etc.
    entity_type = db.Column(db.String(50), nullable=False)  # task, sprint, comment, etc.
    entity_id = db.Column(db.Integer)  # ID of the affected entity
    details = db.Column(db.Text)  # Human-readable description
    metadata = db.Column(db.JSON)  # Additional data about the action
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.String(500))  # Browser/device info
    location = db.Column(db.String(200))  # Geographic location
    session_id = db.Column(db.String(100))  # Browser session ID
    duration = db.Column(db.Integer)  # Duration in milliseconds
    status = db.Column(db.String(20), default='success')  # success, error, warning
    error_message = db.Column(db.Text)  # Error details if status is error
    tags = db.Column(db.JSON)  # List of tags for categorization
    related_activities = db.Column(db.JSON)  # References to related activities

    def __init__(self, **kwargs):
        """Initialize user activity model."""
        super().__init__(**kwargs)
        if not self.metadata:
            self.metadata = {}
        if not self.tags:
            self.tags = []
        if not self.related_activities:
            self.related_activities = []

    def add_tag(self, tag: str) -> None:
        """Add a tag to the activity."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.save()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the activity."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.save()

    def add_related_activity(self, activity_id: int) -> None:
        """Add a related activity reference."""
        if activity_id not in self.related_activities:
            self.related_activities.append(activity_id)
            self.save()

    def remove_related_activity(self, activity_id: int) -> None:
        """Remove a related activity reference."""
        if activity_id in self.related_activities:
            self.related_activities.remove(activity_id)
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

    def mark_as_error(self, error_message: str) -> None:
        """Mark activity as error with message."""
        self.status = 'error'
        self.error_message = error_message
        self.save()

    def mark_as_warning(self) -> None:
        """Mark activity as warning."""
        self.status = 'warning'
        self.save()

    @property
    def age(self) -> int:
        """Get activity age in seconds."""
        return int((datetime.utcnow() - self.created_at).total_seconds())

    @classmethod
    def get_by_user(
        cls,
        user_id: int,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        status: Optional[str] = None,
        tag: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list:
        """Get activities by user with optional filters."""
        query = cls.query.filter_by(user_id=user_id)

        if action:
            query = query.filter_by(action=action)
        if entity_type:
            query = query.filter_by(entity_type=entity_type)
        if entity_id:
            query = query.filter_by(entity_id=entity_id)
        if status:
            query = query.filter_by(status=status)
        if tag:
            query = query.filter(cls.tags.contains([tag]))
        if start_date:
            query = query.filter(cls.created_at >= start_date)
        if end_date:
            query = query.filter(cls.created_at <= end_date)

        # Order by created_at descending
        query = query.order_by(cls.created_at.desc())

        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)

        return query.all()

    @classmethod
    def get_by_entity(
        cls,
        entity_type: str,
        entity_id: int,
        action: Optional[str] = None,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> list:
        """Get activities by entity with optional filters."""
        query = cls.query.filter_by(entity_type=entity_type, entity_id=entity_id)

        if action:
            query = query.filter_by(action=action)
        if user_id:
            query = query.filter_by(user_id=user_id)
        if status:
            query = query.filter_by(status=status)
        if start_date:
            query = query.filter(cls.created_at >= start_date)
        if end_date:
            query = query.filter(cls.created_at <= end_date)

        # Order by created_at descending
        query = query.order_by(cls.created_at.desc())

        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)

        return query.all()

    @classmethod
    def get_activity_summary(
        cls,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Get activity summary for a user."""
        query = cls.query.filter_by(user_id=user_id)

        if start_date:
            query = query.filter(cls.created_at >= start_date)
        if end_date:
            query = query.filter(cls.created_at <= end_date)

        activities = query.all()

        summary = {
            'total_activities': len(activities),
            'actions': {},
            'entity_types': {},
            'status': {
                'success': 0,
                'error': 0,
                'warning': 0
            },
            'average_duration': 0,
            'tags': {}
        }

        total_duration = 0
        for activity in activities:
            # Count actions
            summary['actions'][activity.action] = summary['actions'].get(activity.action, 0) + 1

            # Count entity types
            summary['entity_types'][activity.entity_type] = summary['entity_types'].get(activity.entity_type, 0) + 1

            # Count status
            summary['status'][activity.status] += 1

            # Add duration
            if activity.duration:
                total_duration += activity.duration

            # Count tags
            for tag in activity.tags:
                summary['tags'][tag] = summary['tags'].get(tag, 0) + 1

        # Calculate average duration
        if summary['total_activities'] > 0:
            summary['average_duration'] = total_duration / summary['total_activities']

        return summary

    def to_dict(self) -> dict:
        """Convert activity to dictionary."""
        data = super().to_dict()
        data['metadata'] = self.metadata
        data['tags'] = self.tags
        data['related_activities'] = self.related_activities
        data['age'] = self.age
        return data 