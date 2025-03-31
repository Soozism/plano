"""TimeEntry model class."""
from typing import List, Optional
from flask_backend.models.base import BaseModel
from flask_backend.extensions import db

class TimeEntry(BaseModel):
    """TimeEntry model."""
    __tablename__ = 'time_entries'

    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Integer)  # Duration in seconds
    description = db.Column(db.Text)
    is_billable = db.Column(db.Boolean, default=False)
    billable_amount = db.Column(db.Numeric(10, 2))
    billable_rate = db.Column(db.Numeric(10, 2))
    is_approved = db.Column(db.Boolean, default=False)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    tags = db.Column(db.JSON)  # List of tags for categorization

    def __init__(self, **kwargs):
        """Initialize time entry model."""
        super().__init__(**kwargs)
        if not self.start_time:
            self.start_time = get_current_time()

    def start_tracking(self) -> None:
        """Start time tracking."""
        self.start_time = get_current_time()
        self.end_time = None
        self.duration = None
        self.save()

    def stop_tracking(self) -> None:
        """Stop time tracking and calculate duration."""
        if not self.end_time:
            self.end_time = get_current_time()
            self.duration = int((self.end_time - self.start_time).total_seconds())
            self.save()

    def pause_tracking(self) -> None:
        """Pause time tracking."""
        if not self.end_time:
            self.end_time = get_current_time()
            self.duration = int((self.end_time - self.start_time).total_seconds())
            self.save()

    def resume_tracking(self) -> None:
        """Resume time tracking."""
        if self.end_time:
            self.start_time = get_current_time()
            self.end_time = None
            self.duration = None
            self.save()

    def approve(self, approved_by_id: int) -> None:
        """Approve time entry."""
        self.is_approved = True
        self.approved_by_id = approved_by_id
        self.approved_at = get_current_time()
        self.save()

    def reject(self) -> None:
        """Reject time entry."""
        self.is_approved = False
        self.approved_by_id = None
        self.approved_at = None
        self.save()

    def set_billable(self, amount: float, rate: float) -> None:
        """Set billable amount and rate."""
        self.is_billable = True
        self.billable_amount = amount
        self.billable_rate = rate
        self.save()

    def add_tags(self, tags: List[str]) -> None:
        """Add tags to time entry."""
        if not self.tags:
            self.tags = []
        self.tags.extend(tags)
        self.tags = list(set(self.tags))  # Remove duplicates
        self.save()

    def remove_tags(self, tags: List[str]) -> None:
        """Remove tags from time entry."""
        if self.tags:
            self.tags = [tag for tag in self.tags if tag not in tags]
            self.save()

    @property
    def is_active(self) -> bool:
        """Check if time entry is active."""
        return self.end_time is None

    @property
    def duration_formatted(self) -> str:
        """Get formatted duration string."""
        if not self.duration:
            return '0:00:00'
        
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        
        return f'{hours:02d}:{minutes:02d}:{seconds:02d}'

    @classmethod
    def get_by_task(cls, task_id: int) -> List['TimeEntry']:
        """Get time entries by task."""
        return cls.query.filter_by(task_id=task_id).order_by(cls.start_time.desc()).all()

    @classmethod
    def get_by_user(cls, user_id: int) -> List['TimeEntry']:
        """Get time entries by user."""
        return cls.query.filter_by(user_id=user_id).order_by(cls.start_time.desc()).all()

    @classmethod
    def get_active_entries(cls) -> List['TimeEntry']:
        """Get active time entries."""
        return cls.query.filter_by(end_time=None).all()

    @classmethod
    def get_approved_entries(cls) -> List['TimeEntry']:
        """Get approved time entries."""
        return cls.query.filter_by(is_approved=True).all()

    @classmethod
    def get_billable_entries(cls) -> List['TimeEntry']:
        """Get billable time entries."""
        return cls.query.filter_by(is_billable=True).all()

    @classmethod
    def get_by_date_range(cls, start_date: datetime, end_date: datetime) -> List['TimeEntry']:
        """Get time entries within date range."""
        return cls.query.filter(
            cls.start_time >= start_date,
            cls.start_time <= end_date
        ).order_by(cls.start_time.desc()).all()

    @classmethod
    def get_total_duration(cls, entries: List['TimeEntry']) -> int:
        """Get total duration of time entries."""
        return sum(entry.duration or 0 for entry in entries)

    @classmethod
    def get_total_billable_amount(cls, entries: List['TimeEntry']) -> float:
        """Get total billable amount of time entries."""
        return sum(float(entry.billable_amount or 0) for entry in entries)

    def to_dict(self) -> dict:
        """Convert time entry to dictionary."""
        data = super().to_dict()
        data['is_active'] = self.is_active
        data['duration_formatted'] = self.duration_formatted
        return data 