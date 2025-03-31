from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from ..models import db, User, Task, Role, Status, Priority, Comment, Milestone, TaskTemplate, RecurrenceRule, Tag, Notification
from sqlalchemy import and_
from ..websocket import (
    broadcast_task_update,
    broadcast_task_created,
    broadcast_task_deleted,
    broadcast_milestone_update,
    broadcast_comment_added
)
import re

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('', methods=['GET'])
@jwt_required()
def get_tasks():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    if not current_user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user belongs to an organization
    if not current_user.organization_id:
        return jsonify({'error': 'User is not part of an organization'}), 400
    
    # Get query parameters
    assignee_user_id = request.args.get('assignee_user_id')
    assignee_group_id = request.args.get('assignee_group_id')
    sprint_id = request.args.get('sprint_id')
    status = request.args.get('status')
    priority = request.args.get('priority')
    search = request.args.get('search', '')
    is_backlog = request.args.get('is_backlog', 'false').lower() == 'true'
    tags = request.args.get('tags', '').split(',') if request.args.get('tags') else []
    
    # Build query
    query = Task.query.filter_by(organization_id=current_user.organization_id)
    
    # Apply filters
    if assignee_user_id:
        query = query.filter_by(assignee_user_id=assignee_user_id)
    
    if assignee_group_id:
        query = query.filter_by(assignee_group_id=assignee_group_id)
    
    if sprint_id:
        query = query.filter_by(sprint_id=sprint_id)
    elif is_backlog:
        # Backlog items are those without a sprint
        query = query.filter_by(sprint_id=None)
    
    if status:
        try:
            status_enum = Status[status.upper()]
            query = query.filter_by(status=status_enum)
        except (KeyError, AttributeError):
            pass  # Invalid status, ignore filter
    
    if priority:
        try:
            priority_enum = Priority[priority.upper()]
            query = query.filter_by(priority=priority_enum)
        except (KeyError, AttributeError):
            pass  # Invalid priority, ignore filter
    
    if search:
        query = query.filter(Task.title.ilike(f'%{search}%'))
        
    # Filter by tags
    if tags and tags[0]:  # Check if tags list is not empty
        tag_conditions = []
        for tag_name in tags:
            tag = Tag.query.filter_by(
                name=tag_name.strip(),
                organization_id=current_user.organization_id
            ).first()
            if tag:
                tag_conditions.append(Task.tags.contains(tag))
        if tag_conditions:
            query = query.filter(and_(*tag_conditions))
    
    # Get tasks
    tasks = query.order_by(Task.created_at.desc()).all()
    
    return jsonify([task.to_dict() for task in tasks]), 200

