"""Base model class for database models."""
from datetime import datetime
from typing import Any, Dict, Optional, List
from flask_backend.extensions import db
from flask_backend.utils.helpers import get_current_time

class BaseModel(db.Model):
    """Base model class with common fields and methods."""
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=get_current_time)
    updated_at = db.Column(db.DateTime, default=get_current_time, onupdate=get_current_time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Update model from dictionary."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @classmethod
    def create(cls, **kwargs: Any) -> 'BaseModel':
        """Create a new model instance."""
        instance = cls(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance

    def update(self, **kwargs: Any) -> None:
        """Update model instance."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()

    def delete(self) -> None:
        """Delete model instance."""
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def get_by_id(cls, id: int) -> Optional['BaseModel']:
        """Get model instance by ID."""
        return cls.query.get(id)

    @classmethod
    def get_all(cls) -> List['BaseModel']:
        """Get all model instances."""
        return cls.query.all()

    @classmethod
    def get_by_field(cls, field: str, value: Any) -> Optional['BaseModel']:
        """Get model instance by field value."""
        return cls.query.filter_by(**{field: value}).first()

    @classmethod
    def get_by_fields(cls, **kwargs: Any) -> List['BaseModel']:
        """Get model instances by field values."""
        return cls.query.filter_by(**kwargs).all()

    @classmethod
    def count(cls) -> int:
        """Get total count of model instances."""
        return cls.query.count()

    @classmethod
    def exists(cls, **kwargs: Any) -> bool:
        """Check if model instance exists."""
        return cls.query.filter_by(**kwargs).first() is not None

    def save(self) -> None:
        """Save model instance."""
        db.session.add(self)
        db.session.commit()

    def refresh(self) -> None:
        """Refresh model instance from database."""
        db.session.refresh(self)

    @property
    def created_at_iso(self) -> str:
        """Get ISO format of created_at."""
        return self.created_at.isoformat() if self.created_at else None

    @property
    def updated_at_iso(self) -> str:
        """Get ISO format of updated_at."""
        return self.updated_at.isoformat() if self.updated_at else None

    def __repr__(self) -> str:
        """String representation of model."""
        return f'<{self.__class__.__name__} {self.id}>' 