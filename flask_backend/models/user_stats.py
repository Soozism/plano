"""UserStats model class."""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from flask_backend.models.base import BaseModel
from flask_backend.extensions import db

class UserStats(BaseModel):
    """UserStats model."""
    __tablename__ = 'user_stats'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    total_tasks = db.Column(db.Integer, default=0)
    completed_tasks = db.Column(db.Integer, default=0)
    overdue_tasks = db.Column(db.Integer, default=0)
    total_sprints = db.Column(db.Integer, default=0)
    completed_sprints = db.Column(db.Integer, default=0)
    total_story_points = db.Column(db.Integer, default=0)
    completed_story_points = db.Column(db.Integer, default=0)
    total_time_logged = db.Column(db.Integer, default=0)  # In minutes
    total_comments = db.Column(db.Integer, default=0)
    total_attachments = db.Column(db.Integer, default=0)
    total_activities = db.Column(db.Integer, default=0)
    total_sessions = db.Column(db.Integer, default=0)
    total_logins = db.Column(db.Integer, default=0)
    last_login = db.Column(db.DateTime)
    last_activity = db.Column(db.DateTime)
    average_daily_tasks = db.Column(db.Float, default=0.0)
    average_daily_time = db.Column(db.Float, default=0.0)  # In minutes
    completion_rate = db.Column(db.Float, default=0.0)  # Percentage
    on_time_rate = db.Column(db.Float, default=0.0)  # Percentage
    productivity_score = db.Column(db.Float, default=0.0)  # 0-100
    engagement_score = db.Column(db.Float, default=0.0)  # 0-100
    streak_days = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    daily_stats = db.Column(db.JSON)  # Daily activity stats
    weekly_stats = db.Column(db.JSON)  # Weekly activity stats
    monthly_stats = db.Column(db.JSON)  # Monthly activity stats
    yearly_stats = db.Column(db.JSON)  # Yearly activity stats
    tags = db.Column(db.JSON)  # List of most used tags
    categories = db.Column(db.JSON)  # Most active categories
    metadata = db.Column(db.JSON)  # Additional statistics

    def __init__(self, **kwargs):
        """Initialize user stats model."""
        super().__init__(**kwargs)
        if not self.daily_stats:
            self.daily_stats = {}
        if not self.weekly_stats:
            self.weekly_stats = {}
        if not self.monthly_stats:
            self.monthly_stats = {}
        if not self.yearly_stats:
            self.yearly_stats = {}
        if not self.tags:
            self.tags = {}
        if not self.categories:
            self.categories = {}
        if not self.metadata:
            self.metadata = {}

    def update_task_stats(
        self,
        total_delta: int = 0,
        completed_delta: int = 0,
        overdue_delta: int = 0
    ) -> None:
        """Update task-related statistics."""
        self.total_tasks += total_delta
        self.completed_tasks += completed_delta
        self.overdue_tasks += overdue_delta
        
        if self.total_tasks > 0:
            self.completion_rate = (self.completed_tasks / self.total_tasks) * 100
            self.on_time_rate = ((self.completed_tasks - self.overdue_tasks) / self.total_tasks) * 100
        
        self.save()

    def update_sprint_stats(
        self,
        total_delta: int = 0,
        completed_delta: int = 0,
        story_points_delta: int = 0,
        completed_points_delta: int = 0
    ) -> None:
        """Update sprint-related statistics."""
        self.total_sprints += total_delta
        self.completed_sprints += completed_delta
        self.total_story_points += story_points_delta
        self.completed_story_points += completed_points_delta
        self.save()

    def log_time(self, minutes: int) -> None:
        """Log time spent on tasks."""
        self.total_time_logged += minutes
        self.update_daily_stats('time_logged', minutes)
        self.save()

    def update_activity_counts(
        self,
        comments_delta: int = 0,
        attachments_delta: int = 0,
        activities_delta: int = 0
    ) -> None:
        """Update activity-related counts."""
        self.total_comments += comments_delta
        self.total_attachments += attachments_delta
        self.total_activities += activities_delta
        self.save()

    def record_login(self) -> None:
        """Record a user login."""
        self.total_logins += 1
        self.last_login = datetime.utcnow()
        self.update_daily_stats('logins', 1)
        self.save()

    def record_session(self) -> None:
        """Record a user session."""
        self.total_sessions += 1
        self.update_daily_stats('sessions', 1)
        self.save()

    def update_activity_timestamp(self) -> None:
        """Update last activity timestamp."""
        now = datetime.utcnow()
        
        # Update streak if it's a new day
        if not self.last_activity or self.last_activity.date() < now.date():
            self.streak_days += 1
            self.longest_streak = max(self.streak_days, self.longest_streak)
        # Break streak if more than a day has passed
        elif self.last_activity.date() < (now - timedelta(days=1)).date():
            self.streak_days = 1
        
        self.last_activity = now
        self.save()

    def update_daily_stats(self, key: str, value: int) -> None:
        """Update daily statistics."""
        today = datetime.utcnow().date().isoformat()
        if today not in self.daily_stats:
            self.daily_stats[today] = {}
        
        self.daily_stats[today][key] = self.daily_stats[today].get(key, 0) + value
        
        # Update averages
        days = len(self.daily_stats)
        if days > 0:
            if key == 'tasks':
                self.average_daily_tasks = sum(
                    day.get('tasks', 0) for day in self.daily_stats.values()
                ) / days
            elif key == 'time_logged':
                self.average_daily_time = sum(
                    day.get('time_logged', 0) for day in self.daily_stats.values()
                ) / days

    def update_weekly_stats(self, week: str, data: Dict) -> None:
        """Update weekly statistics."""
        self.weekly_stats[week] = {
            **self.weekly_stats.get(week, {}),
            **data
        }
        self.save()

    def update_monthly_stats(self, month: str, data: Dict) -> None:
        """Update monthly statistics."""
        self.monthly_stats[month] = {
            **self.monthly_stats.get(month, {}),
            **data
        }
        self.save()

    def update_yearly_stats(self, year: str, data: Dict) -> None:
        """Update yearly statistics."""
        self.yearly_stats[year] = {
            **self.yearly_stats.get(year, {}),
            **data
        }
        self.save()

    def update_tag_usage(self, tag: str) -> None:
        """Update tag usage statistics."""
        self.tags[tag] = self.tags.get(tag, 0) + 1
        self.save()

    def update_category_usage(self, category: str) -> None:
        """Update category usage statistics."""
        self.categories[category] = self.categories.get(category, 0) + 1
        self.save()

    def update_metadata(self, key: str, value: Any) -> None:
        """Update metadata statistics."""
        self.metadata[key] = value
        self.save()

    def calculate_productivity_score(self) -> None:
        """Calculate user productivity score."""
        # Base score on task completion rate and on-time rate
        base_score = (self.completion_rate + self.on_time_rate) / 2
        
        # Adjust based on activity level
        activity_multiplier = min(1.2, 0.8 + (self.streak_days * 0.02))
        
        # Calculate final score
        self.productivity_score = min(100, base_score * activity_multiplier)
        self.save()

    def calculate_engagement_score(self) -> None:
        """Calculate user engagement score."""
        # Base score on activity frequency
        daily_activity = len(self.daily_stats)
        activity_score = min(50, (daily_activity / 30) * 50)  # Max 50 points for activity
        
        # Add points for interactions
        interaction_score = min(
            50,
            (
                (self.total_comments * 2) +
                (self.total_attachments * 3) +
                (self.total_activities)
            ) / 100
        )  # Max 50 points for interactions
        
        # Calculate final score
        self.engagement_score = activity_score + interaction_score
        self.save()

    @classmethod
    def get_by_user(cls, user_id: int) -> Optional['UserStats']:
        """Get stats by user ID."""
        return cls.query.filter_by(user_id=user_id).first()

    @classmethod
    def create_default_stats(cls, user_id: int) -> 'UserStats':
        """Create default stats for a user."""
        stats = cls(user_id=user_id)
        stats.save()
        return stats

    def to_dict(self) -> dict:
        """Convert stats to dictionary."""
        data = super().to_dict()
        data['daily_stats'] = self.daily_stats
        data['weekly_stats'] = self.weekly_stats
        data['monthly_stats'] = self.monthly_stats
        data['yearly_stats'] = self.yearly_stats
        data['tags'] = self.tags
        data['categories'] = self.categories
        data['metadata'] = self.metadata
        return data 