"""Flask extensions initialization."""
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_swagger_ui import get_swaggerui_blueprint
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
cors = CORS()
socketio = SocketIO()
bcrypt = Bcrypt()
limiter = Limiter(key_func=get_remote_address)

def init_extensions(app):
    """Initialize Flask extensions."""
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Initialize JWT
    jwt.init_app(app)
    
    # Initialize Flask-Migrate
    migrate.init_app(app, db)
    
    # Initialize CORS
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": app.config['CORS_ORIGINS'],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Initialize SocketIO
    socketio.init_app(app, cors_allowed_origins=app.config['CORS_ORIGINS'])
    
    # Initialize Swagger UI
    swaggerui_blueprint = get_swaggerui_blueprint(
        '/api/docs',
        '/static/swagger.json',
        config={
            'app_name': "Productivity Planner API",
            'docExpansion': 'none',
            'defaultModelsExpandDepth': -1,
            'displayRequestDuration': True,
            'filter': True,
            'showCommonExtensions': True,
            'showExtensions': True,
            'showRequestHeaders': True,
            'supportedSubmitMethods': ['get', 'post', 'put', 'delete', 'patch']
        }
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix='/api/docs')
    
    # Initialize Bcrypt
    bcrypt.init_app(app)
    
    # Initialize Rate Limiter
    limiter.init_app(app)
    
    # Initialize Sentry
    if app.config.get('SENTRY_DSN'):
        sentry_sdk.init(
            dsn=app.config['SENTRY_DSN'],
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0
        ) 