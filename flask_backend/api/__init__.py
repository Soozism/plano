# This file is intentionally left empty to make the directory a Python package

from .auth import auth_bp
from .users import users_bp
from .tasks import tasks_bp
from .messages import messages_bp
from .attachments import attachments_bp

def register_blueprints(app):
    """Register all blueprints with the Flask app."""
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(messages_bp, url_prefix='/api')
    app.register_blueprint(attachments_bp, url_prefix='/api')