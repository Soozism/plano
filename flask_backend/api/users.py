from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import db, User, Role
import re

users_bp = Blueprint('users', __name__)

@users_bp.route('', methods=['GET'])
@jwt_required()
def get_users():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Only managers and owners can list all users
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get users from the same organization
    if not current_user.organization_id:
        return jsonify([]), 200
    
    # Query parameters
    search = request.args.get('search', '')
    role = request.args.get('role')
    
    # Build query
    query = User.query.filter_by(organization_id=current_user.organization_id)
    
    # Apply search if provided
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.name.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%'))
        )
    
    # Apply role filter if provided
    if role:
        try:
            role_enum = Role[role.upper()]
            query = query.filter_by(role=role_enum)
        except (KeyError, AttributeError):
            pass  # Invalid role, ignore filter
    
    # Get results
    users = query.all()
    
    return jsonify([user.to_dict() for user in users]), 200

@users_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_user(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find the requested user
    user = User.query.get(id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if the current user can access this user
    if user.organization_id != current_user.organization_id and current_user.id != id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify(user.to_dict()), 200

@users_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_user(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find the user to update
    user = User.query.get(id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check permissions: users can update their own profile, managers/owners can update any user in their org
    is_self = user_id == id
    is_manager = current_user.role in [Role.MANAGER, Role.OWNER]
    is_same_org = user.organization_id == current_user.organization_id
    
    if not (is_self or (is_manager and is_same_org)):
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Update fields that users can change themselves
    if 'name' in data:
        user.name = data['name']
    
    if 'email' in data and data['email'] != user.email:
        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user and existing_user.id != id:
            return jsonify({'error': 'Email already in use'}), 400
        
        user.email = data['email']
    
    # Fields that only managers/owners can change
    if is_manager and is_same_org:
        if 'role' in data and data['role'] in [r.value for r in Role]:
            # Only owners can assign owner role
            if data['role'] == Role.OWNER.value and current_user.role != Role.OWNER:
                return jsonify({'error': 'Only owners can assign owner role'}), 403
            
            user.role = Role[data['role'].upper()]
    
    db.session.commit()
    
    return jsonify(user.to_dict()), 200

@users_bp.route('/invite', methods=['POST'])
@jwt_required()
def invite_user():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Only managers and owners can invite users
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if user belongs to an organization
    if not current_user.organization_id:
        return jsonify({'error': 'You must belong to an organization to invite users'}), 400
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['username', 'name', 'email', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Validate email format
    if not re.match(r"[^@]+@[^@]+\.[^@]+", data['email']):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Check if username already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    # Check if email already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    # Get role (default to EMPLOYEE)
    role = Role.EMPLOYEE
    if 'role' in data and data['role'] in [r.value for r in Role]:
        # Only owners can assign owner role
        if data['role'] == Role.OWNER.value and current_user.role != Role.OWNER:
            return jsonify({'error': 'Only owners can assign owner role'}), 403
        
        role = Role[data['role'].upper()]
    
    # Create new user
    new_user = User(
        username=data['username'],
        name=data['name'],
        email=data['email'],
        role=role,
        organization_id=current_user.organization_id
    )
    
    # Set password
    new_user.set_password(data['password'])
    
    # Save to database
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify(new_user.to_dict()), 201