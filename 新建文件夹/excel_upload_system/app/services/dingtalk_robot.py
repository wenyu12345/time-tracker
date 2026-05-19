import os
import requests
import json
import re

# 导入Flask应用实例
from flask import current_app as app

# 从环境变量获取webhook地址
# 请确保消息中包含关键词 "@小艺"
# 使用原始dingtalk_robot.py中的有效token作为默认值
DEFAULT_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=96542078ec1e3ca21582ae18edeb6aedcfaf96bf3b4ec1f1f9ce98a2b6ba19a7"
WEBHOOK_URL = os.environ.get('DINGTALK_WEBHOOK', DEFAULT_WEBHOOK)

# 备用的webhook地址（通过环境变量设置）
BACKUP_WEBHOOK_URL = os.environ.get('DINGTALK_BACKUP_WEBHOOK', '')

def upload_image_to_dingtalk(image_path):
    """
    上传图片到钉钉并获取media_id
    
    Args:
        image_path: 图片文件路径
    
    Returns:
        str: media_id，如果上传失败返回空字符串
    """
    # 获取webhook URL
    webhook_url = os.environ.get('DINGTALK_WEBHOOK', '')
    if not webhook_url:
        webhook_url = DEFAULT_WEBHOOK
    
    # 如果还是没有webhook，尝试从配置文件获取备份webhook
    if not webhook_url:
        try:
            from app.config import Config
            webhook_url = getattr(Config, 'BACKUP_WEBHOOK_URL', '')
        except ImportError:
            pass
    
    if not webhook_url:
        return ""
    
    # 提取access_token
    token_match = re.search(r'access_token=([^&]+)', webhook_url)
    if not token_match:
        return ""
    
    access_token = token_match.group(1)
    upload_url = f"https://oapi.dingtalk.com/media/upload?access_token={access_token}&type=image"
    
    try:
        # 检查文件是否存在
        if not os.path.exists(image_path):
            return ""
        
        # 上传图片
        with open(image_path, 'rb') as f:
            files = {'media': f}
            response = requests.post(upload_url, files=files, timeout=10)
            response.raise_for_status()  # 检查HTTP错误
            result = response.json()
            
            if result.get('errcode') == 0:
                return result.get('media_id', '')
            else:
                return ""
    except Exception:
        return ""

def send_image_to_dingtalk(media_id):
    """
    发送图片到钉钉群
    
    Args:
        media_id: 图片的media_id
    
    Returns:
        dict: 钉钉机器人返回的结果
    """
    # 直接使用image类型发送图片（推荐方式）
    data = {
        "msgtype": "image",
        "image": {
            "media_id": media_id
        }
    }
    
    try:
        # 修复字符编码问题
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        payload = json.dumps(data, ensure_ascii=False)
        
        # 发送请求，明确指定UTF-8编码
        response = requests.post(
            WEBHOOK_URL,
            headers=headers,
            data=payload.encode('utf-8'),
            timeout=10
        )
        
        return response.json()
    except UnicodeEncodeError as e:
        return {"errcode": 2, "errmsg": f"字符编码错误: {str(e)}"}
    except Exception:
        return {"errcode": 1, "errmsg": "发送图片失败"}

def send_text_message_to_dingtalk(text):
    """
    发送文本消息到钉钉群
    
    Args:
        text: 要发送的文本内容
    
    Returns:
        dict: 钉钉机器人返回的结果
    """
    data = {
        "msgtype": "text",
        "text": {
            "content": text
        }
    }
    
    try:
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        payload = json.dumps(data, ensure_ascii=False)
        
        response = requests.post(
            WEBHOOK_URL,
            headers=headers,
            data=payload.encode('utf-8'),
            timeout=10
        )
        
        return response.json()
    except UnicodeEncodeError as e:
        return {"errcode": 2, "errmsg": f"字符编码错误: {str(e)}"}
    except Exception as e:
        return {"errcode": 1, "errmsg": f"发送消息失败: {str(e)}"}

def send_honglian_notification(file_name, operation, data_count=0, page_count=0, image_path=None):
    """
    发送红莲模式通知到钉钉群，支持发送图片
    
    Args:
        file_name: 文件名
        operation: 操作类型
        data_count: 数据条数
        page_count: 页数
        image_path: 图片文件路径（可选）
    
    Returns:
        dict: 钉钉机器人返回的结果
    """
    # 如果提供了图片路径，只发送图片，不发送任何文本通知
    if image_path:
        # 获取当前工作目录
        current_dir = os.getcwd()
        
        # 尝试多种可能的图片路径组合
        possible_paths = [
            image_path,  # 直接使用提供的路径
            os.path.join('static', image_path),  # 在static目录中查找
            os.path.join(current_dir, image_path),  # 在当前目录中查找
            os.path.join(current_dir, 'static', image_path),  # 在当前目录的static子目录中查找
        ]
        
        # 针对batch_tables_screenshot.png的特殊路径处理
        if 'batch_tables_screenshot.png' in image_path:
            possible_paths.extend([
                'batch_tables_screenshot.png',  # 直接查找文件名
                os.path.join('static', 'batch_tables_screenshot.png'),
                os.path.join(current_dir, 'batch_tables_screenshot.png'),
                os.path.join(current_dir, 'static', 'batch_tables_screenshot.png'),
            ])
        
        # 如果app实例可用，也尝试在上传目录中查找
        try:
            if app and hasattr(app, 'config'):
                upload_folder = app.config.get('UPLOAD_FOLDER', '')
                if upload_folder:
                    possible_paths.append(os.path.join(upload_folder, image_path))
                    # 针对batch_tables_screenshot.png的特殊处理
                    if 'batch_tables_screenshot.png' in image_path:
                        possible_paths.append(os.path.join(upload_folder, 'batch_tables_screenshot.png'))
        except:
            pass
        
        # 尝试绝对路径（去除可能的相对路径前缀）
        if image_path.startswith('./'):
            possible_paths.append(image_path[2:])
        elif image_path.startswith('../'):
            possible_paths.append(image_path[3:])
        
        # 检查是否能找到文件
        found_path = None
        for path in possible_paths:
            if os.path.exists(path):
                found_path = path
                break
        
        if not found_path:
            # 尝试查找临时目录
            temp_dir = os.environ.get('TEMP', '')
            if temp_dir:
                temp_path = os.path.join(temp_dir, image_path)
                if os.path.exists(temp_path):
                    found_path = temp_path
        
        if not found_path:
            # 最后尝试在项目根目录查找
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            root_path = os.path.join(project_root, image_path)
            if os.path.exists(root_path):
                found_path = root_path
        
        if not found_path:
            return {"errcode": 2, "errmsg": f"找不到图片文件: {image_path}"}
        
        # 尝试上传并获取图片media_id
        media_id = upload_image_to_dingtalk(found_path)
        if media_id:
            # 只发送图片（使用image类型）
            return send_image_to_dingtalk(media_id)
        else:
            return {"errcode": 3, "errmsg": "图片上传失败"}
    else:
        # 没有提供图片路径时返回错误
        return {"errcode": 2, "errmsg": "未提供图片路径"}