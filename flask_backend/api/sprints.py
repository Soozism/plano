from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from ..models import db, User, Sprint, Task, Subgoal, Role, Status
from sqlalchemy import func

sprints_bp = Blueprint('sprints', __name__)

def calculate_remaining_work(sprint_id, date):
    """Calculate remaining work for a sprint on a specific date."""
    # Get all tasks in the sprint
    tasks = Task.query.filter_by(sprint_id=sprint_id).all()
    
    # Calculate total remaining work
    remaining_work = 0
    for task in tasks:
        # Only count incomplete tasks
        if task.status not in [Status.DONE, Status.CANCELLED]:
            # Use story points if available, otherwise use estimated hours
            if task.story_points is not None:
                remaining_work += task.story_points
            elif task.estimated_hours is not None:
                remaining_work += task.estimated_hours
    
    return remaining_work

def calculate_ideal_burndown(sprint):
    """Calculate ideal burndown line points."""
    # Get total work at sprint start
    total_work = calculate_remaining_work(sprint.id, sprint.start_date)
    
    # Calculate daily reduction
    days = (sprint.end_date - sprint.start_date).days + 1
    daily_reduction = total_work / days if days > 0 else 0
    
    # Generate ideal burndown points
    ideal_points = []
    current_date = sprint.start_date
    remaining = total_work
    
    while current_date <= sprint.end_date:
        ideal_points.append({
            'date': current_date.isoformat(),
            'remaining_work': remaining,
            'is_ideal': True
        })
        remaining -= daily_reduction
        current_date += timedelta(days=1)
    
    return ideal_points

@sprints_bp.route('', methods=['GET'])
@jwt_required()
def get_sprints():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Check if user belongs to an organization
    if not current_user.organization_id:
        return jsonify([]), 200
    
    # Get sprints from the organization
    sprints = Sprint.query.filter_by(organization_id=current_user.organization_id).order_by(Sprint.start_date.desc()).all()
    
    return jsonify([sprint.to_dict() for sprint in sprints]), 200

@sprints_bp.route('/current', methods=['GET'])
@jwt_required()
def get_current_sprint():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Check if user belongs to an organization
    if not current_user.organization_id:
        return jsonify({'error': 'User is not part of an organization'}), 400
    
    # Find current sprint (where today is between start_date and end_date)
    now = datetime.utcnow()
    current_sprint = Sprint.query.filter(
        Sprint.organization_id == current_user.organization_id,
        Sprint.start_date <= now,
        Sprint.end_date >= now
    ).first()
    
    if not current_sprint:
        return jsonify({'error': 'No active sprint found'}), 404
    
    return jsonify(current_sprint.to_dict()), 200

@sprints_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_sprint(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find sprint
    sprint = Sprint.query.get(id)
    
    if not sprint:
        return jsonify({'error': 'Sprint not found'}), 404
    
    # Check if user has access to this sprint
    if current_user.organization_id != sprint.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get sprint details
    result = sprint.to_dict()
    
    # Get subgoals
    subgoals = Subgoal.query.filter_by(sprint_id=id).all()
    result['subgoals'] = [subgoal.to_dict() for subgoal in subgoals]
    
    return jsonify(result), 200

@sprints_bp.route('', methods=['POST'])
@jwt_required()
def create_sprint():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Check if user belongs to an organization
    if not current_user.organization_id:
        return jsonify({'error': 'User is not part of an organization'}), 400
    
    # Check permissions: only managers and owners can create sprints
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'start_date', 'end_date']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Parse dates
    try:
        start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
    except ValueError:
        return jsonify({'error': 'Invalid start_date format'}), 400
    
    try:
        end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
    except ValueError:
        return jsonify({'error': 'Invalid end_date format'}), 400
    
    # Validate dates
    if end_date <= start_date:
        return jsonify({'error': 'End date must be after start date'}), 400
    
    # Create new sprint
    new_sprint = Sprint(
        name=data['name'],
        goal=data.get('goal'),
        start_date=start_date,
        end_date=end_date,
        organization_id=current_user.organization_id
    )
    
    db.session.add(new_sprint)
    db.session.commit()
    
    # Add subgoals if provided
    if 'subgoals' in data and isinstance(data['subgoals'], list):
        for subgoal_data in data['subgoals']:
            if isinstance(subgoal_data, dict) and 'description' in subgoal_data:
                subgoal = Subgoal(
                    description=subgoal_data['description'],
                    sprint_id=new_sprint.id
                )
                db.session.add(subgoal)
        
        db.session.commit()
    
    return jsonify(new_sprint.to_dict()), 201

