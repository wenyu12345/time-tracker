from datetime import datetime
from typing import List, Dict, Optional
import json
import os

# 数据存储文件路径
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'notebook')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
NOTES_FILE = os.path.join(DATA_DIR, 'notes.json')
TASKS_FILE = os.path.join(DATA_DIR, 'tasks.json')

# 确保数据目录存在
def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

# 基础模型类
class BaseModel:
    def __init__(self):
        ensure_data_dir()
    
    def save_data(self, data, file_path):
        """保存数据到JSON文件"""
        ensure_data_dir()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_data(self, file_path):
        """从JSON文件加载数据"""
        ensure_data_dir()
        if not os.path.exists(file_path):
            return {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

# 用户模型
class User(BaseModel):
    def __init__(self):
        super().__init__()
    
    def create_user(self, user_id: str, username: str, email: str, password_hash: str) -> dict:
        """创建新用户"""
        users = self.load_data(USERS_FILE)
        user = {
            'user_id': user_id,
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'avatar': '',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        users[user_id] = user
        self.save_data(users, USERS_FILE)
        return user
    
    def get_user(self, user_id: str) -> Optional[dict]:
        """获取用户信息"""
        users = self.load_data(USERS_FILE)
        return users.get(user_id)
    
    def update_user(self, user_id: str, updates: dict) -> Optional[dict]:
        """更新用户信息"""
        users = self.load_data(USERS_FILE)
        if user_id not in users:
            return None
        users[user_id].update(updates)
        users[user_id]['updated_at'] = datetime.now().isoformat()
        self.save_data(users, USERS_FILE)
        return users[user_id]

# 笔记模型
class Note(BaseModel):
    def __init__(self):
        super().__init__()
    
    def create_note(self, user_id: str, title: str, content: dict, tags: List[str] = None, folder_id: str = None) -> dict:
        """创建新笔记"""
        notes = self.load_data(NOTES_FILE)
        note_id = f"note_{len(notes) + 1}"
        note = {
            'note_id': note_id,
            'user_id': user_id,
            'title': title,
            'content': content,
            'tags': tags or [],
            'folder_id': folder_id,
            'priority': 3,  # 默认中等优先级
            'status': 'draft',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'version': 1,
            'history': [{'version': 1, 'content': content, 'created_at': datetime.now().isoformat()}]
        }
        notes[note_id] = note
        self.save_data(notes, NOTES_FILE)
        return note
    
    def get_note(self, note_id: str) -> Optional[dict]:
        """获取笔记信息"""
        notes = self.load_data(NOTES_FILE)
        return notes.get(note_id)
    
    def update_note(self, note_id: str, updates: dict) -> Optional[dict]:
        """更新笔记信息"""
        notes = self.load_data(NOTES_FILE)
        if note_id not in notes:
            return None
        
        # 如果更新内容，添加历史记录
        if 'content' in updates:
            notes[note_id]['version'] += 1
            notes[note_id]['history'].append({
                'version': notes[note_id]['version'],
                'content': updates['content'],
                'created_at': datetime.now().isoformat()
            })
        
        notes[note_id].update(updates)
        notes[note_id]['updated_at'] = datetime.now().isoformat()
        self.save_data(notes, NOTES_FILE)
        return notes[note_id]
    
    def delete_note(self, note_id: str) -> bool:
        """删除笔记"""
        notes = self.load_data(NOTES_FILE)
        if note_id not in notes:
            return False
        del notes[note_id]
        self.save_data(notes, NOTES_FILE)
        return True
    
    def get_user_notes(self, user_id: str) -> List[dict]:
        """获取用户的所有笔记"""
        notes = self.load_data(NOTES_FILE)
        return [note for note in notes.values() if note['user_id'] == user_id]

# 计划任务模型
class Task(BaseModel):
    def __init__(self):
        super().__init__()
    
    def create_task(self, user_id: str, title: str, description: str, 
                   start_time: str, end_time: str, priority: str = 'medium',
                   reminder_time: str = None) -> dict:
        """创建新计划任务"""
        tasks = self.load_data(TASKS_FILE)
        task_id = f"task_{len(tasks) + 1}"
        task = {
            'task_id': task_id,
            'user_id': user_id,
            'title': title,
            'description': description,
            'start_time': start_time,
            'end_time': end_time,
            'priority': priority,
            'status': 'todo',
            'reminder_time': reminder_time,
            'completed_at': None,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        tasks[task_id] = task
        self.save_data(tasks, TASKS_FILE)
        return task
    
    def get_task(self, task_id: str) -> Optional[dict]:
        """获取任务信息"""
        tasks = self.load_data(TASKS_FILE)
        return tasks.get(task_id)
    
    def update_task(self, task_id: str, updates: dict) -> Optional[dict]:
        """更新任务信息"""
        tasks = self.load_data(TASKS_FILE)
        if task_id not in tasks:
            return None
        
        # 如果标记为完成，记录完成时间
        if updates.get('status') == 'done' and tasks[task_id]['status'] != 'done':
            updates['completed_at'] = datetime.now().isoformat()
        
        tasks[task_id].update(updates)
        tasks[task_id]['updated_at'] = datetime.now().isoformat()
        self.save_data(tasks, TASKS_FILE)
        return tasks[task_id]
    
    def get_user_tasks(self, user_id: str) -> List[dict]:
        """获取用户的所有任务"""
        tasks = self.load_data(TASKS_FILE)
        return [task for task in tasks.values() if task['user_id'] == user_id]
    
    def get_pending_reminders(self) -> List[dict]:
        """获取需要提醒的任务"""
        tasks = self.load_data(TASKS_FILE)
        now = datetime.now().isoformat()
        pending = []
        
        for task in tasks.values():
            if task['status'] != 'done' and task['reminder_time'] and task['reminder_time'] <= now:
                pending.append(task)
        
        return pending