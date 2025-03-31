"""UserSettings model class."""
from typing import Optional, Dict, Any
from flask_backend.models.base import BaseModel
from flask_backend.extensions import db

class UserSettings(BaseModel):
    """UserSettings model."""
    __tablename__ = 'user_settings'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    theme = db.Column(db.String(20), default='light')  # light, dark, system
    layout = db.Column(db.String(20), default='default')  # default, compact, spacious
    font_size = db.Column(db.String(20), default='medium')  # small, medium, large
    font_family = db.Column(db.String(50), default='system')
    color_scheme = db.Column(db.String(50), default='default')
    show_animations = db.Column(db.Boolean, default=True)
    reduce_motion = db.Column(db.Boolean, default=False)
    high_contrast = db.Column(db.Boolean, default=False)
    keyboard_shortcuts = db.Column(db.Boolean, default=True)
    notifications_enabled = db.Column(db.Boolean, default=True)
    email_notifications = db.Column(db.Boolean, default=True)
    push_notifications = db.Column(db.Boolean, default=True)
    sound_enabled = db.Column(db.Boolean, default=True)
    vibration_enabled = db.Column(db.Boolean, default=True)
    auto_save = db.Column(db.Boolean, default=True)
    auto_save_interval = db.Column(db.Integer, default=300)  # seconds
    language = db.Column(db.String(10), default='en')
    timezone = db.Column(db.String(50), default='UTC')
    date_format = db.Column(db.String(20), default='YYYY-MM-DD')
    time_format = db.Column(db.String(20), default='24h')
    first_day_of_week = db.Column(db.Integer, default=0)  # 0 = Sunday, 1 = Monday
    week_starts_on = db.Column(db.String(10), default='sunday')
    show_week_numbers = db.Column(db.Boolean, default=False)
    show_today_indicator = db.Column(db.Boolean, default=True)
    show_weekend = db.Column(db.Boolean, default=True)
    default_view = db.Column(db.String(20), default='list')  # list, board, calendar
    items_per_page = db.Column(db.Integer, default=10)
    sort_by = db.Column(db.String(50), default='created_at')
    sort_order = db.Column(db.String(10), default='desc')
    group_by = db.Column(db.String(50))
    filter_by = db.Column(db.JSON)
    columns = db.Column(db.JSON)  # List of visible columns
    custom_settings = db.Column(db.JSON)

    def __init__(self, **kwargs):
        """Initialize user settings model."""
        super().__init__(**kwargs)
        if not self.filter_by:
            self.filter_by = {}
        if not self.columns:
            self.columns = []
        if not self.custom_settings:
            self.custom_settings = {}

    def update_theme_settings(
        self,
        theme: Optional[str] = None,
        layout: Optional[str] = None,
        font_size: Optional[str] = None,
        font_family: Optional[str] = None,
        color_scheme: Optional[str] = None,
        show_animations: Optional[bool] = None,
        reduce_motion: Optional[bool] = None,
        high_contrast: Optional[bool] = None
    ) -> None:
        """Update theme-related settings."""
        if theme is not None:
            self.theme = theme
        if layout is not None:
            self.layout = layout
        if font_size is not None:
            self.font_size = font_size
        if font_family is not None:
            self.font_family = font_family
        if color_scheme is not None:
            self.color_scheme = color_scheme
        if show_animations is not None:
            self.show_animations = show_animations
        if reduce_motion is not None:
            self.reduce_motion = reduce_motion
        if high_contrast is not None:
            self.high_contrast = high_contrast
        self.save()

    def update_notification_settings(
        self,
        notifications_enabled: Optional[bool] = None,
        email_notifications: Optional[bool] = None,
        push_notifications: Optional[bool] = None,
        sound_enabled: Optional[bool] = None,
        vibration_enabled: Optional[bool] = None
    ) -> None:
        """Update notification settings."""
        if notifications_enabled is not None:
            self.notifications_enabled = notifications_enabled
        if email_notifications is not None:
            self.email_notifications = email_notifications
        if push_notifications is not None:
            self.push_notifications = push_notifications
        if sound_enabled is not None:
            self.sound_enabled = sound_enabled
        if vibration_enabled is not None:
            self.vibration_enabled = vibration_enabled
        self.save()

    def update_display_settings(
        self,
        language: Optional[str] = None,
        timezone: Optional[str] = None,
        date_format: Optional[str] = None,
        time_format: Optional[str] = None,
        first_day_of_week: Optional[int] = None,
        week_starts_on: Optional[str] = None,
        show_week_numbers: Optional[bool] = None,
        show_today_indicator: Optional[bool] = None,
        show_weekend: Optional[bool] = None
    ) -> None:
        """Update display settings."""
        if language is not None:
            self.language = language
        if timezone is not None:
            self.timezone = timezone
        if date_format is not None:
            self.date_format = date_format
        if time_format is not None:
            self.time_format = time_format
        if first_day_of_week is not None:
            self.first_day_of_week = first_day_of_week
        if week_starts_on is not None:
            self.week_starts_on = week_starts_on
        if show_week_numbers is not None:
            self.show_week_numbers = show_week_numbers
        if show_today_indicator is not None:
            self.show_today_indicator = show_today_indicator
        if show_weekend is not None:
            self.show_weekend = show_weekend
        self.save()

    def update_list_settings(
        self,
        default_view: Optional[str] = None,
        items_per_page: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        group_by: Optional[str] = None,
        filter_by: Optional[Dict] = None,
        columns: Optional[List[str]] = None
    ) -> None:
        """Update list view settings."""
        if default_view is not None:
            self.default_view = default_view
        if items_per_page is not None:
            self.items_per_page = items_per_page
        if sort_by is not None:
            self.sort_by = sort_by
        if sort_order is not None:
            self.sort_order = sort_order
        if group_by is not None:
            self.group_by = group_by
        if filter_by is not None:
            self.filter_by = filter_by
        if columns is not None:
            self.columns = columns
        self.save()

    def update_auto_save_settings(
        self,
        auto_save: Optional[bool] = None,
        auto_save_interval: Optional[int] = None
    ) -> None:
        """Update auto-save settings."""
        if auto_save is not None:
            self.auto_save = auto_save
        if auto_save_interval is not None:
            self.auto_save_interval = auto_save_interval
        self.save()

    def add_filter(self, key: str, value: Any) -> None:
        """Add a filter."""
        self.filter_by[key] = value
        self.save()

    def remove_filter(self, key: str) -> None:
        """Remove a filter."""
        if key in self.filter_by:
            del self.filter_by[key]
            self.save()

    def add_column(self, column: str) -> None:
        """Add a visible column."""
        if column not in self.columns:
            self.columns.append(column)
            self.save()

    def remove_column(self, column: str) -> None:
        """Remove a visible column."""
        if column in self.columns:
            self.columns.remove(column)
            self.save()

    def update_custom_setting(self, key: str, value: Any) -> None:
        """Update a custom setting."""
        self.custom_settings[key] = value
        self.save()

    def remove_custom_setting(self, key: str) -> None:
        """Remove a custom setting."""
        if key in self.custom_settings:
            del self.custom_settings[key]
            self.save()

    @classmethod
    def get_by_user(cls, user_id: int) -> Optional['UserSettings']:
        """Get settings by user ID."""
        return cls.query.filter_by(user_id=user_id).first()

    @classmethod
    def create_default_settings(cls, user_id: int) -> 'UserSettings':
        """Create default settings for a user."""
        settings = cls(user_id=user_id)
        settings.save()
        return settings

    def to_dict(self) -> dict:
        """Convert settings to dictionary."""
        data = super().to_dict()
        data['filter_by'] = self.filter_by
        data['columns'] = self.columns
        data['custom_settings'] = self.custom_settings
        return data 