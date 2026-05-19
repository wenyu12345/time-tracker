import concurrent.futures
import logging
import os
import time
from typing import Optional, Callable, Any, Dict, List

logger = logging.getLogger(__name__)

class AsyncTaskManager:
    """异步任务管理器
    使用ThreadPoolExecutor来处理异步任务，避免阻塞主线程
    """
    
    def __init__(self, max_workers: Optional[int] = None):
        """
        初始化异步任务管理器
        
        Args:
            max_workers: 最大工作线程数，默认根据CPU核心数动态计算
        """
        # 动态计算线程池大小
        if max_workers is None:
            cpu_count = os.cpu_count() or 4
            # 根据CPU核心数和系统负载动态调整
            self.max_workers = min(cpu_count * 2, 8)  # 最多8个线程
        else:
            self.max_workers = max_workers
        
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="async_task_"
        )
        
        # 任务统计信息
        self.task_stats = {
            'submitted': 0,
            'completed': 0,
            'failed': 0,
            'running': 0
        }
        
        # 任务队列管理
        self.pending_tasks: List[concurrent.futures.Future] = []
        self.max_pending_tasks = self.max_workers * 2  # 最大待处理任务数
        
        logger.info(f"异步任务管理器已初始化，最大工作线程数: {self.max_workers}")
        logger.info(f"最大待处理任务数: {self.max_pending_tasks}")
    
    def submit_task(self, task: Callable, *args, **kwargs) -> concurrent.futures.Future:
        """
        提交异步任务
        
        Args:
            task: 任务函数
            *args: 任务参数
            **kwargs: 任务关键字参数
        
        Returns:
            Future对象
        """
        try:
            # 清理已完成的任务
            self._cleanup_completed_tasks()
            
            # 检查任务队列大小
            if len(self.pending_tasks) >= self.max_pending_tasks:
                logger.warning(f"任务队列已满，等待任务完成...")
                # 等待一个任务完成
                if self.pending_tasks:
                    concurrent.futures.wait(
                        self.pending_tasks[:1],
                        return_when=concurrent.futures.FIRST_COMPLETED
                    )
                self._cleanup_completed_tasks()
            
            future = self.executor.submit(task, *args, **kwargs)
            self.task_stats['submitted'] += 1
            self.task_stats['running'] += 1
            self.pending_tasks.append(future)
            
            # 添加完成回调
            def task_completed_callback(fut):
                self.task_stats['completed'] += 1
                self.task_stats['running'] -= 1
                try:
                    # 检查任务是否成功
                    fut.result()
                except Exception as e:
                    self.task_stats['failed'] += 1
                    logger.error(f"任务执行失败: {str(e)}")
            
            future.add_done_callback(task_completed_callback)
            
            logger.info(f"异步任务已提交: {task.__name__}, 当前运行任务数: {self.task_stats['running']}")
            return future
        except Exception as e:
            logger.error(f"提交异步任务失败: {str(e)}")
            self.task_stats['failed'] += 1
            raise
    
    def map_tasks(self, task: Callable, *iterables) -> list:
        """
        映射多个任务
        
        Args:
            task: 任务函数
            *iterables: 可迭代参数
        
        Returns:
            任务结果列表
        """
        try:
            # 清理已完成的任务
            self._cleanup_completed_tasks()
            
            results = list(self.executor.map(task, *iterables))
            self.task_stats['submitted'] += len(results)
            self.task_stats['completed'] += len(results)
            
            logger.info(f"映射任务已完成: {task.__name__}, 处理了 {len(results)} 个任务")
            return results
        except Exception as e:
            logger.error(f"映射任务失败: {str(e)}")
            self.task_stats['failed'] += 1
            raise
    
    def shutdown(self, wait: bool = True):
        """
        关闭线程池
        
        Args:
            wait: 是否等待所有任务完成
        """
        try:
            # 清理已完成的任务
            self._cleanup_completed_tasks()
            
            logger.info(f"正在关闭线程池，等待所有任务完成: {wait}")
            logger.info(f"当前任务状态: {self.task_stats}")
            
            self.executor.shutdown(wait=wait)
            logger.info(f"线程池已关闭，wait={wait}")
        except Exception as e:
            logger.error(f"关闭线程池失败: {str(e)}")
            raise
    
    def get_task_result(self, future: concurrent.futures.Future, timeout: Optional[float] = None) -> Any:
        """
        获取任务结果
        
        Args:
            future: Future对象
            timeout: 超时时间
        
        Returns:
            任务结果
        """
        try:
            result = future.result(timeout=timeout)
            logger.info("任务结果已获取")
            return result
        except concurrent.futures.TimeoutError:
            logger.error("任务执行超时")
            self.task_stats['failed'] += 1
            raise
        except Exception as e:
            logger.error(f"获取任务结果失败: {str(e)}")
            self.task_stats['failed'] += 1
            raise
    
    def _cleanup_completed_tasks(self):
        """
        清理已完成的任务
        """
        completed_tasks = []
        for future in self.pending_tasks:
            if future.done():
                completed_tasks.append(future)
        
        for future in completed_tasks:
            self.pending_tasks.remove(future)
        
        if completed_tasks:
            logger.debug(f"清理了 {len(completed_tasks)} 个已完成的任务")
    
    def get_stats(self) -> Dict[str, int]:
        """
        获取任务统计信息
        
        Returns:
            统计信息字典
        """
        # 清理已完成的任务
        self._cleanup_completed_tasks()
        
        return {
            **self.task_stats,
            'pending': len(self.pending_tasks),
            'max_workers': self.max_workers
        }

# 创建全局异步任务管理器实例
async_task_manager = AsyncTaskManager()
