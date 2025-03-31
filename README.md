# Productivity Planner

A professional project management and productivity tracking system built with Flask.

## Features

- User Authentication and Authorization
- Task Management
- Sprint Planning and Tracking
- Time Tracking
- Real-time Notifications
- File Attachments (Local Storage)
- Analytics and Reporting
- Audit Logging
- RESTful API with Swagger Documentation

## Tech Stack

- **Backend Framework**: Flask
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Authentication**: JWT
- **Real-time**: Flask-SocketIO
- **API Documentation**: Swagger/OpenAPI
- **Testing**: pytest
- **Code Quality**: flake8, black, isort
- **CI/CD**: GitHub Actions
- **Containerization**: Docker
- **Container Orchestration**: Docker Compose

## Project Structure

```
productivity_planner/
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── nginx/
│   │   └── nginx.conf
│   └── scripts/
│       ├── entrypoint.sh
│       └── wait-for-it.sh
├── flask_backend/
│   ├── api/
│   ├── models/
│   ├── services/
│   ├── utils/
│   ├── config/
│   ├── migrations/
│   ├── tests/
│   ├── static/
│   ├── templates/
│   ├── __init__.py
│   ├── extensions.py
│   └── run.py
├── docs/
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── DEVELOPMENT.md
├── scripts/
│   ├── setup.sh
│   └── deploy.sh
├── .env.example
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Prerequisites

- Docker
- Docker Compose
- Make (optional, for using Makefile commands)

## Quick Start with Docker

1. Clone the repository:
```bash
git clone https://github.com/yourusername/productivity-planner.git
cd productivity-planner
```

2. Create environment file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Build and start the containers:
```bash
docker-compose up --build
```

The application will be available at:
- API: http://localhost:5000
- API Documentation: http://localhost:5000/api/docs

## Development Setup (Without Docker)

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development tools
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize the database:
```bash
flask db upgrade
```

5. Run the development server:
```bash
flask run
```

## Testing

Run tests with pytest:
```bash
# With Docker
docker-compose exec api pytest

# Without Docker
pytest
```

## Code Quality

Format and check code:
```bash
# Format code
black .
isort .

# Check style
flake8
```

## Deployment

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment instructions.

## API Documentation

Access the Swagger UI documentation at:
```
http://localhost:5000/api/docs
```

For detailed API documentation, see [API.md](docs/API.md).

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email support@productivityplanner.com or create an issue in the repository. 