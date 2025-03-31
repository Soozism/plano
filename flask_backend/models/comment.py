"""Comment model class."""
from typing import List, Optional
from flask_backend.models.base import BaseModel
from flask_backend.extensions import db

class Comment(BaseModel):
    """Comment model."""
    __tablename__ = 'comments'

    content = db.Column(db.Text, nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
    is_edited = db.Column(db.Boolean, default=False)
    edited_at = db.Column(db.DateTime)
    edited_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime)
    resolved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Relationships
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    edited_by = db.relationship('User', foreign_keys=[edited_by_id], backref='edited_comments')
    resolved_by = db.relationship('User', foreign_keys=[resolved_by_id], backref='resolved_comments')

    def __init__(self, **kwargs):
        """Initialize comment model."""
        super().__init__(**kwargs)

    def edit(self, user_id: int, content: str) -> None:
        """Edit comment content."""
        self.content = content
        self.is_edited = True
        self.edited_at = get_current_time()
        self.edited_by_id = user_id
        self.save()

    def resolve(self, user_id: int) -> None:
        """Mark comment as resolved."""
        self.is_resolved = True
        self.resolved_at = get_current_time()
        self.resolved_by_id = user_id
        self.save()

    def unresolve(self) -> None:
        """Mark comment as unresolved."""
        self.is_resolved = False
        self.resolved_at = None
        self.resolved_by_id = None
        self.save()

    def add_reply(self, user_id: int, content: str) -> 'Comment':
        """Add reply to comment."""
        reply = Comment(
            content=content,
            task_id=self.task_id,
            user_id=user_id,
            parent_id=self.id
        )
        reply.save()
        return reply

    @property
    def replies_count(self) -> int:
        """Get number of replies."""
        return self.replies.count()

    @property
    def is_reply(self) -> bool:
        """Check if comment is a reply."""
        return self.parent_id is not None

    @property
    def is_thread(self) -> bool:
        """Check if comment is a thread."""
        return self.parent_id is None

    @classmethod
    def get_by_task(cls, task_id: int) -> List['Comment']:
        """Get comments by task."""
        return cls.query.filter_by(
            task_id=task_id,
            parent_id=None
        ).order_by(cls.created_at).all()

    @classmethod
    def get_by_user(cls, user_id: int) -> List['Comment']:
        """Get comments by user."""
        return cls.query.filter_by(user_id=user_id).all()

    @classmethod
    def get_resolved_comments(cls) -> List['Comment']:
        """Get resolved comments."""
        return cls.query.filter_by(is_resolved=True).all()

    @classmethod
    def get_unresolved_comments(cls) -> List['Comment']:
        """Get unresolved comments."""
        return cls.query.filter_by(is_resolved=False).all()

    @classmethod
    def get_edited_comments(cls) -> List['Comment']:
        """Get edited comments."""
        return cls.query.filter_by(is_edited=True).all()

    @classmethod
    def get_recent_comments(cls, limit: int = 10) -> List['Comment']:
        """Get recent comments."""
        return cls.query.order_by(cls.created_at.desc()).limit(limit).all()

    def to_dict(self) -> dict:
        """Convert comment to dictionary."""
        data = super().to_dict()
        data['replies'] = [
            reply.to_dict()
            for reply in self.replies.order_by(Comment.created_at).all()
        ]
        return data 