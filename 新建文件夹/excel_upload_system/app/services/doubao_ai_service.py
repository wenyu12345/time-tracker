import os
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger('doubao_ai_service')

class DoubaoAIService:
    def __init__(self):
        # 从环境变量获取API密钥，也可以从配置文件读取
        self.api_key = os.environ.get('DOUBAO_API_KEY', '')
        self.api_base_url = 'https://api.doubao.com/v1/chat/completions'
    
    def generate_content(self, prompt: str, model: str = 'doubao-pro', temperature: float = 0.7) -> Optional[str]:
        """
        调用豆包AI生成内容
        
        Args:
            prompt: 用户提示词
            model: 使用的模型名称
            temperature: 生成温度，值越大越随机
            
        Returns:
            生成的内容，如果失败返回None
        """
        if not self.api_key:
            logger.error('未配置豆包AI API密钥')
            return None
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': model,
            'messages': [{
                'role': 'user',
                'content': prompt
            }],
            'temperature': temperature
        }
        
        try:
            response = requests.post(self.api_base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result.get('choices', [{}])[0].get('message', {}).get('content')
            
        except Exception as e:
            logger.error(f'豆包AI内容生成失败: {str(e)}')
            return None
    
    def generate_summary(self, text: str, max_length: int = 200) -> Optional[str]:
        """
        生成文本摘要
        
        Args:
            text: 需要摘要的文本
            max_length: 摘要最大长度
            
        Returns:
            生成的摘要
        """
        prompt = f"请为以下文本生成一个简洁的摘要（不超过{max_length}字）：\n\n{text}"
        return self.generate_content(prompt)
    
    def generate_notes_from_keywords(self, keywords: str) -> Optional[str]:
        """
        根据关键词生成笔记内容
        
        Args:
            keywords: 关键词
            
        Returns:
            生成的笔记内容
        """
        prompt = f"请根据以下关键词生成一份详细的笔记内容，格式要清晰，内容要丰富：\n\n关键词：{keywords}"
        return self.generate_content(prompt)
    
    def suggest_tags(self, content: str, max_tags: int = 5) -> Optional[list]:
        """
        智能推荐标签
        
        Args:
            content: 笔记内容
            max_tags: 最大标签数量
            
        Returns:
            推荐的标签列表
        """
        prompt = f"请为以下文本推荐最多{max_tags}个合适的标签，标签要简洁、准确，用逗号分隔：\n\n{content}"
        result = self.generate_content(prompt)
        if result:
            # 解析结果为标签列表
            tags = [tag.strip() for tag in result.split(',') if tag.strip()]
            return tags[:max_tags]
        return []
    
    def optimize_text(self, text: str, improvement_type: str = 'all') -> Optional[str]:
        """
        优化文本内容
        
        Args:
            text: 需要优化的文本
            improvement_type: 优化类型，可选'all'、'grammar'、'expression'
            
        Returns:
            优化后的文本
        """
        if improvement_type == 'grammar':
            prompt = f"请修正以下文本中的语法错误：\n\n{text}"
        elif improvement_type == 'expression':
            prompt = f"请优化以下文本的表达方式，使其更加流畅、专业：\n\n{text}"
        else:
            prompt = f"请全面优化以下文本，包括语法纠错和表达优化：\n\n{text}"
        
        return self.generate_content(prompt)
    
    def enable_api_key(self, api_key: str) -> bool:
        """
        设置API密钥
        
        Args:
            api_key: 豆包AI API密钥
            
        Returns:
            是否设置成功
        """
        try:
            # 验证API密钥是否有效
            self.api_key = api_key
            test_response = self.generate_content('测试API连接')
            return test_response is not None
        except:
            return False
    
    def is_api_enabled(self) -> bool:
        """
        检查API是否已启用
        
        Returns:
            API是否已启用
        """
        return bool(self.api_key)

# 创建单例实例
doubao_ai_service = DoubaoAIService()