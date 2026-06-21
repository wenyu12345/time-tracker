from flask import Blueprint, request, jsonify, send_file
from utils.backup import backup_database, restore_database, get_backup_list, delete_backup, auto_backup
from config import Config
import os

bp = Blueprint('backup', __name__)

@bp.route('/', methods=['GET'])
def create_backup():
    """创建数据库备份"""
    try:
        result = backup_database(Config.DATABASE)
        if result['success']:
            return jsonify({
                'message': '备份成功',
                'backup': result
            }), 200
        else:
            return jsonify({'error': result['error']}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/list', methods=['GET'])
def list_backups():
    """获取备份列表"""
    try:
        result = get_backup_list()
        if result['success']:
            return jsonify({
                'backups': result['backups']
            }), 200
        else:
            return jsonify({'error': result['error']}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<filename>', methods=['GET'])
def download_backup(filename):
    """下载备份文件"""
    try:
        backup_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups', filename)
        if os.path.exists(backup_path):
            return send_file(backup_path, as_attachment=True, download_name=filename)
        else:
            return jsonify({'error': '备份文件不存在'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/restore', methods=['POST'])
def restore_from_backup():
    """从备份恢复数据库"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': '备份文件名不能为空'}), 400
        
        backup_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups', filename)
        if not os.path.exists(backup_path):
            return jsonify({'error': '备份文件不存在'}), 404
        
        result = restore_database(Config.DATABASE, backup_path)
        if result['success']:
            return jsonify({
                'message': '恢复成功',
                'safety_backup': result.get('safety_backup')
            }), 200
        else:
            return jsonify({'error': result['error']}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<filename>', methods=['DELETE'])
def delete_backup_file(filename):
    """删除备份文件"""
    try:
        result = delete_backup(filename)
        if result['success']:
            return jsonify({'message': '删除成功'}), 200
        else:
            return jsonify({'error': result['error']}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<filename>/preview', methods=['GET'])
def preview_backup(filename):
    """预览备份文件内容"""
    try:
        backup_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups', filename)
        if os.path.exists(backup_path):
            with open(backup_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # 限制预览内容长度，避免过大的文件导致浏览器卡顿
            max_preview_length = 10000
            if len(content) > max_preview_length:
                content = content[:max_preview_length] + f"\n\n[内容过长，已截断，显示前{max_preview_length}个字符]"
            return jsonify({
                'content': content,
                'filename': filename,
                'total_length': len(content)
            }), 200
        else:
            return jsonify({'error': '备份文件不存在'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/auto', methods=['GET'])
def run_auto_backup():
    """执行自动备份"""
    try:
        result = auto_backup(Config.DATABASE)
        if result['success']:
            return jsonify({
                'message': '自动备份成功',
                'backup': result
            }), 200
        else:
            return jsonify({'error': result['error']}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
