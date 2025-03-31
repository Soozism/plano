from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import func
from ..models import db, User, AuditLog, Role

audit_bp = Blueprint('audit', __name__)

@audit_bp.route('/logs', methods=['GET'])
@jwt_required()
def get_audit_logs():
    """Get audit logs with filtering options."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Check permissions: only managers and owners can view audit logs
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get query parameters
    entity_type = request.args.get('entity_type')
    entity_id = request.args.get('entity_id', type=int)
    action = request.args.get('action')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    user_id = request.args.get('user_id', type=int)
    
    # Build query
    query = AuditLog.query
    
    # Apply filters
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditLog.entity_id == entity_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if start_date:
        query = query.filter(AuditLog.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(AuditLog.created_at <= datetime.fromisoformat(end_date))
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    # Get logs with pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    logs = query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'logs': [log.to_dict() for log in logs.items],
        'total': logs.total,
        'pages': logs.pages,
        'current_page': logs.page
    }), 200

@audit_bp.route('/logs/summary', methods=['GET'])
@jwt_required()
def get_audit_summary():
    """Get summary of audit logs."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Check permissions: only managers and owners can view audit logs
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get time range from query parameters
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get action counts
    action_counts = db.session.query(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.created_at >= start_date
    ).group_by(AuditLog.action).all()
    
    # Get entity type counts
    entity_counts = db.session.query(
        AuditLog.entity_type,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.created_at >= start_date
    ).group_by(AuditLog.entity_type).all()
    
    # Get user activity counts
    user_counts = db.session.query(
        User.name,
        func.count(AuditLog.id).label('count')
    ).join(AuditLog, AuditLog.user_id == User.id).filter(
        AuditLog.created_at >= start_date
    ).group_by(User.id, User.name).all()
    
    # Get daily activity counts
    daily_counts = db.session.query(
        func.date(AuditLog.created_at).label('date'),
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.created_at >= start_date
    ).group_by(func.date(AuditLog.created_at)).all()
    
    return jsonify({
        'action_counts': {action: count for action, count in action_counts},
        'entity_counts': {entity: count for entity, count in entity_counts},
        'user_counts': {name: count for name, count in user_counts},
        'daily_counts': {date.isoformat(): count for date, count in daily_counts}
    }), 200

@audit_bp.route('/logs/export', methods=['GET'])
@jwt_required()
def export_audit_logs():
    """Export audit logs to CSV."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Check permissions: only managers and owners can export audit logs
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Build query
    query = AuditLog.query
    
    # Apply date filters
    if start_date:
        query = query.filter(AuditLog.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(AuditLog.created_at <= datetime.fromisoformat(end_date))
    
    # Get all logs
    logs = query.order_by(AuditLog.created_at.desc()).all()
    
    # Convert to CSV format
    csv_data = []
    for log in logs:
        csv_data.append({
            'timestamp': log.created_at.isoformat(),
            'user': log.user.name,
            'action': log.action,
            'entity_type': log.entity_type,
            'entity_id': log.entity_id,
            'changes': str(log.changes),
            'ip_address': log.ip_address,
            'user_agent': log.user_agent
        })
    
    return jsonify({
        'logs': csv_data
    }), 200 