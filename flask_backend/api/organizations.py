from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import db, User, Organization, Role

organizations_bp = Blueprint('organizations', __name__)

@organizations_bp.route('', methods=['GET'])
@jwt_required()
def get_organizations():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # If the user belongs to an organization, return it
    if current_user.organization_id:
        organization = Organization.query.get(current_user.organization_id)
        if organization:
            return jsonify([organization.to_dict()]), 200
    
    # If the user is a super admin or doesn't have an organization, return an empty list
    return jsonify([]), 200

@organizations_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_organization(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find organization
    organization = Organization.query.get(id)
    
    if not organization:
        return jsonify({'error': 'Organization not found'}), 404
    
    # Check if user has access to this organization
    if current_user.organization_id != id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify(organization.to_dict()), 200

@organizations_bp.route('', methods=['POST'])
@jwt_required()
def create_organization():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Check if user already belongs to an organization
    if current_user.organization_id:
        return jsonify({'error': 'User already belongs to an organization'}), 400
    
    data = request.get_json()
    
    # Validate required fields
    if 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400
    
    # Create new organization
    new_organization = Organization(
        name=data['name'],
        owner_id=user_id
    )
    
    db.session.add(new_organization)
    db.session.commit()
    
    # Update user's organization and role
    current_user.organization_id = new_organization.id
    current_user.role = Role.OWNER
    db.session.commit()
    
    return jsonify(new_organization.to_dict()), 201

@organizations_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_organization(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Check if user is an owner of this organization
    if current_user.organization_id != id or current_user.role != Role.OWNER:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Find organization
    organization = Organization.query.get(id)
    
    if not organization:
        return jsonify({'error': 'Organization not found'}), 404
    
    data = request.get_json()
    
    # Update name if provided
    if 'name' in data:
        organization.name = data['name']
    
    db.session.commit()
    
    return jsonify(organization.to_dict()), 200

@organizations_bp.route('/<int:id>/users', methods=['GET'])
@jwt_required()
def get_organization_users(id):
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Check if user has access to this organization
    if current_user.organization_id != id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get users from the organization
    users = User.query.filter_by(organization_id=id).all()
    
    return jsonify([user.to_dict() for user in users]), 200