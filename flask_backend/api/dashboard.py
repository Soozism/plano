from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import func
from ..models import db, User, Task, Event, Timer, Status, Priority, Notification

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/personal', methods=['GET'])
@jwt_required()
def get_personal_dashboard():
    """Get personal dashboard data for the authenticated user."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Get active tasks
    active_tasks = Task.query.filter(
        Task.assignee_user_id == user_id,
        Task.status.in_([Status.TODO, Status.IN_PROGRESS])
    ).order_by(Task.priority.desc(), Task.due_date).all()
    
    # Get upcoming events (next 7 days)
    upcoming_events = Event.query.filter(
        Event.organization_id == current_user.organization_id,
        Event.start_date >= datetime.utcnow(),
        Event.start_date <= datetime.utcnow() + timedelta(days=7)
    ).order_by(Event.start_date).all()
    
    # Get active timers
    active_timers = Timer.query.filter(
        Timer.user_id == user_id,
        Timer.is_active == True
    ).all()
    
    # Calculate task statistics
    task_stats = db.session.query(
        func.count(Task.id).label('total_tasks'),
        func.sum(Task.estimated_hours).label('total_hours'),
        func.count(Task.id).filter(Task.status == Status.DONE).label('completed_tasks')
    ).filter(
        Task.assignee_user_id == user_id,
        Task.sprint_id.isnot(None)
    ).first()
    
    # Get sprint progress
    current_sprint = Task.query.filter(
        Task.assignee_user_id == user_id,
        Task.sprint_id.isnot(None),
        Task.status.in_([Status.TODO, Status.IN_PROGRESS])
    ).order_by(Task.sprint_id.desc()).first()
    
    sprint_progress = None
    if current_sprint and current_sprint.sprint:
        sprint_tasks = Task.query.filter_by(sprint_id=current_sprint.sprint_id).all()
        completed_tasks = [t for t in sprint_tasks if t.status == Status.DONE]
        sprint_progress = {
            'sprint_id': current_sprint.sprint_id,
            'sprint_name': current_sprint.sprint.name,
            'total_tasks': len(sprint_tasks),
            'completed_tasks': len(completed_tasks),
            'completion_percentage': (len(completed_tasks) / len(sprint_tasks) * 100) if sprint_tasks else 0
        }
    
    return jsonify({
        'active_tasks': [task.to_dict() for task in active_tasks],
        'upcoming_events': [event.to_dict() for event in upcoming_events],
        'active_timers': [timer.to_dict() for timer in active_timers],
        'task_statistics': {
            'total_tasks': task_stats.total_tasks or 0,
            'total_hours': task_stats.total_hours or 0,
            'completed_tasks': task_stats.completed_tasks or 0
        },
        'sprint_progress': sprint_progress
    }), 200

@dashboard_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get user's recent notifications."""
    user_id = get_jwt_identity()
    
    # Get recent notifications (last 24 hours)
    recent_notifications = Notification.query.filter(
        Notification.user_id == user_id,
        Notification.created_at >= datetime.utcnow() - timedelta(days=1)
    ).order_by(Notification.created_at.desc()).all()
    
    return jsonify({
        'notifications': [notification.to_dict() for notification in recent_notifications]
    }), 200 