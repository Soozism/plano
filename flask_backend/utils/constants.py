"""Constants and enums for the application."""
from enum import Enum
from typing import Dict, List

class UserRole(str, Enum):
    """User role enumeration."""
    OWNER = 'OWNER'
    MANAGER = 'MANAGER'
    MEMBER = 'MEMBER'

class TaskStatus(str, Enum):
    """Task status enumeration."""
    TODO = 'TODO'
    IN_PROGRESS = 'IN_PROGRESS'
    DONE = 'DONE'

class TaskPriority(str, Enum):
    """Task priority enumeration."""
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'

class SprintStatus(str, Enum):
    """Sprint status enumeration."""
    PLANNING = 'PLANNING'
    ACTIVE = 'ACTIVE'
    COMPLETED = 'COMPLETED'

class NotificationType(str, Enum):
    """Notification type enumeration."""
    INFO = 'INFO'
    SUCCESS = 'SUCCESS'
    WARNING = 'WARNING'
    ERROR = 'ERROR'

# API Response Status Codes
class StatusCode:
    """API response status codes."""
    SUCCESS = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503

# API Response Messages
class ResponseMessage:
    """API response messages."""
    SUCCESS = 'Success'
    CREATED = 'Resource created successfully'
    UPDATED = 'Resource updated successfully'
    DELETED = 'Resource deleted successfully'
    NOT_FOUND = 'Resource not found'
    UNAUTHORIZED = 'Unauthorized access'
    FORBIDDEN = 'Access forbidden'
    BAD_REQUEST = 'Bad request'
    VALIDATION_ERROR = 'Validation error'
    INTERNAL_ERROR = 'Internal server error'
    RATE_LIMIT_EXCEEDED = 'Rate limit exceeded'

# File Upload Settings
class FileUpload:
    """File upload settings."""
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {
        'image': ['jpg', 'jpeg', 'png', 'gif'],
        'document': ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'],
        'video': ['mp4', 'avi', 'mov'],
        'audio': ['mp3', 'wav', 'ogg']
    }
    MAX_FILES_PER_TASK = 10

# Pagination Settings
class Pagination:
    """Pagination settings."""
    DEFAULT_PAGE = 1
    DEFAULT_PER_PAGE = 20
    MAX_PER_PAGE = 100

# Cache Settings
class Cache:
    """Cache settings."""
    DEFAULT_TIMEOUT = 300  # 5 minutes
    USER_TIMEOUT = 3600  # 1 hour
    TASK_TIMEOUT = 1800  # 30 minutes
    SPRINT_TIMEOUT = 3600  # 1 hour

# Rate Limiting Settings
class RateLimit:
    """Rate limiting settings."""
    DEFAULT_LIMIT = 100
    DEFAULT_PERIOD = 60  # seconds
    LOGIN_LIMIT = 5
    LOGIN_PERIOD = 300  # 5 minutes

# WebSocket Events
class WebSocketEvent:
    """WebSocket event names."""
    TASK_CREATED = 'task_created'
    TASK_UPDATED = 'task_updated'
    TASK_DELETED = 'task_deleted'
    COMMENT_CREATED = 'comment_created'
    COMMENT_UPDATED = 'comment_updated'
    COMMENT_DELETED = 'comment_deleted'
    NOTIFICATION_CREATED = 'notification_created'
    ATTACHMENT_UPLOADED = 'attachment_uploaded'
    ATTACHMENT_DELETED = 'attachment_deleted'

# Audit Log Actions
class AuditAction:
    """Audit log action types."""
    CREATE = 'create'
    UPDATE = 'update'
    DELETE = 'delete'
    LOGIN = 'login'
    LOGOUT = 'logout'
    PASSWORD_CHANGE = 'password_change'
    ROLE_CHANGE = 'role_change'
    FILE_UPLOAD = 'file_upload'
    FILE_DELETE = 'file_delete'

