from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from ..models import db, User, Sprint, Task, StandupLog, Retrospective, BacklogItem, Epic, UserStory, TaskType, Role, Status, Priority

scrum_bp = Blueprint('scrum', __name__)

# Backlog Management
@scrum_bp.route('/backlog', methods=['GET'])
@jwt_required()
def get_backlog():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    if not current_user.organization_id:
        return jsonify([]), 200
    
    # Get backlog items for user's organization
    items = BacklogItem.query.filter_by(
        organization_id=current_user.organization_id
    ).order_by(BacklogItem.priority).all()
    
    return jsonify([item.to_dict() for item in items]), 200

@scrum_bp.route('/backlog', methods=['POST'])
@jwt_required()
def create_backlog_item():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    if not current_user.organization_id:
        return jsonify({'error': 'User is not part of an organization'}), 400
    
    # Only managers and owners can create backlog items
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['title', 'priority']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Get item type
    item_type = TaskType.TASK
    if 'type' in data:
        try:
            item_type = TaskType[data['type'].upper()]
        except KeyError:
            return jsonify({'error': 'Invalid type value'}), 400
    
    # Create new backlog item
    new_item = BacklogItem(
        title=data['title'],
        description=data.get('description'),
        priority=data['priority'],
        type=item_type,
        story_points=data.get('story_points'),
        organization_id=current_user.organization_id
    )
    
    db.session.add(new_item)
    db.session.commit()
    
    return jsonify(new_item.to_dict()), 201

