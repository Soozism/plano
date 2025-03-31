from flask import Flask
from flask_swagger_ui import get_swaggerui_blueprint

SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
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

def init_swagger(app: Flask):
    """Initialize Swagger documentation."""
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
    
    @app.route('/static/swagger.json')
    def swagger():
        return {
            "swagger": "2.0",
            "info": {
                "title": "Productivity Planner API",
                "description": """
                A comprehensive project management and productivity tracking system API.
                
                ## Features
                - User authentication and authorization
                - Task and sprint management
                - Time tracking and analytics
                - File attachments and real-time updates
                - Team collaboration and notifications
                
                ## Authentication
                All endpoints except /auth/* require a valid JWT token in the Authorization header.
                Format: `Authorization: Bearer <token>`
                
                ## Rate Limiting
                API requests are limited to 100 requests per minute per user.
                
                ## Error Responses
                All endpoints may return the following error responses:
                - 400: Bad Request - Invalid input data
                - 401: Unauthorized - Invalid or missing token
                - 403: Forbidden - Insufficient permissions
                - 404: Not Found - Resource not found
                - 429: Too Many Requests - Rate limit exceeded
                - 500: Internal Server Error - Server-side error
                """,
                "version": "1.0.0",
                "contact": {
                    "name": "API Support",
                    "email": "support@productivityplanner.com"
                },
                "license": {
                    "name": "MIT License",
                    "url": "https://opensource.org/licenses/MIT"
                }
            },
            "host": "api.productivityplanner.com",
            "basePath": "/api",
            "schemes": ["https", "http"],
            "consumes": ["application/json"],
            "produces": ["application/json"],
            "securityDefinitions": {
                "Bearer": {
                    "type": "apiKey",
                    "name": "Authorization",
                    "in": "header",
                    "description": "JWT token obtained from /auth/login endpoint"
                }
            },
            "definitions": {
                "Error": {
                    "type": "object",
                    "properties": {
                        "error": {"type": "string"},
                        "message": {"type": "string"},
                        "code": {"type": "integer"}
                    }
                },
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "username": {"type": "string"},
                        "email": {"type": "string"},
                        "name": {"type": "string"},
                        "role": {"type": "string", "enum": ["OWNER", "MANAGER", "EMPLOYEE"]},
                        "organization_id": {"type": "integer"}
                    }
                },
                "Task": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "status": {"type": "string", "enum": ["todo", "in_progress", "done", "cancelled"]},
                        "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                        "story_points": {"type": "integer"},
                        "estimated_hours": {"type": "integer"},
                        "deadline": {"type": "string", "format": "date-time"},
                        "assignee_user_id": {"type": "integer"},
                        "sprint_id": {"type": "integer"},
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"}
                    }
                },
                "Sprint": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "goal": {"type": "string"},
                        "start_date": {"type": "string", "format": "date-time"},
                        "end_date": {"type": "string", "format": "date-time"},
                        "planned_velocity": {"type": "number"},
                        "actual_velocity": {"type": "number"},
                        "status": {"type": "string", "enum": ["planned", "active", "completed"]}
                    }
                }
            },
            "paths": {
                "/auth/register": {
                    "post": {
                        "tags": ["Authentication"],
                        "summary": "Register a new user",
                        "description": "Create a new user account in the system",
                        "parameters": [
                            {
                                "name": "body",
                                "in": "body",
                                "required": True,
                                "schema": {
                                    "type": "object",
                                    "required": ["username", "email", "password", "name"],
                                    "properties": {
                                        "username": {
                                            "type": "string",
                                            "description": "Unique username (3-30 characters)",
                                            "minLength": 3,
                                            "maxLength": 30
                                        },
                                        "email": {
                                            "type": "string",
                                            "format": "email",
                                            "description": "Valid email address"
                                        },
                                        "password": {
                                            "type": "string",
                                            "format": "password",
                                            "description": "Password (min 8 characters)",
                                            "minLength": 8
                                        },
                                        "name": {
                                            "type": "string",
                                            "description": "Full name"
                                        }
                                    }
                                }
                            }
                        ],
                        "responses": {
                            "201": {
                                "description": "User created successfully",
                                "schema": {
                                    "$ref": "#/definitions/User"
                                }
                            },
                            "400": {
                                "description": "Invalid input",
                                "schema": {
                                    "$ref": "#/definitions/Error"
                                }
                            },
                            "409": {
                                "description": "Username or email already exists",
                                "schema": {
                                    "$ref": "#/definitions/Error"
                                }
                            }
                        }
                    }
                },
                "/auth/login": {
                    "post": {
                        "tags": ["Authentication"],
                        "summary": "Login user",
                        "description": "Authenticate user and return JWT token",
                        "parameters": [
                            {
                                "name": "body",
                                "in": "body",
                                "required": True,
                                "schema": {
                                    "type": "object",
                                    "required": ["email", "password"],
                                    "properties": {
                                        "email": {
                                            "type": "string",
                                            "format": "email",
                                            "description": "Registered email address"
                                        },
                                        "password": {
                                            "type": "string",
                                            "format": "password",
                                            "description": "User password"
                                        }
                                    }
                                }
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Login successful",
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "access_token": {"type": "string"},
                                        "token_type": {"type": "string", "enum": ["Bearer"]},
                                        "expires_in": {"type": "integer"},
                                        "user": {"$ref": "#/definitions/User"}
                                    }
                                }
                            },
                            "401": {
                                "description": "Invalid credentials",
                                "schema": {
                                    "$ref": "#/definitions/Error"
                                }
                            }
                        }
                    }
                },
                "/tasks": {
                    "get": {
                        "tags": ["Tasks"],
                        "summary": "Get all tasks",
                        "description": "Retrieve a list of tasks with optional filtering",
                        "security": [{"Bearer": []}],
                        "parameters": [
                            {
                                "name": "status",
                                "in": "query",
                                "type": "string",
                                "enum": ["todo", "in_progress", "done", "cancelled"],
                                "description": "Filter by task status"
                            },
                            {
                                "name": "priority",
                                "in": "query",
                                "type": "string",
                                "enum": ["low", "medium", "high", "critical"],
                                "description": "Filter by task priority"
                            },
                            {
                                "name": "assignee",
                                "in": "query",
                                "type": "integer",
                                "description": "Filter by assignee ID"
                            },
                            {
                                "name": "sprint_id",
                                "in": "query",
                                "type": "integer",
                                "description": "Filter by sprint ID"
                            },
                            {
                                "name": "page",
                                "in": "query",
                                "type": "integer",
                                "default": 1,
                                "description": "Page number for pagination"
                            },
                            {
                                "name": "per_page",
                                "in": "query",
                                "type": "integer",
                                "default": 20,
                                "description": "Number of items per page"
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "List of tasks",
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "tasks": {
                                            "type": "array",
                                            "items": {"$ref": "#/definitions/Task"}
                                        },
                                        "total": {"type": "integer"},
                                        "pages": {"type": "integer"},
                                        "current_page": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    },
                    "post": {
                        "tags": ["Tasks"],
                        "summary": "Create a new task",
                        "description": "Create a new task in the system",
                        "security": [{"Bearer": []}],
                        "parameters": [
                            {
                                "name": "body",
                                "in": "body",
                                "required": True,
                                "schema": {
                                    "type": "object",
                                    "required": ["title", "description", "priority", "status"],
                                    "properties": {
                                        "title": {
                                            "type": "string",
                                            "description": "Task title",
                                            "maxLength": 200
                                        },
                                        "description": {
                                            "type": "string",
                                            "description": "Task description"
                                        },
                                        "priority": {
                                            "type": "string",
                                            "enum": ["low", "medium", "high", "critical"],
                                            "description": "Task priority level"
                                        },
                                        "status": {
                                            "type": "string",
                                            "enum": ["todo", "in_progress", "done", "cancelled"],
                                            "description": "Task status"
                                        },
                                        "deadline": {
                                            "type": "string",
                                            "format": "date-time",
                                            "description": "Task deadline"
                                        },
                                        "story_points": {
                                            "type": "integer",
                                            "description": "Story points for the task",
                                            "minimum": 0
                                        },
                                        "estimated_hours": {
                                            "type": "integer",
                                            "description": "Estimated hours to complete",
                                            "minimum": 0
                                        },
                                        "assignee_user_id": {
                                            "type": "integer",
                                            "description": "ID of the user assigned to the task"
                                        },
                                        "sprint_id": {
                                            "type": "integer",
                                            "description": "ID of the sprint this task belongs to"
                                        }
                                    }
                                }
                            }
                        ],
                        "responses": {
                            "201": {
                                "description": "Task created successfully",
                                "schema": {
                                    "$ref": "#/definitions/Task"
                                }
                            },
                            "400": {
                                "description": "Invalid input",
                                "schema": {
                                    "$ref": "#/definitions/Error"
                                }
                            }
                        }
                    }
                },
                "/tasks/{task_id}": {
                    "parameters": [
                        {
                            "name": "task_id",
                            "in": "path",
                            "type": "integer",
                            "required": True,
                            "description": "ID of the task"
                        }
                    ],
                    "get": {
                        "tags": ["Tasks"],
                        "summary": "Get task by ID",
                        "description": "Retrieve detailed information about a specific task",
                        "security": [{"Bearer": []}],
                        "responses": {
                            "200": {
                                "description": "Task details",
                                "schema": {
                                    "$ref": "#/definitions/Task"
                                }
                            },
                            "404": {
                                "description": "Task not found",
                                "schema": {
                                    "$ref": "#/definitions/Error"
                                }
                            }
                        }
                    },
                    "put": {
                        "tags": ["Tasks"],
                        "summary": "Update task",
                        "description": "Update an existing task's information",
                        "security": [{"Bearer": []}],
                        "parameters": [
                            {
                                "name": "body",
                                "in": "body",
                                "required": True,
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "title": {
                                            "type": "string",
                                            "description": "Task title",
                                            "maxLength": 200
                                        },
                                        "description": {
                                            "type": "string",
                                            "description": "Task description"
                                        },
                                        "priority": {
                                            "type": "string",
                                            "enum": ["low", "medium", "high", "critical"],
                                            "description": "Task priority level"
                                        },
                                        "status": {
                                            "type": "string",
                                            "enum": ["todo", "in_progress", "done", "cancelled"],
                                            "description": "Task status"
                                        },
                                        "deadline": {
                                            "type": "string",
                                            "format": "date-time",
                                            "description": "Task deadline"
                                        },
                                        "story_points": {
                                            "type": "integer",
                                            "description": "Story points for the task",
                                            "minimum": 0
                                        },
                                        "estimated_hours": {
                                            "type": "integer",
                                            "description": "Estimated hours to complete",
                                            "minimum": 0
                                        },
                                        "assignee_user_id": {
                                            "type": "integer",
                                            "description": "ID of the user assigned to the task"
                                        },
                                        "sprint_id": {
                                            "type": "integer",
                                            "description": "ID of the sprint this task belongs to"
                                        }
                                    }
                                }
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Task updated successfully",
                                "schema": {
                                    "$ref": "#/definitions/Task"
                                }
                            },
                            "404": {
                                "description": "Task not found",
                                "schema": {
                                    "$ref": "#/definitions/Error"
                                }
                            }
                        }
                    },
                    "delete": {
                        "tags": ["Tasks"],
                        "summary": "Delete task",
                        "description": "Delete a task from the system",
                        "security": [{"Bearer": []}],
                        "responses": {
                            "204": {
                                "description": "Task deleted successfully"
                            },
                            "404": {
                                "description": "Task not found",
                                "schema": {
                                    "$ref": "#/definitions/Error"
                                }
                            }
                        }
                    }
                },
                "/sprints": {
                    "get": {
                        "tags": ["Sprints"],
                        "summary": "Get all sprints",
                        "description": "Retrieve a list of all sprints",
                        "security": [{"Bearer": []}],
                        "parameters": [
                            {
                                "name": "status",
                                "in": "query",
                                "type": "string",
                                "enum": ["planned", "active", "completed"],
                                "description": "Filter by sprint status"
                            },
                            {
                                "name": "page",
                                "in": "query",
                                "type": "integer",
                                "default": 1,
                                "description": "Page number for pagination"
                            },
                            {
                                "name": "per_page",
                                "in": "query",
                                "type": "integer",
                                "default": 20,
                                "description": "Number of items per page"
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "List of sprints",
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "sprints": {
                                            "type": "array",
                                            "items": {"$ref": "#/definitions/Sprint"}
                                        },
                                        "total": {"type": "integer"},
                                        "pages": {"type": "integer"},
                                        "current_page": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    },
                    "post": {
                        "tags": ["Sprints"],
                        "summary": "Create a new sprint",
                        "description": "Create a new sprint in the system",
                        "security": [{"Bearer": []}],
                        "parameters": [
                            {
                                "name": "body",
                                "in": "body",
                                "required": True,
                                "schema": {
                                    "type": "object",
                                    "required": ["name", "goal", "start_date", "end_date"],
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                            "description": "Sprint name",
                                            "maxLength": 100
                                        },
                                        "goal": {
                                            "type": "string",
                                            "description": "Sprint goal"
                                        },
                                        "start_date": {
                                            "type": "string",
                                            "format": "date-time",
                                            "description": "Sprint start date"
                                        },
                                        "end_date": {
                                            "type": "string",
                                            "format": "date-time",
                                            "description": "Sprint end date"
                                        },
                                        "planned_velocity": {
                                            "type": "number",
                                            "description": "Planned velocity for the sprint",
                                            "minimum": 0
                                        }
                                    }
                                }
                            }
                        ],
                        "responses": {
                            "201": {
                                "description": "Sprint created successfully",
                                "schema": {
                                    "$ref": "#/definitions/Sprint"
                                }
                            },
                            "400": {
                                "description": "Invalid input",
                                "schema": {
                                    "$ref": "#/definitions/Error"
                                }
                            }
                        }
                    }
                },
                "/sprints/{sprint_id}/burndown": {
                    "tags": ["Sprints"],
                    "summary": "Get sprint burndown chart data",
                    "description": "Retrieve data for the sprint burndown chart",
                    "security": [{"Bearer": []}],
                    "parameters": [
                        {
                            "name": "sprint_id",
                            "in": "path",
                            "type": "integer",
                            "required": True,
                            "description": "ID of the sprint"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Burndown chart data",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "dates": {
                                        "type": "array",
                                        "items": {"type": "string", "format": "date"}
                                    },
                                    "ideal_remaining": {
                                        "type": "array",
                                        "items": {"type": "number"}
                                    },
                                    "actual_remaining": {
                                        "type": "array",
                                        "items": {"type": "number"}
                                    }
                                }
                            }
                        },
                        "404": {
                            "description": "Sprint not found",
                            "schema": {
                                "$ref": "#/definitions/Error"
                            }
                        }
                    }
                },
                "/dashboard/personal": {
                    "get": {
                        "tags": ["Dashboard"],
                        "summary": "Get personal dashboard data",
                        "description": "Retrieve personal dashboard data including tasks, events, and analytics",
                        "security": [{"Bearer": []}],
                        "responses": {
                            "200": {
                                "description": "Dashboard data",
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "active_tasks": {
                                            "type": "array",
                                            "items": {"$ref": "#/definitions/Task"}
                                        },
                                        "upcoming_events": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "integer"},
                                                    "title": {"type": "string"},
                                                    "start_time": {"type": "string", "format": "date-time"},
                                                    "end_time": {"type": "string", "format": "date-time"}
                                                }
                                            }
                                        },
                                        "active_timers": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "integer"},
                                                    "task_id": {"type": "integer"},
                                                    "start_time": {"type": "string", "format": "date-time"},
                                                    "duration": {"type": "integer"}
                                                }
                                            }
                                        },
                                        "task_stats": {
                                            "type": "object",
                                            "properties": {
                                                "total_tasks": {"type": "integer"},
                                                "completed_tasks": {"type": "integer"},
                                                "in_progress_tasks": {"type": "integer"},
                                                "overdue_tasks": {"type": "integer"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/organization/analytics/tasks": {
                    "get": {
                        "tags": ["Analytics"],
                        "summary": "Get task analytics",
                        "description": "Retrieve analytics data for tasks in the organization",
                        "security": [{"Bearer": []}],
                        "parameters": [
                            {
                                "name": "start_date",
                                "in": "query",
                                "type": "string",
                                "format": "date",
                                "description": "Start date for analytics period"
                            },
                            {
                                "name": "end_date",
                                "in": "query",
                                "type": "string",
                                "format": "date",
                                "description": "End date for analytics period"
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Task analytics data",
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "total_tasks": {"type": "integer"},
                                        "completed_tasks": {"type": "integer"},
                                        "completion_rate": {"type": "number"},
                                        "average_completion_time": {"type": "number"},
                                        "tasks_by_status": {
                                            "type": "object",
                                            "properties": {
                                                "todo": {"type": "integer"},
                                                "in_progress": {"type": "integer"},
                                                "done": {"type": "integer"},
                                                "cancelled": {"type": "integer"}
                                            }
                                        },
                                        "tasks_by_priority": {
                                            "type": "object",
                                            "properties": {
                                                "low": {"type": "integer"},
                                                "medium": {"type": "integer"},
                                                "high": {"type": "integer"},
                                                "critical": {"type": "integer"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/audit/logs": {
                    "get": {
                        "tags": ["Audit"],
                        "summary": "Get audit logs",
                        "description": "Retrieve audit logs with filtering options",
                        "security": [{"Bearer": []}],
                        "parameters": [
                            {
                                "name": "entity_type",
                                "in": "query",
                                "type": "string",
                                "description": "Filter by entity type (e.g., task, sprint, user)"
                            },
                            {
                                "name": "entity_id",
                                "in": "query",
                                "type": "integer",
                                "description": "Filter by entity ID"
                            },
                            {
                                "name": "action",
                                "in": "query",
                                "type": "string",
                                "description": "Filter by action (e.g., create, update, delete)"
                            },
                            {
                                "name": "start_date",
                                "in": "query",
                                "type": "string",
                                "format": "date-time",
                                "description": "Filter by start date"
                            },
                            {
                                "name": "end_date",
                                "in": "query",
                                "type": "string",
                                "format": "date-time",
                                "description": "Filter by end date"
                            },
                            {
                                "name": "page",
                                "in": "query",
                                "type": "integer",
                                "default": 1,
                                "description": "Page number for pagination"
                            },
                            {
                                "name": "per_page",
                                "in": "query",
                                "type": "integer",
                                "default": 50,
                                "description": "Number of items per page"
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "List of audit logs",
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "logs": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "integer"},
                                                    "user_id": {"type": "integer"},
                                                    "action": {"type": "string"},
                                                    "entity_type": {"type": "string"},
                                                    "entity_id": {"type": "integer"},
                                                    "changes": {"type": "object"},
                                                    "created_at": {"type": "string", "format": "date-time"},
                                                    "ip_address": {"type": "string"},
                                                    "user_agent": {"type": "string"}
                                                }
                                            }
                                        },
                                        "total": {"type": "integer"},
                                        "pages": {"type": "integer"},
                                        "current_page": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        } 