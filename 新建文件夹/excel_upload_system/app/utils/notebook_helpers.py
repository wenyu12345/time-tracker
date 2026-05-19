from datetime import datetime, timedelta
import re
import json
from typing import Optional, List, Dict
import hashlib

class NotebookHelpers:
    @staticmethod
    def format_datetime(datetime_str: Optional[str]) -> str:
        """
        格式化日期时间字符串
        
        Args:
            datetime_str: ISO格式的日期时间字符串
            
        Returns:
            格式化后的日期时间字符串，如"2023-05-20 14:30"
        """
        if not datetime_str:
            return ""
        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return datetime_str
    
    @staticmethod
    def format_date(date_str: Optional[str]) -> str:
        """
        格式化日期字符串
        
        Args:
            date_str: ISO格式的日期时间字符串
            
        Returns:
            格式化后的日期字符串，如"2023-05-20"
        """
        if not date_str:
            return ""
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d")
        except:
            return date_str[:10] if date_str else ""
    
    @staticmethod
    def calculate_reading_time(text: str, words_per_minute: int = 300) -> int:
        """
        计算阅读时间
        
        Args:
            text: 文本内容
            words_per_minute: 每分钟阅读的字数
            
        Returns:
            预计阅读时间（分钟）
        """
        if not text:
            return 0
        # 简单估算：中文字符按每个字算，英文字符按空格分割
        # 对于富文本，先尝试提取纯文本
        plain_text = NotebookHelpers.extract_plain_text(text)
        
        # 中文字符数
        chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', plain_text))
        # 英文字词数（按空格分割）
        english_words = len(plain_text.split())
        
        total_words = chinese_chars + english_words
        return max(1, round(total_words / words_per_minute))
    
    @staticmethod
    def extract_plain_text(html_content: str) -> str:
        """
        从HTML内容中提取纯文本
        
        Args:
            html_content: HTML内容
            
        Returns:
            提取的纯文本
        """
        if isinstance(html_content, dict):
            # 处理可能是结构化内容的情况
            html_content = json.dumps(html_content)
        
        # 移除HTML标签
        plain_text = re.sub(r'<[^>]+>', '', str(html_content))
        # 移除多余的空白字符
        plain_text = re.sub(r'\s+', ' ', plain_text)
        return plain_text.strip()
    
    @staticmethod
    def generate_unique_id(prefix: str = 'id') -> str:
        """
        生成唯一ID
        
        Args:
            prefix: ID前缀
            
        Returns:
            唯一ID字符串
        """
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        random_part = hashlib.md5(timestamp.encode()).hexdigest()[:8]
        return f"{prefix}_{timestamp}_{random_part}"
    
    @staticmethod
    def get_priority_color(priority: str or int) -> str:
        """
        获取优先级对应的颜色
        
        Args:
            priority: 优先级值
            
        Returns:
            颜色代码
        """
        priority_map = {
            1: '#dc3545',  # 红色 - 最高
            2: '#fd7e14',  # 橙色
            3: '#ffc107',  # 黄色 - 中等
            4: '#28a745',  # 绿色
            5: '#6c757d',  # 灰色 - 最低
            'high': '#dc3545',
            'medium': '#ffc107',
            'low': '#28a745'
        }
        return priority_map.get(priority, '#6c757d')
    
    @staticmethod
    def get_task_status_badge(status: str) -> str:
        """
        获取任务状态的徽章样式
        
        Args:
            status: 任务状态
            
        Returns:
            Bootstrap徽章类名
        """
        status_map = {
            'todo': 'badge-secondary',
            'in_progress': 'badge-primary',
            'done': 'badge-success',
            'cancelled': 'badge-danger',
            'pending': 'badge-warning'
        }
        return status_map.get(status, 'badge-secondary')
    
    @staticmethod
    def parse_reminder_time(reminder_str: str) -> Optional[str]:
        """
        解析提醒时间字符串
        
        Args:
            reminder_str: 提醒时间字符串，如"5分钟前"、"1小时后"、"明天10:00"
            
        Returns:
            ISO格式的日期时间字符串
        """
        now = datetime.now()
        
        # 处理相对时间
        if '分钟前' in reminder_str:
            minutes = int(re.search(r'(\d+)分钟前', reminder_str).group(1))
            return (now - timedelta(minutes=minutes)).isoformat()
        elif '小时前' in reminder_str:
            hours = int(re.search(r'(\d+)小时前', reminder_str).group(1))
            return (now - timedelta(hours=hours)).isoformat()
        elif '天后' in reminder_str:
            days = int(re.search(r'(\d+)天后', reminder_str).group(1))
            return (now + timedelta(days=days)).isoformat()
        elif '分钟后' in reminder_str:
            minutes = int(re.search(r'(\d+)分钟后', reminder_str).group(1))
            return (now + timedelta(minutes=minutes)).isoformat()
        elif '小时后' in reminder_str:
            hours = int(re.search(r'(\d+)小时后', reminder_str).group(1))
            return (now + timedelta(hours=hours)).isoformat()
        elif reminder_str == '明天':
            return (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0).isoformat()
        elif '明天' in reminder_str:
            # 格式：明天10:00
            time_part = re.search(r'明天(\d+):(\d+)', reminder_str)
            if time_part:
                hour, minute = map(int, time_part.groups())
                return (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat()
        
        # 尝试解析绝对时间
        try:
            # 尝试不同的日期格式
            formats = ['%Y-%m-%d %H:%M', '%Y-%m-%d', '%H:%M']
            for fmt in formats:
                try:
                    dt = datetime.strptime(reminder_str, fmt)
                    if fmt == '%H:%M':
                        # 如果只有时间，使用今天的日期
                        dt = dt.replace(year=now.year, month=now.month, day=now.day)
                    return dt.isoformat()
                except ValueError:
                    continue
        except:
            pass
        
        return None
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        验证邮箱格式
        
        Args:
            email: 邮箱地址
            
        Returns:
            是否为有效邮箱
        """
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        清理文件名，移除不允许的字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        # 移除或替换不允许的字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        # 移除控制字符
        filename = ''.join(char for char in filename if ord(char) > 31)
        # 限制文件名长度
        return filename[:200]  # 限制为200个字符

# 创建单例实例
notebook_helpers = NotebookHelpers()