import os
import re
import json
import requests
from io import BytesIO
import base64
from datetime import datetime
import logging
from template_manager import get_template_config

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,  # 修改为DEBUG级别，确保所有日志都能被记录
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('dingtalk_robot')

# 优先从环境变量获取webhook地址，如果没有则使用默认值
DEFAULT_WEBHOOK = os.environ.get('DINGTALK_WEBHOOK', "https://oapi.dingtalk.com/robot/send?access_token=96542078ec1e3ca21582ae18edeb6aedcfaf96bf3b4ec1f1f9ce98a2b6ba19a7")

def send_dingtalk_message(content, message_type='text', title='@小艺 通知', webhook_url=None):
    """
    发送消息到钉钉群
    
    参数:
    - content: 消息内容
    - message_type: 消息类型，可选 'text', 'markdown', 'link'
    - title: 消息标题（用于markdown和link类型）
    - webhook_url: 钉钉机器人webhook地址
    
    返回:
    - 响应结果字典，包含原始errcode和errmsg
    """
    import sys
    import locale
    
    # 强制设置UTF-8编码（解决Windows环境编码问题）
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except:
            pass
    
    logger.info(f"开始发送钉钉消息，类型: {message_type}, 标题: {title}")
    
    # 默认webhook地址
    if webhook_url is None:
        webhook_url = DEFAULT_WEBHOOK
        logger.info("使用默认webhook地址")
    else:
        logger.info("使用自定义webhook地址")
    
    headers = {
        'Content-Type': 'application/json; charset=utf-8'
    }
    
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
    
    # 根据消息类型构造请求体
    if message_type == 'text':
        data = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }
    elif message_type == 'markdown':
        # 确保标题包含@小艺关键词
        if '@小艺' not in title:
            title = f"@小艺 {title}"
            logger.info(f"标题中添加@小艺关键词: {title}")
        
        # 同样处理markdown内容
        try:
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            elif not isinstance(content, str):
                content = str(content)
            content = ''.join(char for char in content if ord(char) >= 32 or char in '\n\r\t')
        except:
            content = str(content)
        
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": content
            }
        }
        logger.info(f"构建markdown消息，标题: {title}, 内容长度: {len(content)}字符")
    elif message_type == 'link':
        data = {
            "msgtype": "link",
            "link": {
                "text": content,
                "title": title,
                "picUrl": "",
                "messageUrl": ""
            }
        }
    else:
        return {'errcode': -1, 'errmsg': '不支持的消息类型'}
    
    try:
        # 记录发送前的信息
        logger.info(f"准备发送HTTP请求到webhook")
        
        # 修复字符编码问题：明确指定UTF-8编码
        try:
            payload = json.dumps(data, ensure_ascii=False)
        except UnicodeError:
            # 如果JSON序列化失败，使用ASCII fallback
            payload = json.dumps(data, ensure_ascii=True, default=str)
        
        try:
            encoded_payload = payload.encode('utf-8')
        except UnicodeEncodeError:
            # 如果UTF-8编码失败，使用ASCII fallback
            encoded_payload = payload.encode('ascii', errors='ignore')
        
        # 修改日志级别，确保能看到请求体内容用于调试
        logger.info(f"请求体: {payload[:200]}...")  # 增加日志级别到INFO，确保能看到
        
        # 使用data参数并明确指定编码，而不是json参数
        response = requests.post(webhook_url, headers=headers, data=encoded_payload, timeout=10)
        logger.info(f"收到HTTP响应，状态码: {response.status_code}")
        
        # 记录响应内容 - 显示完整内容，不截断
        response_text = response.text
        logger.info(f"完整响应内容: {response_text}")  # 不截断响应内容
        
        try:
            # 解析响应内容
            result = response.json()
            logger.info(f"消息发送结果: {result}")
            
            # 检查是否包含errcode和errmsg字段
            if isinstance(result, dict) and 'errcode' in result:
                # 原样返回原始错误码和消息
                return result
            else:
                logger.error(f"响应格式异常，缺少errcode字段: {result}")
                return {"errcode": 500, "errmsg": f"响应格式异常: {str(result)}"}
                
        except json.JSONDecodeError as e:
            logger.error(f"响应解析失败: {response_text}, 错误: {str(e)}")
            # 尝试直接返回响应文本作为错误信息
            return {"errcode": 500, "errmsg": response_text}
    except UnicodeEncodeError as e:
        error_msg = f"字符编码错误: {str(e)}"
        logger.error(error_msg)
        return {'errcode': -4, 'errmsg': error_msg}
    except requests.exceptions.Timeout:
        error_msg = "请求超时，请检查网络连接"
        logger.error(f"发送超时: {error_msg}")
        return {'errcode': 408, 'errmsg': error_msg}
    except requests.exceptions.RequestException as e:
        error_msg = f"请求失败: {str(e)}"
        logger.error(error_msg)
        return {'errcode': 500, 'errmsg': error_msg}
    except json.JSONDecodeError:
        error_msg = "响应不是有效的JSON格式"
        logger.error(f"JSON解析错误: {error_msg}")
        return {'errcode': -3, 'errmsg': error_msg}
    except Exception as e:
        error_msg = f'发送失败: {str(e)}'
        logger.error(error_msg)
        return {'errcode': -2, 'errmsg': error_msg}

