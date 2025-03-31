"""Utility decorators for the application."""
from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from flask_backend.extensions import db
from flask_backend.models.user import User

def admin_required():
    """Decorator to require admin role."""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user or user.role != 'OWNER':
                return jsonify({
                    'error': 'Forbidden',
                    'message': 'Admin privileges required',
                    'code': 403
                }), 403
                
            return fn(*args, **kwargs)
        return decorator
    return wrapper

def manager_required():
    """Decorator to require manager role."""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user or user.role not in ['OWNER', 'MANAGER']:
                return jsonify({
                    'error': 'Forbidden',
                    'message': 'Manager privileges required',
                    'code': 403
                }), 403
                
            return fn(*args, **kwargs)
        return decorator
    return wrapper

def validate_json(schema):
    """Decorator to validate JSON request body against a schema."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'error': 'Bad Request',
                    'message': 'Content-Type must be application/json',
                    'code': 400
                }), 400
                
            data = request.get_json()
            errors = schema.validate(data)
            
            if errors:
                return jsonify({
                    'error': 'Bad Request',
                    'message': 'Validation error',
                    'errors': errors,
                    'code': 400
                }), 400
                
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def handle_db_errors(fn):
    """Decorator to handle database errors."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'error': 'Internal Server Error',
                'message': str(e),
                'code': 500
            }), 500
    return wrapper

def cache_response(timeout=300):
    """Decorator to cache response data."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from flask_backend.extensions import redis_client
            
            # Generate cache key from function name and arguments
            cache_key = f"{fn.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get cached response
            cached_response = redis_client.get(cache_key)
            if cached_response:
                return jsonify(cached_response)
            
            # Get fresh response
            response = fn(*args, **kwargs)
            
            # Cache the response
            redis_client.setex(cache_key, timeout, response)
            
            return response
        return wrapper
    return decorator

def rate_limit(limit=100, period=60):
    """Decorator to rate limit endpoints."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from flask_backend.extensions import limiter
            
            @limiter.limit(f"{limit}/{period}seconds")
            def rate_limited(*args, **kwargs):
                return fn(*args, **kwargs)
                
            return rate_limited(*args, **kwargs)
        return wrapper
    return decorator 