"""Utility helper functions for the application."""
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from flask import current_app
from werkzeug.utils import secure_filename
from flask_backend.extensions import s3_client

def get_current_time() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)

def format_datetime(dt: datetime) -> str:
    """Format datetime to ISO format."""
    return dt.isoformat() if dt else None

def parse_datetime(dt_str: str) -> Optional[datetime]:
    """Parse datetime from ISO format."""
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return None

def generate_filename(original_filename: str) -> str:
    """Generate a secure filename with timestamp."""
    filename = secure_filename(original_filename)
    name, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{name}_{timestamp}{ext}"

def upload_to_s3(file_obj: Any, folder: str) -> Optional[str]:
    """Upload file to S3 bucket."""
    try:
        filename = generate_filename(file_obj.filename)
        key = f"{folder}/{filename}"
        
        s3_client.upload_fileobj(
            file_obj,
            current_app.config['AWS_BUCKET_NAME'],
            key,
            ExtraArgs={
                'ACL': 'public-read',
                'ContentType': file_obj.content_type
            }
        )
        
        return f"https://{current_app.config['AWS_BUCKET_NAME']}.s3.amazonaws.com/{key}"
    except Exception as e:
        current_app.logger.error(f"Error uploading to S3: {str(e)}")
        return None

def delete_from_s3(key: str) -> bool:
    """Delete file from S3 bucket."""
    try:
        s3_client.delete_object(
            Bucket=current_app.config['AWS_BUCKET_NAME'],
            Key=key
        )
        return True
    except Exception as e:
        current_app.logger.error(f"Error deleting from S3: {str(e)}")
        return False

def paginate_query(query: Any, page: int, per_page: int) -> Dict[str, Any]:
    """Paginate a SQLAlchemy query."""
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return {
        'items': pagination.items,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    }

def format_pagination_response(
    items: List[Any],
    total: int,
    pages: int,
    current_page: int,
    has_next: bool,
    has_prev: bool
) -> Dict[str, Any]:
    """Format pagination response."""
    return {
        'data': items,
        'meta': {
            'total': total,
            'pages': pages,
            'current_page': current_page,
            'has_next': has_next,
            'has_prev': has_prev
        }
    }

def get_client_ip() -> str:
    """Get client IP address from request."""
    if 'X-Forwarded-For' in request.headers:
        return request.headers['X-Forwarded-For'].split(',')[0]
    return request.remote_addr

def sanitize_input(data: Union[str, Dict, List]) -> Union[str, Dict, List]:
    """Sanitize input data to prevent XSS."""
    if isinstance(data, str):
        return bleach.clean(data)
    elif isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    return data

def generate_password_hash(password: str) -> str:
    """Generate password hash using bcrypt."""
    from flask_backend.extensions import bcrypt
    return bcrypt.generate_password_hash(password).decode('utf-8')

def check_password_hash(password: str, password_hash: str) -> bool:
    """Check password against hash using bcrypt."""
    from flask_backend.extensions import bcrypt
    return bcrypt.check_password_hash(password_hash, password)

def generate_token(user_id: int) -> str:
    """Generate JWT token."""
    from flask_jwt_extended import create_access_token
    return create_access_token(identity=user_id)

def get_user_from_token() -> Optional[User]:
    """Get user from JWT token."""
    from flask_jwt_extended import get_jwt_identity
    from flask_backend.models.user import User
    
    user_id = get_jwt_identity()
    return User.query.get(user_id) if user_id else None 