@scrum_bp.route('/backlog/<int:id>', methods=['PUT'])
@jwt_required()
def update_backlog_item(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    if not current_user.organization_id:
        return jsonify({'error': 'User is not part of an organization'}), 400
    
    # Only managers and owners can update backlog items
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Find backlog item
    item = BacklogItem.query.get(id)
    
    if not item:
        return jsonify({'error': 'Backlog item not found'}), 404
    
    # Check if user has access to this item (in same org)
    if current_user.organization_id != item.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Update fields if provided
    if 'title' in data:
        item.title = data['title']
    
    if 'description' in data:
        item.description = data['description']
    
    if 'priority' in data:
        item.priority = data['priority']
    
    if 'type' in data:
        try:
            item.type = TaskType[data['type'].upper()]
        except KeyError:
            return jsonify({'error': 'Invalid type value'}), 400
    
    if 'story_points' in data:
        item.story_points = data['story_points']
    
    db.session.commit()
    
    return jsonify(item.to_dict()), 200

@scrum_bp.route('/backlog/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_backlog_item(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Only managers and owners can delete backlog items
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Find backlog item
    item = BacklogItem.query.get(id)
    
    if not item:
        return jsonify({'error': 'Backlog item not found'}), 404
    
    # Check if user has access to this item (in same org)
    if current_user.organization_id != item.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({'message': 'Backlog item deleted successfully'}), 200

@scrum_bp.route('/backlog/reorder', methods=['PUT'])
@jwt_required()
def reorder_backlog():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Only managers and owners can reorder backlog
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Validate data
    if 'items' not in data or not isinstance(data['items'], list):
        return jsonify({'error': 'Items array is required'}), 400
    
    # Update priorities
    for idx, item_data in enumerate(data['items']):
        if 'id' not in item_data:
            continue
            
        item = BacklogItem.query.get(item_data['id'])
        
        if item and item.organization_id == current_user.organization_id:
            item.priority = idx + 1
    
    db.session.commit()
    
    return jsonify({'message': 'Backlog reordered successfully'}), 200

# Epics and User Stories
@scrum_bp.route('/epics', methods=['GET'])
@jwt_required()
def get_epics():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    if not current_user.organization_id:
        return jsonify([]), 200
    
    # Get epics for user's organization
    epics = Epic.query.filter_by(
        organization_id=current_user.organization_id
    ).all()
    
    return jsonify([epic.to_dict() for epic in epics]), 200

@scrum_bp.route('/epics/<int:id>', methods=['GET'])
@jwt_required()
def get_epic(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find epic
    epic = Epic.query.get(id)
    
    if not epic:
        return jsonify({'error': 'Epic not found'}), 404
    
    # Check if user has access to this epic (in same org)
    if current_user.organization_id != epic.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get user stories for this epic
    stories = UserStory.query.filter_by(epic_id=id).all()
    
    result = epic.to_dict()
    result['user_stories'] = [story.to_dict() for story in stories]
    
    return jsonify(result), 200

@scrum_bp.route('/epics', methods=['POST'])
@jwt_required()
def create_epic():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    if not current_user.organization_id:
        return jsonify({'error': 'User is not part of an organization'}), 400
    
    # Only managers and owners can create epics
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    if 'title' not in data:
        return jsonify({'error': 'Title is required'}), 400
    
    # Create new epic
    new_epic = Epic(
        title=data['title'],
        description=data.get('description'),
        organization_id=current_user.organization_id
    )
    
    db.session.add(new_epic)
    db.session.commit()
    
    return jsonify(new_epic.to_dict()), 201

@scrum_bp.route('/user-stories', methods=['POST'])
@jwt_required()
def create_user_story():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Only managers and owners can create user stories
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['title', 'description']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # If epic_id is provided, validate it
    if 'epic_id' in data and data['epic_id']:
        epic = Epic.query.get(data['epic_id'])
        
        if not epic:
            return jsonify({'error': 'Epic not found'}), 404
            
        # Check if user has access to this epic (in same org)
        if current_user.organization_id != epic.organization_id:
            return jsonify({'error': 'Unauthorized'}), 403
    
    # Create new user story
    new_story = UserStory(
        title=data['title'],
        description=data['description'],
        epic_id=data.get('epic_id'),
        acceptance_criteria=data.get('acceptance_criteria'),
        story_points=data.get('story_points')
    )
    
    db.session.add(new_story)
    db.session.commit()
    
    return jsonify(new_story.to_dict()), 201

# Standup Logs
@scrum_bp.route('/standups', methods=['GET'])
@jwt_required()
def get_standups():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Get query parameters
    sprint_id = request.args.get('sprint_id', type=int)
    date_str = request.args.get('date')
    
    if not sprint_id:
        return jsonify({'error': 'Sprint ID is required'}), 400
    
    # Validate sprint
    sprint = Sprint.query.get(sprint_id)
    if not sprint:
        return jsonify({'error': 'Sprint not found'}), 404
    
    # Check if user has access to this sprint (in same org)
    if current_user.organization_id != sprint.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Parse date if provided, otherwise use today
    if date_str:
        try:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
    else:
        date = datetime.utcnow().date()
    
    # Build query
    query = StandupLog.query.filter_by(sprint_id=sprint_id)
    
    # If date is provided, filter by that date
    if date:
        # Find logs from the specific date
        query = query.filter(db.func.date(StandupLog.date) == date)
    
    # Get standup logs
    logs = query.all()
    
    return jsonify([log.to_dict() for log in logs]), 200

@scrum_bp.route('/standups', methods=['POST'])
@jwt_required()
def create_standup():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['sprint_id', 'yesterday', 'today']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Validate sprint
    sprint = Sprint.query.get(data['sprint_id'])
    if not sprint:
        return jsonify({'error': 'Sprint not found'}), 404
    
    # Check if user has access to this sprint (in same org)
    if current_user.organization_id != sprint.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if a standup already exists for today
    today = datetime.utcnow()
    existing = StandupLog.query.filter(
        StandupLog.user_id == user_id,
        StandupLog.sprint_id == data['sprint_id'],
        db.func.date(StandupLog.date) == today.date()
    ).first()
    
    if existing:
        return jsonify({'error': 'You have already submitted a standup log for today', 'log': existing.to_dict()}), 400
    
    # Create new standup log
    new_log = StandupLog(
        user_id=user_id,
        sprint_id=data['sprint_id'],
        date=today,
        yesterday=data['yesterday'],
        today=data['today'],
        blockers=data.get('blockers')
    )
    
    db.session.add(new_log)
    db.session.commit()
    
    return jsonify(new_log.to_dict()), 201

# Retrospectives
@scrum_bp.route('/retrospectives', methods=['GET'])
@jwt_required()
def get_retrospectives():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Get sprint ID from query parameters
    sprint_id = request.args.get('sprint_id', type=int)
    
    if not sprint_id:
        return jsonify({'error': 'Sprint ID is required'}), 400
    
    # Validate sprint
    sprint = Sprint.query.get(sprint_id)
    if not sprint:
        return jsonify({'error': 'Sprint not found'}), 404
    
    # Check if user has access to this sprint (in same org)
    if current_user.organization_id != sprint.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get all retrospectives for this sprint
    retros = Retrospective.query.filter_by(sprint_id=sprint_id).all()
    
    # Build response based on user's role
    results = []
    for retro in retros:
        # For anonymous retros, only show user info to managers/owners
        if retro.is_anonymous and current_user.role not in [Role.MANAGER, Role.OWNER]:
            retro_dict = retro.to_dict()
            retro_dict['user_id'] = None  # Hide user ID for anonymous entries
            results.append(retro_dict)
        else:
            results.append(retro.to_dict())
    
    return jsonify(results), 200

@scrum_bp.route('/retrospectives', methods=['POST'])
@jwt_required()
def create_retrospective():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    data = request.get_json()
    
    # Validate sprint_id is provided
    if 'sprint_id' not in data:
        return jsonify({'error': 'Sprint ID is required'}), 400
    
    # Validate sprint
    sprint = Sprint.query.get(data['sprint_id'])
    if not sprint:
        return jsonify({'error': 'Sprint not found'}), 404
    
    # Check if user has access to this sprint (in same org)
    if current_user.organization_id != sprint.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if user already submitted a retro for this sprint
    existing = Retrospective.query.filter_by(
        user_id=user_id,
        sprint_id=data['sprint_id']
    ).first()
    
    if existing:
        return jsonify({'error': 'You have already submitted a retrospective for this sprint', 'retro': existing.to_dict()}), 400
    
    # Create new retrospective
    new_retro = Retrospective(
        sprint_id=data['sprint_id'],
        user_id=user_id,
        went_well=data.get('went_well'),
        went_wrong=data.get('went_wrong'),
        action_items=data.get('action_items'),
        is_anonymous=data.get('is_anonymous', False)
    )
    
    db.session.add(new_retro)
    db.session.commit()
    
    return jsonify(new_retro.to_dict()), 201

@scrum_bp.route('/board', methods=['GET'])
@jwt_required()
def get_scrum_board():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Get sprint ID from query parameters
    sprint_id = request.args.get('sprint_id', type=int)
    
    if not sprint_id:
        return jsonify({'error': 'Sprint ID is required'}), 400
    
    # Validate sprint
    sprint = Sprint.query.get(sprint_id)
    if not sprint:
        return jsonify({'error': 'Sprint not found'}), 404
    
    # Check if user has access to this sprint (in same org)
    if current_user.organization_id != sprint.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get all tasks for this sprint
    tasks = Task.query.filter_by(sprint_id=sprint_id).all()
    
    # Group tasks by status
    board = {
        'todo': [],
        'in_progress': [],
        'done': []
    }
    
    for task in tasks:
        status_key = task.status.value
        board[status_key].append(task.to_dict())
    
    return jsonify(board), 200

def create_subtask(parent_task, data, user_id):
    """Create a subtask from the parent task data."""
    # Calculate story points proportion
    parent_points = parent_task.story_points or 0
    subtask_points = int(parent_points * data.get('story_points_ratio', 0.5))
    
    # Calculate estimated hours proportion
    parent_hours = parent_task.estimated_hours or 0
    subtask_hours = int(parent_hours * data.get('hours_ratio', 0.5))
    
    # Create new task
    new_task = Task(
        title=data['title'],
        description=data.get('description', ''),
        priority=data.get('priority', parent_task.priority),
        status=Status.TODO,
        story_points=subtask_points,
        estimated_hours=subtask_hours,
        acceptance_criteria=data.get('acceptance_criteria', ''),
        assignee_user_id=data.get('assignee_user_id'),
        assignee_group_id=data.get('assignee_group_id'),
        parent_task_id=parent_task.id,
        sprint_id=parent_task.sprint_id,
        organization_id=parent_task.organization_id,
        created_by_id=user_id
    )
    
    return new_task

@scrum_bp.route('/backlog/<int:item_id>/split', methods=['POST'])
@jwt_required()
def split_backlog_item(item_id):
    """Split a backlog item into smaller tasks."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find backlog item
    backlog_item = BacklogItem.query.get(item_id)
    
    if not backlog_item:
        return jsonify({'error': 'Backlog item not found'}), 404
    
    # Check if user has access to this backlog item
    if current_user.organization_id != backlog_item.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check permissions: only managers and owners can split backlog items
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    if 'subtasks' not in data or not isinstance(data['subtasks'], list):
        return jsonify({'error': 'Subtasks list is required'}), 400
    
    if not data['subtasks']:
        return jsonify({'error': 'At least one subtask is required'}), 400
    
    # Create parent task from backlog item
    parent_task = Task(
        title=backlog_item.title,
        description=backlog_item.description,
        priority=Priority(backlog_item.priority),
        status=Status.TODO,
        story_points=backlog_item.story_points,
        organization_id=backlog_item.organization_id,
        created_by_id=user_id
    )
    
    db.session.add(parent_task)
    
    # Create subtasks
    subtasks = []
    for subtask_data in data['subtasks']:
        if 'title' not in subtask_data:
            return jsonify({'error': 'Each subtask must have a title'}), 400
        
        subtask = create_subtask(parent_task, subtask_data, user_id)
        db.session.add(subtask)
        subtasks.append(subtask)
    
    # Delete the backlog item since it's now converted to tasks
    db.session.delete(backlog_item)
    db.session.commit()
    
    return jsonify({
        'message': 'Backlog item split successfully',
        'parent_task': parent_task.to_dict(),
        'subtasks': [subtask.to_dict() for subtask in subtasks]
    }), 201

@scrum_bp.route('/tasks/<int:task_id>/split', methods=['POST'])
@jwt_required()
def split_task(task_id):
    """Split an existing task into smaller subtasks."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find task
    parent_task = Task.query.get(task_id)
    
    if not parent_task:
        return jsonify({'error': 'Task not found'}), 404
    
    # Check if user has access to this task
    if current_user.organization_id != parent_task.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check permissions: only managers and owners can split tasks
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    if 'subtasks' not in data or not isinstance(data['subtasks'], list):
        return jsonify({'error': 'Subtasks list is required'}), 400
    
    if not data['subtasks']:
        return jsonify({'error': 'At least one subtask is required'}), 400
    
    # Create subtasks
    subtasks = []
    for subtask_data in data['subtasks']:
        if 'title' not in subtask_data:
            return jsonify({'error': 'Each subtask must have a title'}), 400
        
        subtask = create_subtask(parent_task, subtask_data, user_id)
        db.session.add(subtask)
        subtasks.append(subtask)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Task split successfully',
        'parent_task': parent_task.to_dict(),
        'subtasks': [subtask.to_dict() for subtask in subtasks]
    }), 201

@scrum_bp.route('/tasks/<int:task_id>/subtasks', methods=['GET'])
@jwt_required()
def get_subtasks(task_id):
    """Get all subtasks of a task."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find task
    parent_task = Task.query.get(task_id)
    
    if not parent_task:
        return jsonify({'error': 'Task not found'}), 404
    
    # Check if user has access to this task
    if current_user.organization_id != parent_task.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get subtasks
    subtasks = Task.query.filter_by(parent_task_id=task_id).all()
    
    return jsonify({
        'parent_task': parent_task.to_dict(),
        'subtasks': [subtask.to_dict() for subtask in subtasks]
    }), 200