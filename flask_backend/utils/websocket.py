from flask_socketio import emit, join_room, leave_room
from flask_jwt_extended import decode_token
from functools import wraps
from flask import request
from flask_backend.app import socketio
from flask_backend.models import User

# Dictionary to map user IDs to socket rooms
user_rooms = {}

def jwt_required_socket(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            emit('error', {'message': 'Authentication required'})
            return
        
        token = auth_header.split(' ')[1]
        
        try:
            # Decode token to get user ID
            decoded = decode_token(token)
            user_id = decoded['sub']
            
            # Add user ID to kwargs
            kwargs['user_id'] = user_id
            
            return f(*args, **kwargs)
        except Exception as e:
            emit('error', {'message': str(e)})
            return
    
    return decorated

def get_user_organization_room(user_id):
    """Get the organization room name for a user"""
    user = User.query.get(user_id)
    if user and user.organization_id:
        return f'org_{user.organization_id}'
    return None

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('message', {'message': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    # Clean up user rooms if socket ID is in user_rooms
    if request.sid in user_rooms:
        user_id = user_rooms[request.sid]
        org_room = get_user_organization_room(user_id)
        
        if org_room:
            leave_room(org_room)
        
        leave_room(f'user_{user_id}')
        del user_rooms[request.sid]

@socketio.on('authenticate')
@jwt_required_socket
def handle_authenticate(data, user_id):
    """Authenticate user and join rooms"""
    # Store user_id for this socket
    user_rooms[request.sid] = user_id
    
    # Join user's private room
    join_room(f'user_{user_id}')
    
    # Join organization room if user belongs to one
    org_room = get_user_organization_room(user_id)
    if org_room:
        join_room(org_room)
    
    emit('authenticated', {'user_id': user_id})

def send_to_user(user_id, event, data):
    """Send an event to a specific user"""
    socketio.emit(event, data, room=f'user_{user_id}')

def send_to_organization(organization_id, event, data):
    """Send an event to all users in an organization"""
    socketio.emit(event, data, room=f'org_{organization_id}')

def broadcast(event, data):
    """Send an event to all connected clients"""
    socketio.emit(event, data)