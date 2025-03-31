from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from ..models import db, User, Task, Event, Attachment
from ..websocket import broadcast_attachment_added, broadcast_attachment_deleted

attachments_bp = Blueprint('attachments', __name__)

ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx',
    'ppt', 'pptx', 'zip', 'rar', 'csv', 'json', 'xml', 'md'
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_s3_key(organization_id, task_id, filename):
    """Generate a unique S3 key for the file."""
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    return f'organizations/{organization_id}/tasks/{task_id}/{timestamp}_{filename}'

@attachments_bp.route('/tasks/<int:task_id>/attachments', methods=['GET'])
@jwt_required()
def get_task_attachments(task_id):
    """Get all attachments for a task."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find task
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    # Check if user has access to this task (in same org)
    if current_user.organization_id != task.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get attachments
    attachments = Attachment.query.filter_by(task_id=task_id).all()
    
    # Generate presigned URLs for each attachment
    for attachment in attachments:
        attachment_dict = attachment.to_dict()
        attachment_dict['download_url'] = Attachment.generate_presigned_url(attachment.file_url)
    
    return jsonify([attachment.to_dict() for attachment in attachments]), 200

@attachments_bp.route('/tasks/<int:task_id>/attachments', methods=['POST'])
@jwt_required()
def upload_task_attachment(task_id):
    """Upload a file attachment for a task."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find task
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    # Check if user has access to this task (in same org)
    if current_user.organization_id != task.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if file was uploaded
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    # Check if file name is empty
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check if file type is allowed
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return jsonify({'error': 'File too large'}), 400
    
    # Secure the filename
    filename = secure_filename(file.filename)
    
    # Generate S3 key
    s3_key = generate_s3_key(task.organization_id, task_id, filename)
    
    try:
        # Upload to S3
        s3_client.upload_fileobj(
            file,
            current_app.config['AWS_S3_BUCKET'],
            s3_key,
            ExtraArgs={'ContentType': file.content_type}
        )
        
        # Create attachment record
        attachment = Attachment(
            file_name=filename,
            file_url=f"https://{current_app.config['AWS_S3_BUCKET']}.s3.amazonaws.com/{s3_key}",
            file_type=file.content_type,
            file_size=file_size,
            task_id=task_id,
            uploaded_by_id=user_id,
            organization_id=task.organization_id
        )
        
        db.session.add(attachment)
        db.session.commit()
        
        # Generate presigned URL for immediate download
        attachment_dict = attachment.to_dict()
        attachment_dict['download_url'] = Attachment.generate_presigned_url(attachment.file_url)
        
        # Broadcast attachment
        broadcast_attachment_added(task_id, attachment_dict, task.organization_id)
        
        return jsonify(attachment_dict), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attachments_bp.route('/tasks/<int:task_id>/attachments/<int:attachment_id>', methods=['DELETE'])
@jwt_required()
def delete_task_attachment(task_id, attachment_id):
    """Delete a task attachment."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find task and attachment
    task = Task.query.get(task_id)
    attachment = Attachment.query.get(attachment_id)
    
    if not task or not attachment:
        return jsonify({'error': 'Task or attachment not found'}), 404
    
    # Check if attachment belongs to task
    if attachment.task_id != task_id:
        return jsonify({'error': 'Attachment does not belong to this task'}), 400
    
    # Check if user has access to this task (in same org)
    if current_user.organization_id != task.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if user owns the attachment or is a manager/owner
    is_owner = attachment.uploaded_by_id == user_id
    is_manager = current_user.role in ['MANAGER', 'OWNER']
    
    if not (is_owner or is_manager):
        return jsonify({'error': 'You do not have permission to delete this attachment'}), 403
    
    # Store organization_id before deletion
    organization_id = task.organization_id
    
    # Delete from S3
    if not attachment.delete_from_s3():
        return jsonify({'error': 'Failed to delete file from storage'}), 500
    
    # Delete from database
    db.session.delete(attachment)
    db.session.commit()
    
    # Broadcast deletion
    broadcast_attachment_deleted(task_id, attachment_id, organization_id)
    
    return jsonify({'message': 'Attachment deleted successfully'}), 200

@attachments_bp.route('/tasks/<int:task_id>/attachments/<int:attachment_id>/download', methods=['GET'])
@jwt_required()
def download_task_attachment(task_id, attachment_id):
    """Get a presigned URL for downloading an attachment."""
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # Find task and attachment
    task = Task.query.get(task_id)
    attachment = Attachment.query.get(attachment_id)
    
    if not task or not attachment:
        return jsonify({'error': 'Task or attachment not found'}), 404
    
    # Check if attachment belongs to task
    if attachment.task_id != task_id:
        return jsonify({'error': 'Attachment does not belong to this task'}), 400
    
    # Check if user has access to this task (in same org)
    if current_user.organization_id != task.organization_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Generate presigned URL
    download_url = Attachment.generate_presigned_url(attachment.file_url)
    
    if not download_url:
        return jsonify({'error': 'Failed to generate download URL'}), 500
    
    return jsonify({'download_url': download_url}), 200 