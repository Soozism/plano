"""Task model class."""
from typing import List, Optional
from flask_backend.models.base import BaseModel
from flask_backend.utils.constants import TaskStatus, TaskPriority
from flask_backend.extensions import db

class Task(BaseModel):
    """Task model."""
    __tablename__ = 'tasks'

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default=TaskStatus.TODO)
    priority = db.Column(db.String(20), nullable=False, default=TaskPriority.MEDIUM)
    due_date = db.Column(db.DateTime)
    estimated_hours = db.Column(db.Float)
    actual_hours = db.Column(db.Float)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sprint_id = db.Column(db.Integer, db.ForeignKey('sprints.id'))
    parent_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    tags = db.Column(db.JSON)

    # Relationships
    comments = db.relationship('Comment', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    attachments = db.relationship('Attachment', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    subtasks = db.relationship('Task', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    time_entries = db.relationship('TimeEntry', backref='task', lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        """Initialize task model."""
        super().__init__(**kwargs)
        if not self.status:
            self.status = TaskStatus.TODO
        if not self.priority:
            self.priority = TaskPriority.MEDIUM

    def update_status(self, status: str) -> None:
        """Update task status."""
        self.status = status
        if status == TaskStatus.DONE:
            self.is_completed = True
            self.completed_at = get_current_time()
        else:
            self.is_completed = False
            self.completed_at = None
        self.save()

    def update_priority(self, priority: str) -> None:
        """Update task priority."""
        self.priority = priority
        self.save()

    def assign_to(self, user_id: int) -> None:
        """Assign task to user."""
        self.assigned_to_id = user_id
        self.save()

    def add_subtask(self, task: 'Task') -> None:
        """Add subtask."""
        task.parent_task_id = self.id
        task.save()

    def remove_subtask(self, task: 'Task') -> None:
        """Remove subtask."""
        task.parent_task_id = None
        task.save()

    def add_comment(self, user_id: int, content: str) -> 'Comment':
        """Add comment to task."""
        from flask_backend.models.comment import Comment
        comment = Comment(
            content=content,
            task_id=self.id,
            user_id=user_id
        )
        comment.save()
        return comment

    def add_attachment(self, user_id: int, filename: str, file_url: str, file_size: int, file_type: str) -> 'Attachment':
        """Add attachment to task."""
        from flask_backend.models.attachment import Attachment
        attachment = Attachment(
            filename=filename,
            file_url=file_url,
            file_size=file_size,
            file_type=file_type,
            task_id=self.id,
            user_id=user_id
        )
        attachment.save()
        return attachment

    def add_time_entry(self, user_id: int, hours: float, description: str = None) -> 'TimeEntry':
        """Add time entry to task."""
        from flask_backend.models.time_entry import TimeEntry
        time_entry = TimeEntry(
            hours=hours,
            description=description,
            task_id=self.id,
            user_id=user_id
        )
        time_entry.save()
        self.actual_hours = (self.actual_hours or 0) + hours
        self.save()
        return time_entry

    @property
    def total_hours(self) -> float:
        """Get total hours spent on task."""
        return self.actual_hours or 0

    @property
    def remaining_hours(self) -> float:
        """Get remaining hours."""
        if not self.estimated_hours:
            return 0
        return max(0, self.estimated_hours - (self.actual_hours or 0))

    @property
    def progress(self) -> float:
        """Get task progress percentage."""
        if not self.estimated_hours:
            return 0
        return min(100, (self.actual_hours or 0) / self.estimated_hours * 100)

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if not self.due_date or self.is_completed:
            return False
        return get_current_time() > self.due_date

    @property
    def days_overdue(self) -> int:
        """Get days overdue."""
        if not self.is_overdue:
            return 0
        return (get_current_time() - self.due_date).days

    @classmethod
    def get_by_status(cls, status: str) -> List['Task']:
        """Get tasks by status."""
        return cls.query.filter_by(status=status).all()

    @classmethod
    def get_by_priority(cls, priority: str) -> List['Task']:
        """Get tasks by priority."""
        return cls.query.filter_by(priority=priority).all()

    @classmethod
    def get_by_assignee(cls, user_id: int) -> List['Task']:
        """Get tasks assigned to user."""
        return cls.query.filter_by(assigned_to_id=user_id).all()

    @classmethod
    def get_by_creator(cls, user_id: int) -> List['Task']:
        """Get tasks created by user."""
        return cls.query.filter_by(created_by_id=user_id).all()

    @classmethod
    def get_by_sprint(cls, sprint_id: int) -> List['Task']:
        """Get tasks in sprint."""
        return cls.query.filter_by(sprint_id=sprint_id).all()

    @classmethod
    def get_overdue_tasks(cls) -> List['Task']:
        """Get overdue tasks."""
        return cls.query.filter(
            cls.due_date < get_current_time(),
            cls.is_completed == False
        ).all()

    @classmethod
    def get_completed_tasks(cls) -> List['Task']:
        """Get completed tasks."""
        return cls.query.filter_by(is_completed=True).all()

    @classmethod
    def get_active_tasks(cls) -> List['Task']:
        """Get active tasks."""
        return cls.query.filter_by(is_completed=False).all()

    @classmethod
    def get_tasks_by_tag(cls, tag: str) -> List['Task']:
        """Get tasks by tag."""
        return cls.query.filter(cls.tags.contains([tag])).all() 