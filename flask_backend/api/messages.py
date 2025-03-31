from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from ..models import db, User, Task, Message
from ..websocket import broadcast_message

messages_bp = Blueprint('messages', __name__)

@messages_bp.route('/tasks/<int:task_id>/messages', methods=['GET'])
@jwt_required()
def get_task_messages(task_id):
    """Get all messages for a specific task."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find task
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    # Check if user has access to this task (in same org)
    if current_user.organization_id != task.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get messages
    messages = Message.query.filter_by(task_id=task_id).order_by(Message.created_at).all()
    
    return jsonify([message.to_dict() for message in messages]), 200

@messages_bp.route('/tasks/<int:task_id>/messages', methods=['POST'])
@jwt_required()
def create_message(task_id):
    """Create a new message for a task."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find task
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    # Check if user has access to this task (in same org)
    if current_user.organization_id != task.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Validate content
    if 'content' not in data or not data['content'].strip():
        return jsonify({'error': 'Message content is required'}), 400
    
    # Create message
    new_message = Message(
        task_id=task_id,
        user_id=user_id,
        content=data['content']
    )
    
    db.session.add(new_message)
    db.session.commit()
    
    # Broadcast message
    broadcast_message(task_id, new_message.to_dict(), task.organization_id)
    
    return jsonify(new_message.to_dict()), 201

@messages_bp.route('/tasks/<int:task_id>/messages/<int:message_id>', methods=['PUT'])
@jwt_required()
def update_message(task_id, message_id):
    """Update an existing message."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find task and message
    task = Task.query.get(task_id)
    message = Message.query.get(message_id)
    
    if not task or not message:
        return jsonify({'error': 'Task or message not found'}), 404
    
    # Check if message belongs to task
    if message.task_id != task_id:
        return jsonify({'error': 'Message does not belong to this task'}), 400
    
    # Check if user has access to this task (in same org)
    if current_user.organization_id != task.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if user owns the message
    if message.user_id != user_id:
        return jsonify({'error': 'You can only edit your own messages'}), 403
    
    data = request.get_json()
    
    # Update content
    if 'content' in data and data['content'].strip():
        message.content = data['content']
    
    db.session.commit()
    
    # Broadcast message update
    broadcast_message(task_id, message.to_dict(), task.organization_id, is_update=True)
    
    return jsonify(message.to_dict()), 200

@messages_bp.route('/tasks/<int:task_id>/messages/<int:message_id>', methods=['DELETE'])
@jwt_required()
def delete_message(task_id, message_id):
    """Delete a message."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find task and message
    task = Task.query.get(task_id)
    message = Message.query.get(message_id)
    
    if not task or not message:
        return jsonify({'error': 'Task or message not found'}), 404
    
    # Check if message belongs to task
    if message.task_id != task_id:
        return jsonify({'error': 'Message does not belong to this task'}), 400
    
    # Check if user has access to this task (in same org)
    if current_user.organization_id != task.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if user owns the message or is a manager/owner
    is_owner = message.user_id == user_id
    is_manager = current_user.role in ['MANAGER', 'OWNER']
    
    if not (is_owner or is_manager):
        return jsonify({'error': 'You do not have permission to delete this message'}), 403
    
    # Store organization_id before deletion
    organization_id = task.organization_id
    
    # Delete message
    db.session.delete(message)
    db.session.commit()
    
    # Broadcast message deletion
    broadcast_message(task_id, {'id': message_id, 'deleted': True}, organization_id, is_deletion=True)
    
    return jsonify({'message': 'Message deleted successfully'}), 200 