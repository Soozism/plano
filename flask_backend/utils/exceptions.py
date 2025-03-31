"""Custom exceptions for the application."""
from typing import Any, Dict, List, Optional

class APIException(Exception):
    """Base API exception."""
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        payload: Optional[Dict[str, Any]] = None
    ):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['code'] = self.status_code
        return rv

class ValidationError(APIException):
    """Validation error exception."""
    def __init__(
        self,
        message: str = 'Validation error',
        errors: Optional[List[Dict[str, str]]] = None
    ):
        super().__init__(
            message=message,
            status_code=422,
            payload={'errors': errors} if errors else None
        )

class AuthenticationError(APIException):
    """Authentication error exception."""
    def __init__(self, message: str = 'Authentication failed'):
        super().__init__(
            message=message,
            status_code=401
        )

class AuthorizationError(APIException):
    """Authorization error exception."""
    def __init__(self, message: str = 'Not authorized'):
        super().__init__(
            message=message,
            status_code=403
        )

class ResourceNotFound(APIException):
    """Resource not found exception."""
    def __init__(self, message: str = 'Resource not found'):
        super().__init__(
            message=message,
            status_code=404
        )

class ResourceConflict(APIException):
    """Resource conflict exception."""
    def __init__(self, message: str = 'Resource already exists'):
        super().__init__(
            message=message,
            status_code=409
        )

class RateLimitExceeded(APIException):
    """Rate limit exceeded exception."""
    def __init__(self, message: str = 'Rate limit exceeded'):
        super().__init__(
            message=message,
            status_code=429
        )

class FileUploadError(APIException):
    """File upload error exception."""
    def __init__(
        self,
        message: str = 'File upload failed',
        errors: Optional[List[Dict[str, str]]] = None
    ):
        super().__init__(
            message=message,
            status_code=400,
            payload={'errors': errors} if errors else None
        )

class DatabaseError(APIException):
    """Database error exception."""
    def __init__(self, message: str = 'Database error occurred'):
        super().__init__(
            message=message,
            status_code=500
        )

class ExternalServiceError(APIException):
    """External service error exception."""
    def __init__(
        self,
        message: str = 'External service error',
        service: Optional[str] = None
    ):
        super().__init__(
            message=message,
            status_code=503,
            payload={'service': service} if service else None
        )

class WebSocketError(APIException):
    """WebSocket error exception."""
    def __init__(self, message: str = 'WebSocket error occurred'):
        super().__init__(
            message=message,
            status_code=500
        )

class CacheError(APIException):
    """Cache error exception."""
    def __init__(self, message: str = 'Cache error occurred'):
        super().__init__(
            message=message,
            status_code=500
        )

class EmailError(APIException):
    """Email error exception."""
    def __init__(self, message: str = 'Email sending failed'):
        super().__init__(
            message=message,
            status_code=500
        )

class AuditLogError(APIException):
    """Audit log error exception."""
    def __init__(self, message: str = 'Audit logging failed'):
        super().__init__(
            message=message,
            status_code=500
        )

class MetricError(APIException):
    """Metric error exception."""
    def __init__(self, message: str = 'Metric recording failed'):
        super().__init__(
            message=message,
            status_code=500
        )

def handle_api_exception(error: APIException) -> tuple[Dict[str, Any], int]:
    """Handle API exceptions."""
    response = error.to_dict()
    return response, error.status_code

def handle_validation_error(error: ValidationError) -> tuple[Dict[str, Any], int]:
    """Handle validation errors."""
    response = error.to_dict()
    return response, error.status_code

def handle_database_error(error: DatabaseError) -> tuple[Dict[str, Any], int]:
    """Handle database errors."""
    response = error.to_dict()
    return response, error.status_code

def handle_external_service_error(error: ExternalServiceError) -> tuple[Dict[str, Any], int]:
    """Handle external service errors."""
    response = error.to_dict()
    return response, error.status_code 