
"""任务提醒 API路由
"""
from flask import Blueprint, request, jsonify
import sys
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入钉钉机器人
from dingtalk_robot import send_task_to_dingtalk

task_reminder_bp = Blueprint('task_reminder', __name__)


@task_reminder_bp.route('/send', methods=['POST'])
def send_task_reminder():
    """发送任务提醒到钉钉
    
    请求体格式：
    {
        "title": "任务标题",
        "description": "任务描述（可选）",
        "date": "2026-05-17",
        "time": "09:00",
        "dingtalk_push": true,
        "parent_id": "xxx",
        "task_id": "xxx"
    }
    """
    try:
        logger.info('收到任务提醒请求')
        data = request.get_json()
        logger.info('请求数据: %s', data)
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空'
            }), 400
        
        # 检查是否启用钉钉推送
        if not data.get('dingtalk_push'):
            return jsonify({
                'success': True,
                'message': '钉钉推送未启用'
            })
        
        # 构建任务数据
        task_data = {
            'task_id': data.get('task_id', 'unknown'),
            'parent_id': data.get('parent_id'),
            'title': data.get('title', '无标题'),
            'date': data.get('date'),
            'time': data.get('time'),
            'status': 'pending'
        }
        
        # 添加可选字段
        if data.get('description'):
            task_data['description'] = data['description']
        if data.get('priority'):
            task_data['priority'] = data['priority']
        
        logger.info('准备发送钉钉消息，任务数据: %s', task_data)
        
        # 发送钉钉消息
        result = send_task_to_dingtalk(task_data)
        logger.info('钉钉消息发送结果: %s', result)
        
        return jsonify({
            'success': result.get('errcode') == 0,
            'result': result
        })
    except Exception as e:
        logger.error('发送任务提醒时发生异常: %s', str(e), exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