@sprints_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_sprint(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find sprint
    sprint = Sprint.query.get(id)
    
    if not sprint:
        return jsonify({'error': 'Sprint not found'}), 404
    
    # Check if user has access to this sprint and has permissions
    if current_user.organization_id != sprint.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check permissions: only managers and owners can update sprints
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Update fields
    if 'name' in data:
        sprint.name = data['name']
    
    if 'goal' in data:
        sprint.goal = data['goal']
    
    if 'start_date' in data:
        try:
            start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
            sprint.start_date = start_date
        except ValueError:
            return jsonify({'error': 'Invalid start_date format'}), 400
    
    if 'end_date' in data:
        try:
            end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
            sprint.end_date = end_date
        except ValueError:
            return jsonify({'error': 'Invalid end_date format'}), 400
    
    # Validate dates
    if sprint.end_date <= sprint.start_date:
        return jsonify({'error': 'End date must be after start date'}), 400
    
    db.session.commit()
    
    return jsonify(sprint.to_dict()), 200

@sprints_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_sprint(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find sprint
    sprint = Sprint.query.get(id)
    
    if not sprint:
        return jsonify({'error': 'Sprint not found'}), 404
    
    # Check if user has access to this sprint and has permissions
    if current_user.organization_id != sprint.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check permissions: only managers and owners can delete sprints
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if sprint has tasks
    tasks = Task.query.filter_by(sprint_id=id).count()
    if tasks > 0:
        return jsonify({'error': 'Cannot delete sprint with tasks. Please remove all tasks first.'}), 400
    
    # Delete subgoals
    Subgoal.query.filter_by(sprint_id=id).delete()
    
    # Delete sprint
    db.session.delete(sprint)
    db.session.commit()
    
    return jsonify({'message': 'Sprint deleted successfully'}), 200

@sprints_bp.route('/<int:id>/subgoals', methods=['GET'])
@jwt_required()
def get_sprint_subgoals(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find sprint
    sprint = Sprint.query.get(id)
    
    if not sprint:
        return jsonify({'error': 'Sprint not found'}), 404
    
    # Check if user has access to this sprint
    if current_user.organization_id != sprint.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get subgoals
    subgoals = Subgoal.query.filter_by(sprint_id=id).all()
    
    return jsonify([subgoal.to_dict() for subgoal in subgoals]), 200

@sprints_bp.route('/<int:id>/subgoals', methods=['POST'])
@jwt_required()
def add_subgoal(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find sprint
    sprint = Sprint.query.get(id)
    
    if not sprint:
        return jsonify({'error': 'Sprint not found'}), 404
    
    # Check if user has access to this sprint and has permissions
    if current_user.organization_id != sprint.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check permissions: only managers and owners can add subgoals
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    if 'description' not in data:
        return jsonify({'error': 'Description is required'}), 400
    
    # Create new subgoal
    new_subgoal = Subgoal(
        description=data['description'],
        sprint_id=id
    )
    
    db.session.add(new_subgoal)
    db.session.commit()
    
    return jsonify(new_subgoal.to_dict()), 201

@sprints_bp.route('/<int:id>/tasks', methods=['GET'])
@jwt_required()
def get_sprint_tasks(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find sprint
    sprint = Sprint.query.get(id)
    
    if not sprint:
        return jsonify({'error': 'Sprint not found'}), 404
    
    # Check if user has access to this sprint
    if current_user.organization_id != sprint.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get tasks
    tasks = Task.query.filter_by(sprint_id=id).all()
    
    # Get task stats
    task_count = len(tasks)
    completed_tasks = sum(1 for task in tasks if task.status == Status.DONE)
    total_story_points = sum(task.story_points or 0 for task in tasks)
    completed_story_points = sum((task.story_points or 0) for task in tasks if task.status == Status.DONE)
    
    # Create response
    response = {
        'tasks': [task.to_dict() for task in tasks],
        'stats': {
            'total_tasks': task_count,
            'completed_tasks': completed_tasks,
            'completion_percentage': round((completed_tasks / task_count) * 100 if task_count > 0 else 0, 1),
            'total_story_points': total_story_points,
            'completed_story_points': completed_story_points,
            'story_points_percentage': round((completed_story_points / total_story_points) * 100 if total_story_points > 0 else 0, 1)
        }
    }
    
    return jsonify(response), 200

@sprints_bp.route('/<int:id>/tasks', methods=['POST'])
@jwt_required()
def add_tasks_to_sprint(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find sprint
    sprint = Sprint.query.get(id)
    
    if not sprint:
        return jsonify({'error': 'Sprint not found'}), 404
    
    # Check if user has access to this sprint and has permissions
    if current_user.organization_id != sprint.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check permissions: only managers and owners can add tasks to sprints
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    if 'task_ids' not in data or not isinstance(data['task_ids'], list):
        return jsonify({'error': 'Task IDs are required'}), 400
    
    # Add tasks to sprint
    added_tasks = []
    for task_id in data['task_ids']:
        task = Task.query.get(task_id)
        if task and task.organization_id == current_user.organization_id:
            task.sprint_id = id
            added_tasks.append(task)
    
    db.session.commit()
    
    return jsonify({'message': f'{len(added_tasks)} tasks added to sprint'}), 200

@sprints_bp.route('/<int:id>/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def remove_task_from_sprint(id, task_id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find sprint
    sprint = Sprint.query.get(id)
    
    if not sprint:
        return jsonify({'error': 'Sprint not found'}), 404
    
    # Check if user has access to this sprint and has permissions
    if current_user.organization_id != sprint.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check permissions: only managers and owners can remove tasks from sprints
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Find task
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    # Check if task belongs to this sprint
    if task.sprint_id != id:
        return jsonify({'error': 'Task does not belong to this sprint'}), 400
    
    # Remove task from sprint
    task.sprint_id = None
    db.session.commit()
    
    return jsonify({'message': 'Task removed from sprint successfully'}), 200

@sprints_bp.route('/<int:sprint_id>/burndown', methods=['GET'])
@jwt_required()
def get_sprint_burndown(sprint_id):
    """Get burndown chart data for a sprint."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find sprint
    sprint = Sprint.query.get(sprint_id)
    
    if not sprint:
        return jsonify({'error': 'Sprint not found'}), 404
    
    # Check if user has access to this sprint (in same org)
    if current_user.organization_id != sprint.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get actual burndown points
    actual_points = []
    current_date = sprint.start_date
    
    while current_date <= sprint.end_date:
        remaining_work = calculate_remaining_work(sprint_id, current_date)
        actual_points.append({
            'date': current_date.isoformat(),
            'remaining_work': remaining_work,
            'is_ideal': False
        })
        current_date += timedelta(days=1)
    
    # Get ideal burndown points
    ideal_points = calculate_ideal_burndown(sprint)
    
    # Combine and sort points
    all_points = actual_points + ideal_points
    all_points.sort(key=lambda x: (x['date'], not x['is_ideal']))
    
    # Calculate sprint statistics
    total_work = calculate_remaining_work(sprint_id, sprint.start_date)
    completed_work = total_work - calculate_remaining_work(sprint_id, sprint.end_date)
    completion_percentage = (completed_work / total_work * 100) if total_work > 0 else 0
    
    return jsonify({
        'points': all_points,
        'statistics': {
            'total_work': total_work,
            'completed_work': completed_work,
            'completion_percentage': completion_percentage,
            'days_remaining': (sprint.end_date - datetime.utcnow()).days
        }
    }), 200

@sprints_bp.route('/<int:sprint_id>/velocity', methods=['GET'])
@jwt_required()
def get_sprint_velocity(sprint_id):
    """Get velocity metrics for a sprint."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find sprint
    sprint = Sprint.query.get(sprint_id)
    
    if not sprint:
        return jsonify({'error': 'Sprint not found'}), 404
    
    # Check if user has access to this sprint (in same org)
    if current_user.organization_id != sprint.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Calculate completed work
    completed_tasks = Task.query.filter(
        Task.sprint_id == sprint_id,
        Task.status.in_([Status.DONE, Status.CANCELLED])
    ).all()
    
    completed_story_points = sum(task.story_points or 0 for task in completed_tasks)
    completed_hours = sum(task.estimated_hours or 0 for task in completed_tasks)
    
    # Calculate velocity metrics
    days_elapsed = (datetime.utcnow() - sprint.start_date).days + 1
    daily_velocity = {
        'story_points': completed_story_points / days_elapsed if days_elapsed > 0 else 0,
        'hours': completed_hours / days_elapsed if days_elapsed > 0 else 0
    }
    
    return jsonify({
        'completed_work': {
            'story_points': completed_story_points,
            'hours': completed_hours
        },
        'daily_velocity': daily_velocity,
        'days_elapsed': days_elapsed
    }), 200

@sprints_bp.route('/<int:id>/complete', methods=['POST'])
@jwt_required()
def complete_sprint(id):
    """Complete a sprint and calculate its velocity."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find sprint
    sprint = Sprint.query.get(id)
    
    if not sprint:
        return jsonify({'error': 'Sprint not found'}), 404
    
    # Check if user has access to this sprint and has permissions
    if current_user.organization_id != sprint.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check permissions: only managers and owners can complete sprints
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if sprint is already completed
    if sprint.is_completed:
        return jsonify({'error': 'Sprint is already completed'}), 400
    
    # Complete sprint and calculate velocity
    sprint.complete()
    
    return jsonify({
        'message': 'Sprint completed successfully',
        'velocity': sprint.velocity
    }), 200

@sprints_bp.route('/velocity', methods=['GET'])
@jwt_required()
def get_organization_velocity():
    """Get velocity metrics for the organization's completed sprints."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Check if user belongs to an organization
    if not current_user.organization_id:
        return jsonify({'error': 'User is not part of an organization'}), 400
    
    # Get completed sprints
    completed_sprints = Sprint.query.filter(
        Sprint.organization_id == current_user.organization_id,
        Sprint.is_completed == True
    ).order_by(Sprint.end_date.desc()).all()
    
    # Calculate velocity metrics
    velocities = [sprint.velocity for sprint in completed_sprints if sprint.velocity is not None]
    avg_velocity = sum(velocities) / len(velocities) if velocities else 0
    
    # Get velocity trend
    velocity_trend = []
    for sprint in completed_sprints:
        if sprint.velocity is not None:
            velocity_trend.append({
                'sprint_id': sprint.id,
                'sprint_name': sprint.name,
                'end_date': sprint.end_date.isoformat(),
                'velocity': sprint.velocity,
                'planned_velocity': sprint.planned_velocity
            })
    
    return jsonify({
        'average_velocity': avg_velocity,
        'completed_sprints': len(completed_sprints),
        'velocity_trend': velocity_trend
    }), 200

@sprints_bp.route('/<int:id>/planned-velocity', methods=['PUT'])
@jwt_required()
def update_planned_velocity(id):
    """Update the planned velocity for a sprint."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find sprint
    sprint = Sprint.query.get(id)
    
    if not sprint:
        return jsonify({'error': 'Sprint not found'}), 404
    
    # Check if user has access to this sprint and has permissions
    if current_user.organization_id != sprint.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check permissions: only managers and owners can update planned velocity
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if sprint is already completed
    if sprint.is_completed:
        return jsonify({'error': 'Cannot update planned velocity for completed sprint'}), 400
    
    data = request.get_json()
    
    # Validate planned velocity
    if 'planned_velocity' not in data:
        return jsonify({'error': 'Planned velocity is required'}), 400
    
    try:
        planned_velocity = float(data['planned_velocity'])
        if planned_velocity < 0:
            return jsonify({'error': 'Planned velocity cannot be negative'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid planned velocity value'}), 400
    
    # Update planned velocity
    sprint.planned_velocity = planned_velocity
    db.session.commit()
    
    return jsonify({
        'message': 'Planned velocity updated successfully',
        'planned_velocity': sprint.planned_velocity
    }), 200