import requests
import json
import logging

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"

def get_available_models():
    """获取可用的Ollama模型列表"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/v1/models")
        response.raise_for_status()
        result = response.json()
        return [model["id"] for model in result.get("data", [])]
    except Exception as e:
        logger.error(f"获取模型列表失败: {str(e)}")
        return []

def generate_response(prompt, model="qwen3:8b"):
    """调用Ollama生成响应"""
    try:
        data = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "max_tokens": 1024
            }
        }
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/v1/completions",
            headers={"Content-Type": "application/json"},
            data=json.dumps(data)
        )
        
        response.raise_for_status()
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["text"].strip()
        
        return result.get("message", {}).get("content", "")
    except Exception as e:
        logger.error(f"调用Ollama失败: {str(e)}")
        return None

def generate_chat_response(messages, model="qwen3:8b"):
    """调用Ollama进行对话"""
    try:
        data = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "max_tokens": 1024
            }
        }
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            data=json.dumps(data)
        )
        
        response.raise_for_status()
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"].strip()
        
        return None
    except Exception as e:
        logger.error(f"调用Ollama聊天接口失败: {str(e)}")
        return None

def parse_task_from_natural_language(text):
    """使用AI解析自然语言任务命令"""
    prompt = f"""
你是一个任务管理助手，需要将用户的自然语言输入解析为结构化的任务命令。

用户输入: {text}

请按照以下JSON格式输出解析结果：
{{
    "command": "命令类型",
    "title": "任务标题",
    "description": "任务描述",
    "priority": "优先级 (high/medium/low)",
    "due_date": "截止日期 (YYYY-MM-DD格式，可选)",
    "target_task": "目标任务ID或标题 (用于完成/删除/修改操作)"
}}

命令类型包括: add, complete, delete, update, list, toggle, unknown

如果无法确定具体操作，command请填"unknown"。
如果没有截止日期，due_date请留空字符串。
如果是列表查询操作，title和description可以留空。

只输出JSON格式，不要输出其他内容。
"""
    
    response = generate_response(prompt, model="qwen3:8b")
    if response:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.error(f"AI响应解析失败: {response}")
            return None
    return None

def chat_with_ai(message, model="qwen3:8b"):
    """与AI进行对话"""
    messages = [
        {
            "role": "system",
            "content": "你是一个智能任务管理助手，擅长帮助用户管理日常任务。你可以回答问题、提供建议、协助规划工作。"
        },
        {
            "role": "user",
            "content": message
        }
    ]
    return generate_chat_response(messages, model)

def summarize_tasks(tasks):
    """使用AI总结任务列表"""
    if not tasks:
        return "暂无任务"
    
    tasks_text = "\n".join([
        f"- [{task['task_id']}] {task['title']} (状态: {task['status']}, 截止: {task.get('due_date', '无')})"
        for task in tasks
    ])
    
    prompt = f"""
请帮我总结以下任务列表：

{tasks_text}

请用简洁友好的语言总结这些任务，包括：
1. 任务总数和完成情况
2. 即将到期的任务
3. 优先级高的任务

输出格式要清晰易读。
"""
    
    return generate_response(prompt, model="qwen3:8b")