def check_image_validity(image_data, image_name):
    """
    检查图片的格式和大小是否符合钉钉要求
    
    Args:
        image_data: base64编码的图片数据
        image_name: 图片名称
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # 检查图片格式
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    if image_name and not any(image_name.lower().endswith(ext) for ext in valid_extensions):
        return False, f'不支持的图片格式，仅支持: {"/ ".join(valid_extensions)}'
    
    # 检查图片大小（钉钉限制最大20MB）
    # 先处理base64前缀
    processed_data = image_data
    if image_data.startswith('data:image/') and 'base64,' in image_data:
        processed_data = image_data.split('base64,')[1]
    
    # 估算图片大小（base64编码会增加约33%的大小）
    estimated_size_bytes = len(processed_data) * 3 / 4
    if estimated_size_bytes > 20 * 1024 * 1024:  # 20MB限制
        return False, f'图片大小超过20MB限制，当前约为{estimated_size_bytes/1024/1024:.2f}MB'
    
    return True, None

def upload_image_from_data(image_data, image_name, webhook=None):
    """
    从base64数据上传图片到钉钉服务器并获取media_id
    根据钉钉官方文档，使用正确的媒体文件上传接口
    
    Args:
        image_data: base64编码的图片数据
        image_name: 图片名称
        webhook: 钉钉机器人webhook地址
    
    Returns:
        dict: 包含media_id或错误信息的字典
    """
    # 获取webhook
    if webhook is None:
        webhook = os.environ.get('DINGTALK_WEBHOOK', DEFAULT_WEBHOOK)
    
    if not webhook:
        return {'errcode': 300005, 'errmsg': 'token不存在'}
    
    # 提取access_token
    match = re.search(r'access_token=(\w+)', webhook)
    if not match:
        return {'errcode': 300005, 'errmsg': '无效的webhook格式'}
    
    # 检查图片有效性
    is_valid, error_msg = check_image_validity(image_data, image_name)
    if not is_valid:
        return {'errcode': 400, 'errmsg': error_msg}
    
    access_token = match.group(1)
    # 使用钉钉官方的媒体文件上传接口
    upload_url = f"https://oapi.dingtalk.com/media/upload?access_token={access_token}&type=image"
    
    try:
        # 解码base64数据 - 处理不同格式的base64前缀
        if image_data.startswith('data:image/png;base64,'):
            image_data = image_data[22:]  # 移除data:image/png;base64,前缀
        elif image_data.startswith('data:image/jpeg;base64,'):
            image_data = image_data[23:]  # 移除data:image/jpeg;base64,前缀
        elif image_data.startswith('data:image/jpg;base64,'):
            image_data = image_data[22:]  # 移除data:image/jpg;base64,前缀
        
        # 确保base64字符串有效，补充必要的padding
        image_data = image_data.strip()
        # 补充base64 padding
        padding = len(image_data) % 4
        if padding > 0:
            image_data += '=' * (4 - padding)
        
        # 解码base64数据
        image_bytes = base64.b64decode(image_data)
        image_io = BytesIO(image_bytes)
        
        # 上传图片 - 确保文件数据正确添加到请求中
        files = {'media': (image_name, image_io, 'image/png')}
        print(f"[上传图片] 文件名: {image_name}, 大小: {len(image_bytes)} 字节")
        
        # 添加超时设置，避免请求卡住
        response = requests.post(upload_url, files=files, timeout=30)
        
        # 记录详细的响应信息以便调试
        print(f"[上传响应] 状态码: {response.status_code}")
        print(f"[上传响应] 内容: {response.text}")
        
        if response.status_code != 200:
            return {'errcode': response.status_code, 'errmsg': f'上传失败: HTTP {response.status_code}, {response.text}'}
        
        try:
            response_json = response.json()
            print(f"[解析响应] JSON: {response_json}")
            
            # 检查是否有错误码
            if response_json.get('errcode') != 0:
                return response_json
            
            # 确保返回了media_id
            if 'media_id' not in response_json:
                return {'errcode': 404, 'errmsg': '上传成功但未返回media_id'}
            
            return response_json
        except json.JSONDecodeError:
            return {'errcode': 500, 'errmsg': f'无法解析响应: {response.text}'}
    except base64.binascii.Error as e:
        print(f"[上传异常] Base64解码错误: {str(e)}")
        return {'errcode': 400, 'errmsg': f'图片数据base64格式无效: {str(e)}'}
    except Exception as e:
        print(f"[上传异常] 未知错误: {str(e)}")
        return {'errcode': 500, 'errmsg': f'上传图片异常: {str(e)}'}

def send_image_to_dingtalk(image_data=None, image_name=None, webhook=None):
    """
    发送图片到钉钉群
    按照钉钉机器人文档的正确流程：先上传获取media_id，再发送图片消息
    
    Args:
        image_data: 图片base64数据
        image_name: 图片名称
        webhook: 钉钉机器人webhook地址
    
    Returns:
        dict: 发送结果
    """
    if not image_data:
        return {'errcode': 400, 'errmsg': '必须提供图片数据'}
    
    if not image_name:
        image_name = 'table_screenshot.png'
    
    print(f"[图片发送] 开始处理图片: {image_name}")
    
    # 步骤1: 上传图片获取media_id
    print(f"[步骤1] 上传图片获取media_id...")
    upload_result = upload_image_from_data(image_data, image_name, webhook)
    
    if upload_result.get('errcode') != 0:
        print(f"[上传失败] {upload_result.get('errmsg')}")
        return upload_result
    
    # 检查是否获取到了有效的media_id
    media_id = upload_result.get('media_id')
    if not media_id:
        print(f"[获取失败] 未返回有效的media_id")
        return {'errcode': 500, 'errmsg': '上传成功但未获取到media_id'}
    
    print(f"[获取成功] media_id: {media_id}")
    
    # 步骤2: 使用获取的media_id发送图片消息
    print(f"[步骤2] 使用media_id发送图片消息...")
    if webhook is None:
        webhook = os.environ.get('DINGTALK_WEBHOOK', DEFAULT_WEBHOOK)
    
    if not webhook:
        return {'errcode': 300005, 'errmsg': 'token不存在'}
    
    # 按照钉钉机器人文档的图片消息标准格式
    message = {
        "msgtype": "image",
        "image": {
            "media_id": media_id  # 必须使用上传返回的media_id
        }
    }
    
    try:
        headers = {'Content-Type': 'application/json'}
        # 确保数据正确序列化
        payload = json.dumps(message, ensure_ascii=False)
        print(f"[发送请求] 消息体: {payload}")
        
        # 使用json参数而不是data参数，让requests自动处理序列化和Content-Type
        response = requests.post(webhook, json=message, timeout=30)
        
        # 记录详细的响应信息
        print(f"[发送响应] 状态码: {response.status_code}")
        print(f"[发送响应] 内容: {response.text}")
        
        if response.status_code != 200:
            return {'errcode': response.status_code, 'errmsg': f'发送失败: HTTP {response.status_code}, {response.text}'}
        
        response_json = response.json()
        if response_json.get('errcode') != 0:
            return response_json
        
        print(f"[发送成功] 图片消息发送成功")
        return response_json
    except requests.exceptions.Timeout:
        print(f"[发送异常] 请求超时")
        return {'errcode': 408, 'errmsg': '发送请求超时，请检查网络连接'}
    except Exception as e:
        print(f"[发送异常] 未知错误: {str(e)}")
        return {'errcode': 500, 'errmsg': f'发送消息异常: {str(e)}'}

def send_honglian_notification(file_name, data_count, operation='数据处理', page_count=None, image_data=None, image_name=None, operation_time_range='无相关时间记录'):
    """
    发送红联系统通知到钉钉群
    
    参数:
    - file_name: 文件名
    - data_count: 数据条数
    - operation: 操作类型
    - page_count: 页码（可选）
    - image_data: 图片base64数据（可选）
    - image_name: 图片名称（可选）
    - operation_time_range: 操作时间段（可选）
    
    返回:
    - 响应结果字典
    """
    # 添加详细的调试日志
    logger.debug(f"开始发送红莲模式通知 - 文件名: {file_name}, 操作: {operation}, 数据量: {data_count}")
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 构建消息内容，确保标题包含@小艺关键词
    markdown_content = f"""
