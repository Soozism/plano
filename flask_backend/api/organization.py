from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from ..models import db, User, Task, Event, Timer, Status, Priority, Organization, Role

org_bp = Blueprint('organization', __name__)

@org_bp.route('/analytics/tasks', methods=['GET'])
@jwt_required()
def get_task_analytics():
    """Get task analytics for the organization."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Check permissions
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get date range from query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Build base query
    query = Task.query.filter_by(organization_id=current_user.organization_id)
    
    # Apply date filters if provided
    if start_date:
        query = query.filter(Task.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Task.created_at <= datetime.fromisoformat(end_date))
    
    # Get task statistics
    stats = db.session.query(
        func.count(Task.id).label('total_tasks'),
        func.count(Task.id).filter(Task.status == Status.DONE).label('completed_tasks'),
        func.sum(Task.estimated_hours).label('total_hours'),
        func.sum(Task.actual_hours).label('actual_hours'),
        func.avg(Task.estimated_hours).label('avg_estimated_hours'),
        func.avg(Task.actual_hours).label('avg_actual_hours')
    ).filter(
        Task.organization_id == current_user.organization_id
    ).first()
    
    # Get tasks by status
    status_counts = db.session.query(
        Task.status,
        func.count(Task.id).label('count')
    ).filter(
        Task.organization_id == current_user.organization_id
    ).group_by(Task.status).all()
    
    # Get tasks by priority
    priority_counts = db.session.query(
        Task.priority,
        func.count(Task.id).label('count')
    ).filter(
        Task.organization_id == current_user.organization_id
    ).group_by(Task.priority).all()
    
    # Get tasks by assignee
    assignee_counts = db.session.query(
        User.name,
        func.count(Task.id).label('count')
    ).join(Task, Task.assignee_user_id == User.id).filter(
        Task.organization_id == current_user.organization_id
    ).group_by(User.id, User.name).all()
    
    return jsonify({
        'statistics': {
            'total_tasks': stats.total_tasks or 0,
            'completed_tasks': stats.completed_tasks or 0,
            'total_hours': stats.total_hours or 0,
            'actual_hours': stats.actual_hours or 0,
            'avg_estimated_hours': float(stats.avg_estimated_hours or 0),
            'avg_actual_hours': float(stats.avg_actual_hours or 0),
            'completion_rate': (stats.completed_tasks / stats.total_tasks * 100) if stats.total_tasks else 0
        },
        'by_status': {status.value: count for status, count in status_counts},
        'by_priority': {priority.value: count for priority, count in priority_counts},
        'by_assignee': {name: count for name, count in assignee_counts}
    }), 200

@org_bp.route('/analytics/velocity', methods=['GET'])
@jwt_required()
def get_velocity_analytics():
    """Get velocity analytics for the organization."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Check permissions
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get completed sprints
    completed_sprints = Sprint.query.filter(
        Sprint.organization_id == current_user.organization_id,
        Sprint.is_completed == True
    ).order_by(Sprint.end_date.desc()).all()
    
    # Calculate velocity metrics
    velocities = []
    for sprint in completed_sprints:
        completed_tasks = Task.query.filter(
            Task.sprint_id == sprint.id,
            Task.status == Status.DONE
        ).all()
        
        total_story_points = sum(task.story_points or 0 for task in completed_tasks)
        total_hours = sum(task.actual_hours or 0 for task in completed_tasks)
        
        velocities.append({
            'sprint_id': sprint.id,
            'sprint_name': sprint.name,
            'end_date': sprint.end_date.isoformat(),
            'story_points': total_story_points,
            'hours': total_hours,
            'planned_velocity': sprint.planned_velocity
        })
    
    # Calculate average velocity
    if velocities:
        avg_story_points = sum(v['story_points'] for v in velocities) / len(velocities)
        avg_hours = sum(v['hours'] for v in velocities) / len(velocities)
    else:
        avg_story_points = 0
        avg_hours = 0
    
    return jsonify({
        'sprint_velocities': velocities,
        'average_velocity': {
            'story_points': avg_story_points,
            'hours': avg_hours
        }
    }), 200

@org_bp.route('/analytics/team', methods=['GET'])
@jwt_required()
def get_team_analytics():
    """Get team performance analytics."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Check permissions
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get team members
    team_members = User.query.filter_by(
        organization_id=current_user.organization_id
    ).all()
    
    # Calculate metrics for each team member
    team_metrics = []
    for member in team_members:
        # Get completed tasks
        completed_tasks = Task.query.filter(
            Task.assignee_user_id == member.id,
            Task.status == Status.DONE
        ).all()
        
        # Calculate metrics
        total_story_points = sum(task.story_points or 0 for task in completed_tasks)
        total_hours = sum(task.actual_hours or 0 for task in completed_tasks)
        active_tasks = Task.query.filter(
            Task.assignee_user_id == member.id,
            Task.status.in_([Status.TODO, Status.IN_PROGRESS])
        ).count()
        
        team_metrics.append({
            'user_id': member.id,
            'name': member.name,
            'role': member.role.value,
            'completed_tasks': len(completed_tasks),
            'total_story_points': total_story_points,
            'total_hours': total_hours,
            'active_tasks': active_tasks
        })
    
    return jsonify({
        'team_metrics': team_metrics
    }), 200 