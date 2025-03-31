import os
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_backend import create_app
from flask_backend.models import db
from flask_backend.scheduler import init_scheduler

# Create the application instance
app = create_app()

# Initialize database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # Initialize the task scheduler
    scheduler = init_scheduler(app)
    
    # Run the Flask application
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5001))  # Use port 5001 to avoid conflict with the Express server on 5000
    app.run(host=host, port=port, debug=True)