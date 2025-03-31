from flask import Flask, jsonify
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from .config import config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()

def create_app(config_name='default'):
    """
    Application factory function to create and configure the Flask app
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    
    # Enable CORS
    CORS(app, supports_credentials=True)
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def server_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    # Register blueprints
    from .api.auth import auth_bp
    from .api.users import users_bp
    from .api.organizations import organizations_bp
    from .api.groups import groups_bp
    from .api.tasks import tasks_bp
    from .api.events import events_bp
    from .api.sprints import sprints_bp
    from .api.time_tracking import time_tracking_bp
    from .api.scrum import scrum_bp
    
    # Register blueprints with URL prefixes
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(organizations_bp, url_prefix='/api/organizations')
    app.register_blueprint(groups_bp, url_prefix='/api/groups')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(events_bp, url_prefix='/api/events')
    app.register_blueprint(sprints_bp, url_prefix='/api/sprints')
    app.register_blueprint(time_tracking_bp, url_prefix='/api/time-tracking')
    app.register_blueprint(scrum_bp, url_prefix='/api/scrum')
    
    # Create a simple route for testing
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'status': 'ok',
            'message': 'Flask API is running',
            'version': '1.0.0'
        })
    
    return app