# @小艺 
**文件名**: {file_name}
**操作**: {operation}
**处理数据量**: {data_count} 条
**处理时间**: {timestamp}
**操作时间段**: {operation_time_range}
"""
    
    if page_count:
        markdown_content += f"**总页数**: {page_count} 页\n"
    
    markdown_content += "\n> 此消息由系统自动发送"
    
    logger.debug(f"构建的markdown内容: {markdown_content}")
    logger.debug(f"准备发送红联通知，包含文本和{'图片' if image_data else '无图片'}")
    
    # 验证webhook配置
    webhook = os.environ.get('DINGTALK_WEBHOOK', DEFAULT_WEBHOOK)
    if not webhook:
        error_msg = "钉钉webhook配置为空，请检查环境变量DINGTALK_WEBHOOK"
        logger.error(error_msg)
        return {'errcode': 300005, 'errmsg': error_msg}
    
    # 发送文本消息
    text_result = send_dingtalk_message(
        content=markdown_content,
        message_type='markdown',
        title='@小艺 红莲模式通知',
        webhook_url=webhook
    )
    
    logger.debug(f"文本消息发送结果: {text_result}")
    
    if text_result.get('errcode') != 0:
        error_msg = f"文本消息发送失败: {text_result.get('errmsg', '未知错误')}"
        logger.error(error_msg)
        return text_result
    
    # 如果有图片数据，发送图片消息
    if image_data and image_data.strip(): 
        logger.debug(f"检测到图片数据，长度: {len(image_data)} 字符")
        
        # 验证图片数据格式
        if image_data.startswith('data:image/') and 'base64,' in image_data:
            logger.debug("图片数据格式正确，包含data:image/base64前缀")
        else:
            logger.warning("警告：图片数据可能缺少data:image/base64前缀")
        
        image_name = image_name or f"{file_name}_screenshot.png"
        logger.debug(f"准备发送图片: {image_name}")
        
        # 先检查图片有效性
        is_valid, validity_error = check_image_validity(image_data, image_name)
        if not is_valid:
            error_msg = f"图片验证失败: {validity_error}"
            logger.error(error_msg)
            return {'errcode': 400, 'errmsg': error_msg}
        
        image_result = send_image_to_dingtalk(image_data=image_data, image_name=image_name, webhook=webhook)
        logger.debug(f"图片发送结果: {image_result}")
        
        if image_result.get('errcode') != 0:
            error_msg = f"图片发送失败: {image_result.get('errmsg', '未知错误')}"
            logger.error(error_msg)
            # 图片发送失败，但文本已发送成功，返回警告信息
            return {
                'errcode': image_result.get('errcode', 500),
                'errmsg': f'文本消息发送成功，但图片发送失败: {image_result.get("errmsg", "未知错误")}'
            }
        else:
            logger.info("图片发送成功！")
    else:
        logger.debug("未检测到有效的图片数据，跳过图片发送")
    
    logger.info("红联通知发送完成")
    return text_result

def send_table_data_to_dingtalk(table_data, title='表格数据通知', operation='数据处理', file_name=None, operation_time_range='无相关时间记录', data_count=None):
    """
    发送红莲模式筛选后的表格数据到钉钉，按照指定格式分组显示
    
    参数:
    - table_data: 表格数据，支持字典列表格式 [{"字段1": "值1", "字段2": "值2", ...}, ...]
    - title: 消息标题
    - operation: 操作类型
    - file_name: 文件名（可选）
    - operation_time_range: 操作时间段（可选）
    - data_count: 数据总数，如果提供则使用，否则自动计算
    
    返回:
    - 响应结果字典
    
    功能说明：
    1. 固定标题格式为"@小艺 红莲模式明细 - 红莲模式 明细"
    2. 按接收车间（一级筛选项）和产品类型（二级筛选项）分组显示
    3. 每个产品类型下显示批次号和重量信息
    4. 自动添加时间戳和文件名信息
    5. 显示原车间信息和操作时间段
    """
    logger.info(f"开始处理表格数据发送请求，标题: {title}, 文件: {file_name}, 数据行数: {len(table_data) if table_data else 0}")
    
    # 加载模板配置
    template_config = get_template_config()
    
    # 使用配置的标题模板，如果没有配置则使用默认标题
    if template_config and template_config.get('honglian_title_template'):
        title = template_config['honglian_title_template']
    else:
        # 固定标题格式，确保包含@小艺
        title = '@小艺 红莲模式明细'
    
    # 构建消息头部
    markdown_content = f"### {title}\n\n"
    
    # 添加文件名和操作信息 - 固定为'红莲模式 明细'
    if file_name:
        markdown_content += f"**文件名:** 红莲模式明细\n"
    markdown_content += f"**操作:** 红莲模式 明细\n"
    markdown_content += f"**处理时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    # 添加操作时间段
    markdown_content += f"**操作时间段:** {operation_time_range}\n\n"
    
    # 添加二级标题
    markdown_content += "#### 红莲模式明细数据\n\n"
    
    # 按原车间、接收车间和产品类型分组数据
    grouped_data = {}
    
    # 处理表格数据，进行分组
    for row in table_data:
        if not isinstance(row, dict):
            continue
        
        # 提取原车间
        original_workshop = None
        for key, value in row.items():
            key_lower = str(key).strip().lower()
            if any(keyword in key_lower for keyword in ['原车间', '源车间', 'from']):
                original_workshop = str(value).strip()
                # 清理车间名称，只保留"一一车间"等基本名称
                if original_workshop:
                    # 提取中文数字+"车间"的模式
                    workshop_match = re.search(r'[一二三四五六七八九十百]+车间', original_workshop)
                    if workshop_match:
                        original_workshop = workshop_match.group()
                break
        
        # 提取接收车间
        receive_workshop = None
        for key, value in row.items():
            key_lower = str(key).strip().lower()
            if any(keyword in key_lower for keyword in ['接收车间', '接收', 'receive']):
                receive_workshop = str(value).strip()
                # 清理车间名称，只保留"一一车间"等基本名称
                if receive_workshop:
                    # 提取中文数字+"车间"的模式
                    workshop_match = re.search(r'[一二三四五六七八九十百]+车间', receive_workshop)
                    if workshop_match:
                        receive_workshop = workshop_match.group()
                break
        
        # 提取产品类型（型号）
        product_type = None
        for key, value in row.items():
            key_lower = str(key).strip().lower()
            if any(keyword in key_lower for keyword in ['型号', 'model', 'type']):
                product_type = str(value).strip()
                break
        
        # 提取批号
        batch_no = None
        for key, value in row.items():
            key_lower = str(key).strip().lower()
            if any(keyword in key_lower for keyword in ['批号', '批次号', 'batch', 'lot']):
                batch_no = str(value).strip()
                break
        
        # A732型号特殊处理：批号提取前12个字符，剩余字符分别显示
        batch_display = batch_no  # 用于显示的批号
        batch_prefix = batch_no   # 用于汇总的前缀
        if product_type == 'A732' and batch_no and len(batch_no) >= 12:
            batch_prefix = batch_no[:12]  # 前12个字符用于汇总
            batch_suffix = batch_no[12:]   # 剩余字符
            if batch_suffix:
                batch_display = f"{batch_prefix} {batch_suffix}"  # 格式：前12字符 剩余字符（空格分隔）
            else:
                batch_display = batch_prefix
        
        # 提取重量
        weight = None
        for key, value in row.items():
            key_lower = str(key).strip().lower()
            if any(keyword in key_lower for keyword in ['重量', 'weight', 'kg']):
                weight = str(value).strip()
                break
        
        # 优化：只需要批次号作为必要字段，其他字段可以为空
        if batch_no:  # 只检查批次号是否存在
            # 使用原车间和接收车间作为分组键，为空时使用默认值
            workshop_key = f"{original_workshop or '未知'}-{receive_workshop or '未知'}"
            if workshop_key not in grouped_data:
                grouped_data[workshop_key] = {
                    'original_workshop': original_workshop or '未知',
                    'receive_workshop': receive_workshop or '未知',
                    'products': {}
                }
            
            # 产品类型为空时使用默认值
            product_type_key = product_type or '未知型号'
            if product_type_key not in grouped_data[workshop_key]['products']:
                grouped_data[workshop_key]['products'][product_type_key] = []
            
            # 保存批次和重量信息
            weight_str = f"{weight}kg" if weight else ""
            grouped_data[workshop_key]['products'][product_type_key].append((batch_display, weight_str, batch_prefix))  # 保存显示批号、重量和前缀
        else:
            # 记录被过滤的数据，便于调试
            logger.debug(f"数据行缺少批次号，被过滤: {row}")
    
    # 计算每个车间和产品的重量汇总
    workshop_totals = {}
    product_totals = {}
    
    # 构建内容并同时计算汇总
    for workshop_key, workshop_data in grouped_data.items():
        original_workshop = workshop_data['original_workshop']
        receive_workshop = workshop_data['receive_workshop']
        products = workshop_data['products']
        
        # 一级筛选项：原车间和接收车间，确保换行
        markdown_content += f"**原车间：{original_workshop}      接收: {receive_workshop}**\n\n"
        workshop_total = 0.0
        
        for product_type, batches in products.items():
            # 二级筛选项：产品类型，确保换行
            # 在型号后面添加工序筛选项
            process_info = ""
            # 收集该产品型号对应的所有工序
            processes = set()
            for row in table_data:
                # 检查是否属于当前产品型号
                row_product_type = None
                for key, value in row.items():
                    key_lower = str(key).strip().lower()
                    if any(keyword in key_lower for keyword in ['型号', 'model', 'type']):
                        row_product_type = str(value).strip()
                        break
                
                if row_product_type == product_type:
                    # 提取工序信息
                    for key, value in row.items():
                        key_lower = str(key).strip().lower()
                        if any(keyword in key_lower for keyword in ['工序', 'process']):
                            if value and str(value).strip():
                                processes.add(str(value).strip())
                            break
            
            # 如果有工序信息，添加到型号后面
            if processes:
                process_info = f"({', '.join(sorted(processes))})"
            
            # 添加批次数量统计，使不同型号的批号更清晰地区分
            batch_count = len(batches)
            batch_count_info = f"【{batch_count}批】"
            
            # 使用更醒目的分隔线来区分不同型号
            markdown_content += f"\n{'='*10}\n"
            markdown_content += f"**{product_type} {process_info} {batch_count_info}**\n\n"
            product_total = 0.0
            product_summary_groups = {}  # A732型号按前缀分组的汇总
            
            # 显示每个批次和重量，每条占一行并在前面加点号
            for i, (batch_display_item, weight_str, batch_prefix_item) in enumerate(batches, 1):
                if weight_str:
                    # 每条数据前加点号，批次号和重量信息，添加序号使区分更清晰
                    markdown_content += f"- 【{i}】{batch_display_item}, {weight_str}\n"
                    # 提取重量数值用于汇总 - 使用前缀进行汇总
                    try:
                        weight_value = float(weight_str.replace('kg', '').strip())
                        # A732型号按前12字符分组汇总
                        if product_type == 'A732':
                            if batch_prefix_item not in product_summary_groups:
                                product_summary_groups[batch_prefix_item] = 0.0
                            product_summary_groups[batch_prefix_item] += weight_value
                        else:
                            product_total += weight_value
                        workshop_total += weight_value
                    except (ValueError, AttributeError):
                        pass
                else:
                    # 只有批次号的情况，添加序号
                    markdown_content += f"- 【{i}】{batch_display_item}\n"
            
            # 保存产品总重量
            if receive_workshop not in product_totals:
                product_totals[receive_workshop] = {}
            product_totals[receive_workshop][product_type] = product_total
            
            # 添加产品级别的汇总信息，使型号区分更清晰
            if product_total > 0:
                markdown_content += f"  **小计**: {product_total:.1f}kg\n"
            
            # A732型号特殊汇总：按前12字符分组显示
            if product_type == 'A732' and product_summary_groups:
                markdown_content += "  **A732前缀汇总**:\n"
                for prefix, group_total in sorted(product_summary_groups.items()):
                    # 查找相同前缀的所有批次
                    same_prefix_batches = [batch for batch, weight, batch_prefix in batches if batch_prefix == prefix]
                    # 提取后缀部分（去掉前12字符）
                    suffixes = []
                    for batch_item in same_prefix_batches:
                        if len(batch_item) > 12:
                            suffix = batch_item[12:].strip()
                            if suffix:
                                suffixes.append(suffix)
                    
                    # 构建新的显示格式：【数量】前12字符 后缀1 后缀2, 总重量kg
                    if suffixes:
                        suffix_str = '  '.join(suffixes)  # 用两个空格分隔后缀
                        markdown_content += f"    - 【{len(suffixes)}】{prefix} {suffix_str}, {group_total:.1f}kg\n"
                    else:
                        markdown_content += f"    - 【{len(same_prefix_batches)}】{prefix}, {group_total:.1f}kg\n"
            
            # 添加结束分隔线，让型号区分更明显
            markdown_content += f"{'='*10}\n"
        
        # 保存车间总重量
        workshop_totals[receive_workshop] = workshop_total
    
    # 如果没有数据，添加提示信息
    if not grouped_data:
        markdown_content += "暂无符合条件的数据\n"
    
    # 如果没有提供data_count参数，则自动计算
    if data_count is None:
        data_count = sum(len(batches) for products in grouped_data.values() for batches in products.values())
    
    # 添加数据总数，加粗显示
    markdown_content += f"\n**数据总数**: {data_count} 条\n"
    
    # 添加分类汇总信息
    markdown_content += "\n#### 分类汇总\n\n"
    
    # 添加一级筛选项汇总
    for workshop, total_weight in workshop_totals.items():
        markdown_content += f"**接收: {workshop}** 汇总: {total_weight:.1f}kg\n"
        
        # 添加二级筛选项汇总
        if workshop in product_totals:
            for product_type, prod_weight in product_totals[workshop].items():
                markdown_content += f"  - {product_type}: {prod_weight:.1f}kg\n"
        markdown_content += "\n"
    
    # 加载模板配置
    template_config = get_template_config()
    
    # 使用配置的尾部模板，如果没有配置则使用默认格式
    if template_config and template_config.get('honglian_footer_template'):
        footer_template = template_config['honglian_footer_template']
        markdown_content += footer_template
    else:
        # 添加系统自动发送标识（默认格式）
        markdown_content += "\n此消息由系统自动发送"
    
    print(f"准备发送表格数据通知，数据条数: {data_count}")
    
    # 发送markdown消息
    logger.info(f"准备调用send_dingtalk_message，使用标题: {title}")
    
    try:
        # 调用发送函数并记录结果
        result = send_dingtalk_message(
            content=markdown_content,
            message_type='markdown',
            title=title  # 使用配置或默认标题
        )
        
        # 确保返回的是字典格式
        if not isinstance(result, dict):
            logger.error(f"send_dingtalk_message返回非字典格式: {result}")
            return {"errcode": 500, "errmsg": f"内部错误: {str(result)}"}
        
        logger.info(f"表格数据发送完成，结果: {result}")
        # 原样返回结果，不做任何修改
        return result
    except Exception as e:
        logger.error(f"发送表格数据时发生异常: {str(e)}")
        # 返回异常信息
        return {"errcode": 500, "errmsg": f"异常: {str(e)}"}

def send_production_summary_to_dingtalk(table_data, title='产能汇总分析', operation='数据处理', file_name=None, operation_time_range='无相关时间记录'):
    """
    发送产能汇总分析到钉钉，按照指定格式分AB班汇总和全天汇总
    
    参数:
    - table_data: 表格数据，支持字典列表格式 [{'日期': '...', '班次': '...', '产品型号': '...', ...}, ...] 或前端传来的表格格式
    - title: 消息标题
    - operation: 操作类型
    - file_name: 文件名（可选）
    - operation_time_range: 操作时间段（可选）
    
    返回:
    - 响应结果字典
    """
    logger.info(f"开始处理产能汇总分析数据发送请求，标题: {title}, 文件: {file_name}")
    
    # 固定标题格式，确保包含@小艺
    title = '@小艺 产能汇总分析精简模板'
    
    # 构建消息头部
    markdown_content = f"### {title}\n\n"
    
    # 加载模板配置
    template_config = get_template_config()
    
    # 使用配置的头部模板，如果没有配置则使用默认格式
    if template_config and template_config.get('honglian_header_template'):
        header_template = template_config['honglian_header_template']
        # 替换模板变量
        header_template = header_template.replace('{file_name}', file_name or '')
        header_template = header_template.replace('{operation}', operation)
        header_template = header_template.replace('{datetime}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        header_template = header_template.replace('{time_range}', operation_time_range)
        markdown_content += header_template
    else:
        # 添加文件名和操作信息（默认格式）
        if file_name:
            markdown_content += f"**文件名:** {file_name}\n"
        markdown_content += f"**操作:** {operation}\n"
        markdown_content += f"**处理时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        markdown_content += f"**操作时间段:** {operation_time_range}\n"
    
    # 处理表格数据，确保是字典列表格式
    data_records = []
    if isinstance(table_data, dict) and 'rows' in table_data and 'headers' in table_data:
        # 前端传来的格式：{headers: [...], rows: [...]}，需要转换为字典列表
        headers = table_data['headers']
        rows = table_data['rows']
        for row in rows:
            record = {}
            for i, header in enumerate(headers):
                if i < len(row):
                    record[header] = row[i]
            data_records.append(record)
    elif isinstance(table_data, list):
        # 已经是字典列表格式
        data_records = table_data
    
    logger.info(f"成功解析表格数据，共{len(data_records)}条记录")
    
    # 检查必要字段是否存在
    required_fields = ['日期', '班次', '产品型号', '工序名称', '良品数(kg)', '报废数(kg)', '光箔*', '去光箔后报废']
    missing_fields = []
    for field in required_fields:
        if not any(field in record for record in data_records):
            missing_fields.append(field)
    
    if missing_fields:
        logger.warning(f"数据缺少必要字段: {missing_fields}")
    
    # 数据清洗：将'-'或空值视为0处理，并确保数值列为数值类型
    def clean_numeric_value(value):
        if value == '-' or value == '' or value is None:
            return 0
        try:
            return float(value)
        except:
            return 0
    
    # 清洗数据
    for record in data_records:
        for field in ['良品数(kg)', '报废数(kg)', '光箔*', '去光箔后报废']:
            if field in record:
                record[field] = clean_numeric_value(record[field])
    
    # 按日期分组
    date_groups = {}
    for record in data_records:
        date = record.get('日期', '未知日期')
        if date not in date_groups:
            date_groups[date] = []
        date_groups[date].append(record)
    
    # 按日期升序排序
    sorted_dates = sorted(date_groups.keys())
    
    # 定义工序排序函数
    def process_sort_key(process):
        process_order = {'涂布': 1, '辊压': 2, '分条': 3}
        return process_order.get(process, 999), process
    
    # 定义产品型号排序函数
    def model_sort_key(model):
        if 'A7' in model:
            return 1, model
        elif model == 'D640':
            return 2, model
        elif model == 'D652':
            return 3, model
        elif model == 'D350':
            return 4, model
        else:
            return 999, model
    
    # 第一部分：分AB班汇总分析
    markdown_content += "\n#### 第一部分：分AB班汇总分析\n\n"
    
    # 按日期分组处理
    for date in sorted_dates:
        date_records = date_groups[date]
        
        # 按班次分组（A班/B班）
        shift_a_records = [r for r in date_records if str(r.get('班次', '')).strip().upper() == 'A']
        shift_b_records = [r for r in date_records if str(r.get('班次', '')).strip().upper() == 'B']
        
        markdown_content += f"**日期: {date}**\n\n"
        
        # A班汇总
        if shift_a_records:
            markdown_content += "- **A班汇总**\n"
            # 按产品型号分组
            model_groups = {}
            for record in shift_a_records:
                model = record.get('产品型号', '未知型号')
                if model not in model_groups:
                    model_groups[model] = []
                model_groups[model].append(record)
            
            # 按自定义产品型号排序
            sorted_models = sorted(model_groups.keys(), key=model_sort_key)
            
            for model in sorted_models:
                model_records = model_groups[model]
                markdown_content += f"  - 产品型号: {model}\n"
                
                # 按工序名称分组
                process_groups = {}
                for record in model_records:
                    process = record.get('工序名称', '未知工序')
                    if process not in process_groups:
                        process_groups[process] = []
                    process_groups[process].append(record)
                
                # 按自定义工序排序
                sorted_processes = sorted(process_groups.keys(), key=process_sort_key)
                
                for process in sorted_processes:
                    process_records = process_groups[process]
                    markdown_content += f"    - 工序名称: {process}\n"
                    
                    # 计算该工序的汇总值
                    totals = {'良品数(kg)': 0, '报废数(kg)': 0, '光箔*': 0, '去光箔后报废': 0}
                    for record in process_records:
                        for field in totals:
                            if field in record:
                                totals[field] += record[field]
                    
                    # 输出数值字段，保留一位小数
                    for field in ['良品数(kg)', '报废数(kg)', '光箔*', '去光箔后报废']:
                        markdown_content += f"      - {field}: {totals[field]:.1f}\n"
            markdown_content += "\n"
        
        # B班汇总
        if shift_b_records:
            markdown_content += "- **B班汇总**\n"
            # 按产品型号分组
            model_groups = {}
            for record in shift_b_records:
                model = record.get('产品型号', '未知型号')
                if model not in model_groups:
                    model_groups[model] = []
                model_groups[model].append(record)
            
            # 按自定义产品型号排序
            sorted_models = sorted(model_groups.keys(), key=model_sort_key)
            
            for model in sorted_models:
                model_records = model_groups[model]
                markdown_content += f"  - 产品型号: {model}\n"
                
                # 按工序名称分组
                process_groups = {}
                for record in model_records:
                    process = record.get('工序名称', '未知工序')
                    if process not in process_groups:
                        process_groups[process] = []
                    process_groups[process].append(record)
                
                # 按自定义工序排序
                sorted_processes = sorted(process_groups.keys(), key=process_sort_key)
                
                for process in sorted_processes:
                    process_records = process_groups[process]
                    markdown_content += f"    - 工序名称: {process}\n"
                    
                    # 计算该工序的汇总值
                    totals = {'良品数(kg)': 0, '报废数(kg)': 0, '光箔*': 0, '去光箔后报废': 0}
                    for record in process_records:
                        for field in totals:
                            if field in record:
                                totals[field] += record[field]
                    
                    # 输出数值字段，保留一位小数
                    for field in ['良品数(kg)', '报废数(kg)', '光箔*', '去光箔后报废']:
                        markdown_content += f"      - {field}: {totals[field]:.1f}\n"
            markdown_content += "\n"
    
    # 第二部分：全天汇总分析
    markdown_content += "\n#### 第二部分：全天汇总分析\n\n"
    
    # 按日期分组处理
    for date in sorted_dates:
        date_records = date_groups[date]
        
        markdown_content += f"**日期: {date}**\n\n"
        
        # 按产品型号分组（不区分班次）
        model_groups = {}
        for record in date_records:
            model = record.get('产品型号', '未知型号')
            if model not in model_groups:
                model_groups[model] = []
            model_groups[model].append(record)
        
        # 按自定义产品型号排序
        sorted_models = sorted(model_groups.keys(), key=model_sort_key)
        
        for model in sorted_models:
            model_records = model_groups[model]
            markdown_content += f"- 产品型号: {model}\n"
            
            # 按工序名称分组
            process_groups = {}
            for record in model_records:
                process = record.get('工序名称', '未知工序')
                if process not in process_groups:
                    process_groups[process] = []
                process_groups[process].append(record)
            
            # 按自定义工序排序
            sorted_processes = sorted(process_groups.keys(), key=process_sort_key)
            
            for process in sorted_processes:
                process_records = process_groups[process]
                markdown_content += f"  - 工序名称: {process}\n"
                
                # 计算该工序的汇总值
                totals = {'良品数(kg)': 0, '报废数(kg)': 0, '光箔*': 0, '去光箔后报废': 0}
                for record in process_records:
                    for field in totals:
                        if field in record:
                            totals[field] += record[field]
                
                # 输出汇总值，保留一位小数
                for field in ['良品数(kg)', '报废数(kg)', '光箔*', '去光箔后报废']:
                    markdown_content += f"    - {field}: {totals[field]:.1f}\n"
        markdown_content += "\n"
    
    # 第三部分：报废数据汇总表
    markdown_content += "\n#### 第三部分：报废数据汇总表\n\n"
    markdown_content += "**表头**: 日期 工序名称 正负极 报废数(kg) 光箔* 去光箔后报废总和\n\n"
    
    # 正负极判断函数
    def determine_polarity(model):
        model_str = str(model)
        if '正极' in model_str:
            return '正极'
        elif '负极' in model_str:
            return '负极'
        else:
            return '其他'
    
    # 按日期、工序名称、正负极分组汇总
    scrap_summary = {}
    total_scrap = 0
    total_foil_removed_scrap = 0
    
    for record in data_records:
        date = record.get('日期', '未知日期')
        process = record.get('工序名称', '未知工序')
        model = record.get('产品型号', '未知型号')
        polarity = determine_polarity(model)
        
        # 构建分组键
        key = (date, process, polarity)
        
        if key not in scrap_summary:
            scrap_summary[key] = {'报废数(kg)': 0, '光箔*': 0, '去光箔后报废总和': 0}
        
        # 汇总数据
        scrap_summary[key]['报废数(kg)'] += record.get('报废数(kg)', 0)
        scrap_summary[key]['光箔*'] += record.get('光箔*', 0)
        scrap_summary[key]['去光箔后报废总和'] += record.get('去光箔后报废', 0)
        
        # 累计总计
        total_scrap += record.get('报废数(kg)', 0)
        total_foil_removed_scrap += record.get('去光箔后报废', 0)
    
    # 自定义排序函数
    def summary_sort_key(item):
        date, process, polarity = item
        # 正负极排序：正极在前，负极在后
        polarity_order = {'正极': 1, '负极': 2, '其他': 3}
        return date, process_sort_key(process)[0], process, polarity_order.get(polarity, 999)
    
    # 按排序规则排序
    sorted_summary = sorted(scrap_summary.items(), key=lambda x: summary_sort_key(x[0]))
    
    # 构建列表格式，确保每行前面都有点标记，按照新的表头顺序展示
    for key, values in sorted_summary:
        date, process, polarity = key
        markdown_content += f"- **日期**: {date}, **工序名称**: {process}, **正负极**: {polarity}, **报废数(kg)**: {values['报废数(kg)']:.1f}, **光箔***: {values['光箔*']:.1f}, **去光箔后报废总和**: {values['去光箔后报废总和']:.1f}\n"
    
    # 添加合计行
    markdown_content += "\n- **合计**:\n"
    markdown_content += f"  - **总报废数(kg)**: {total_scrap:.1f}\n"
    markdown_content += f"  - **总去光箔后报废总和**: {total_foil_removed_scrap:.1f}\n"
    
    # 数据总数
    markdown_content += f"\n**数据总数**: {len(data_records)} 条\n"
    
    # 添加系统自动发送标识
    markdown_content += "\n此消息由系统自动发送"
    
    print(f"准备发送产能汇总分析数据通知，数据条数: {len(data_records)}")
    
    # 发送markdown消息
    logger.info(f"准备调用send_dingtalk_message，使用标题: {title}")
    
    try:
        # 调用发送函数并记录结果
        result = send_dingtalk_message(
            content=markdown_content,
            message_type='markdown',
            title=title  # 使用固定标题
        )
        
        # 确保返回的是字典格式
        if not isinstance(result, dict):
            logger.error(f"send_dingtalk_message返回非字典格式: {result}")
            return {"errcode": 500, "errmsg": f"内部错误: {str(result)}"}
        
        logger.info(f"产能汇总分析数据发送完成，结果: {result}")
        # 原样返回结果，不做任何修改
        return result
    except Exception as e:
        logger.error(f"发送产能汇总分析数据时发生异常: {str(e)}")
        # 返回异常信息
        return {"errcode": 500, "errmsg": f"异常: {str(e)}"}

def send_task_to_dingtalk(task, title='@小艺 任务提醒'):
    """发送任务到钉钉，使用专属的任务模板
    
    Args:
        task: 任务数据字典
        title: 消息标题
        
    Returns:
        发送结果字典
    """
    from datetime import datetime
    
    # 构建消息内容
    markdown_content = f"### {title}\n\n"
    
    # 任务标题
    markdown_content += f"**📋 任务标题**\n"
    markdown_content += f"{task.get('title', '无标题')}\n\n"
    
    # 任务描述
    if task.get('description'):
        markdown_content += f"**📝 任务描述**\n"
        markdown_content += f"{task['description']}\n\n"
    
    # 优先级
    priority_text = {
        'high': '🔴 高优先级',
        'medium': '🟡 中优先级',
        'low': '🟢 低优先级'
    }.get(task.get('priority', 'medium'), '🟡 中优先级')
    
    markdown_content += f"**⚡ 优先级**\n"
    markdown_content += f"{priority_text}\n\n"
    
    # 截止时间
    if task.get('due_date'):
        try:
            due_date = datetime.fromisoformat(task['due_date'])
            due_date_str = due_date.strftime('%Y年%m月%d日')
            now = datetime.now()
            
            # 判断是否逾期
            is_overdue = False
            if task.get('status') != 'completed' and due_date.date() < now.date():
                is_overdue = True
            
            if is_overdue:
                markdown_content += f"**⚠️ 截止时间**\n"
                markdown_content += f"❌ {due_date_str} (已逾期)\n\n"
            else:
                markdown_content += f"**📅 截止时间**\n"
                markdown_content += f"{due_date_str}\n\n"
        except (ValueError, TypeError):
            markdown_content += f"**📅 截止时间**\n"
            markdown_content += f"{task['due_date']}\n\n"
    
    # 任务状态
    status_text = {
        'pending': '⏳ 待完成',
        'completed': '✅ 已完成'
    }.get(task.get('status', 'pending'), '⏳ 待完成')
    
    markdown_content += f"**📍 任务状态**\n"
    markdown_content += f"{status_text}\n\n"
    
    # 任务ID
    markdown_content += f"**🆔 任务编号**\n"
    markdown_content += f"{task.get('task_id', '未知')}\n\n"
    
    # 创建时间
    if task.get('created_at'):
        try:
            created_at = datetime.fromisoformat(task['created_at'])
            created_at_str = created_at.strftime('%Y年%m月%d日 %H:%M')
            markdown_content += f"**📌 创建时间**\n"
            markdown_content += f"{created_at_str}\n\n"
        except (ValueError, TypeError):
            pass
    
    # 添加系统标识
    markdown_content += "\n---\n"
    markdown_content += "此消息由系统自动发送"
    
    logger.info(f"准备发送任务通知，任务ID: {task.get('task_id')}")
    
    # 发送消息
    return send_dingtalk_message(
        content=markdown_content,
        message_type='markdown',
        title=title
    )


def send_process_files_to_dingtalk(table_data, fields=None, title='@小艺 工艺文件分享', operation='数据分享', file_name=None, operation_time_range='无相关时间记录', data_count=None):
    """
    发送工艺文件数据到钉钉，使用专门的工艺文件模板
    
    参数:
    - table_data: 表格数据，支持字典列表格式 [{"字段1": "值1", "字段2": "值2", ...}, ...]
    - fields: 字段配置列表，包含 key 和 label 映射关系
    - title: 消息标题
    - operation: 操作类型
    - file_name: 文件名（可选）
    - operation_time_range: 操作时间段（可选）
    - data_count: 数据总数，如果提供则使用，否则自动计算
    
    返回:
    - 响应结果字典
    """
    logger.info(f"开始处理工艺文件数据发送请求，标题: {title}, 文件: {file_name}, 数据行数: {len(table_data) if table_data else 0}")
    
    # 构建字段key到label的映射
    key_to_label = {}
    if fields:
        for field in fields:
            key_to_label[field['key']] = field['label']
    
    # 加载模板配置
    template_config = get_template_config()
    
    # 使用配置的标题模板，如果没有配置则使用默认标题
    if template_config and template_config.get('process_files_title_template'):
        title = template_config['process_files_title_template']
    else:
        title = '@小艺 工艺文件分享'
    
    # 构建消息头部
    markdown_content = f"### {title}\n\n"
    
    # 使用配置的头部模板
    if template_config and template_config.get('process_files_header_template'):
        header_template = template_config['process_files_header_template']
        # 替换模板变量
        header_template = header_template.replace('{file_name}', file_name or '')
        header_template = header_template.replace('{operation}', operation)
        header_template = header_template.replace('{datetime}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        header_template = header_template.replace('{data_count}', str(data_count or len(table_data)))
        header_template = header_template.replace('{time_range}', operation_time_range)
        markdown_content += header_template + "\n"
    else:
        # 默认头部格式
        if file_name:
            markdown_content += f"**文件名:** {file_name}\n"
        markdown_content += f"**操作:** {operation}\n"
        markdown_content += f"**处理时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        markdown_content += f"**操作时间段:** {operation_time_range}\n\n"
    
    # 添加二级标题
    markdown_content += "#### 工艺文件数据\n\n"
    
    # 显示每条记录
    for i, record in enumerate(table_data, 1):
        markdown_content += f"**【第{i}条记录】**\n"
        
        # 如果有字段配置，按配置顺序显示
        if fields:
            for field in fields:
                key = field['key']
                value = record.get(key, '')
                
                # 格式化显示
                display_key = field['label']
                display_value = str(value) if value else "-"
                
                # 特殊格式化正负极
                if key in ['electrode_type'] or display_key in ['正负极']:
                    if display_value in ['正', '负极', '正极片', '负极片']:
                        display_value = f"{'⚡' if '正' in display_value else '🔋'} {display_value}"
                
                markdown_content += f"- **{display_key}**: {display_value}\n"
        else:
            # 没有字段配置时，按原方式显示
            for key, value in record.items():
                # 跳过系统字段
                if key in ['id', 'created_at', 'updated_at']:
                    continue
                    
                # 格式化显示
                display_key = key_to_label.get(key, str(key))
                display_value = str(value) if value else "-"
                
                # 特殊格式化正负极
                if key in ['electrode_type'] or display_key in ['正负极']:
                    if display_value in ['正', '负极', '正极片', '负极片']:
                        display_value = f"{'⚡' if '正' in display_value else '🔋'} {display_value}"
                
                markdown_content += f"- **{display_key}**: {display_value}\n"
        
        markdown_content += "\n---\n"
    
    # 如果没有数据，添加提示信息
    if not table_data:
        markdown_content += "暂无数据\n"
    
    # 如果没有提供data_count参数，则自动计算
    if data_count is None:
        data_count = len(table_data)
    
    # 添加数据总数，加粗显示
    markdown_content += f"\n**数据总数**: {data_count} 条\n"
    
    # 使用配置的尾部模板
    if template_config and template_config.get('process_files_footer_template'):
        footer_template = template_config['process_files_footer_template']
        markdown_content += footer_template
    else:
        # 默认尾部格式
        markdown_content += "\n此消息由系统自动发送"
    
    print(f"准备发送工艺文件数据通知，数据条数: {data_count}")
    
    # 发送markdown消息
    logger.info(f"准备调用send_dingtalk_message，使用标题: {title}")
    
    try:
        # 调用发送函数并记录结果
        result = send_dingtalk_message(
            content=markdown_content,
            message_type='markdown',
            title=title
        )
        
        # 确保返回的是字典格式
        if not isinstance(result, dict):
            logger.error(f"send_dingtalk_message返回非字典格式: {result}")
            return {"errcode": 500, "errmsg": f"内部错误: {str(result)}"}
        
        logger.info(f"工艺文件数据发送完成，结果: {result}")
        return result
    except Exception as e:
        logger.error(f"发送工艺文件数据时发生异常: {str(e)}")
        return {"errcode": 500, "errmsg": f"异常: {str(e)}"}


# 测试代码
if __name__ == '__main__':
    # 测试文本消息
    print("测试文本消息:")
    result = send_dingtalk_message("@小艺 测试消息发送")
    print(result)
    
    # 测试Markdown消息
    print("\n测试Markdown消息:")
    markdown_content = """
# @小艺 测试Markdown消息

**这是一个测试**

> 这是引用内容
"""
    result = send_dingtalk_message(markdown_content, message_type='markdown')
    print(result)
    
    # 测试红莲模式通知
    print("\n测试红莲模式通知:")
    result = send_honglian_notification("测试文件.xlsx", 100)
    print(result)
    
    # 测试表格数据发送功能（8行隔两行）
    print("\n测试表格数据发送:")
    # 创建测试表格数据（10行3列）
    test_table_data = [
        ['姓名', '部门', '工号'],
        ['张三', '技术部', '001'],
        ['李四', '市场部', '002'],
        ['王五', '财务部', '003'],
        ['赵六', '人事科', '004'],
        ['钱七', '行政部', '005'],
        ['孙八', '销售部', '006'],
        ['周九', '客服部', '007'],
        ['吴十', '研发部', '008'],
        ['郑十一', '运维部', '009']
    ]
    result = send_table_data_to_dingtalk(
        table_data=test_table_data,
        title='@小艺 表格数据通知',
        operation='数据同步',
        file_name='员工信息.xlsx'
    )
    print(result)
