import json
import hashlib
import os
import logging
import time
from typing import Optional, Any, Dict, Tuple

logger = logging.getLogger(__name__)

class CacheManager:
    """缓存管理器
    用于管理文件处理结果的缓存，提高系统性能
    """
    
    def __init__(self, max_memory_cache_size: int = 100, memory_cache_ttl: int = 3600):
        """初始化缓存管理器
        
        Args:
            max_memory_cache_size: 内存缓存最大条目数
            memory_cache_ttl: 内存缓存过期时间（秒）
        """
        try:
            # 尝试导入redis模块
            import redis
            # 尝试连接Redis服务器
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True
            )
            # 测试连接
            self.redis_client.ping()
            self.enabled = True
            logger.info("Redis缓存已启用")
        except ImportError:
            # 如果redis模块不存在，使用内存缓存
            logger.warning("Redis模块不存在，使用内存缓存")
            self.redis_client = None
            self.enabled = False
            self.memory_cache = {}
            self.memory_cache_metadata = {}
        except Exception as e:
            # 如果Redis连接失败，使用内存缓存作为备选
            logger.warning(f"Redis连接失败，使用内存缓存: {str(e)}")
            self.redis_client = None
            self.enabled = False
            self.memory_cache = {}
            self.memory_cache_metadata = {}
        
        # 内存缓存配置
        self.max_memory_cache_size = max_memory_cache_size
        self.memory_cache_ttl = memory_cache_ttl
        
        # 缓存统计信息
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_sets = 0
        self.cache_errors = 0
    
    def generate_cache_key(self, file_content: bytes, params: Dict[str, Any] = None) -> str:
        """
        生成缓存键
        
        Args:
            file_content: 文件内容
            params: 处理参数
        
        Returns:
            缓存键字符串
        """
        # 使用文件内容的哈希值作为基础
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # 如果有参数，也将参数加入哈希计算
        if params:
            # 只包含关键参数，减少键的大小
            filtered_params = {k: v for k, v in params.items() if k in ['mode', 'time_option', 'shift_type']}
            params_str = json.dumps(filtered_params, sort_keys=True)
            combined = f"{file_hash}:{params_str}"
            return hashlib.sha256(combined.encode()).hexdigest()
        
        return file_hash
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
        
        Returns:
            缓存值或None
        """
        try:
            # 检查内存缓存是否过期
            if not self.enabled or not self.redis_client:
                self._cleanup_expired_memory_cache()
            
            if self.enabled and self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    self.cache_hits += 1
                    return json.loads(value)
            else:
                # 使用内存缓存
                if key in self.memory_cache:
                    # 更新访问时间
                    self.memory_cache_metadata[key]['last_accessed'] = time.time()
                    self.cache_hits += 1
                    return self.memory_cache[key]
            
            self.cache_misses += 1
        except Exception as e:
            logger.error(f"获取缓存失败: {str(e)}")
            self.cache_errors += 1
        
        return None
    
    def set(self, key: str, value: Any, expire_seconds: int = 3600) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            expire_seconds: 过期时间（秒）
        
        Returns:
            是否成功
        """
        try:
            if self.enabled and self.redis_client:
                self.redis_client.setex(key, expire_seconds, json.dumps(value, ensure_ascii=False))
            else:
                # 使用内存缓存
                # 检查缓存大小限制
                self._enforce_memory_cache_limit()
                
                # 存储值和元数据
                self.memory_cache[key] = value
                self.memory_cache_metadata[key] = {
                    'created': time.time(),
                    'last_accessed': time.time(),
                    'expire_at': time.time() + expire_seconds
                }
            
            self.cache_sets += 1
            return True
        except Exception as e:
            logger.error(f"设置缓存失败: {str(e)}")
            self.cache_errors += 1
            return False
    
    def delete(self, key: str) -> bool:
        """
        删除缓存值
        
        Args:
            key: 缓存键
        
        Returns:
            是否成功
        """
        try:
            if self.enabled and self.redis_client:
                self.redis_client.delete(key)
            else:
                # 使用内存缓存
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    del self.memory_cache_metadata[key]
            return True
        except Exception as e:
            logger.error(f"删除缓存失败: {str(e)}")
            self.cache_errors += 1
            return False
    
    def clear(self) -> bool:
        """
        清空所有缓存
        
        Returns:
            是否成功
        """
        try:
            if self.enabled and self.redis_client:
                self.redis_client.flushdb()
            else:
                # 使用内存缓存
                self.memory_cache.clear()
                self.memory_cache_metadata.clear()
            
            # 重置统计信息
            self.cache_hits = 0
            self.cache_misses = 0
            self.cache_sets = 0
            self.cache_errors = 0
            
            return True
        except Exception as e:
            logger.error(f"清空缓存失败: {str(e)}")
            self.cache_errors += 1
            return False
    
    def _cleanup_expired_memory_cache(self):
        """
        清理过期的内存缓存
        """
        current_time = time.time()
        expired_keys = []
        
        for key, metadata in self.memory_cache_metadata.items():
            if current_time > metadata['expire_at']:
                expired_keys.append(key)
        
        for key in expired_keys:
            if key in self.memory_cache:
                del self.memory_cache[key]
                del self.memory_cache_metadata[key]
        
        if expired_keys:
            logger.info(f"清理了 {len(expired_keys)} 个过期的内存缓存项")
    
    def _enforce_memory_cache_limit(self):
        """
        强制内存缓存大小限制，使用LRU策略
        """
        if len(self.memory_cache) >= self.max_memory_cache_size:
            # 按最后访问时间排序，删除最旧的项
            sorted_items = sorted(
                self.memory_cache_metadata.items(),
                key=lambda x: x[1]['last_accessed']
            )
            
            # 删除超出限制的项
            items_to_delete = len(self.memory_cache) - self.max_memory_cache_size + 1
            for key, _ in sorted_items[:items_to_delete]:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    del self.memory_cache_metadata[key]
            
            logger.info(f"内存缓存达到限制，删除了 {items_to_delete} 个最旧的缓存项")
    
    def get_stats(self) -> Dict[str, int]:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'sets': self.cache_sets,
            'errors': self.cache_errors,
            'memory_cache_size': len(self.memory_cache) if not self.enabled or not self.redis_client else 0
        }

# 创建全局缓存管理器实例
cache_manager = CacheManager()
