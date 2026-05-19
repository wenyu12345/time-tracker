import re
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple

from app.models.task_models import Task, TaskStorage

class TaskParser:
    def __init__(self):
        self.storage = TaskStorage()
        self.ai_available = False
        self._check_ai_availability()

    def _check_ai_availability(self):
        """检查Ollama是否可用"""
        try:
            from app.services.ollama_service import get_available_models
            models = get_available_models()
            self.ai_available = len(models) > 0
        except Exception:
            self.ai_available = False

    def parse_message(self, message: str) -> Tuple[str, Optional[Task], str]:
        message = message.strip()
        
        if message.startswith("添加任务"):
            return self._parse_add_task(message)
        elif message.startswith("完成任务"):
            return self._parse_complete_task(message)
        elif message.startswith("删除任务"):
            return self._parse_delete_task(message)
        elif message.startswith("查看任务"):
            return self._parse_list_tasks(message)
        elif message.startswith("修改任务"):
            return self._parse_update_task(message)
        elif message.startswith("任务状态"):
            return self._parse_toggle_status(message)
        elif message in ["任务列表", "待办", "待办列表"]:
            return self._parse_list_pending_tasks()
        elif message == "帮助":
            return self._show_help()
        elif message.startswith("AI ") or message.startswith("ai ") or message.startswith("@"):
            return self._parse_ai_query(message)
        elif message.startswith("总结任务"):
            return self._parse_summarize_tasks()
        else:
            return self._try_parse_with_ai(message)

    def _try_parse_with_ai(self, message: str) -> Tuple[str, Optional[Task], str]:
        """尝试使用AI解析自然语言命令"""
        if not self.ai_available:
            return ("unknown", None, "未识别的命令，请输入'帮助'查看可用命令")
        
        try:
            from app.services.ollama_service import parse_task_from_natural_language
            
            result = parse_task_from_natural_language(message)
            if not result or result.get("command") == "unknown":
                return self._parse_ai_query(message)
            
            command = result.get("command")
            title = result.get("title", "")
            description = result.get("description", "")
            priority = result.get("priority", "medium")
            due_date = result.get("due_date", "")
            target_task = result.get("target_task", "")
            
            if command == "add" and title:
                return self._create_task(title, description, priority, due_date)
            elif command == "complete" and target_task:
                return self._parse_complete_task(f"完成任务 {target_task}")
            elif command == "delete" and target_task:
                return self._parse_delete_task(f"删除任务 {target_task}")
            elif command == "list":
                return self._parse_list_pending_tasks()
            elif command == "toggle" and target_task:
                return self._parse_toggle_status(f"任务状态 {target_task}")
            else:
                return self._parse_ai_query(message)
                
        except Exception as e:
            return ("unknown", None, f"AI解析失败: {str(e)}")

    def _create_task(self, title: str, description: str, priority: str, due_date: str) -> Tuple[str, Optional[Task], str]:
        """创建任务"""
        task_id = str(uuid.uuid4())[:8]
        task = Task(
            task_id=task_id,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date if due_date else None
        )
        
        if self.storage.add_task(task):
            return ("add", task, f"✅ 任务已添加\n📋 标题: {task.title}\n📝 描述: {task.description}\n⏰ 截止: {task.due_date or '无'}\n🔄 状态: 待办")
        else:
            return ("error", None, "任务添加失败")

    def _parse_ai_query(self, message: str) -> Tuple[str, Optional[Task], str]:
        """处理AI查询"""
        if not self.ai_available:
            return ("error", None, "AI服务不可用，请确保Ollama已启动")
        
        try:
            from app.services.ollama_service import chat_with_ai
            
            # 移除"AI "或"ai "前缀
            query = message[3:].strip() if message.lower().startswith("ai ") else message
            
            # 如果是以@开头，也移除
            if query.startswith("@"):
                query = query[1:].strip()
            
            response = chat_with_ai(query)
            if response:
                return ("ai", None, response)
            else:
                return ("error", None, "AI响应为空")
        except Exception as e:
            return ("error", None, f"AI查询失败: {str(e)}")

    def _parse_summarize_tasks(self) -> Tuple[str, Optional[Task], str]:
        """使用AI总结任务"""
        if not self.ai_available:
            return ("error", None, "AI服务不可用，请确保Ollama已启动")
        
        try:
            from app.services.ollama_service import summarize_tasks
            
            tasks = self.storage.get_all_tasks()
            tasks_dict = [task.to_dict() for task in tasks]
            summary = summarize_tasks(tasks_dict)
            
            if summary:
                return ("summary", None, summary)
            else:
                return ("error", None, "任务总结失败")
        except Exception as e:
            return ("error", None, f"任务总结失败: {str(e)}")

    def _parse_add_task(self, message: str) -> Tuple[str, Optional[Task], str]:
        content = message[4:].strip()
        if not content:
            return ("error", None, "请提供任务内容，格式：添加任务 [标题] [描述] [优先级:高/中/低] [截止日期:YYYY-MM-DD]")
        
        title = content
        description = ""
        priority = "medium"
        due_date = None
        
        priority_match = re.search(r'(优先级[:：]\s*)?(高|中|低)', content)
        if priority_match:
            priority_map = {"高": "high", "中": "medium", "低": "low"}
            priority = priority_map[priority_match.group(2)]
            title = re.sub(r'(优先级[:：]\s*)?(高|中|低)', '', title).strip()
        
        date_match = re.search(r'(截止日期[:：]\s*)?(\d{4}-\d{2}-\d{2})', content)
        if date_match:
            due_date = date_match.group(2)
            title = re.sub(r'(截止日期[:：]\s*)?(\d{4}-\d{2}-\d{2})', '', title).strip()
        else:
            date_match2 = re.search(r'(今天|明天|后天)', content)
            if date_match2:
                days_offset = {"今天": 0, "明天": 1, "后天": 2}[date_match2.group(1)]
                due_date = (datetime.now() + timedelta(days=days_offset)).strftime("%Y-%m-%d")
                title = re.sub(r'(今天|明天|后天)', '', title).strip()
        
        parts = title.split(' ', 1)
        if len(parts) > 1:
            title = parts[0]
            description = parts[1]
        else:
            title = parts[0]
        
        if not title:
            return ("error", None, "任务标题不能为空")
        
        task_id = str(uuid.uuid4())[:8]
        task = Task(
            task_id=task_id,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date
        )
        
        if self.storage.add_task(task):
            return ("add", task, f"✅ 任务已添加\n📋 标题: {task.title}\n📝 描述: {task.description}\n⏰ 截止: {task.due_date or '无'}\n🔄 状态: 待办")
        else:
            return ("error", None, "任务添加失败")

    def _parse_complete_task(self, message: str) -> Tuple[str, Optional[Task], str]:
        content = message[4:].strip()
        if not content:
            return ("error", None, "请提供任务ID或标题，格式：完成任务 [ID或标题]")
        
        tasks = self.storage.get_all_tasks()
        target_task = None
        
        for task in tasks:
            if task.task_id == content or task.title == content:
                target_task = task
                break
        
        if not target_task:
            return ("error", None, f"未找到任务: {content}")
        
        if self.storage.toggle_task_status(target_task.task_id):
            updated_task = self.storage.get_task(target_task.task_id)
            return ("complete", updated_task, f"✅ 任务已完成\n📋 {updated_task.title}")
        else:
            return ("error", None, "任务状态更新失败")

    def _parse_delete_task(self, message: str) -> Tuple[str, Optional[Task], str]:
        content = message[4:].strip()
        if not content:
            return ("error", None, "请提供任务ID或标题，格式：删除任务 [ID或标题]")
        
        tasks = self.storage.get_all_tasks()
        target_task = None
        
        for task in tasks:
            if task.task_id == content or task.title == content:
                target_task = task
                break
        
        if not target_task:
            return ("error", None, f"未找到任务: {content}")
        
        if self.storage.delete_task(target_task.task_id):
            return ("delete", target_task, f"🗑️ 任务已删除\n📋 {target_task.title}")
        else:
            return ("error", None, "任务删除失败")

    def _parse_update_task(self, message: str) -> Tuple[str, Optional[Task], str]:
        content = message[4:].strip()
        if not content:
            return ("error", None, "请提供任务ID和更新内容，格式：修改任务 [ID] [新标题]")
        
        parts = content.split(' ', 1)
        if len(parts) < 2:
            return ("error", None, "请提供任务ID和新标题")
        
        task_id_or_title = parts[0]
        new_content = parts[1]
        
        tasks = self.storage.get_all_tasks()
        target_task = None
        
        for task in tasks:
            if task.task_id == task_id_or_title or task.title == task_id_or_title:
                target_task = task
                break
        
        if not target_task:
            return ("error", None, f"未找到任务: {task_id_or_title}")
        
        new_title = new_content
        new_description = ""
        
        if self.storage.update_task(target_task.task_id, title=new_title, description=new_description):
            updated_task = self.storage.get_task(target_task.task_id)
            return ("update", updated_task, f"🔄 任务已更新\n📋 标题: {updated_task.title}")
        else:
            return ("error", None, "任务更新失败")

    def _parse_toggle_status(self, message: str) -> Tuple[str, Optional[Task], str]:
        content = message[4:].strip()
        if not content:
            return ("error", None, "请提供任务ID或标题，格式：任务状态 [ID或标题]")
        
        tasks = self.storage.get_all_tasks()
        target_task = None
        
        for task in tasks:
            if task.task_id == content or task.title == content:
                target_task = task
                break
        
        if not target_task:
            return ("error", None, f"未找到任务: {content}")
        
        if self.storage.toggle_task_status(target_task.task_id):
            updated_task = self.storage.get_task(target_task.task_id)
            status_text = "✅ 已完成" if updated_task.status == "completed" else "🔄 待办"
            return ("toggle", updated_task, f"🔄 任务状态已切换\n📋 {updated_task.title}\n状态: {status_text}")
        else:
            return ("error", None, "任务状态切换失败")

    def _parse_list_tasks(self, message: str) -> Tuple[str, Optional[Task], str]:
        content = message[4:].strip()
        
        if content == "全部":
            tasks = self.storage.get_all_tasks()
        elif content == "待办":
            tasks = self.storage.get_pending_tasks()
        elif content == "已完成":
            tasks = self.storage.get_completed_tasks()
        elif content == "逾期":
            tasks = self.storage.get_overdue_tasks()
        elif content == "今日":
            tasks = self.storage.get_today_due_tasks()
        else:
            tasks = self.storage.get_all_tasks()
        
        if not tasks:
            return ("list", None, "暂无任务")
        
        result = "📋 任务列表\n"
        result += "────────────\n"
        
        for i, task in enumerate(tasks, 1):
            status_icon = "✅" if task.status == "completed" else "🔄"
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.priority, "⚪")
            
            result += f"{i}. {status_icon} {priority_icon} [{task.task_id}] {task.title}\n"
            if task.due_date:
                result += f"   ⏰ 截止: {task.due_date}\n"
            if task.description:
                result += f"   📝 {task.description}\n"
        
        return ("list", None, result)

    def _parse_list_pending_tasks(self) -> Tuple[str, Optional[Task], str]:
        tasks = self.storage.get_pending_tasks()
        
        if not tasks:
            return ("list", None, "🎉 暂无待办任务！")
        
        result = "📋 待办任务\n"
        result += "────────────\n"
        
        for i, task in enumerate(tasks, 1):
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.priority, "⚪")
            
            result += f"{i}. 🔄 {priority_icon} [{task.task_id}] {task.title}\n"
            if task.due_date:
                result += f"   ⏰ 截止: {task.due_date}\n"
            if task.description:
                result += f"   📝 {task.description}\n"
        
        return ("list", None, result)

    def _show_help(self) -> Tuple[str, Optional[Task], str]:
        help_text = """
🤖 任务管理助手命令列表：

📝 添加任务:
  添加任务 [标题] [描述] [优先级:高/中/低] [截止日期:YYYY-MM-DD]
  示例: 添加任务 完成报告 下午3点前 优先级:高 截止日期:2024-01-15
  示例: 添加任务 开会 明天

✅ 完成任务:
  完成任务 [ID或标题]
  示例: 完成任务 abc12345
  示例: 完成任务 完成报告

🗑️ 删除任务:
  删除任务 [ID或标题]

🔄 修改任务:
  修改任务 [ID或标题] [新标题]

📋 查看任务:
  任务列表 / 待办           - 查看待办任务
  查看任务 全部             - 查看所有任务
  查看任务 待办             - 查看待办任务
  查看任务 已完成           - 查看已完成任务
  查看任务 逾期             - 查看逾期任务
  查看任务 今日             - 查看今日到期任务

🔄 切换状态:
  任务状态 [ID或标题]       - 切换任务完成/待办状态

🤖 AI功能 (需要Ollama):
  AI [问题]                 - 与AI聊天
  @[问题]                   - 与AI聊天(简写)
  总结任务                  - 使用AI总结任务列表
  自然语言命令              - 直接用中文描述任务操作

❓ 帮助                    - 显示此帮助信息
        """.strip()
        return ("help", None, help_text)