@tasks_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_task(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find task
    task = Task.query.get(id)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    # Check if user has access to this task (in same org)
    if current_user.organization_id != task.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Build response with task details and comments
    result = task.to_dict()
    
    # Get comments
    comments = Comment.query.filter_by(task_id=id).order_by(Comment.created_at).all()
    result['comments'] = [comment.to_dict() for comment in comments]
    
    return jsonify(result), 200

@tasks_bp.route('', methods=['POST'])
@jwt_required()
def create_task():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Check if user belongs to an organization
    if not current_user.organization_id:
        return jsonify({'error': 'User is not part of an organization'}), 400
    
    data = request.get_json()
    
    # Validate required fields
    if 'title' not in data:
        return jsonify({'error': 'Title is required'}), 400
    
    # Create new task
    new_task = Task(
        title=data['title'],
        description=data.get('description'),
        organization_id=current_user.organization_id,
        created_by_id=user_id,
        status=Status.TODO,  # Default status
        priority=Priority.MEDIUM  # Default priority
    )
    
    # Set optional fields if provided
    if 'priority' in data:
        try:
            new_task.priority = Priority[data['priority'].upper()]
        except (KeyError, AttributeError):
            return jsonify({'error': 'Invalid priority value'}), 400
    
    if 'status' in data:
        try:
            new_task.status = Status[data['status'].upper()]
        except (KeyError, AttributeError):
            return jsonify({'error': 'Invalid status value'}), 400
    
    if 'deadline' in data and data['deadline']:
        try:
            new_task.deadline = datetime.fromisoformat(data['deadline'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid deadline format'}), 400
    
    if 'story_points' in data and data['story_points'] is not None:
        new_task.story_points = data['story_points']
    
    if 'estimated_hours' in data and data['estimated_hours'] is not None:
        new_task.estimated_hours = data['estimated_hours']
    
    if 'acceptance_criteria' in data:
        new_task.acceptance_criteria = data['acceptance_criteria']
    
    if 'assignee_user_id' in data and data['assignee_user_id']:
        # Check if assignee exists and is in the same org
        assignee = User.query.get(data['assignee_user_id'])
        if not assignee or assignee.organization_id != current_user.organization_id:
            return jsonify({'error': 'Invalid assignee user ID'}), 400
        
        new_task.assignee_user_id = data['assignee_user_id']
    
    if 'assignee_group_id' in data and data['assignee_group_id']:
        # Validate group ID (would need a Group model import to fully validate)
        new_task.assignee_group_id = data['assignee_group_id']
    
    if 'parent_task_id' in data and data['parent_task_id']:
        # Check if parent task exists and is in the same org
        parent_task = Task.query.get(data['parent_task_id'])
        if not parent_task or parent_task.organization_id != current_user.organization_id:
            return jsonify({'error': 'Invalid parent task ID'}), 400
        
        new_task.parent_task_id = data['parent_task_id']
    
    if 'sprint_id' in data and data['sprint_id']:
        # Validate sprint ID (would need a Sprint model import to fully validate)
        new_task.sprint_id = data['sprint_id']
        
    # Handle recurrence settings
    if 'recurrence_rule' in data:
        try:
            new_task.recurrence_rule = RecurrenceRule[data['recurrence_rule'].upper()]
        except (KeyError, AttributeError):
            return jsonify({'error': 'Invalid recurrence rule'}), 400
            
    if 'recurrence_end' in data and data['recurrence_end']:
        try:
            new_task.recurrence_end = datetime.fromisoformat(data['recurrence_end'].replace('Z', '+00:00'))
            # Validate that end date is after creation date
            if new_task.recurrence_end <= new_task.created_at:
                return jsonify({'error': 'Recurrence end date must be after creation date'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid recurrence end date format'}), 400
            
    # Handle tags
    if 'tags' in data and data['tags']:
        for tag_name in data['tags']:
            # Find or create tag
            tag = Tag.query.filter_by(
                name=tag_name.strip(),
                organization_id=current_user.organization_id
            ).first()
            if not tag:
                tag = Tag(
                    name=tag_name.strip(),
                    organization_id=current_user.organization_id
                )
                db.session.add(tag)
            new_task.tags.append(tag)
    
    db.session.add(new_task)
    db.session.commit()
    
    # Broadcast task creation
    broadcast_task_created(new_task.to_dict())
    
    return jsonify(new_task.to_dict()), 201

@tasks_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_task(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find task
    task = Task.query.get(id)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    # Check if user has access to this task (in same org)
    if current_user.organization_id != task.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Update fields
    if 'title' in data:
        task.title = data['title']
    
    if 'description' in data:
        task.description = data['description']
    
    if 'priority' in data:
        try:
            task.priority = Priority[data['priority'].upper()]
        except (KeyError, AttributeError):
            return jsonify({'error': 'Invalid priority value'}), 400
    
    if 'status' in data:
        try:
            task.status = Status[data['status'].upper()]
        except (KeyError, AttributeError):
            return jsonify({'error': 'Invalid status value'}), 400
    
    if 'deadline' in data:
        if data['deadline'] is None:
            task.deadline = None
        else:
            try:
                task.deadline = datetime.fromisoformat(data['deadline'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid deadline format'}), 400
    
    if 'story_points' in data:
        task.story_points = data['story_points']
    
    if 'estimated_hours' in data:
        task.estimated_hours = data['estimated_hours']
    
    if 'acceptance_criteria' in data:
        task.acceptance_criteria = data['acceptance_criteria']
    
    if 'assignee_user_id' in data:
        if data['assignee_user_id'] is None:
            task.assignee_user_id = None
        else:
            # Check if assignee exists and is in the same org
            assignee = User.query.get(data['assignee_user_id'])
            if not assignee or assignee.organization_id != current_user.organization_id:
                return jsonify({'error': 'Invalid assignee user ID'}), 400
            
            task.assignee_user_id = data['assignee_user_id']
    
    if 'assignee_group_id' in data:
        task.assignee_group_id = data['assignee_group_id']
    
    if 'parent_task_id' in data:
        if data['parent_task_id'] is None:
            task.parent_task_id = None
        else:
            # Check if parent task exists and is in the same org
            parent_task = Task.query.get(data['parent_task_id'])
            if not parent_task or parent_task.organization_id != current_user.organization_id:
                return jsonify({'error': 'Invalid parent task ID'}), 400
            
            # Prevent circular dependencies
            if parent_task.id == id or parent_task.parent_task_id == id:
                return jsonify({'error': 'Circular task dependency not allowed'}), 400
            
            task.parent_task_id = data['parent_task_id']
    
    if 'sprint_id' in data:
        task.sprint_id = data['sprint_id']
        
    # Handle tags
    if 'tags' in data:
        # Clear existing tags
        task.tags = []
        # Add new tags
        if data['tags']:
            for tag_name in data['tags']:
                # Find or create tag
                tag = Tag.query.filter_by(
                    name=tag_name.strip(),
                    organization_id=current_user.organization_id
                ).first()
                if not tag:
                    tag = Tag(
                        name=tag_name.strip(),
                        organization_id=current_user.organization_id
                    )
                    db.session.add(tag)
                task.tags.append(tag)
    
    # Update task
    task.updated_at = datetime.utcnow()
    db.session.commit()
    
    # Broadcast task update
    broadcast_task_update(task.to_dict())
    
    return jsonify(task.to_dict()), 200

@tasks_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_task(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find task
    task = Task.query.get(id)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    # Check if user has access to this task (in same org)
    if current_user.organization_id != task.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check permissions: creator, assignee, or manager/owner can delete
    is_creator = task.created_by_id == user_id
    is_assignee = task.assignee_user_id == user_id
    is_manager = current_user.role in [Role.MANAGER, Role.OWNER]
    
    if not (is_creator or is_assignee or is_manager):
        return jsonify({'error': 'You do not have permission to delete this task'}), 403
    
    # Check if task has subtasks
    if Task.query.filter_by(parent_task_id=id).count() > 0:
        return jsonify({'error': 'Cannot delete task with subtasks'}), 400
    
    # Store organization_id before deletion
    organization_id = task.organization_id
    
    # Delete task
    db.session.delete(task)
    db.session.commit()
    
    # Broadcast task deletion
    broadcast_task_deleted(id, organization_id)
    
    return jsonify({'message': 'Task deleted successfully'}), 200

def extract_mentions(content):
    """Extract mentioned usernames from content."""
    # Match @username pattern
    mention_pattern = r'@(\w+)'
    return re.findall(mention_pattern, content)

def create_mention_notifications(task_id, comment_id, content, mentioned_users, commenter_id):
    """Create notifications for mentioned users."""
    for user in mentioned_users:
        # Skip if user is the commenter
        if user.id == commenter_id:
            continue
            
        notification = Notification(
            user_id=user.id,
            message=f"You were mentioned in a comment on task {task_id}",
            type='mention',
            read=False,
            related_id=comment_id,
            related_type='comment'
        )
        db.session.add(notification)
    
    db.session.commit()

@tasks_bp.route('/<int:id>/comments', methods=['POST'])
@jwt_required()
def add_comment(id):
    """Add a comment to a task."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find task
    task = Task.query.get(id)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    # Check if user has access to this task (in same org)
    if current_user.organization_id != task.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Validate content
    if 'content' not in data or not data['content'].strip():
        return jsonify({'error': 'Comment content is required'}), 400
    
    # Extract mentions from content
    mentioned_usernames = extract_mentions(data['content'])
    
    # Find mentioned users in the same organization
    mentioned_users = User.query.filter(
        User.username.in_(mentioned_usernames),
        User.organization_id == task.organization_id
    ).all()
    
    # Create comment
    new_comment = Comment(
        task_id=id,
        user_id=user_id,
        content=data['content']
    )
    
    db.session.add(new_comment)
    db.session.commit()
    
    # Create notifications for mentioned users
    create_mention_notifications(id, new_comment.id, data['content'], mentioned_users, user_id)
    
    # Broadcast comment
    broadcast_comment_added(id, new_comment.to_dict(), task.organization_id)
    
    return jsonify(new_comment.to_dict()), 201

@tasks_bp.route('/<int:id>/milestones', methods=['POST'])
@jwt_required()
def create_milestone(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find task
    task = Task.query.get(id)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    # Check if user has access to this task (in same org)
    if current_user.organization_id != task.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    if 'description' not in data or not data['description'].strip():
        return jsonify({'error': 'Milestone description is required'}), 400
    
    # Create milestone
    new_milestone = Milestone(
        task_id=id,
        description=data['description'],
        is_completed=data.get('is_completed', False)
    )
    
    if new_milestone.is_completed:
        new_milestone.completed_at = datetime.utcnow()
    
    db.session.add(new_milestone)
    db.session.commit()
    
    # Broadcast milestone creation
    broadcast_milestone_update(id, new_milestone.to_dict(), task.organization_id)
    
    return jsonify(new_milestone.to_dict()), 201

@tasks_bp.route('/<int:id>/milestones/<int:milestone_id>', methods=['PUT'])
@jwt_required()
def update_milestone(id, milestone_id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find task and milestone
    task = Task.query.get(id)
    milestone = Milestone.query.get(milestone_id)
    
    if not task or not milestone:
        return jsonify({'error': 'Task or milestone not found'}), 404
    
    # Check if milestone belongs to task
    if milestone.task_id != id:
        return jsonify({'error': 'Milestone does not belong to this task'}), 400
    
    # Check if user has access to this task (in same org)
    if current_user.organization_id != task.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Update fields
    if 'description' in data and data['description'].strip():
        milestone.description = data['description']
    
    if 'is_completed' in data:
        milestone.is_completed = data['is_completed']
        if data['is_completed'] and not milestone.completed_at:
            milestone.completed_at = datetime.utcnow()
        elif not data['is_completed']:
            milestone.completed_at = None
    
    db.session.commit()
    
    # Broadcast milestone update
    broadcast_milestone_update(id, milestone.to_dict(), task.organization_id)
    
    return jsonify(milestone.to_dict()), 200

@tasks_bp.route('/<int:id>/milestones/<int:milestone_id>', methods=['DELETE'])
@jwt_required()
def delete_milestone(id, milestone_id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find task and milestone
    task = Task.query.get(id)
    milestone = Milestone.query.get(milestone_id)
    
    if not task or not milestone:
        return jsonify({'error': 'Task or milestone not found'}), 404
    
    # Check if milestone belongs to task
    if milestone.task_id != id:
        return jsonify({'error': 'Milestone does not belong to this task'}), 400
    
    # Check if user has access to this task (in same org)
    if current_user.organization_id != task.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check permissions: creator, assignee, or manager/owner can delete
    is_creator = task.created_by_id == user_id
    is_assignee = task.assignee_user_id == user_id
    is_manager = current_user.role in [Role.MANAGER, Role.OWNER]
    
    if not (is_creator or is_assignee or is_manager):
        return jsonify({'error': 'You do not have permission to delete this milestone'}), 403
    
    # Store organization_id before deletion
    organization_id = task.organization_id
    
    # Delete milestone
    db.session.delete(milestone)
    db.session.commit()
    
    # Broadcast milestone deletion
    broadcast_milestone_update(id, {'id': milestone_id, 'deleted': True}, organization_id)
    
    return jsonify({'message': 'Milestone deleted successfully'}), 200

@tasks_bp.route('/templates', methods=['GET'])
@jwt_required()
def get_task_templates():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    if not current_user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user belongs to an organization
    if not current_user.organization_id:
        return jsonify({'error': 'User is not part of an organization'}), 400
    
    # Get templates for the user's organization
    templates = TaskTemplate.query.filter_by(organization_id=current_user.organization_id).all()
    
    return jsonify([template.to_dict() for template in templates]), 200

@tasks_bp.route('/templates', methods=['POST'])
@jwt_required()
def create_task_template():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    if not current_user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user belongs to an organization
    if not current_user.organization_id:
        return jsonify({'error': 'User is not part of an organization'}), 400
    
    data = request.get_json()
    
    # Validate required fields
    if 'name' not in data or not data['name'].strip():
        return jsonify({'error': 'Template name is required'}), 400
    if 'title' not in data or not data['title'].strip():
        return jsonify({'error': 'Task title is required'}), 400
    
    # Create template
    new_template = TaskTemplate(
        name=data['name'],
        title=data['title'],
        description=data.get('description'),
        priority=Priority.MEDIUM,  # Default priority
        estimated_hours=data.get('estimated_hours'),
        acceptance_criteria=data.get('acceptance_criteria'),
        user_id=user_id,
        organization_id=current_user.organization_id
    )
    
    # Set priority if provided
    if 'priority' in data:
        try:
            new_template.priority = Priority[data['priority'].upper()]
        except (KeyError, AttributeError):
            return jsonify({'error': 'Invalid priority value'}), 400
    
    db.session.add(new_template)
    db.session.commit()
    
    return jsonify(new_template.to_dict()), 201

@tasks_bp.route('/templates/<int:id>', methods=['PUT'])
@jwt_required()
def update_task_template(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find template
    template = TaskTemplate.query.get(id)
    
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    # Check if user has access to this template (in same org)
    if current_user.organization_id != template.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if user owns the template
    if template.user_id != user_id:
        return jsonify({'error': 'You can only edit your own templates'}), 403
    
    data = request.get_json()
    
    # Update fields
    if 'name' in data and data['name'].strip():
        template.name = data['name']
    
    if 'title' in data and data['title'].strip():
        template.title = data['title']
    
    if 'description' in data:
        template.description = data['description']
    
    if 'priority' in data:
        try:
            template.priority = Priority[data['priority'].upper()]
        except (KeyError, AttributeError):
            return jsonify({'error': 'Invalid priority value'}), 400
    
    if 'estimated_hours' in data:
        template.estimated_hours = data['estimated_hours']
    
    if 'acceptance_criteria' in data:
        template.acceptance_criteria = data['acceptance_criteria']
    
    db.session.commit()
    
    return jsonify(template.to_dict()), 200

@tasks_bp.route('/templates/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_task_template(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find template
    template = TaskTemplate.query.get(id)
    
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    # Check if user has access to this template (in same org)
    if current_user.organization_id != template.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if user owns the template
    if template.user_id != user_id:
        return jsonify({'error': 'You can only delete your own templates'}), 403
    
    # Delete template
    db.session.delete(template)
    db.session.commit()
    
    return jsonify({'message': 'Template deleted successfully'}), 200

@tasks_bp.route('/templates/<int:id>/instantiate', methods=['POST'])
@jwt_required()
def instantiate_task_template(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find template
    template = TaskTemplate.query.get(id)
    
    if not template:
        return jsonify({'error': 'Template not found'}), 404
    
    # Check if user has access to this template (in same org)
    if current_user.organization_id != template.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Create task from template with optional overrides
    new_task = template.create_task(user_id, **data)
    
    db.session.add(new_task)
    db.session.commit()
    
    return jsonify(new_task.to_dict()), 201