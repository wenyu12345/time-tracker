from flask import Blueprint, request, jsonify
from utils.db import get_db
from datetime import datetime
import requests

bp = Blueprint('user_config', __name__)

@bp.route('/<int:user_id>', methods=['GET'])
def get_user_config(user_id):
    """获取用户配置"""
    db = get_db()
    
    # 先确保用户配置存在
    db.execute('''
        INSERT OR IGNORE INTO user_configs (user_id, ai_chat_enabled, ai_can_modify_attendance, ai_can_view_attendance, ai_can_analyze_attendance, ai_can_search, ai_model)
        VALUES (?, 1, 0, 1, 1, 0, 'qwen3:latest')
    ''', (user_id,))
    db.commit()
    
    config = db.execute('SELECT * FROM user_configs WHERE user_id = ?', (user_id,)).fetchone()
    
    if not config:
        return jsonify({'error': 'Config not found'}), 404
    
    return jsonify(dict(config)), 200

@bp.route('/<int:user_id>', methods=['PUT'])
def update_user_config(user_id):
    """更新用户配置"""
    data = request.get_json()
    db = get_db()
    
    try:
        update_fields = []
        update_params = []
        
        if 'ai_chat_enabled' in data:
            update_fields.append('ai_chat_enabled = ?')
            update_params.append(bool(data['ai_chat_enabled']))
        if 'ai_can_modify_attendance' in data:
            update_fields.append('ai_can_modify_attendance = ?')
            update_params.append(bool(data['ai_can_modify_attendance']))
        if 'ai_can_view_attendance' in data:
            update_fields.append('ai_can_view_attendance = ?')
            update_params.append(bool(data['ai_can_view_attendance']))
        if 'ai_can_analyze_attendance' in data:
            update_fields.append('ai_can_analyze_attendance = ?')
            update_params.append(bool(data['ai_can_analyze_attendance']))
        if 'ai_can_search' in data:
            update_fields.append('ai_can_search = ?')
            update_params.append(bool(data['ai_can_search']))
        if 'ai_model' in data:
            update_fields.append('ai_model = ?')
            update_params.append(str(data['ai_model']))
        
        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400
        
        update_fields.append('updated_at = ?')
        update_params.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        update_params.append(user_id)
        
        query = f'UPDATE user_configs SET {", ".join(update_fields)} WHERE user_id = ?'
        db.execute(query, update_params)
        db.commit()
        
        # 获取更新后的配置
        config = db.execute('SELECT * FROM user_configs WHERE user_id = ?', (user_id,)).fetchone()
        return jsonify(dict(config)), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/ai-can-modify/<int:user_id>', methods=['GET'])
def check_ai_can_modify(user_id):
    """检查AI是否有权限修改用户考勤"""
    db = get_db()
    
    config = db.execute('SELECT ai_can_modify_attendance FROM user_configs WHERE user_id = ?', (user_id,)).fetchone()
    
    if not config:
        return jsonify({'can_modify': False}), 200
    
    return jsonify({'can_modify': bool(config['ai_can_modify_attendance'])}), 200

@bp.route('/available-models', methods=['GET'])
def get_available_models():
    """获取 Ollama 可用的模型列表"""
    try:
        response = requests.get('http://localhost:11434/v1/models', timeout=10)
        if response.status_code == 200:
            data = response.json()
            models = [model['id'] for model in data.get('data', [])]
            return jsonify({'models': models}), 200
        else:
            return jsonify({'models': ['qwen3:latest'], 'warning': '无法连接到 Ollama，使用默认模型'}), 200
    except Exception as e:
        return jsonify({'models': ['qwen3:latest'], 'warning': f'获取模型列表失败: {str(e)}'}), 200
