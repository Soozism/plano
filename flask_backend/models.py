from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import enum
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError
import os

db = SQLAlchemy()
bcrypt = Bcrypt()

# AWS S3 Configuration
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', 'us-east-1')
)
S3_BUCKET = os.getenv('AWS_S3_BUCKET')

# Junction tables for many-to-many relationships
group_memberships = db.Table('group_memberships',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id'), primary_key=True)
)

event_attendance = db.Table('event_attendance',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('event_id', db.Integer, db.ForeignKey('events.id'), primary_key=True)
)

task_tags = db.Table('task_tags',
    db.Column('task_id', db.Integer, db.ForeignKey('tasks.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)

# Enum classes
class Role(enum.Enum):
    OWNER = "owner"
    MANAGER = "manager"
    EMPLOYEE = "employee"

class Priority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Status(enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"

class TaskType(enum.Enum):
    TASK = "task"
    STORY = "story"
    BUG = "bug"

class RecurrenceRule(enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    NONE = "none"

# Base model class with common attributes
class BaseModel:
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model, BaseModel):
    __tablename__ = 'users'
    
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.Enum(Role), default=Role.EMPLOYEE)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    
    # Relationships
    organization = db.relationship('Organization', back_populates='users')
    groups = db.relationship('Group', secondary=group_memberships, back_populates='members')
    tasks_assigned = db.relationship('Task', foreign_keys='Task.assignee_user_id', back_populates='assignee_user')
    tasks_created = db.relationship('Task', foreign_keys='Task.created_by_id', back_populates='created_by')
    events_organized = db.relationship('Event', back_populates='organizer')
    comments = db.relationship('Comment', back_populates='user')
    time_logs = db.relationship('TimeLog', back_populates='user')
    notifications = db.relationship('Notification', back_populates='user')
    standup_logs = db.relationship('StandupLog', back_populates='user')
    retrospectives = db.relationship('Retrospective', back_populates='user')
    task_templates = db.relationship('TaskTemplate', back_populates='user')
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'email': self.email,
            'role': self.role.value if self.role else None,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Organization(db.Model, BaseModel):
    __tablename__ = 'organizations'
    
    name = db.Column(db.String(100), nullable=False)
    owner_id = db.Column(db.Integer, nullable=False)
    
    # Relationships
    users = db.relationship('User', back_populates='organization')
    groups = db.relationship('Group', back_populates='organization')
    sprints = db.relationship('Sprint', back_populates='organization')
    events = db.relationship('Event', back_populates='organization')
    tags = db.relationship('Tag', back_populates='organization')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'owner_id': self.owner_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Group(db.Model, BaseModel):
    __tablename__ = 'groups'
    
    name = db.Column(db.String(100), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    # Relationships
    organization = db.relationship('Organization', back_populates='groups')
    members = db.relationship('User', secondary=group_memberships, back_populates='groups')
    tasks = db.relationship('Task', back_populates='assignee_group')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'members_count': len(self.members)
        }

class Sprint(db.Model, BaseModel):
    """Model for sprints."""
    __tablename__ = 'sprints'
    
    name = db.Column(db.String(100), nullable=False)
    goal = db.Column(db.Text)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    velocity = db.Column(db.Float)  # Average velocity in story points
    planned_velocity = db.Column(db.Float)  # Planned velocity for this sprint
    is_completed = db.Column(db.Boolean, default=False)
    
    # Relationships
    organization = db.relationship('Organization', backref=db.backref('sprints', lazy=True))
    tasks = db.relationship('Task', back_populates='sprint')
    subgoals = db.relationship('Subgoal', back_populates='sprint')
    standup_logs = db.relationship('StandupLog', back_populates='sprint')
    retrospectives = db.relationship('Retrospective', back_populates='sprint')
    
    def calculate_velocity(self):
        """Calculate sprint velocity based on completed work."""
        # Get all completed tasks in this sprint
        completed_tasks = Task.query.filter(
            Task.sprint_id == self.id,
            Task.status.in_([Status.DONE, Status.CANCELLED])
        ).all()
        
        # Calculate total completed story points
        total_story_points = sum(task.story_points or 0 for task in completed_tasks)
        
        # Calculate total completed hours
        total_hours = sum(task.estimated_hours or 0 for task in completed_tasks)
        
        # Calculate velocity (prefer story points, fallback to hours)
        if total_story_points > 0:
            self.velocity = total_story_points
        elif total_hours > 0:
            self.velocity = total_hours
        else:
            self.velocity = 0
            
        return self.velocity
    
    def complete(self):
        """Mark sprint as completed and calculate final velocity."""
        self.is_completed = True
        self.calculate_velocity()
        db.session.commit()
    
    def to_dict(self):
        """Convert sprint to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'goal': self.goal,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'organization_id': self.organization_id,
            'velocity': self.velocity,
            'planned_velocity': self.planned_velocity,
            'is_completed': self.is_completed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Sprint {self.name}>'

class Subgoal(db.Model, BaseModel):
    """Model for sprint subgoals."""
    __tablename__ = 'subgoals'
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    sprint_id = db.Column(db.Integer, db.ForeignKey('sprints.id'), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    completed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    sprint = db.relationship('Sprint', back_populates='subgoals')
    completed_by = db.relationship('User', foreign_keys=[completed_by_id])
    
    def complete(self, user_id):
        """Mark subgoal as completed."""
        self.is_completed = True
        self.completed_at = datetime.utcnow()
        self.completed_by_id = user_id
        db.session.commit()
    
    def to_dict(self):
        """Convert subgoal to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'sprint_id': self.sprint_id,
            'is_completed': self.is_completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'completed_by': self.completed_by.to_dict() if self.completed_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Task(db.Model, BaseModel):
    __tablename__ = 'tasks'
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.Enum(Priority), default=Priority.MEDIUM)
    status = db.Column(db.Enum(Status), default=Status.TODO)
    deadline = db.Column(db.DateTime)
    story_points = db.Column(db.Integer)
    estimated_hours = db.Column(db.Integer)
    acceptance_criteria = db.Column(db.Text)
    assignee_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    assignee_group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    parent_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    sprint_id = db.Column(db.Integer, db.ForeignKey('sprints.id'))
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Recurrence fields
    recurrence_rule = db.Column(db.Enum(RecurrenceRule), default=RecurrenceRule.NONE)
    recurrence_end = db.Column(db.DateTime)
    original_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    
    # Relationships
    assignee_user = db.relationship('User', foreign_keys=[assignee_user_id], back_populates='tasks_assigned')
    assignee_group = db.relationship('Group', back_populates='tasks')
    created_by = db.relationship('User', foreign_keys=[created_by_id], back_populates='tasks_created')
    parent_task = db.relationship('Task', remote_side=[id], backref=db.backref('subtasks', lazy='dynamic'))
    sprint = db.relationship('Sprint', back_populates='tasks')
    time_logs = db.relationship('TimeLog', back_populates='task')
    comments = db.relationship('Comment', back_populates='task')
    milestones = db.relationship('Milestone', back_populates='task', cascade='all, delete-orphan')
    original_task = db.relationship('Task', remote_side=[id], backref=db.backref('recurring_instances', lazy='dynamic'))
    tags = db.relationship('Tag', secondary=task_tags, back_populates='tasks')
    
    def to_dict(self):
        # Basic task info
        result = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority.value if self.priority else None,
            'status': self.status.value if self.status else None,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'story_points': self.story_points,
            'estimated_hours': self.estimated_hours,
            'acceptance_criteria': self.acceptance_criteria,
            'assignee_user_id': self.assignee_user_id,
            'assignee_group_id': self.assignee_group_id,
            'parent_task_id': self.parent_task_id,
            'sprint_id': self.sprint_id,
            'organization_id': self.organization_id,
            'created_by_id': self.created_by_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'recurrence_rule': self.recurrence_rule.value if self.recurrence_rule else None,
            'recurrence_end': self.recurrence_end.isoformat() if self.recurrence_end else None,
            'original_task_id': self.original_task_id,
            'tags': [tag.to_dict() for tag in self.tags]
        }
        
        # Add assignee name if available
        if self.assignee_user:
            result['assignee_user_name'] = self.assignee_user.name
        
        if self.assignee_group:
            result['assignee_group_name'] = self.assignee_group.name
        
        if self.created_by:
            result['created_by_name'] = self.created_by.name
            
        # Add milestones and progress
        result['milestones'] = [milestone.to_dict() for milestone in self.milestones]
        result['progress'] = self.calculate_progress()
        
        return result
        
    def calculate_progress(self):
        """Calculate task progress based on completed milestones."""
        if not self.milestones:
            return 0
        completed_milestones = sum(1 for milestone in self.milestones if milestone.is_completed)
        return round((completed_milestones / len(self.milestones)) * 100, 1)

    def create_next_recurrence(self):
        """Create the next instance of this recurring task."""
        if not self.recurrence_rule or self.recurrence_rule == RecurrenceRule.NONE:
            return None
            
        # Calculate next occurrence date
        next_date = self.created_at
        if self.recurrence_rule == RecurrenceRule.DAILY:
            next_date = self.created_at + timedelta(days=1)
        elif self.recurrence_rule == RecurrenceRule.WEEKLY:
            next_date = self.created_at + timedelta(weeks=1)
        elif self.recurrence_rule == RecurrenceRule.MONTHLY:
            # Add one month (approximate)
            next_date = self.created_at + timedelta(days=30)
            
        # Check if we've passed the recurrence end date
        if self.recurrence_end and next_date > self.recurrence_end:
            return None
            
        # Create new task instance
        new_task = Task(
            title=self.title,
            description=self.description,
            priority=self.priority,
            estimated_hours=self.estimated_hours,
            acceptance_criteria=self.acceptance_criteria,
            assignee_user_id=self.assignee_user_id,
            assignee_group_id=self.assignee_group_id,
            organization_id=self.organization_id,
            created_by_id=self.created_by_id,
            created_at=next_date,
            original_task_id=self.id if not self.original_task_id else self.original_task_id
        )
        
        return new_task

class Event(db.Model, BaseModel):
    __tablename__ = 'events'
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    series_id = db.Column(db.Integer)  # For recurring events
    is_canceled = db.Column(db.Boolean, default=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    # Relationships
    organizer = db.relationship('User', back_populates='events_organized')
    organization = db.relationship('Organization', back_populates='events')
    attendees = db.relationship('User', secondary=event_attendance)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'organizer_id': self.organizer_id,
            'organizer_name': self.organizer.name if self.organizer else None,
            'series_id': self.series_id,
            'is_canceled': self.is_canceled,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class TimeLog(db.Model, BaseModel):
    __tablename__ = 'time_logs'
    
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Integer)  # in minutes
    description = db.Column(db.Text)
    
    # Relationships
    task = db.relationship('Task', back_populates='time_logs')
    user = db.relationship('User', back_populates='time_logs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'task_title': self.task.title if self.task else None,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Comment(db.Model, BaseModel):
    __tablename__ = 'comments'
    
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    # Relationships
    task = db.relationship('Task', back_populates='comments')
    user = db.relationship('User', back_populates='comments')
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Notification(db.Model, BaseModel):
    __tablename__ = 'notifications'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    read = db.Column(db.Boolean, default=False)
    related_id = db.Column(db.Integer)  # ID of related entity (task, event, etc.)
    related_type = db.Column(db.String(50))  # Type of related entity
    
    # Relationships
    user = db.relationship('User', back_populates='notifications')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message': self.message,
            'type': self.type,
            'read': self.read,
            'related_id': self.related_id,
            'related_type': self.related_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class BacklogItem(db.Model, BaseModel):
    __tablename__ = 'backlog_items'
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.Integer, nullable=False)  # Numeric priority for ordering
    type = db.Column(db.Enum(TaskType), default=TaskType.TASK)
    story_points = db.Column(db.Integer)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'type': self.type.value if self.type else None,
            'story_points': self.story_points,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Epic(db.Model, BaseModel):
    __tablename__ = 'epics'
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    # Relationships
    user_stories = db.relationship('UserStory', back_populates='epic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class UserStory(db.Model, BaseModel):
    __tablename__ = 'user_stories'
    
    epic_id = db.Column(db.Integer, db.ForeignKey('epics.id'))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    acceptance_criteria = db.Column(db.Text)
    story_points = db.Column(db.Integer)
    
    # Relationships
    epic = db.relationship('Epic', back_populates='user_stories')
    
    def to_dict(self):
        return {
            'id': self.id,
            'epic_id': self.epic_id,
            'title': self.title,
            'description': self.description,
            'acceptance_criteria': self.acceptance_criteria,
            'story_points': self.story_points,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class StandupLog(db.Model, BaseModel):
    __tablename__ = 'standup_logs'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sprint_id = db.Column(db.Integer, db.ForeignKey('sprints.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    yesterday = db.Column(db.Text, nullable=False)
    today = db.Column(db.Text, nullable=False)
    blockers = db.Column(db.Text)
    
    # Relationships
    user = db.relationship('User', back_populates='standup_logs')
    sprint = db.relationship('Sprint', back_populates='standup_logs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'sprint_id': self.sprint_id,
            'date': self.date.isoformat() if self.date else None,
            'yesterday': self.yesterday,
            'today': self.today,
            'blockers': self.blockers,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Retrospective(db.Model, BaseModel):
    __tablename__ = 'retrospectives'
    
    sprint_id = db.Column(db.Integer, db.ForeignKey('sprints.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    went_well = db.Column(db.Text)
    went_wrong = db.Column(db.Text)
    action_items = db.Column(db.Text)
    is_anonymous = db.Column(db.Boolean, default=False)
    
    # Relationships
    sprint = db.relationship('Sprint', back_populates='retrospectives')
    user = db.relationship('User', back_populates='retrospectives')
    
    def to_dict(self):
        return {
            'id': self.id,
            'sprint_id': self.sprint_id,
            'user_id': self.user_id,
            'user_name': None if self.is_anonymous else (self.user.name if self.user else None),
            'went_well': self.went_well,
            'went_wrong': self.went_wrong,
            'action_items': self.action_items,
            'is_anonymous': self.is_anonymous,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Milestone(db.Model, BaseModel):
    __tablename__ = 'milestones'
    
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    task = db.relationship('Task', back_populates='milestones')
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'description': self.description,
            'is_completed': self.is_completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class TaskTemplate(db.Model, BaseModel):
    __tablename__ = 'task_templates'
    
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.Enum(Priority), default=Priority.MEDIUM)
    estimated_hours = db.Column(db.Integer)
    acceptance_criteria = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    # Relationships
    user = db.relationship('User', back_populates='task_templates')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'title': self.title,
            'description': self.description,
            'priority': self.priority.value if self.priority else None,
            'estimated_hours': self.estimated_hours,
            'acceptance_criteria': self.acceptance_criteria,
            'user_id': self.user_id,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
    def create_task(self, user_id, **kwargs):
        """Create a new task from this template with optional overrides."""
        task_data = {
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'estimated_hours': self.estimated_hours,
            'acceptance_criteria': self.acceptance_criteria,
            'organization_id': self.organization_id,
            'created_by_id': user_id,
            'status': Status.TODO
        }
        
        # Apply any overrides
        task_data.update(kwargs)
        
        return Task(**task_data)

class Tag(db.Model, BaseModel):
    __tablename__ = 'tags'
    
    name = db.Column(db.String(50), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    # Relationships
    organization = db.relationship('Organization', back_populates='tags')
    tasks = db.relationship('Task', secondary=task_tags, back_populates='tags')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Message(db.Model):
    """Model for task-related chat messages."""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    task = db.relationship('Task', backref=db.backref('messages', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('messages', lazy=True))
    
    def to_dict(self):
        """Convert message to dictionary."""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Message {self.id} on Task {self.task_id}>'

class Attachment(db.Model, BaseModel):
    """Model for file attachments on tasks and events."""
    __tablename__ = 'attachments'
    
    file_name = db.Column(db.String(255), nullable=False)
    file_url = db.Column(db.String(512), nullable=False)
    file_type = db.Column(db.String(100))
    file_size = db.Column(db.Integer)  # in bytes
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    # Relationships
    task = db.relationship('Task', backref=db.backref('attachments', lazy=True, cascade='all, delete-orphan'))
    event = db.relationship('Event', backref=db.backref('attachments', lazy=True, cascade='all, delete-orphan'))
    uploaded_by = db.relationship('User', backref=db.backref('attachments', lazy=True))
    organization = db.relationship('Organization', backref=db.backref('attachments', lazy=True))
    
    def to_dict(self):
        """Convert attachment to dictionary."""
        return {
            'id': self.id,
            'file_name': self.file_name,
            'file_url': self.file_url,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'task_id': self.task_id,
            'event_id': self.event_id,
            'uploaded_by_id': self.uploaded_by_id,
            'uploaded_by_name': self.uploaded_by.name if self.uploaded_by else None,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Attachment {self.file_name}>'
    
    @staticmethod
    def generate_presigned_url(file_url, expiration=3600):
        """Generate a presigned URL for temporary file access."""
        try:
            # Extract the key from the file_url
            key = file_url.split(f'https://{S3_BUCKET}.s3.amazonaws.com/')[1]
            
            # Generate presigned URL
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': S3_BUCKET, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None
    
    def delete_from_s3(self):
        """Delete the file from S3."""
        try:
            # Extract the key from the file_url
            key = self.file_url.split(f'https://{S3_BUCKET}.s3.amazonaws.com/')[1]
            
            # Delete from S3
            s3_client.delete_object(Bucket=S3_BUCKET, Key=key)
            return True
        except ClientError as e:
            print(f"Error deleting file from S3: {e}")
            return False

class AuditLog(db.Model, BaseModel):
    """Model for audit logging."""
    __tablename__ = 'audit_logs'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # e.g., 'create', 'update', 'delete'
    entity_type = db.Column(db.String(50), nullable=False)  # e.g., 'task', 'event', 'sprint'
    entity_id = db.Column(db.Integer, nullable=False)
    changes = db.Column(db.JSON)  # Store the changes made
    ip_address = db.Column(db.String(45))  # Store IP address for security
    user_agent = db.Column(db.String(255))  # Store user agent string
    
    # Relationships
    user = db.relationship('User', backref=db.backref('audit_logs', lazy=True))
    
    @classmethod
    def log_action(cls, user_id, action, entity_type, entity_id, changes=None, request=None):
        """Create an audit log entry."""
        log = cls(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=changes,
            ip_address=request.remote_addr if request else None,
            user_agent=request.user_agent.string if request else None
        )
        db.session.add(log)
        db.session.commit()
        return log
    
    def to_dict(self):
        """Convert audit log to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'changes': self.changes,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

