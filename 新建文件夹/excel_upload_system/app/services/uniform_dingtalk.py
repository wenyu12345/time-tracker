#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
员工工装系统钉钉通知服务
"""

import os
import sys
import logging
from datetime import datetime

# 配置日志
logger = logging.getLogger(__name__)

# 添加项目根目录到路径，以便导入dingtalk_robot
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

try:
    # 尝试从app.services导入dingtalk_robot
    from app.services.dingtalk_robot import send_image_to_dingtalk
except ImportError:
    try:
        # 如果失败，尝试直接导入
        import sys
        sys.path.append(os.path.dirname(__file__))
        from dingtalk_robot import send_image_to_dingtalk
    except ImportError:
        # 如果都失败了，定义一个模拟函数
        logger.warning("无法导入钉钉机器人模块，将使用模拟函数")
        def send_dingtalk_message(content, message_type='text', title='@小艺 通知', webhook_url=None):
            return {
                'errcode': 0,
                'errmsg': '模拟发送成功',
                'message': '钉钉通知功能暂不可用，使用模拟模式'
            }

# 简化版本的发送函数，直接使用requests发送
def send_dingtalk_message(content, message_type='text', title='@小艺 通知', webhook_url=None):
    """
    简化版钉钉消息发送函数
    """
    import requests
    import json
    import sys
    import locale
    
    # 强制设置UTF-8编码（解决Windows环境编码问题）
    if sys.platform == 'win32':
        # Windows系统强制设置编码
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except:
            pass
    
    # 默认webhook地址
    if webhook_url is None:
        webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=96542078ec1e3ca21582ae18edeb6aedcfaf96bf3b4ec1f1f9ce98a2b6ba19a7"
    
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    
    # 强制处理内容编码问题
    try:
        # 如果content是字符串，确保它是正确的Unicode字符串
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='ignore')
        elif not isinstance(content, str):
            content = str(content)
        
        # 移除可能导致编码问题的特殊字符
        content = ''.join(char for char in content if ord(char) >= 32 or char in '\n\r\t')
    except:
        content = str(content)
    
    if message_type == 'text':
        data = {
            "msgtype": "text",
            "text": {"content": content}
        }
    else:
        data = {
            "msgtype": "text",
            "text": {"content": content}
        }
    
    try:
        # 减少超时时间，避免长时间阻塞
        logger.info(f"发送钉钉消息: {content[:50]}...")
        
        # 修复字符编码问题：确保JSON序列化时正确处理中文字符
        try:
            encoded_data = json.dumps(data, ensure_ascii=False)
        except UnicodeError:
            # 如果JSON序列化失败，使用ASCII fallback
            encoded_data = json.dumps(data, ensure_ascii=True, default=str)
        
        # 使用data参数并明确指定编码，而不是json参数
        try:
            encoded_bytes = encoded_data.encode('utf-8')
        except UnicodeEncodeError:
            # 如果UTF-8编码失败，使用ASCII fallback
            encoded_bytes = encoded_data.encode('ascii', errors='ignore')
        
        response = requests.post(webhook_url, headers=headers, data=encoded_bytes, timeout=10)
        result = response.json()
        logger.info(f"钉钉消息发送结果: {result}")
        return result
    except UnicodeEncodeError as e:
        error_msg = f"字符编码错误: {str(e)}"
        logger.error(error_msg)
        return {'errcode': -4, 'errmsg': error_msg}
    except requests.exceptions.Timeout:
        error_msg = "钉钉消息发送超时"
        logger.warning(error_msg)
        return {'errcode': -2, 'errmsg': error_msg}
    except requests.exceptions.RequestException as e:
        error_msg = f"钉钉消息网络错误: {str(e)}"
        logger.error(error_msg)
        return {'errcode': -3, 'errmsg': error_msg}
    except Exception as e:
        error_msg = f"发送钉钉消息失败: {str(e)}"
        logger.error(error_msg)
        return {'errcode': -1, 'errmsg': error_msg}

def send_uniform_issue_notification(employee_id, employee_name, uniform_type_name, quantity, issuer_name="赵恩辉"):
    """
    发送工装发放通知到钉钉群
    
    参数:
    - employee_id: 员工工号
    - employee_name: 员工姓名
    - uniform_type_name: 工装类型名称
    - quantity: 发放数量
    - issuer_name: 发放人姓名，默认为"赵恩辉"
    
    返回:
    - dict: 钉钉机器人返回的结果
    """
    
    try:
        # 构建通知消息，使用指定的模板格式（工装型号和数量中间加*）
        message = f"@小艺 恭喜{employee_name}（{employee_id}）获得{issuer_name}发放的{uniform_type_name}*{quantity}，祝你武德充沛，天下无敌"
        
        logger.info(f"准备发送工装发放通知: {message}")
        
        # 发送消息到钉钉群
        result = send_dingtalk_message(
            content=message,
            message_type='text',
            title=f'@小艺 工装发放通知'
        )
        
        logger.info(f"工装发放通知发送结果: {result}")
        
        # 返回发送结果
        return {
            'success': result.get('errcode') == 0,
            'message': '发送成功' if result.get('errcode') == 0 else f"发送失败: {result.get('errmsg', '未知错误')}",
            'dingtalk_result': result
        }
        
    except Exception as e:
        error_msg = f"发送工装发放通知异常: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg,
            'dingtalk_result': {'errcode': -1, 'errmsg': error_msg}
        }

def send_batch_uniform_issue_notification(issue_results, uniform_type_name, issuer_name="赵恩辉"):
    """
    批量发送工装发放通知到钉钉群
    
    参数:
    - issue_results: 发放结果列表，格式: [{'employee_id': 'xxx', 'employee_name': 'xxx', 'success': True/False}, ...]
    - uniform_type_name: 工装类型名称
    - issuer_name: 发放人姓名，默认为"赵恩辉"
    
    返回:
    - dict: 发送结果汇总
    """
    
    try:
        # 筛选成功的发放记录
        successful_issues = [result for result in issue_results if result.get('success', False)]
        
        if not successful_issues:
            logger.warning("没有成功的发放记录，跳过钉钉通知")
            return {
                'success': False,
                'message': '没有成功的发放记录',
                'sent_count': 0,
                'failed_count': 0
            }
        
        # 批量发送通知
        sent_count = 0
        failed_count = 0
        send_results = []
        
        for result in successful_issues:
            employee_id = result.get('employee_id', '')
            employee_name = result.get('employee_name', '')
            quantity = result.get('quantity', 1)
            
            if employee_id and employee_name:
                send_result = send_uniform_issue_notification(
                    employee_id=employee_id,
                    employee_name=employee_name,
                    uniform_type_name=uniform_type_name,
                    quantity=quantity,
                    issuer_name=issuer_name
                )
                
                send_results.append(send_result)
                
                if send_result['success']:
                    sent_count += 1
                else:
                    failed_count += 1
            else:
                failed_count += 1
                logger.warning(f"跳过无效的发放记录: {result}")
        
        logger.info(f"批量工装发放通知完成: 发送成功 {sent_count} 条，失败 {failed_count} 条")
        
        return {
            'success': failed_count == 0,
            'message': f'批量通知完成：成功 {sent_count} 条，失败 {failed_count} 条',
            'sent_count': sent_count,
            'failed_count': failed_count,
            'send_results': send_results
        }
        
    except Exception as e:
        error_msg = f"批量发送工装发放通知异常: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg,
            'sent_count': 0,
            'failed_count': len(issue_results)
        }