# Metric Names
class MetricName:
    """Metric names for monitoring."""
    REQUEST_COUNT = 'http_requests_total'
    REQUEST_LATENCY = 'http_request_duration_seconds'
    ERROR_COUNT = 'http_errors_total'
    ACTIVE_USERS = 'active_users'
    TASK_COUNT = 'task_count'
    SPRINT_COUNT = 'sprint_count'
    COMMENT_COUNT = 'comment_count'
    FILE_UPLOAD_COUNT = 'file_upload_count'

# API Endpoints
class Endpoint:
    """API endpoint paths."""
    AUTH = {
        'LOGIN': '/auth/login',
        'REGISTER': '/auth/register',
        'LOGOUT': '/auth/logout',
        'REFRESH': '/auth/refresh',
        'ME': '/auth/me'
    }
    USERS = {
        'LIST': '/users',
        'DETAIL': '/users/<int:user_id>',
        'UPDATE': '/users/<int:user_id>',
        'DELETE': '/users/<int:user_id>'
    }
    TASKS = {
        'LIST': '/tasks',
        'CREATE': '/tasks',
        'DETAIL': '/tasks/<int:task_id>',
        'UPDATE': '/tasks/<int:task_id>',
        'DELETE': '/tasks/<int:task_id>',
        'COMMENTS': '/tasks/<int:task_id>/comments',
        'ATTACHMENTS': '/tasks/<int:task_id>/attachments'
    }
    SPRINTS = {
        'LIST': '/sprints',
        'CREATE': '/sprints',
        'DETAIL': '/sprints/<int:sprint_id>',
        'UPDATE': '/sprints/<int:sprint_id>',
        'DELETE': '/sprints/<int:sprint_id>',
        'BURNDOWN': '/sprints/<int:sprint_id>/burndown'
    }
    NOTIFICATIONS = {
        'LIST': '/notifications',
        'DETAIL': '/notifications/<int:notification_id>',
        'UPDATE': '/notifications/<int:notification_id>',
        'DELETE': '/notifications/<int:notification_id>'
    }
    ANALYTICS = {
        'TASKS': '/analytics/tasks',
        'SPRINTS': '/analytics/sprints',
        'USERS': '/analytics/users'
    }
    AUDIT = {
        'LOGS': '/audit/logs'
    }

# Database Models
class ModelName:
    """Database model names."""
    USER = 'User'
    TASK = 'Task'
    SPRINT = 'Sprint'
    COMMENT = 'Comment'
    ATTACHMENT = 'Attachment'
    NOTIFICATION = 'Notification'
    AUDIT_LOG = 'AuditLog'

# Error Messages
class ErrorMessage:
    """Error messages."""
    VALIDATION = {
        'REQUIRED': 'This field is required',
        'INVALID_EMAIL': 'Invalid email address',
        'INVALID_PASSWORD': 'Password must be at least 8 characters long',
        'PASSWORDS_MISMATCH': 'Passwords do not match',
        'INVALID_ROLE': 'Invalid role',
        'INVALID_STATUS': 'Invalid status',
        'INVALID_PRIORITY': 'Invalid priority',
        'INVALID_DATE': 'Invalid date format',
        'END_DATE_BEFORE_START': 'End date must be after start date',
        'FILE_TOO_LARGE': 'File size exceeds maximum limit',
        'INVALID_FILE_TYPE': 'Invalid file type',
        'MAX_FILES_EXCEEDED': 'Maximum number of files exceeded'
    }
    AUTH = {
        'INVALID_CREDENTIALS': 'Invalid email or password',
        'TOKEN_EXPIRED': 'Token has expired',
        'INVALID_TOKEN': 'Invalid token',
        'UNAUTHORIZED': 'Unauthorized access',
        'FORBIDDEN': 'Access forbidden'
    }
    NOT_FOUND = {
        'USER': 'User not found',
        'TASK': 'Task not found',
        'SPRINT': 'Sprint not found',
        'COMMENT': 'Comment not found',
        'ATTACHMENT': 'Attachment not found',
        'NOTIFICATION': 'Notification not found'
    }
    CONFLICT = {
        'USER_EXISTS': 'User already exists',
        'EMAIL_EXISTS': 'Email already registered',
        'TASK_EXISTS': 'Task already exists',
        'SPRINT_EXISTS': 'Sprint already exists'
    } 