# Productivity Planner API Documentation

## Project Overview
Productivity Planner is a comprehensive project management and productivity tracking system that helps teams manage tasks, sprints, and projects efficiently. The system includes features for task management, sprint planning, time tracking, file attachments, and real-time collaboration.

## Core Features

### 1. User Management
- User authentication and authorization
- Role-based access control (Owner, Manager, Employee)
- Organization management
- User profiles and preferences

### 2. Task Management
- Task creation, assignment, and tracking
- Priority and status management
- Story points and time estimation
- Task dependencies and subtasks
- File attachments
- Comments and discussions
- Tags and categorization

### 3. Sprint Management
- Sprint planning and tracking
- Sprint velocity calculation
- Burndown charts
- Sprint retrospectives
- Subgoal tracking
- Standup logs

### 4. Time Tracking
- Task time logging
- Timer functionality
- Time estimates vs. actuals
- Productivity analytics

### 5. File Management
- File attachments for tasks and events
- AWS S3 integration
- Secure file access
- File type validation

### 6. Real-time Features
- WebSocket integration
- Live updates for tasks and comments
- Real-time notifications
- Chat functionality

### 7. Analytics and Reporting
- Task analytics
- Velocity tracking
- Team performance metrics
- Audit logging
- Custom reports

## Project Structure

```
flask_backend/
├── api/
│   ├── __init__.py
│   ├── auth.py
│   ├── tasks.py
│   ├── sprints.py
│   ├── events.py
│   ├── timers.py
│   ├── messages.py
│   ├── attachments.py
│   ├── dashboard.py
│   ├── organization.py
│   └── audit.py
├── models.py
├── config.py
├── run.py
└── websocket.py
```

## Models

### User
- Core user information
- Authentication details
- Role and permissions
- Organization association

### Organization
- Organization details
- User management
- Resource management

### Task
- Task details
- Assignment and tracking
- Time and effort estimation
- Status and priority
- Dependencies and relationships

### Sprint
- Sprint planning
- Velocity tracking
- Progress monitoring
- Subgoal management

### Event
- Calendar events
- Meeting scheduling
- Attendance tracking

### TimeLog
- Time tracking
- Duration calculation
- Activity logging

### Comment
- Task discussions
- User interactions
- Mention support

### Notification
- User notifications
- Real-time updates
- Activity alerts

### Attachment
- File management
- S3 integration
- Access control

### AuditLog
- Activity tracking
- Change history
- Security monitoring

## API Endpoints

### Authentication
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout
- GET /api/auth/me

### Tasks
- GET /api/tasks
- POST /api/tasks
- GET /api/tasks/<id>
- PUT /api/tasks/<id>
- DELETE /api/tasks/<id>
- POST /api/tasks/<id>/comments
- POST /api/tasks/<id>/attachments
- POST /api/tasks/<id>/time-logs

### Sprints
- GET /api/sprints
- POST /api/sprints
- GET /api/sprints/<id>
- PUT /api/sprints/<id>
- DELETE /api/sprints/<id>
- POST /api/sprints/<id>/complete
- GET /api/sprints/<id>/burndown

### Events
- GET /api/events
- POST /api/events
- GET /api/events/<id>
- PUT /api/events/<id>
- DELETE /api/events/<id>

### Dashboard
- GET /api/dashboard/personal
- GET /api/dashboard/notifications

### Organization
- GET /api/organization/analytics/tasks
- GET /api/organization/analytics/velocity
- GET /api/organization/analytics/team

### Audit
- GET /api/audit/logs
- GET /api/audit/logs/summary
- GET /api/audit/logs/export

## WebSocket Events

### Task Events
- task_created
- task_updated
- task_deleted
- task_status_changed

### Comment Events
- comment_added
- comment_updated
- comment_deleted

### Notification Events
- notification_received

### Attachment Events
- attachment_added
- attachment_deleted

## Security Features
- JWT authentication
- Role-based access control
- Organization data isolation
- File access control
- Audit logging
- Input validation
- XSS protection
- CSRF protection

## Database Schema
The project uses PostgreSQL with SQLAlchemy ORM. Key tables include:
- users
- organizations
- tasks
- sprints
- events
- time_logs
- comments
- notifications
- attachments
- audit_logs

## Environment Variables
Required environment variables:
```
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
JWT_SECRET_KEY=your-secret-key
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=your-aws-region
AWS_S3_BUCKET=your-s3-bucket
```

## Setup and Installation
1. Clone the repository
2. Create a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Set up environment variables
5. Initialize the database: `flask db upgrade`
6. Run the application: `flask run`

## Testing
The project includes unit tests and integration tests. Run tests with:
```bash
python -m pytest
```

## Deployment
The application can be deployed to various platforms:
- Heroku
- AWS Elastic Beanstalk
- DigitalOcean App Platform
- Google Cloud Run

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Create a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details. 