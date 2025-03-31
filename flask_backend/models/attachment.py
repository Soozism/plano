"""Attachment model class."""
from typing import List, Optional
from flask_backend.models.base import BaseModel
from flask_backend.extensions import db
from flask_backend.utils.helpers import delete_from_s3

class Attachment(BaseModel):
    """Attachment model."""
    __tablename__ = 'attachments'

    filename = db.Column(db.String(255), nullable=False)
    file_url = db.Column(db.String(512), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    description = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=False)
    download_count = db.Column(db.Integer, default=0)
    last_downloaded = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        """Initialize attachment model."""
        super().__init__(**kwargs)

    def delete(self) -> None:
        """Delete attachment and file."""
        # Delete file from S3
        key = self.file_url.split('/')[-1]
        delete_from_s3(key)
        
        # Delete database record
        super().delete()

    def increment_download_count(self) -> None:
        """Increment download count."""
        self.download_count += 1
        self.last_downloaded = get_current_time()
        self.save()

    @property
    def file_extension(self) -> str:
        """Get file extension."""
        return self.filename.split('.')[-1].lower()

    @property
    def is_image(self) -> bool:
        """Check if file is an image."""
        return self.file_type.startswith('image/')

    @property
    def is_document(self) -> bool:
        """Check if file is a document."""
        return self.file_type in [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/plain'
        ]

    @property
    def is_video(self) -> bool:
        """Check if file is a video."""
        return self.file_type.startswith('video/')

    @property
    def is_audio(self) -> bool:
        """Check if file is an audio file."""
        return self.file_type.startswith('audio/')

    @property
    def file_size_formatted(self) -> str:
        """Get formatted file size."""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size / (1024 * 1024 * 1024):.1f} GB"

    @classmethod
    def get_by_task(cls, task_id: int) -> List['Attachment']:
        """Get attachments by task."""
        return cls.query.filter_by(task_id=task_id).all()

    @classmethod
    def get_by_user(cls, user_id: int) -> List['Attachment']:
        """Get attachments by user."""
        return cls.query.filter_by(user_id=user_id).all()

    @classmethod
    def get_by_type(cls, file_type: str) -> List['Attachment']:
        """Get attachments by file type."""
        return cls.query.filter_by(file_type=file_type).all()

    @classmethod
    def get_public_attachments(cls) -> List['Attachment']:
        """Get public attachments."""
        return cls.query.filter_by(is_public=True).all()

    @classmethod
    def get_private_attachments(cls) -> List['Attachment']:
        """Get private attachments."""
        return cls.query.filter_by(is_public=False).all()

    @classmethod
    def get_recent_attachments(cls, limit: int = 10) -> List['Attachment']:
        """Get recent attachments."""
        return cls.query.order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_most_downloaded(cls, limit: int = 10) -> List['Attachment']:
        """Get most downloaded attachments."""
        return cls.query.order_by(cls.download_count.desc()).limit(limit).all()

    def to_dict(self) -> dict:
        """Convert attachment to dictionary."""
        data = super().to_dict()
        data['file_size_formatted'] = self.file_size_formatted
        data['file_extension'] = self.file_extension
        data['is_image'] = self.is_image
        data['is_document'] = self.is_document
        data['is_video'] = self.is_video
        data['is_audio'] = self.is_audio
        return data 