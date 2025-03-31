# This file is intentionally left empty to make the directory a Python package

"""Flask application factory."""
import os
from flask import Flask
from flask_backend.config import config
from flask_backend.extensions import init_extensions
from flask_backend.api import register_blueprints

def create_app(config_name='default'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register CLI commands
    register_commands(app)
    
    return app

def register_error_handlers(app):
    """Register error handlers."""
    from flask import jsonify
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': str(error),
            'code': 400
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': str(error),
            'code': 401
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'Forbidden',
            'message': str(error),
            'code': 403
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': str(error),
            'code': 404
        }), 404
    
    @app.errorhandler(429)
    def too_many_requests(error):
        return jsonify({
            'error': 'Too Many Requests',
            'message': str(error),
            'code': 429
        }), 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(error),
            'code': 500
        }), 500

def register_commands(app):
    """Register CLI commands."""
    @app.cli.command()
    def test():
        """Run the unit tests."""
        import pytest
        pytest.main(['tests'])
    
    @app.cli.command()
    def init_db():
        """Initialize the database."""
        from flask_backend.extensions import db
        db.create_all()
    
    @app.cli.command()
    def create_admin():
        """Create an admin user."""
        from flask_backend.models.user import User
        from flask_backend.extensions import db, bcrypt
        
        username = input('Enter admin username: ')
        email = input('Enter admin email: ')
        password = input('Enter admin password: ')
        
        user = User(
            username=username,
            email=email,
            password=bcrypt.generate_password_hash(password).decode('utf-8'),
            role='OWNER'
        )
        
        db.session.add(user)
        db.session.commit()
        
        print('Admin user created successfully!')