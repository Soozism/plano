from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from ..models import db, User, Task, TimeLog

time_tracking_bp = Blueprint('time_tracking', __name__)

@time_tracking_bp.route('/logs', methods=['GET'])
@jwt_required()
def get_time_logs():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    if not current_user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    user_id_param = request.args.get('user_id')
    task_id = request.args.get('task_id')
    
    # Parse dates
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid start_date format'}), 400
    
    if end_date_str:
        try:
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid end_date format'}), 400
    
    # Default to current week if no dates provided
    if not start_date and not end_date:
        today = datetime.utcnow().date()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        start_date = datetime.combine(start_of_week, datetime.min.time())
        end_date = datetime.combine(end_of_week, datetime.max.time())
    
    # Build query
    query = TimeLog.query
    
    # Filter by date range
    if start_date:
        query = query.filter(TimeLog.start_time >= start_date)
    
    if end_date:
        query = query.filter(TimeLog.start_time <= end_date)
    
    # Filter by user ID
    target_user_id = user_id_param if user_id_param else user_id
    query = query.filter_by(user_id=target_user_id)
    
    # Filter by task ID if provided
    if task_id:
        query = query.filter_by(task_id=task_id)
    
    # Get time logs
    time_logs = query.order_by(TimeLog.start_time.desc()).all()
    
    return jsonify([log.to_dict() for log in time_logs]), 200

