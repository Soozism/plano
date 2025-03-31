from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from ..models import db, User, Event, Role

events_bp = Blueprint('events', __name__)

@events_bp.route('', methods=['GET'])
@jwt_required()
def get_events():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Check if user belongs to an organization
    if not current_user.organization_id:
        return jsonify([]), 200
    
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
    
    # Build query
    query = Event.query.filter_by(organization_id=current_user.organization_id)
    
    # Filter by date range
    if start_date:
        query = query.filter(Event.end_time >= start_date)
    
    if end_date:
        query = query.filter(Event.start_time <= end_date)
    
    # Filter out canceled events
    query = query.filter(Event.is_canceled == False)
    
    # Get events
    events = query.order_by(Event.start_time).all()
    
    return jsonify([event.to_dict() for event in events]), 200

@events_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_event(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find event
    event = Event.query.get(id)
    
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    # Check if user has access to this event
    if current_user.organization_id != event.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify(event.to_dict()), 200

@events_bp.route('', methods=['POST'])
@jwt_required()
def create_event():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Check if user belongs to an organization
    if not current_user.organization_id:
        return jsonify({'error': 'User is not part of an organization'}), 400
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['title', 'start_time', 'end_time']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Parse dates
    try:
        start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
    except ValueError:
        return jsonify({'error': 'Invalid start_time format'}), 400
    
    try:
        end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
    except ValueError:
        return jsonify({'error': 'Invalid end_time format'}), 400
    
    # Validate dates
    if end_time <= start_time:
        return jsonify({'error': 'End time must be after start time'}), 400
    
    # Create new event
    new_event = Event(
        title=data['title'],
        description=data.get('description'),
        start_time=start_time,
        end_time=end_time,
        organizer_id=user_id,
        organization_id=current_user.organization_id,
        series_id=data.get('series_id'),
        is_canceled=False
    )
    
    db.session.add(new_event)
    db.session.commit()
    
    # Add attendees if provided
    if 'attendee_ids' in data and isinstance(data['attendee_ids'], list):
        for attendee_id in data['attendee_ids']:
            attendee = User.query.get(attendee_id)
            if attendee and attendee.organization_id == current_user.organization_id:
                new_event.attendees.append(attendee)
        
        db.session.commit()
    
    return jsonify(new_event.to_dict()), 201

@events_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_event(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find event
    event = Event.query.get(id)
    
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    # Check if user has access to this event
    if current_user.organization_id != event.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if user is the organizer or has manager/owner role
    is_organizer = event.organizer_id == user_id
    is_manager = current_user.role in [Role.MANAGER, Role.OWNER]
    
    if not (is_organizer or is_manager):
        return jsonify({'error': 'Only the organizer or managers can update events'}), 403
    
    data = request.get_json()
    
    # Update fields
    if 'title' in data:
        event.title = data['title']
    
    if 'description' in data:
        event.description = data['description']
    
    if 'start_time' in data:
        try:
            start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
            event.start_time = start_time
        except ValueError:
            return jsonify({'error': 'Invalid start_time format'}), 400
    
    if 'end_time' in data:
        try:
            end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
            event.end_time = end_time
        except ValueError:
            return jsonify({'error': 'Invalid end_time format'}), 400
    
    # Validate dates
    if event.end_time <= event.start_time:
        return jsonify({'error': 'End time must be after start time'}), 400
    
    if 'is_canceled' in data:
        event.is_canceled = bool(data['is_canceled'])
    
    # Update organizer if provided
    if 'organizer_id' in data and is_manager:  # Only managers can change organizer
        organizer = User.query.get(data['organizer_id'])
        if not organizer or organizer.organization_id != current_user.organization_id:
            return jsonify({'error': 'Invalid organizer ID'}), 400
        
        event.organizer_id = data['organizer_id']
    
    db.session.commit()
    
    return jsonify(event.to_dict()), 200

@events_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_event(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find event
    event = Event.query.get(id)
    
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    # Check if user has access to this event
    if current_user.organization_id != event.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if user is the organizer or has manager/owner role
    is_organizer = event.organizer_id == user_id
    is_manager = current_user.role in [Role.MANAGER, Role.OWNER]
    
    if not (is_organizer or is_manager):
        return jsonify({'error': 'Only the organizer or managers can delete events'}), 403
    
    db.session.delete(event)
    db.session.commit()
    
    return jsonify({'message': 'Event deleted successfully'}), 200

@events_bp.route('/<int:id>/attendees', methods=['GET'])
@jwt_required()
def get_event_attendees(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find event
    event = Event.query.get(id)
    
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    # Check if user has access to this event
    if current_user.organization_id != event.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get attendees
    attendees = event.attendees
    
    return jsonify([attendee.to_dict() for attendee in attendees]), 200

@events_bp.route('/<int:id>/attendees', methods=['POST'])
@jwt_required()
def add_attendee(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find event
    event = Event.query.get(id)
    
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    # Check if user has access to this event
    if current_user.organization_id != event.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    if 'user_id' not in data:
        return jsonify({'error': 'User ID is required'}), 400
    
    # Find user to add
    attendee = User.query.get(data['user_id'])
    
    if not attendee:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user belongs to the same organization
    if attendee.organization_id != current_user.organization_id:
        return jsonify({'error': 'User does not belong to the same organization'}), 400
    
    # Check if user is already an attendee
    if attendee in event.attendees:
        return jsonify({'error': 'User is already an attendee of this event'}), 400
    
    # Add user to event
    event.attendees.append(attendee)
    db.session.commit()
    
    return jsonify(event.to_dict()), 200

@events_bp.route('/<int:id>/attendees/<int:user_id>', methods=['DELETE'])
@jwt_required()
def remove_attendee(id, user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Find event
    event = Event.query.get(id)
    
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    # Check if user has access to this event
    if current_user.organization_id != event.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Find user to remove
    attendee = User.query.get(user_id)
    
    if not attendee:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user is an attendee
    if attendee not in event.attendees:
        return jsonify({'error': 'User is not an attendee of this event'}), 400
    
    # Check if current user is the organizer, the attendee, or has manager/owner role
    is_organizer = event.organizer_id == current_user_id
    is_self = current_user_id == user_id
    is_manager = current_user.role in [Role.MANAGER, Role.OWNER]
    
    if not (is_organizer or is_self or is_manager):
        return jsonify({'error': 'Unauthorized to remove this attendee'}), 403
    
    # Remove user from event
    event.attendees.remove(attendee)
    db.session.commit()
    
    return jsonify({'message': 'Attendee removed from event successfully'}), 200