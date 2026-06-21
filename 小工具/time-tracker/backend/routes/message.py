from flask import Blueprint, request, jsonify, Response
from utils.db import get_db
from utils.search import search_duckduckgo, build_search_context
from datetime import datetime, timezone
import requests
import threading
import re
import json

# 创建蓝图
message_bp = Blueprint('message', __name__)

# Ollama API 配置
OLLAMA_URL = "http://localhost:11434"
AI_USER_ID = 0  # AI 用户ID
AI_USERNAME = "AI助手"

def get_ollama_response_stream(prompt, model="qwen3:latest"):
    """流式调用 Ollama API 获取 AI 回复"""
    
    # 尝试的模型列表（按优先级排序）
    fallback_models = [
        model,  # 先尝试用户选择的模型
        "qwen3:8b",
        "qwen3:latest", 
        "deepseek-r1:8b"
    ]
    
    # 去重，按顺序尝试
    tried_models = []
    for m in fallback_models:
        if m not in tried_models:
            tried_models.append(m)
    
    print(f"流式响应 - 模型尝试顺序: {tried_models}")
    
    for current_model in tried_models:
        print(f"\n正在尝试流式模型: {current_model}")
        try:
            # 使用流式请求
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": current_model,
                    "prompt": prompt,
                    "stream": True,  # 启用流式
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 2048,
                        "num_ctx": 4096
                    }
                },
                stream=True,  # 启用流式响应
                timeout=300
            )
            
            if response.status_code == 200:
                # 逐行读取响应
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            token = data.get("response", "")
                            if token:
                                full_response += token
                                # 返回每个token用于前端显示
                                yield token
                        except json.JSONDecodeError:
                            continue
                
                print(f"✅ {current_model} 流式响应完成")
                return
            else:
                print(f"❌ {current_model} 错误: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"❌ {current_model} 流式调用超时")
        except requests.exceptions.ConnectionError:
            print(f"❌ {current_model} 无法连接")
        except Exception as e:
            print(f"❌ {current_model} 错误: {e}")
    
    print("\n❌ 所有模型都失败了")
    yield ""


def get_ollama_response(prompt, model="qwen3:latest"):
    """调用 Ollama API 获取 AI 回复，带有自动回退机制"""
    
    # 尝试的模型列表（按优先级排序）
    fallback_models = [
        model,  # 先尝试用户选择的模型
        "qwen3:8b",
        "qwen3:latest", 
        "deepseek-r1:8b"
    ]
    
    # 去重，按顺序尝试
    tried_models = []
    for m in fallback_models:
        if m not in tried_models:
            tried_models.append(m)
    
    print(f"模型尝试顺序: {tried_models}")
    
    for current_model in tried_models:
        print(f"\n正在尝试模型: {current_model}")
        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": current_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.5,
                        "num_predict": 200,
                        "num_ctx": 2048
                    }
                },
                timeout=60  # 减少超时时间到1分钟
            )
            print(f"Ollama API 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                ai_text = result.get("response", "")
                if ai_text:
                    print(f"✅ {current_model} 成功生成回复: {ai_text[:100]}...")
                    return ai_text
                else:
                    print(f"⚠️ {current_model} 返回空回复")
            else:
                print(f"❌ {current_model} 错误: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"❌ {current_model} 调用超时")
        except requests.exceptions.ConnectionError:
            print(f"❌ {current_model} 无法连接")
        except Exception as e:
            print(f"❌ {current_model} 错误: {e}")
    
    print("\n❌ 所有模型都失败了")
    return ""

def check_ai_chat_enabled(user_id):
    """检查用户是否启用了 AI 聊天"""
    try:
        db = get_db()
        config = db.execute('SELECT ai_chat_enabled FROM user_configs WHERE user_id = ?', (user_id,)).fetchone()
        if config:
            return bool(config['ai_chat_enabled'])
        return True  # 默认启用
    except:
        return True

def check_ai_can_modify_attendance(user_id):
    """检查 AI 是否有权限修改用户考勤"""
    try:
        db = get_db()
        config = db.execute('SELECT ai_can_modify_attendance FROM user_configs WHERE user_id = ?', (user_id,)).fetchone()
        if config:
            return bool(config['ai_can_modify_attendance'])
        return False  # 默认不启用
    except:
        return False


def check_ai_can_view_attendance(user_id):
    """检查 AI 是否有权限查看用户考勤"""
    try:
        db = get_db()
        config = db.execute('SELECT ai_can_view_attendance FROM user_configs WHERE user_id = ?', (user_id,)).fetchone()
        if config:
            return bool(config['ai_can_view_attendance'])
        return True  # 默认启用
    except:
        return True


def check_ai_can_analyze_attendance(user_id):
    """检查 AI 是否有权限分析用户考勤"""
    try:
        db = get_db()
        config = db.execute('SELECT ai_can_analyze_attendance FROM user_configs WHERE user_id = ?', (user_id,)).fetchone()
        if config:
            return bool(config['ai_can_analyze_attendance'])
        return True  # 默认启用
    except:
        return True


def check_ai_can_search(user_id):
    """检查 AI 是否有权限搜索网络信息"""
    try:
        db = get_db()
        config = db.execute('SELECT ai_can_search FROM user_configs WHERE user_id = ?', (user_id,)).fetchone()
        if config:
            return bool(config['ai_can_search'])
        return False  # 默认不启用
    except:
        return False


def get_user_ai_model(user_id):
    """获取用户配置的 AI 模型"""
    try:
        db = get_db()
        config = db.execute('SELECT ai_model FROM user_configs WHERE user_id = ?', (user_id,)).fetchone()
        if config and config['ai_model']:
            return config['ai_model']
        return "qwen3:latest"  # 默认模型
    except:
        return "qwen3:latest"

def parse_attendance_command(message):
    """解析考勤修改命令"""
    # 示例命令：修改考勤 2024-05-15 白班 08:00 18:00
    import re
    pattern = r'(修改|添加|调整)考勤\s+(\d{4}-\d{2}-\d{2})\s+(\S+)(?:\s+(\d{1,2}:\d{2}))?(?:\s+(\d{1,2}:\d{2}))?'
    match = re.search(pattern, message)
    if match:
        return {
            'action': match.group(1),
            'date': match.group(2),
            'shift_type': match.group(3),
            'start_time': match.group(4),
            'end_time': match.group(5)
        }
    return None


def parse_view_attendance_command(message):
    """解析查看考勤命令"""
    import re
    from datetime import datetime, timedelta
    
    # 查看某天考勤
    date_pattern = r'查看(?:考勤|出勤)\s+(\d{4}-\d{2}-\d{2})'
    match = re.search(date_pattern, message)
    if match:
        return {
            'type': 'date',
            'date': match.group(1)
        }
    
    # 查看某月考勤
    month_pattern = r'查看(?:考勤|出勤)\s+(\d{4}-\d{2})'
    match = re.search(month_pattern, message)
    if match:
        return {
            'type': 'month',
            'month': match.group(1)
        }
    
    # 支持中文日期词
    if '今天' in message:
        return {
            'type': 'today'
        }
    elif '明天' in message:
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        return {
            'type': 'date',
            'date': tomorrow
        }
    elif '昨天' in message:
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        return {
            'type': 'date',
            'date': yesterday
        }
    
    # 简单的查看考勤
    simple_pattern = r'(查看|看看)(考勤|出勤)'
    if re.search(simple_pattern, message):
        return {
            'type': 'today'
        }
    return None


def parse_analyze_attendance_command(message):
    """解析考勤分析命令"""
    import re
    analyze_pattern = r'(分析|汇总|统计)(?:考勤|工时)'
    if re.search(analyze_pattern, message):
        return True
    return False


def get_attendance_by_date(user_id, date):
    """获取指定日期的考勤记录"""
    try:
        db = get_db()
        records = db.execute('''
            SELECT id, shift_type, start_time, end_time, duration, is_leave
            FROM time_records
            WHERE user_id = ? AND DATE(start_time) = DATE(?)
        ''', (user_id, date)).fetchall()
        
        return [dict(r) for r in records] if records else []
    except Exception as e:
        print(f"获取考勤记录失败: {e}")
        return []


def get_attendance_by_month(user_id, year_month):
    """获取指定月份的考勤记录"""
    try:
        db = get_db()
        records = db.execute('''
            SELECT id, shift_type, start_time, end_time, duration, is_leave
            FROM time_records
            WHERE user_id = ? AND strftime('%Y-%m', start_time) = ?
            ORDER BY start_time
        ''', (user_id, year_month)).fetchall()
        
        return [dict(r) for r in records] if records else []
    except Exception as e:
        print(f"获取月份考勤记录失败: {e}")
        return []


def analyze_attendance_summary(user_id):
    """分析用户的考勤汇总（基于当前自然月）"""
    from datetime import datetime
    try:
        db = get_db()
        
        # 获取当前自然月的第一天
        now = datetime.now()
        first_day = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        first_day_str = first_day.strftime('%Y-%m-%d')
        current_month_str = now.strftime('%Y-%m')
        
        records = db.execute('''
            SELECT id, shift_type, duration, is_leave, start_time
            FROM time_records
            WHERE user_id = ? AND strftime('%Y-%m', start_time) = ?
            ORDER BY start_time
        ''', (user_id, current_month_str)).fetchall()
        
        stats = {
            'total_days': 0,
            'total_hours': 0,
            'shift_counts': {},
            'leave_days': 0,
            'rest_days': 0,
            'month': current_month_str
        }
        
        for r in records:
            stats['total_days'] += 1
            stats['total_hours'] += (r['duration'] or 0) / 60  # 转换为小时
            
            shift_type = r['shift_type']
            if shift_type not in stats['shift_counts']:
                stats['shift_counts'][shift_type] = 0
            stats['shift_counts'][shift_type] += 1
            
            if r['is_leave']:
                stats['leave_days'] += 1
            if shift_type == '休息':
                stats['rest_days'] += 1
        
        return stats
    except Exception as e:
        print(f"分析考勤失败: {e}")
        return None


def parse_user_intent_with_ai(user_message, model):
    """用 AI 理解用户意图，返回 JSON 格式"""
    from datetime import datetime, timedelta
    today = datetime.now()
    
    # 优先检测：以 "1" 开头的消息，代表搜索功能
    if user_message.strip().startswith("1"):
        query = user_message.strip()[1:].strip()  # 去掉开头的 "1" 和空格
        if not query:
            query = user_message.strip()
        return {
            "type": "search",
            "query": query
        }
    
    # 先进行简单的关键词检查，优先识别搜索意图
    search_keywords = ['搜索', '查找', '查一下', '搜索一下', '帮我找', '了解一下', '什么是', '怎么', '如何', '为什么', '是什么', '在哪里']
    for keyword in search_keywords:
        if keyword in user_message:
            return {
                "type": "search",
                "query": user_message
            }
    
    prompt = f'''你是一个专门的意图识别AI。请分析用户的输入，只返回JSON格式，不要返回其他内容。

今天是 {today.strftime('%Y-%m-%d')}

可能的意图类型（按优先级）：
1. search: 用户想了解外部信息、搜索资料、询问天气、问问题等
2. view_attendance: 查看自己的考勤记录（只有用户明确提到考勤/工时才选这个）
3. modify_attendance: 修改/添加考勤记录（只有用户明确提到修改/添加考勤才选这个）
4. analyze_attendance: 分析考勤（本月）
5. chat: 普通聊天

JSON格式要求：
{{
    "type": "view_attendance|modify_attendance|analyze_attendance|search|chat",
    "date": "2024-05-15", // 查看或修改的日期，格式YYYY-MM-DD
    "shift_type": "白班|夜班|请假|休息", // 只在modify_attendance时需要
    "query": "搜索关键词", // 只在search时需要
    "start_time": "08:00", // 可选
    "end_time": "18:00" // 可选
}}

例子：
- 用户说"查看明天的考勤" → {{"type":"view_attendance","date":"{ (today + timedelta(days=1)).strftime('%Y-%m-%d') }"}}
- 用户说"帮我把昨天的改成白班" → {{"type":"modify_attendance","date":"{ (today - timedelta(days=1)).strftime('%Y-%m-%d') }","shift_type":"白班"}}
- 用户说"分析一下考勤" → {{"type":"analyze_attendance"}}
- 用户说"搜索一下今天的天气" → {{"type":"search","query":"今天的天气"}}
- 用户说"扬州天气" → {{"type":"search","query":"扬州天气"}}
- 用户说"你好" → {{"type":"chat"}}

请只返回纯JSON，不要有其他内容。

用户输入: {user_message}
'''
    
    print(f"调用 AI 意图识别，模型: {model}")
    try:
        response = get_ollama_response(prompt, model)
        print(f"AI 原始返回: {response}")
        
        # 清理回复，提取 JSON
        if '{' in response and '}' in response:
            start = response.find('{')
            end = response.rfind('}') + 1
            json_str = response[start:end]
            import json
            result = json.loads(json_str)
            return result
        else:
            print("未找到有效 JSON")
            return None
    except Exception as e:
        print(f"AI 意图解析失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def execute_attendance_modification(user_id, command):
    """执行考勤修改（先删除当天所有旧记录，再添加新记录）"""
    try:
        db = get_db()
        
        date = command['date']
        shift_type = command['shift_type']
        start_time = command.get('start_time', '08:00')
        end_time = command.get('end_time', '18:00')
        
        # 处理默认时间
        if shift_type == '夜班':
            start_time = start_time or '20:00'
            end_time = end_time or '06:00'
        else:
            start_time = start_time or '08:00'
            end_time = end_time or '18:00'
        
        # 构建完整的时间
        start_datetime = f"{date}T{start_time}:00"
        end_datetime = f"{date}T{end_time}:00"
        
        # 如果是夜班跨天，需要处理结束时间
        if shift_type == '夜班' and end_time < start_time:
            from datetime import timedelta
            end_date = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
            end_datetime = f"{end_date}T{end_time}:00"
        
        # 计算时长（分钟）
        try:
            start_dt = datetime.strptime(start_datetime, '%Y-%m-%dT%H:%M:%S')
            end_dt = datetime.strptime(end_datetime, '%Y-%m-%dT%H:%M:%S')
            duration = int((end_dt - start_dt).total_seconds() / 60)
        except:
            duration = 480  # 默认8小时
        
        # 删除当天所有旧记录（包括休息、请假等任何记录）
        print(f"正在删除用户 {user_id} 在 {date} 的所有旧考勤记录...")
        delete_result = db.execute(
            '''DELETE FROM time_records WHERE user_id = ? AND DATE(start_time) = DATE(?)''',
            (user_id, date)
        )
        delete_count = delete_result.rowcount
        print(f"已删除 {delete_count} 条旧记录")
        
        # 添加新记录
        db.execute(
            '''INSERT INTO time_records 
            (user_id, start_time, end_time, duration, shift_type, is_leave, description) 
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (user_id, start_datetime, end_datetime, duration, shift_type, shift_type in ['请假', '休假'], "AI助手修改")
        )
        
        action_result = f"已成功处理 {date} 的考勤：{shift_type}（已覆盖当天所有旧记录）"
        
        db.commit()
        return action_result
    except Exception as e:
        print(f"考勤修改失败: {e}")
        import traceback
        traceback.print_exc()
        return f"修改失败：{str(e)}"

def generate_ai_reply_async(user_message, message_id, user_id):
    """简化版异步生成 AI 回复：直接回复，不做复杂意图识别"""
    print(f"开始处理 AI 回复，用户ID: {user_id}, 消息ID: {message_id}")
    from datetime import datetime
    try:
        from app import app
        with app.app_context():
            db = get_db()
            
            # 检查是否启用了 AI 聊天
            if not check_ai_chat_enabled(user_id):
                print(f"用户 {user_id} 未启用 AI 聊天，跳过回复")
                return
            
            # 检查是否是简单的考勤相关关键词（快速处理）
            msg_lower = user_message.lower()
            
            # 处理搜索请求（以1开头）
            if user_message.startswith('1'):
                if check_ai_can_search(user_id):
                    query = user_message[1:].strip()
                    print(f"用户触发搜索: {query}")
                    model = get_user_ai_model(user_id)
                    
                    # 优化提示词
                    prompt = f'''【重要】这是一条新消息，请基于这条消息直接回复。

当前用户消息：{query}

请作为友好的AI助手，简洁地回答用户的问题。只基于这条消息回复，不要联想。'''
                    
                    ai_response = get_ollama_response(prompt, model)
                    if not ai_response:
                        ai_response = f"关于「{query}」，让我来告诉你一些相关信息！"
                else:
                    ai_response = "抱歉，您还没有授权我搜索网络信息。"
            
            # 处理查看考勤
            elif '查看考勤' in user_message or '看考勤' in user_message or '查考勤' in user_message:
                if check_ai_can_view_attendance(user_id):
                    today = datetime.now().strftime('%Y-%m-%d')
                    records = get_attendance_by_date(user_id, today)
                    if records:
                        ai_response = f"📅 {today} 的考勤：\n"
                        for r in records:
                            dur = (r['duration'] or 0) / 60
                            ai_response += f"  • {r['shift_type']} {r['start_time']}-{r['end_time']} ({dur:.1f}小时)\n"
                    else:
                        ai_response = f"📅 {today} 没有找到考勤记录哦～"
                else:
                    ai_response = "抱歉，您还没有授权我查看考勤。"
            
            # 处理考勤分析
            elif '分析' in user_message and '考勤' in user_message:
                if check_ai_can_analyze_attendance(user_id):
                    stats = analyze_attendance_summary(user_id)
                    if stats:
                        ai_response = f"📊 {stats['month']} 月考勤：\n"
                        ai_response += f"  • 出勤 {stats['total_days']} 天\n"
                        ai_response += f"  • 总工时 {stats['total_hours']:.1f} 小时"
                    else:
                        ai_response = "本月还没有考勤记录呢～"
                else:
                    ai_response = "抱歉，您还没有授权我分析考勤。"
            
            # 其他情况，直接让 AI 回复（只调用一次！）
            else:
                model = get_user_ai_model(user_id)
                print(f"直接调用 AI 回复，模型: {model}")
                
                # 优化提示词，明确强调这是当前消息
                prompt = f'''【重要】这是一条新消息，请基于这条消息直接回复，不要参考任何历史对话。

当前用户消息：{user_message}

请作为友好的AI助手，基于上述消息直接回复。要求：
1. 只基于这条消息的内容回复，不要联想或延伸
2. 回复简洁、自然，不要太长
3. 回复要直接对应用户的问题'''
                
                ai_response = get_ollama_response(prompt, model)
                
                if not ai_response:
                    ai_response = "好的，我收到了！"
            
            # 保存 AI 回复到数据库
            if ai_response:
                print(f"AI 回复准备保存: {ai_response[:50]}...")
                db.execute(
                    'INSERT INTO messages (user_id, content, is_system, reply_to) VALUES (?, ?, ?, ?)',
                    (AI_USER_ID, ai_response, False, message_id)
                )
                db.commit()
                print(f"AI 回复已保存到数据库")
            else:
                print("AI 没有生成回复")
    except Exception as e:
        print(f"生成 AI 回复失败: {e}")
        import traceback
        traceback.print_exc()

@message_bp.route('/', methods=['GET'])
def get_messages():
    """获取留言列表"""
    db = get_db()
    
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    offset = (page - 1) * per_page
    
    # 查询留言列表，按创建时间倒序排列
    # 使用LEFT JOIN，即使user_id不存在也能返回留言
    messages = db.execute(
        '''SELECT m.*, u.username 
        FROM messages m 
        LEFT JOIN users u ON m.user_id = u.id 
        ORDER BY m.created_at DESC 
        LIMIT ? OFFSET ?''',
        (per_page, offset)
    ).fetchall()
    
    # 查询总留言数
    total = db.execute('SELECT COUNT(*) as count FROM messages').fetchone()['count']
    
    # 转换时间格式，将UTC时间转换为本地时间
    messages_list = []
    for message in messages:
        message_dict = dict(message)
        # 将字符串格式的UTC时间转换为datetime对象
        utc_time = datetime.strptime(message_dict['created_at'], '%Y-%m-%d %H:%M:%S')
        # 添加UTC时区信息
        utc_time = utc_time.replace(tzinfo=timezone.utc)
        # 转换为本地时间
        local_time = utc_time.astimezone()
        # 格式化为字符串
        message_dict['created_at'] = local_time.strftime('%Y-%m-%d %H:%M:%S')
        # 如果是 AI 消息，设置 username
        if message_dict['user_id'] == AI_USER_ID:
            message_dict['username'] = AI_USERNAME
        messages_list.append(message_dict)
    
    return jsonify({
        'messages': messages_list,
        'total': total,
        'page': page,
        'per_page': per_page
    }), 200

@message_bp.route('/', methods=['POST'])
def create_message():
    """添加留言"""
    data = request.get_json()
    user_id = data.get('user_id')
    content = data.get('content')
    is_system = data.get('is_system', False)
    enable_ai_reply = data.get('enable_ai_reply', True)  # 是否启用 AI 回复
    
    if not user_id or not content:
        return jsonify({'error': 'User ID and content are required'}), 400
    
    db = get_db()
    
    try:
        # 插入留言
        cursor = db.execute(
            '''INSERT INTO messages (user_id, content, is_system) 
            VALUES (?, ?, ?)''',
            (user_id, content, is_system)
        )
        db.commit()
        
        message_id = cursor.lastrowid
        
        # 如果不是 AI 自己的消息，且启用了 AI 回复，则异步生成回复
        if enable_ai_reply and user_id != AI_USER_ID and not is_system:
            threading.Thread(
                target=generate_ai_reply_async,
                args=(content, message_id, user_id),
                daemon=True
            ).start()
        
        return jsonify({'message': 'Message created successfully', 'id': message_id}), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

@message_bp.route('/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    """删除留言"""
    db = get_db()
    
    try:
        # 检查留言是否存在
        message = db.execute('SELECT id FROM messages WHERE id = ?', (message_id,)).fetchone()
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        # 删除留言
        db.execute('DELETE FROM messages WHERE id = ?', (message_id,))
        db.commit()
        
        return jsonify({'message': 'Message deleted successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


@message_bp.route('/stream', methods=['POST'])
def create_message_with_stream_response():
    """创建消息并使用流式响应返回AI回复"""
    data = request.get_json()
    user_id = data.get('user_id')
    content = data.get('content', '').strip()
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    if not content:
        return jsonify({'error': 'Content is required'}), 400
    
    db = get_db()
    
    try:
        # 插入用户消息
        cursor = db.execute(
            '''INSERT INTO messages (user_id, content, is_system) 
            VALUES (?, ?, ?)''',
            (user_id, content, False)
        )
        db.commit()
        message_id = cursor.lastrowid
        
        # 先检查是否启用 AI 回复
        enable_ai_reply = check_ai_chat_enabled(user_id)
        
        if not enable_ai_reply:
            return jsonify({
                'message_id': message_id,
                'ai_response': None,
                'ai_reply_enabled': False
            }), 201
        
        # 获取用户选择的 AI 模型
        model = get_user_ai_model(user_id)
        
        # 解析用户意图
        ai_parsed_result = parse_user_intent_with_ai(content, model)
        
        # 根据意图生成提示词
        prompt = build_prompt_for_intent(content, user_id, ai_parsed_result, model)
        
        # 返回流式响应
        return Response(
            generate_stream_response(message_id, user_id, prompt, model),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


def build_prompt_for_intent(user_message, user_id, ai_parsed_result, model):
    """根据意图构建提示词"""
    from datetime import datetime
    
    if ai_parsed_result:
        intent_type = ai_parsed_result.get('type', '')
        
        if intent_type == 'search':
            query = ai_parsed_result.get("query", user_message)
            return f'''用户想了解关于：{query}

请作为专业且友好的AI助手，直接回答用户的问题。
- 如果是常识性问题，请用简洁明了的语言给出答案
- 如果需要实时信息（如天气、新闻），请说明情况并给出一些通用建议
- 如果问题比较开放，请分享相关的知识和见解
- 尽可能提供具体、有价值的信息'''
        
        elif intent_type == 'view_attendance':
            if check_ai_can_view_attendance(user_id):
                date = ai_parsed_result.get('date', datetime.now().strftime('%Y-%m-%d'))
                records = get_attendance_by_date(user_id, date)
                if records:
                    result = f"📅 {date} 的考勤记录：\n"
                    for r in records:
                        dur = (r['duration'] or 0) / 60
                        result += f"  • {r['shift_type']} {r['start_time']}-{r['end_time']} ({dur:.1f}小时)\n"
                    return result
                else:
                    return f"📅 {date} 没有找到考勤记录哦～"
            else:
                return "抱歉，您还没有授权我查看考勤记录。"
        
        elif intent_type == 'analyze_attendance':
            if check_ai_can_analyze_attendance(user_id):
                stats = analyze_attendance_summary(user_id)
                if stats:
                    result = f"📊 {stats['month']} 月考勤分析：\n"
                    result += f"  • 出勤天数：{stats['total_days']} 天\n"
                    result += f"  • 总工时：{stats['total_hours']:.1f} 小时\n"
                    for shift, count in stats['shift_counts'].items():
                        result += f"  • {shift}：{count} 次\n"
                    result += f"  • 请假天数：{stats['leave_days']} 天\n"
                    result += f"  • 休息天数：{stats['rest_days']} 天\n"
                    avg_hours = stats['total_hours'] / stats['total_days'] if stats['total_days'] > 0 else 0
                    result += f"  • 平均每天：{avg_hours:.1f} 小时"
                    return result
                else:
                    return "本月还没有考勤记录呢～"
            else:
                return "抱歉，您还没有授权我分析考勤记录。"
        
        elif intent_type == 'modify_attendance':
            if check_ai_can_modify_attendance(user_id):
                command = {
                    'date': ai_parsed_result.get('date', datetime.now().strftime('%Y-%m-%d')),
                    'shift_type': ai_parsed_result.get('shift_type', '白班')
                }
                result = execute_attendance_modification(user_id, command)
                return f"好的，{result}！"
            else:
                return "抱歉，您还没有授权我修改考勤记录。"
        
        else:
            # 其他意图
            return f'''当前对话信息：
- 当前时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
- 用户ID：{user_id}

用户消息：{user_message}

请作为专业、友好、有帮助的AI助手回复用户。回复要求：
1. 直接、清晰地回答用户的问题
2. 如果不确定，可以诚实说明
3. 保持简洁但信息完整
4. 语气友好，像朋友聊天一样自然'''
    
    else:
        # 无法解析意图，使用备用方案
        return f'''当前对话信息：
- 当前时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
- 用户ID：{user_id}

用户消息：{user_message}

请作为专业、友好、有帮助的AI助手回复用户。回复要求：
1. 直接、清晰地回答用户的问题
2. 如果不确定，可以诚实说明
3. 保持简洁但信息完整
4. 语气友好，像朋友聊天一样自然'''


def generate_stream_response(message_id, user_id, prompt, model):
    """生成流式响应"""
    from app import app
    
    full_response = ""
    
    try:
        # 获取流式响应
        for token in get_ollama_response_stream(prompt, model):
            full_response += token
            # 发送 SSE 事件
            yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"
        
        # 保存完整的AI回复到数据库
        if full_response:
            with app.app_context():
                db = get_db()
                db.execute(
                    '''INSERT INTO messages (user_id, content, is_system, reply_to) 
                    VALUES (?, ?, ?, ?)''',
                    (AI_USER_ID, full_response, False, message_id)
                )
                db.commit()
        
        # 发送完成事件
        yield f"data: {json.dumps({'token': '', 'done': True, 'message_id': message_id})}\n\n"
        
    except Exception as e:
        print(f"流式响应生成失败: {e}")
        import traceback
        traceback.print_exc()
        yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"


@message_bp.route('/system', methods=['POST'])
def create_system_message():
    """创建系统消息"""
    data = request.get_json()
    content = data.get('content')
    
    if not content:
        return jsonify({'error': 'Content is required'}), 400
    
    db = get_db()
    
    try:
        # 插入系统消息，user_id为1（假设1为系统用户）
        db.execute(
            '''INSERT INTO messages (user_id, content, is_system) 
            VALUES (1, ?, ?)''',
            (content, True)
        )
        db.commit()
        
        return jsonify({'message': 'System message created successfully'}), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500

# ========== AI 专用 API ==========
@message_bp.route('/ai/attendance', methods=['POST'])
def ai_modify_attendance():
    """AI 修改考勤 API（开放给 AI 调用）"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        date = data.get('date')
        shift_type = data.get('shift_type')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if not user_id or not date or not shift_type:
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 检查权限
        if not check_ai_can_modify_attendance(user_id):
            return jsonify({'error': 'AI 没有权限修改该用户的考勤'}), 403
        
        # 执行修改
        result = execute_attendance_modification(user_id, {
            'date': date,
            'shift_type': shift_type,
            'start_time': start_time,
            'end_time': end_time
        })
        
        return jsonify({'success': True, 'message': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@message_bp.route('/ai/attendance/<int:user_id>/<date>', methods=['GET'])
def ai_get_attendance(user_id, date):
    """AI 查询考勤 API（开放给 AI 调用）"""
    try:
        db = get_db()
        records = db.execute(
            '''SELECT * FROM time_records WHERE user_id = ? AND DATE(start_time) = DATE(?)''',
            (user_id, date)
        ).fetchall()
        
        records_list = [dict(record) for record in records]
        return jsonify({'attendance': records_list}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@message_bp.route('/ai/tools', methods=['GET'])
def ai_get_tools():
    """获取 AI 可用工具列表"""
    tools = [
        {
            'name': 'modify_attendance',
            'description': '修改或添加用户考勤记录',
            'parameters': {
                'user_id': '用户ID',
                'date': '日期 (YYYY-MM-DD)',
                'shift_type': '班别 (白班/夜班/请假/休假)',
                'start_time': '开始时间 (可选，例如 08:00)',
                'end_time': '结束时间 (可选，例如 18:00)'
            }
        },
        {
            'name': 'query_attendance',
            'description': '查询用户指定日期的考勤记录',
            'parameters': {
                'user_id': '用户ID',
                'date': '日期 (YYYY-MM-DD)'
            }
        }
    ]
    return jsonify({'tools': tools}), 200
