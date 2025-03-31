"""Sprint model class."""
from typing import List, Optional
from flask_backend.models.base import BaseModel
from flask_backend.utils.constants import SprintStatus
from flask_backend.extensions import db

class Sprint(BaseModel):
    """Sprint model."""
    __tablename__ = 'sprints'

    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default=SprintStatus.PLANNING)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goal = db.Column(db.Text)
    velocity = db.Column(db.Float)
    story_points = db.Column(db.Float)
    completed_story_points = db.Column(db.Float, default=0)
    is_active = db.Column(db.Boolean, default=False)
    retrospective = db.Column(db.Text)

    # Relationships
    tasks = db.relationship('Task', backref='sprint', lazy='dynamic')
    created_by = db.relationship('User', backref='created_sprints', lazy='joined')

    def __init__(self, **kwargs):
        """Initialize sprint model."""
        super().__init__(**kwargs)
        if not self.status:
            self.status = SprintStatus.PLANNING

    def update_status(self, status: str) -> None:
        """Update sprint status."""
        self.status = status
        if status == SprintStatus.ACTIVE:
            self.is_active = True
        elif status == SprintStatus.COMPLETED:
            self.is_active = False
        self.save()

    def add_task(self, task: 'Task') -> None:
        """Add task to sprint."""
        task.sprint_id = self.id
        task.save()

    def remove_task(self, task: 'Task') -> None:
        """Remove task from sprint."""
        task.sprint_id = None
        task.save()

    def calculate_velocity(self) -> float:
        """Calculate sprint velocity."""
        completed_tasks = self.tasks.filter_by(is_completed=True).all()
        total_points = sum(task.estimated_hours or 0 for task in completed_tasks)
        self.velocity = total_points
        self.save()
        return total_points

    def calculate_story_points(self) -> float:
        """Calculate total story points."""
        total_points = sum(task.estimated_hours or 0 for task in self.tasks.all())
        self.story_points = total_points
        self.save()
        return total_points

    def calculate_completed_story_points(self) -> float:
        """Calculate completed story points."""
        completed_points = sum(
            task.estimated_hours or 0
            for task in self.tasks.filter_by(is_completed=True).all()
        )
        self.completed_story_points = completed_points
        self.save()
        return completed_points

    def calculate_burndown(self) -> List[Dict[str, Any]]:
        """Calculate burndown chart data."""
        from datetime import timedelta
        from flask_backend.models.time_entry import TimeEntry

        burndown_data = []
        current_date = self.start_date
        total_points = self.story_points or 0
        remaining_points = total_points

        while current_date <= self.end_date:
            # Calculate completed points up to current date
            completed_points = sum(
                task.estimated_hours or 0
                for task in self.tasks.filter(
                    Task.is_completed == True,
                    Task.completed_at <= current_date
                ).all()
            )

            # Calculate ideal burndown
            days_total = (self.end_date - self.start_date).days
            days_elapsed = (current_date - self.start_date).days
            ideal_points = total_points * (1 - days_elapsed / days_total) if days_total > 0 else 0

            burndown_data.append({
                'date': current_date.isoformat(),
                'actual': total_points - completed_points,
                'ideal': ideal_points
            })

            current_date += timedelta(days=1)

        return burndown_data

    @property
    def progress(self) -> float:
        """Get sprint progress percentage."""
        if not self.story_points:
            return 0
        return min(100, (self.completed_story_points or 0) / self.story_points * 100)

    @property
    def days_remaining(self) -> int:
        """Get days remaining in sprint."""
        if not self.is_active:
            return 0
        return max(0, (self.end_date - get_current_time()).days)

    @property
    def is_overdue(self) -> bool:
        """Check if sprint is overdue."""
        if not self.is_active:
            return False
        return get_current_time() > self.end_date

    @property
    def tasks_count(self) -> int:
        """Get total task count."""
        return self.tasks.count()

    @property
    def completed_tasks_count(self) -> int:
        """Get completed task count."""
        return self.tasks.filter_by(is_completed=True).count()

    @property
    def active_tasks_count(self) -> int:
        """Get active task count."""
        return self.tasks.filter_by(is_completed=False).count()

    @classmethod
    def get_active_sprint(cls) -> Optional['Sprint']:
        """Get currently active sprint."""
        return cls.query.filter_by(
            status=SprintStatus.ACTIVE,
            is_active=True
        ).first()

    @classmethod
    def get_completed_sprints(cls) -> List['Sprint']:
        """Get completed sprints."""
        return cls.query.filter_by(status=SprintStatus.COMPLETED).all()

    @classmethod
    def get_planning_sprints(cls) -> List['Sprint']:
        """Get planning sprints."""
        return cls.query.filter_by(status=SprintStatus.PLANNING).all()

    @classmethod
    def get_sprints_by_creator(cls, user_id: int) -> List['Sprint']:
        """Get sprints created by user."""
        return cls.query.filter_by(created_by_id=user_id).all()

    @classmethod
    def get_overdue_sprints(cls) -> List['Sprint']:
        """Get overdue sprints."""
        return cls.query.filter(
            cls.end_date < get_current_time(),
            cls.status == SprintStatus.ACTIVE
        ).all()

    def to_dict(self) -> dict:
        """Convert sprint to dictionary."""
        data = super().to_dict()
        data['burndown_data'] = self.calculate_burndown()
        return data 