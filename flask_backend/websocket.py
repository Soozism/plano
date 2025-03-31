from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_jwt_extended import decode_token
from functools import wraps
from flask_sqlalchemy import SQLAlchemy

socketio = SocketIO()
db = SQLAlchemy()

def get_organization_id_from_token(token):
    """Extract organization_id from JWT token."""
    try:
        decoded = decode_token(token)
        return decoded.get('organization_id')
    except:
        return None

def authenticated_only(f):
    """Decorator to ensure socket connection is authenticated."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not request.sid:
            disconnect()
        return f(*args, **kwargs)
    return wrapped

@socketio.on('connect')
def handle_connect():
    """Handle client connection and join organization room."""
    token = request.args.get('token')
    if not token:
        return False
        
    organization_id = get_organization_id_from_token(token)
    if not organization_id:
        return False
        
    # Join organization-specific room
    join_room(f'organization_{organization_id}')
    return True

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    token = request.args.get('token')
    if token:
        organization_id = get_organization_id_from_token(token)
        if organization_id:
            leave_room(f'organization_{organization_id}')

def send_to_organization(organization_id, event, data):
    """Send data to all clients in an organization's room."""
    room = f'organization_{organization_id}'
    emit(event, data, room=room)

def broadcast_task_update(task_data):
    """Broadcast task update to organization members."""
    organization_id = task_data.get('organization_id')
    if organization_id:
        send_to_organization(organization_id, 'task_updated', task_data)

def broadcast_task_created(task_data):
    """Broadcast new task to organization members."""
    organization_id = task_data.get('organization_id')
    if organization_id:
        send_to_organization(organization_id, 'task_created', task_data)

def broadcast_task_deleted(task_id, organization_id):
    """Broadcast task deletion to organization members."""
    if organization_id:
        send_to_organization(organization_id, 'task_deleted', {'task_id': task_id})

def broadcast_milestone_update(task_id, milestone_data, organization_id):
    """Broadcast milestone update to organization members."""
    if organization_id:
        data = {
            'task_id': task_id,
            'milestone': milestone_data
        }
        send_to_organization(organization_id, 'milestone_updated', data)

def broadcast_comment_added(task_id, comment_data, organization_id):
    """Broadcast new comment to organization members."""
    if organization_id:
        data = {
            'task_id': task_id,
            'comment': comment_data
        }
        send_to_organization(organization_id, 'comment_added', data)

def broadcast_message(task_id, message_data, organization_id, is_update=False, is_deletion=False):
    """Broadcast message to organization members."""
    if organization_id:
        data = {
            'task_id': task_id,
            'message': message_data
        }
        
        if is_update:
            event = 'message_updated'
        elif is_deletion:
            event = 'message_deleted'
        else:
            event = 'message_added'
            
        send_to_organization(organization_id, event, data)

@socketio.on('join_task')
@authenticated_only
def handle_join_task(data):
    """Handle joining a task's chat room."""
    task_id = data.get('task_id')
    if not task_id:
        return False
        
    # Find task
    task = Task.query.get(task_id)
    if not task:
        return False
        
    # Check if user has access to this task (in same org)
    token = request.args.get('token')
    organization_id = get_organization_id_from_token(token)
    if organization_id != task.organization_id:
        return False
        
    # Join task-specific room
    join_room(f'task_{task_id}')
    return True

@socketio.on('leave_task')
@authenticated_only
def handle_leave_task(data):
    """Handle leaving a task's chat room."""
    task_id = data.get('task_id')
    if task_id:
        leave_room(f'task_{task_id}')
    return True

def broadcast_attachment_added(task_id, attachment_data, organization_id):
    """Broadcast new attachment to organization members."""
    if organization_id:
        data = {
            'task_id': task_id,
            'attachment': attachment_data
        }
        send_to_organization(organization_id, 'attachment_added', data)

def broadcast_attachment_deleted(task_id, attachment_id, organization_id):
    """Broadcast attachment deletion to organization members."""
    if organization_id:
        data = {
            'task_id': task_id,
            'attachment_id': attachment_id
        }
        send_to_organization(organization_id, 'attachment_deleted', data) 