"""UserProfile model class."""
from typing import Optional, Dict, Any, List
from flask_backend.models.base import BaseModel
from flask_backend.extensions import db

class UserProfile(BaseModel):
    """UserProfile model."""
    __tablename__ = 'user_profiles'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    display_name = db.Column(db.String(100))
    avatar_url = db.Column(db.String(512))
    bio = db.Column(db.Text)
    location = db.Column(db.String(100))
    website = db.Column(db.String(200))
    company = db.Column(db.String(100))
    job_title = db.Column(db.String(100))
    department = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    timezone = db.Column(db.String(50))
    language = db.Column(db.String(10))
    skills = db.Column(db.JSON)  # List of skills
    interests = db.Column(db.JSON)  # List of interests
    social_links = db.Column(db.JSON)  # Dictionary of social media links
    preferences = db.Column(db.JSON)  # Additional preferences
    metadata = db.Column(db.JSON)

    def __init__(self, **kwargs):
        """Initialize user profile model."""
        super().__init__(**kwargs)
        if not self.skills:
            self.skills = []
        if not self.interests:
            self.interests = []
        if not self.social_links:
            self.social_links = {}
        if not self.preferences:
            self.preferences = {}
        if not self.metadata:
            self.metadata = {}

    def update_basic_info(
        self,
        display_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        bio: Optional[str] = None,
        location: Optional[str] = None,
        website: Optional[str] = None
    ) -> None:
        """Update basic profile information."""
        if display_name is not None:
            self.display_name = display_name
        if avatar_url is not None:
            self.avatar_url = avatar_url
        if bio is not None:
            self.bio = bio
        if location is not None:
            self.location = location
        if website is not None:
            self.website = website
        self.save()

    def update_professional_info(
        self,
        company: Optional[str] = None,
        job_title: Optional[str] = None,
        department: Optional[str] = None,
        phone: Optional[str] = None
    ) -> None:
        """Update professional information."""
        if company is not None:
            self.company = company
        if job_title is not None:
            self.job_title = job_title
        if department is not None:
            self.department = department
        if phone is not None:
            self.phone = phone
        self.save()

    def update_preferences(
        self,
        timezone: Optional[str] = None,
        language: Optional[str] = None
    ) -> None:
        """Update user preferences."""
        if timezone is not None:
            self.timezone = timezone
        if language is not None:
            self.language = language
        self.save()

    def add_skill(self, skill: str) -> None:
        """Add a skill to the profile."""
        if skill not in self.skills:
            self.skills.append(skill)
            self.save()

    def remove_skill(self, skill: str) -> None:
        """Remove a skill from the profile."""
        if skill in self.skills:
            self.skills.remove(skill)
            self.save()

    def add_interest(self, interest: str) -> None:
        """Add an interest to the profile."""
        if interest not in self.interests:
            self.interests.append(interest)
            self.save()

    def remove_interest(self, interest: str) -> None:
        """Remove an interest from the profile."""
        if interest in self.interests:
            self.interests.remove(interest)
            self.save()

    def add_social_link(self, platform: str, url: str) -> None:
        """Add a social media link."""
        self.social_links[platform] = url
        self.save()

    def remove_social_link(self, platform: str) -> None:
        """Remove a social media link."""
        if platform in self.social_links:
            del self.social_links[platform]
            self.save()

    def update_preference(self, key: str, value: Any) -> None:
        """Update a preference."""
        self.preferences[key] = value
        self.save()

    def remove_preference(self, key: str) -> None:
        """Remove a preference."""
        if key in self.preferences:
            del self.preferences[key]
            self.save()

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to profile."""
        self.metadata[key] = value
        self.save()

    def remove_metadata(self, key: str) -> None:
        """Remove metadata from profile."""
        if key in self.metadata:
            del self.metadata[key]
            self.save()

    @classmethod
    def get_by_user(cls, user_id: int) -> Optional['UserProfile']:
        """Get profile by user ID."""
        return cls.query.filter_by(user_id=user_id).first()

    @classmethod
    def create_profile(cls, user_id: int, **kwargs) -> 'UserProfile':
        """Create a new user profile."""
        profile = cls(user_id=user_id, **kwargs)
        profile.save()
        return profile

    @classmethod
    def get_by_skill(cls, skill: str) -> List['UserProfile']:
        """Get profiles by skill."""
        return cls.query.filter(cls.skills.contains([skill])).all()

    @classmethod
    def get_by_interest(cls, interest: str) -> List['UserProfile']:
        """Get profiles by interest."""
        return cls.query.filter(cls.interests.contains([interest])).all()

    @classmethod
    def get_by_department(cls, department: str) -> List['UserProfile']:
        """Get profiles by department."""
        return cls.query.filter_by(department=department).all()

    @classmethod
    def get_by_company(cls, company: str) -> List['UserProfile']:
        """Get profiles by company."""
        return cls.query.filter_by(company=company).all()

    def to_dict(self) -> dict:
        """Convert profile to dictionary."""
        data = super().to_dict()
        data['skills'] = self.skills
        data['interests'] = self.interests
        data['social_links'] = self.social_links
        data['preferences'] = self.preferences
        data['metadata'] = self.metadata
        return data 