from flask import Blueprint, request, jsonify
from utils.db import get_db

bp = Blueprint('project', __name__)

@bp.route('/', methods=['GET'])
def get_projects():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    db = get_db()
    projects = db.execute(
        'SELECT * FROM projects WHERE user_id = ? ORDER BY created_at DESC',
        (user_id,)
    ).fetchall()
    
    return jsonify([dict(project) for project in projects]), 200

@bp.route('/', methods=['POST'])
def create_project():
    data = request.get_json()
    user_id = data.get('user_id')
    name = data.get('name')
    description = data.get('description')
    color = data.get('color')
    
    if not user_id or not name:
        return jsonify({'error': 'User ID and project name are required'}), 400
    
    db = get_db()
    db.execute(
        'INSERT INTO projects (user_id, name, description, color) VALUES (?, ?, ?, ?)',
        (user_id, name, description, color)
    )
    db.commit()
    
    return jsonify({'message': 'Project created successfully'}), 201

@bp.route('/<int:project_id>', methods=['GET'])
def get_project(project_id):
    db = get_db()
    project = db.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    return jsonify(dict(project)), 200

@bp.route('/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    color = data.get('color')
    
    if not name:
        return jsonify({'error': 'Project name is required'}), 400
    
    db = get_db()
    db.execute(
        'UPDATE projects SET name = ?, description = ?, color = ? WHERE id = ?',
        (name, description, color, project_id)
    )
    db.commit()
    
    return jsonify({'message': 'Project updated successfully'}), 200

@bp.route('/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    db = get_db()
    db.execute('DELETE FROM projects WHERE id = ?', (project_id,))
    db.commit()
    
    return jsonify({'message': 'Project deleted successfully'}), 200