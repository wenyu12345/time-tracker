#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板管理路由模块
用于管理钉钉消息模板，支持A732型号等特殊格式的配置
"""

from flask import Blueprint, request, jsonify, render_template
import json
import os
from datetime import datetime
import logging

# 配置日志
logger = logging.getLogger(__name__)

template_manager_bp = Blueprint('template_manager', __name__)

# 模板配置文件路径
TEMPLATE_CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'template_config.json')

def load_template_config():
    """加载模板配置"""
    try:
        if os.path.exists(TEMPLATE_CONFIG_FILE):
            with open(TEMPLATE_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 默认配置
            return {
                'a732_template': {
                    'enabled': True,
                    'format': '【{count}】{prefix} {suffixes}, {total_weight}kg',
                    'description': 'A732型号批号显示格式',
                    'example': '【7】466TCMK16J06 1_1  1_2  2_1  2_2  3_1  3_2  4_1, 1164.0kg'
                },
                'general_template': {
                    'enabled': True,
                    'format': '{batch_display}, {weight_str}',
                    'description': '通用批号显示格式'
                }
            }
    except Exception as e:
        logger.error(f"加载模板配置失败: {e}")
        return {}

def save_template_config(config):
    """保存模板配置"""
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(TEMPLATE_CONFIG_FILE), exist_ok=True)
        
        with open(TEMPLATE_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        logger.info("模板配置保存成功")
        return True
    except Exception as e:
        logger.error(f"保存模板配置失败: {e}")
        return False

@template_manager_bp.route('/template-manager')
def template_manager():
    """模板管理页面"""
    return render_template('template_manager.html')

@template_manager_bp.route('/api/templates', methods=['GET'])
def get_templates():
    """获取所有模板配置"""
    try:
        config = load_template_config()
        return jsonify({
            'success': True,
            'data': config,
            'message': '模板配置获取成功'
        })
    except Exception as e:
        logger.error(f"获取模板配置失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取模板配置失败: {str(e)}'
        }), 500

@template_manager_bp.route('/api/templates/<template_name>', methods=['GET'])
def get_template(template_name):
    """获取指定模板配置"""
    try:
        config = load_template_config()
        if template_name in config:
            return jsonify({
                'success': True,
                'data': config[template_name],
                'message': '模板配置获取成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '模板不存在'
            }), 404
    except Exception as e:
        logger.error(f"获取模板配置失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取模板配置失败: {str(e)}'
        }), 500

@template_manager_bp.route('/api/templates/<template_name>', methods=['POST'])
def update_template(template_name):
    """更新模板配置"""
    try:
        config = load_template_config()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 验证必需字段
        required_fields = ['enabled', 'format', 'description']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'缺少必需字段: {field}'
                }), 400
        
        # 更新模板配置
        config[template_name] = {
            'enabled': data['enabled'],
            'format': data['format'],
            'description': data['description'],
            'example': data.get('example', ''),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 保存配置
        if save_template_config(config):
            return jsonify({
                'success': True,
                'message': '模板配置更新成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '模板配置保存失败'
            }), 500
            
    except Exception as e:
        logger.error(f"更新模板配置失败: {e}")
        return jsonify({
            'success': False,
            'message': f'更新模板配置失败: {str(e)}'
        }), 500

@template_manager_bp.route('/api/templates/<template_name>/toggle', methods=['POST'])
def toggle_template(template_name):
    """启用/禁用模板"""
    try:
        config = load_template_config()
        
        if template_name not in config:
            return jsonify({
                'success': False,
                'message': '模板不存在'
            }), 404
        
        # 切换启用状态
        config[template_name]['enabled'] = not config[template_name].get('enabled', True)
        config[template_name]['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 保存配置
        if save_template_config(config):
            status = '启用' if config[template_name]['enabled'] else '禁用'
            return jsonify({
                'success': True,
                'message': f'模板已{status}',
                'data': {'enabled': config[template_name]['enabled']}
            })
        else:
            return jsonify({
                'success': False,
                'message': '模板配置保存失败'
            }), 500
            
    except Exception as e:
        logger.error(f"切换模板状态失败: {e}")
        return jsonify({
            'success': False,
            'message': f'切换模板状态失败: {str(e)}'
        }), 500

@template_manager_bp.route('/api/templates/reset', methods=['POST'])
def reset_templates():
    """重置所有模板为默认配置"""
    try:
        # 默认配置
        default_config = {
            'a732_template': {
                'enabled': True,
                'format': '【{count}】{prefix} {suffixes}, {total_weight}kg',
                'description': 'A732型号批号显示格式',
                'example': '【7】466TCMK16J06 1_1  1_2  2_1  2_2  3_1  3_2  4_1, 1164.0kg'
            },
            'general_template': {
                'enabled': True,
                'format': '{batch_display}, {weight_str}',
                'description': '通用批号显示格式'
            }
        }
        
        # 保存默认配置
        if save_template_config(default_config):
            return jsonify({
                'success': True,
                'message': '模板配置已重置为默认值'
            })
        else:
            return jsonify({
                'success': False,
                'message': '模板配置重置失败'
            }), 500
            
    except Exception as e:
        logger.error(f"重置模板配置失败: {e}")
        return jsonify({
            'success': False,
            'message': f'重置模板配置失败: {str(e)}'
        }), 500