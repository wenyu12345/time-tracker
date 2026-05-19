import json
import os
from flask import Blueprint, render_template, jsonify, request

# 创建蓝图
template_manager_bp = Blueprint('template_manager', __name__)

# 模板配置文件路径
TEMPLATE_CONFIG_FILE = 'template_config.json'

# 默认模板配置
DEFAULT_TEMPLATES = {
    'honglian_title_template': '@小艺 红莲模式明细',
    'honglian_header_template': '**文件名:** {file_name}\n**操作:** {operation}\n**处理时间:** {datetime}\n**操作时间段:** {time_range}\n',
    'honglian_footer_template': '\n此消息由系统自动发送',
    'process_files_title_template': '@小艺 工艺文件推送',
    'process_files_header_template': '**文件名:** {file_name}\n**操作:** {operation}\n**处理时间:** {datetime}\n**数据条数:** {data_count}\n',
    'process_files_footer_template': '\n此消息由系统自动发送'
}

def load_template_config():
    """加载模板配置"""
    try:
        if os.path.exists(TEMPLATE_CONFIG_FILE):
            with open(TEMPLATE_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"加载模板配置失败: {e}")
        return {}

def save_template_config(config):
    """保存模板配置"""
    try:
        with open(TEMPLATE_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存模板配置失败: {e}")
        return False

@template_manager_bp.route('/', methods=['GET'])
def template_manager():
    """模板管理页面"""
    return render_template('template_manager.html')

@template_manager_bp.route('/api/templates', methods=['GET'])
def get_templates():
    """获取所有模板配置"""
    config = load_template_config()
    return jsonify({
        'success': True,
        'data': config
    })

@template_manager_bp.route('/api/templates', methods=['POST'])
def update_template():
    """更新模板配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据为空'
            })
        
        # 保存配置
        if save_template_config(data):
            return jsonify({
                'success': True,
                'message': '模板配置保存成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '保存配置失败'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新模板失败: {str(e)}'
        })

@template_manager_bp.route('/api/templates/reset', methods=['POST'])
def reset_templates():
    """重置为默认模板"""
    try:
        if save_template_config(DEFAULT_TEMPLATES):
            return jsonify({
                'success': True,
                'message': '已重置为默认模板',
                'data': DEFAULT_TEMPLATES
            })
        else:
            return jsonify({
                'success': False,
                'message': '重置模板失败'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'重置模板失败: {str(e)}'
        })

# 全局变量，用于缓存模板配置
template_config_cache = None

def get_template_config():
    """获取模板配置（带缓存）"""
    global template_config_cache
    if template_config_cache is None:
        template_config_cache = load_template_config()
    return template_config_cache or {}