@time_tracking_bp.route('/logs/<int:id>', methods=['GET'])
@jwt_required()
def get_time_log(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find time log
    time_log = TimeLog.query.get(id)
    
    if not time_log:
        return jsonify({'error': 'Time log not found'}), 404
    
    # Check if user has access to this log
    if time_log.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify(time_log.to_dict()), 200

@time_tracking_bp.route('/logs', methods=['POST'])
@jwt_required()
def create_time_log():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['task_id', 'start_time']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Check if task exists
    task = Task.query.get(data['task_id'])
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    # Check if user belongs to the same organization as the task
    if current_user.organization_id != task.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Parse dates
    try:
        start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
    except ValueError:
        return jsonify({'error': 'Invalid start_time format'}), 400
    
    end_time = None
    if 'end_time' in data and data['end_time']:
        try:
            end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid end_time format'}), 400
        
        # Ensure end_time is after start_time
        if end_time <= start_time:
            return jsonify({'error': 'End time must be after start time'}), 400
    
    # Calculate duration if end_time is provided
    duration = None
    if end_time:
        duration = int((end_time - start_time).total_seconds() / 60)  # Duration in minutes
    
    # Create new time log
    new_time_log = TimeLog(
        task_id=data['task_id'],
        user_id=user_id,
        start_time=start_time,
        end_time=end_time,
        duration=duration,
        description=data.get('description')
    )
    
    db.session.add(new_time_log)
    db.session.commit()
    
    return jsonify(new_time_log.to_dict()), 201

@time_tracking_bp.route('/logs/<int:id>', methods=['PUT'])
@jwt_required()
def update_time_log(id):
    user_id = get_jwt_identity()
    
    # Find time log
    time_log = TimeLog.query.get(id)
    
    if not time_log:
        return jsonify({'error': 'Time log not found'}), 404
    
    # Check if user has access to this log
    if time_log.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Update start_time if provided
    if 'start_time' in data:
        try:
            start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
            time_log.start_time = start_time
        except ValueError:
            return jsonify({'error': 'Invalid start_time format'}), 400
    
    # Update end_time if provided
    if 'end_time' in data:
        if data['end_time'] is None:
            time_log.end_time = None
            time_log.duration = None
        else:
            try:
                end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
                time_log.end_time = end_time
                
                # Ensure end_time is after start_time
                if end_time <= time_log.start_time:
                    return jsonify({'error': 'End time must be after start time'}), 400
                
                # Recalculate duration
                time_log.duration = int((end_time - time_log.start_time).total_seconds() / 60)
            except ValueError:
                return jsonify({'error': 'Invalid end_time format'}), 400
    
    # Update description if provided
    if 'description' in data:
        time_log.description = data['description']
    
    # Update task_id if provided
    if 'task_id' in data:
        # Check if task exists
        task = Task.query.get(data['task_id'])
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Check if user can access this task
        current_user = User.query.get(user_id)
        if current_user.organization_id != task.organization_id:
            return jsonify({'error': 'Unauthorized to log time for this task'}), 403
        
        time_log.task_id = data['task_id']
    
    db.session.commit()
    
    return jsonify(time_log.to_dict()), 200

@time_tracking_bp.route('/logs/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_time_log(id):
    user_id = get_jwt_identity()
    
    # Find time log
    time_log = TimeLog.query.get(id)
    
    if not time_log:
        return jsonify({'error': 'Time log not found'}), 404
    
    # Check if user has access to this log
    if time_log.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(time_log)
    db.session.commit()
    
    return jsonify({'message': 'Time log deleted successfully'}), 200

@time_tracking_bp.route('/timer/start', methods=['POST'])
@jwt_required()
def start_timer():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    data = request.get_json()
    
    # Validate task_id
    if 'task_id' not in data:
        return jsonify({'error': 'Task ID is required'}), 400
    
    # Check if task exists
    task = Task.query.get(data['task_id'])
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    # Check if user belongs to the same organization as the task
    if current_user.organization_id != task.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if user already has an active timer
    active_timer = TimeLog.query.filter_by(user_id=user_id, end_time=None).first()
    if active_timer:
        return jsonify({'error': 'User already has an active timer', 'active_timer': active_timer.to_dict()}), 400
    
    # Create new time log with start_time and no end_time
    now = datetime.utcnow()
    new_timer = TimeLog(
        task_id=data['task_id'],
        user_id=user_id,
        start_time=now,
        description=data.get('description')
    )
    
    db.session.add(new_timer)
    db.session.commit()
    
    return jsonify(new_timer.to_dict()), 201

@time_tracking_bp.route('/timer/stop', methods=['POST'])
@jwt_required()
def stop_timer():
    user_id = get_jwt_identity()
    
    # Find active timer
    active_timer = TimeLog.query.filter_by(user_id=user_id, end_time=None).first()
    
    if not active_timer:
        return jsonify({'error': 'No active timer found'}), 404
    
    # Set end_time and calculate duration
    now = datetime.utcnow()
    active_timer.end_time = now
    active_timer.duration = int((now - active_timer.start_time).total_seconds() / 60)
    
    # Update description if provided
    data = request.get_json()
    if data and 'description' in data:
        active_timer.description = data['description']
    
    db.session.commit()
    
    return jsonify(active_timer.to_dict()), 200

@time_tracking_bp.route('/timer/current', methods=['GET'])
@jwt_required()
def get_current_timer():
    user_id = get_jwt_identity()
    
    # Find active timer
    active_timer = TimeLog.query.filter_by(user_id=user_id, end_time=None).first()
    
    if not active_timer:
        return jsonify({'active': False}), 200
    
    result = active_timer.to_dict()
    result['active'] = True
    result['elapsed_seconds'] = int((datetime.utcnow() - active_timer.start_time).total_seconds())
    
    return jsonify(result), 200

@time_tracking_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_time_summary():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Get query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # Parse dates
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid start_date format'}), 400
    
    if end_date_str:
        try:
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid end_date format'}), 400
    
    # Default to current week if no dates provided
    if not start_date and not end_date:
        today = datetime.utcnow().date()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        start_date = datetime.combine(start_of_week, datetime.min.time())
        end_date = datetime.combine(end_of_week, datetime.max.time())
    
    # Build query for user's time logs
    query = TimeLog.query.filter_by(user_id=user_id)
    
    # Filter by date range
    if start_date:
        query = query.filter(TimeLog.start_time >= start_date)
    
    if end_date:
        query = query.filter(TimeLog.start_time <= end_date)
    
    # Get time logs
    time_logs = query.all()
    
    # Calculate total time spent
    total_minutes = sum(log.duration or 0 for log in time_logs)
    
    # Group by task
    task_totals = {}
    for log in time_logs:
        task_id = log.task_id
        if task_id not in task_totals:
            task = Task.query.get(task_id)
            task_totals[task_id] = {
                'task_id': task_id,
                'task_title': task.title if task else 'Unknown Task',
                'minutes': 0
            }
        task_totals[task_id]['minutes'] += log.duration or 0
    
    # Group by day
    day_totals = {}
    for log in time_logs:
        day = log.start_time.date().isoformat()
        if day not in day_totals:
            day_totals[day] = {
                'date': day,
                'minutes': 0
            }
        day_totals[day]['minutes'] += log.duration or 0
    
    result = {
        'total_minutes': total_minutes,
        'total_hours': round(total_minutes / 60, 1),
        'task_totals': list(task_totals.values()),
        'day_totals': list(day_totals.values())
    }
    
    return jsonify(result), 200