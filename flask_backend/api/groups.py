from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import db, User, Group, Role

groups_bp = Blueprint('groups', __name__)

@groups_bp.route('', methods=['GET'])
@jwt_required()
def get_groups():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Check if user belongs to an organization
    if not current_user.organization_id:
        return jsonify([]), 200
    
    # Get groups from the organization
    groups = Group.query.filter_by(organization_id=current_user.organization_id).all()
    
    return jsonify([group.to_dict() for group in groups]), 200

@groups_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_group(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find group
    group = Group.query.get(id)
    
    if not group:
        return jsonify({'error': 'Group not found'}), 404
    
    # Check if user has access to this group
    if current_user.organization_id != group.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify(group.to_dict()), 200

@groups_bp.route('', methods=['POST'])
@jwt_required()
def create_group():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Check if user belongs to an organization
    if not current_user.organization_id:
        return jsonify({'error': 'User is not part of an organization'}), 400
    
    # Check permissions: only managers and owners can create groups
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    if 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400
    
    # Create new group
    new_group = Group(
        name=data['name'],
        organization_id=current_user.organization_id
    )
    
    db.session.add(new_group)
    db.session.commit()
    
    return jsonify(new_group.to_dict()), 201

@groups_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_group(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find group
    group = Group.query.get(id)
    
    if not group:
        return jsonify({'error': 'Group not found'}), 404
    
    # Check if user has access to this group and has permissions
    if current_user.organization_id != group.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check permissions: only managers and owners can update groups
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Update name if provided
    if 'name' in data:
        group.name = data['name']
    
    db.session.commit()
    
    return jsonify(group.to_dict()), 200

@groups_bp.route('/<int:id>/members', methods=['GET'])
@jwt_required()
def get_group_members(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find group
    group = Group.query.get(id)
    
    if not group:
        return jsonify({'error': 'Group not found'}), 404
    
    # Check if user has access to this group
    if current_user.organization_id != group.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get members
    members = group.members
    
    return jsonify([member.to_dict() for member in members]), 200

@groups_bp.route('/<int:id>/members', methods=['POST'])
@jwt_required()
def add_member_to_group(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find group
    group = Group.query.get(id)
    
    if not group:
        return jsonify({'error': 'Group not found'}), 404
    
    # Check if user has access to this group and has permissions
    if current_user.organization_id != group.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check permissions: only managers and owners can add members
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    if 'user_id' not in data:
        return jsonify({'error': 'User ID is required'}), 400
    
    # Find user to add
    member = User.query.get(data['user_id'])
    
    if not member:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user belongs to the same organization
    if member.organization_id != current_user.organization_id:
        return jsonify({'error': 'User does not belong to the same organization'}), 400
    
    # Check if user is already a member
    if member in group.members:
        return jsonify({'error': 'User is already a member of this group'}), 400
    
    # Add user to group
    group.members.append(member)
    db.session.commit()
    
    return jsonify(group.to_dict()), 200

@groups_bp.route('/<int:id>/members/<int:user_id>', methods=['DELETE'])
@jwt_required()
def remove_member_from_group(id, user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Find group
    group = Group.query.get(id)
    
    if not group:
        return jsonify({'error': 'Group not found'}), 404
    
    # Check if current user has access to this group and has permissions
    if current_user.organization_id != group.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check permissions: only managers and owners can remove members
    if current_user.role not in [Role.MANAGER, Role.OWNER]:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Find user to remove
    member = User.query.get(user_id)
    
    if not member:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user is a member
    if member not in group.members:
        return jsonify({'error': 'User is not a member of this group'}), 400
    
    # Remove user from group
    group.members.remove(member)
    db.session.commit()
    
    return jsonify({'message': 'User removed from group successfully'}), 200