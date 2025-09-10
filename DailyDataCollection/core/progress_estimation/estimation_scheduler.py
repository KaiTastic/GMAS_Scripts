"""
估算调度器 - 智能任务调度和资源管理
"""

import asyncio
import threading
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from queue import PriorityQueue, Empty

from .estimation_facade import EstimationFacade
from .core_estimator import EstimationConfig, EstimationMode

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class EstimationTask:
    """估算任务"""
    task_id: str
    task_type: str  # 'project', 'mapsheet', 'batch', 'real_time'
    parameters: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    callback: Optional[Callable] = None
    created_at: datetime = None
    started_at: datetime = None
    completed_at: datetime = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def __lt__(self, other):
        """优先级比较（优先级数值越大，优先级越高）"""
        return self.priority.value > other.priority.value


class EstimationScheduler:
    """估算调度器 - 管理多个估算任务的并发执行"""
    
    def __init__(self, max_workers: int = 4, workspace_path: str = None):
        """
        初始化调度器
        
        Args:
            max_workers: 最大工作线程数
            workspace_path: 工作空间路径
        """
        self.max_workers = max_workers
        self.workspace_path = workspace_path
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.facade = EstimationFacade(workspace_path)
        
        # 任务管理
        self.task_queue = PriorityQueue()
        self.running_tasks: Dict[str, EstimationTask] = {}
        self.completed_tasks: Dict[str, EstimationTask] = {}
        self.all_tasks: Dict[str, EstimationTask] = {}
        
        # 状态管理
        self.is_running = False
        self._shutdown_event = threading.Event()
        self._worker_thread = None
        
        # 统计信息
        self.stats = {
            'total_submitted': 0,
            'total_completed': 0,
            'total_failed': 0,
            'start_time': None
        }
        
        logger.info(f"估算调度器初始化完成 - 最大工作线程: {max_workers}")
    
    def submit_project_estimation(self, 
                                 task_id: str,
                                 target_points: int,
                                 current_points: int = None,
                                 confidence_level: float = 0.8,
                                 priority: TaskPriority = TaskPriority.NORMAL,
                                 callback: Callable = None) -> str:
        """
        提交项目估算任务
        
        Args:
            task_id: 任务ID
            target_points: 目标点数
            current_points: 当前点数
            confidence_level: 置信水平
            priority: 任务优先级
            callback: 回调函数
            
        Returns:
            str: 任务ID
        """
        task = EstimationTask(
            task_id=task_id,
            task_type='project',
            parameters={
                'target_points': target_points,
                'current_points': current_points,
                'confidence_level': confidence_level
            },
            priority=priority,
            callback=callback
        )
        
        return self._submit_task(task)
    
    def submit_batch_estimation(self, 
                               task_id: str,
                               mapsheet_list: List[str],
                               confidence_level: float = 0.8,
                               priority: TaskPriority = TaskPriority.NORMAL,
                               callback: Callable = None) -> str:
        """
        提交批量估算任务
        
        Args:
            task_id: 任务ID
            mapsheet_list: 图幅列表
            confidence_level: 置信水平
            priority: 任务优先级
            callback: 回调函数
            
        Returns:
            str: 任务ID
        """
        task = EstimationTask(
            task_id=task_id,
            task_type='batch',
            parameters={
                'mapsheet_list': mapsheet_list,
                'confidence_level': confidence_level
            },
            priority=priority,
            callback=callback
        )
        
        return self._submit_task(task)
    
    def submit_mapsheet_estimation(self,
                                  task_id: str,
                                  mapsheet_no: str,
                                  confidence_level: float = 0.8,
                                  priority: TaskPriority = TaskPriority.NORMAL,
                                  callback: Callable = None) -> str:
        """
        提交单个图幅估算任务
        
        Args:
            task_id: 任务ID
            mapsheet_no: 图幅编号
            confidence_level: 置信水平
            priority: 任务优先级
            callback: 回调函数
            
        Returns:
            str: 任务ID
        """
        task = EstimationTask(
            task_id=task_id,
            task_type='mapsheet',
            parameters={
                'mapsheet_no': mapsheet_no,
                'confidence_level': confidence_level
            },
            priority=priority,
            callback=callback
        )
        
        return self._submit_task(task)
    
    def submit_real_time_estimation(self,
                                   task_id: str,
                                   target_points: int,
                                   current_points: int = None,
                                   update_interval_hours: int = 1,
                                   priority: TaskPriority = TaskPriority.HIGH,
                                   callback: Callable = None) -> str:
        """
        提交实时估算任务
        
        Args:
            task_id: 任务ID
            target_points: 目标点数
            current_points: 当前点数
            update_interval_hours: 更新间隔
            priority: 任务优先级
            callback: 回调函数
            
        Returns:
            str: 任务ID
        """
        task = EstimationTask(
            task_id=task_id,
            task_type='real_time',
            parameters={
                'target_points': target_points,
                'current_points': current_points,
                'update_interval_hours': update_interval_hours
            },
            priority=priority,
            callback=callback
        )
        
        return self._submit_task(task)
    
    def _submit_task(self, task: EstimationTask) -> str:
        """提交任务到队列"""
        try:
            self.all_tasks[task.task_id] = task
            self.task_queue.put(task)
            self.stats['total_submitted'] += 1
            
            logger.info(f"任务已提交: {task.task_id} ({task.task_type}, 优先级: {task.priority.name})")
            
            # 如果调度器未运行，自动启动
            if not self.is_running:
                self.start_processing()
            
            return task.task_id
            
        except Exception as e:
            logger.error(f"提交任务失败 {task.task_id}: {e}")
            raise
    
    def start_processing(self):
        """开始处理任务队列"""
        if self.is_running:
            logger.warning("调度器已在运行")
            return
        
        self.is_running = True
        self.stats['start_time'] = datetime.now()
        self._shutdown_event.clear()
        
        # 启动工作线程
        self._worker_thread = threading.Thread(target=self._process_tasks, daemon=True)
        self._worker_thread.start()
        
        logger.info("估算调度器已启动")
    
    def stop_processing(self, wait_for_completion: bool = True):
        """停止处理任务队列"""
        if not self.is_running:
            logger.warning("调度器未运行")
            return
        
        logger.info("正在停止估算调度器...")
        
        self.is_running = False
        self._shutdown_event.set()
        
        # 等待工作线程完成
        if self._worker_thread and wait_for_completion:
            self._worker_thread.join(timeout=30)
        
        # 关闭线程池
        self.executor.shutdown(wait=wait_for_completion)
        
        logger.info("估算调度器已停止")
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        try:
            if task_id in self.all_tasks:
                task = self.all_tasks[task_id]
                
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.CANCELLED
                    logger.info(f"任务已取消: {task_id}")
                    return True
                elif task.status == TaskStatus.RUNNING:
                    logger.warning(f"任务正在运行，无法取消: {task_id}")
                    return False
                else:
                    logger.warning(f"任务状态无法取消: {task_id} (状态: {task.status.value})")
                    return False
            else:
                logger.warning(f"任务不存在: {task_id}")
                return False
                
        except Exception as e:
            logger.error(f"取消任务失败 {task_id}: {e}")
            return False
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        if task_id not in self.all_tasks:
            return {'status': 'not_found'}
        
        task = self.all_tasks[task_id]
        
        status_info = {
            'task_id': task.task_id,
            'task_type': task.task_type,
            'status': task.status.value,
            'priority': task.priority.name,
            'created_at': task.created_at.isoformat(),
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'result': task.result,
            'error': task.error
        }
        
        # 计算运行时间
        if task.started_at:
            end_time = task.completed_at or datetime.now()
            duration = (end_time - task.started_at).total_seconds()
            status_info['duration_seconds'] = duration
        
        return status_info
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        pending_count = sum(1 for task in self.all_tasks.values() if task.status == TaskStatus.PENDING)
        running_count = len(self.running_tasks)
        completed_count = sum(1 for task in self.all_tasks.values() if task.status == TaskStatus.COMPLETED)
        failed_count = sum(1 for task in self.all_tasks.values() if task.status == TaskStatus.FAILED)
        
        return {
            'is_running': self.is_running,
            'max_workers': self.max_workers,
            'pending_tasks': pending_count,
            'running_tasks': running_count,
            'completed_tasks': completed_count,
            'failed_tasks': failed_count,
            'total_tasks': len(self.all_tasks),
            'queue_size': self.task_queue.qsize(),
            'uptime_seconds': (datetime.now() - self.stats['start_time']).total_seconds() if self.stats['start_time'] else 0
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        
        # 计算成功率
        if stats['total_submitted'] > 0:
            stats['success_rate'] = stats['total_completed'] / stats['total_submitted']
        else:
            stats['success_rate'] = 0
        
        # 计算平均处理时间
        completed_tasks = [task for task in self.all_tasks.values() if task.status == TaskStatus.COMPLETED and task.started_at and task.completed_at]
        if completed_tasks:
            durations = [(task.completed_at - task.started_at).total_seconds() for task in completed_tasks]
            stats['avg_processing_time_seconds'] = sum(durations) / len(durations)
        else:
            stats['avg_processing_time_seconds'] = 0
        
        return stats
    
    def _process_tasks(self):
        """处理任务队列的主循环"""
        logger.info("任务处理循环已启动")
        
        futures = {}
        
        while self.is_running and not self._shutdown_event.is_set():
            try:
                # 提交新任务（在空闲线程数允许的情况下）
                available_workers = self.max_workers - len(futures)
                
                for _ in range(available_workers):
                    if self._shutdown_event.is_set():
                        break
                    
                    try:
                        # 从队列获取任务（超时1秒）
                        task = self.task_queue.get(timeout=1.0)
                        
                        # 检查任务是否被取消
                        if task.status == TaskStatus.CANCELLED:
                            continue
                        
                        # 提交任务到线程池
                        future = self.executor.submit(self._execute_task, task)
                        futures[future] = task
                        
                        # 更新任务状态
                        task.status = TaskStatus.RUNNING
                        task.started_at = datetime.now()
                        self.running_tasks[task.task_id] = task
                        
                        logger.debug(f"任务开始执行: {task.task_id}")
                        
                    except Empty:
                        # 队列为空，跳出内循环
                        break
                    except Exception as e:
                        logger.error(f"提交任务到线程池失败: {e}")
                
                # 检查已完成的任务
                completed_futures = [f for f in futures if f.done()]
                for future in completed_futures:
                    task = futures.pop(future)
                    
                    try:
                        # 获取任务结果
                        result = future.result()
                        
                        # 更新任务状态
                        task.status = TaskStatus.COMPLETED
                        task.completed_at = datetime.now()
                        task.result = result
                        
                        self.running_tasks.pop(task.task_id, None)
                        self.completed_tasks[task.task_id] = task
                        self.stats['total_completed'] += 1
                        
                        logger.info(f"任务执行完成: {task.task_id}")
                        
                        # 执行回调
                        if task.callback:
                            try:
                                task.callback(task.task_id, result)
                            except Exception as e:
                                logger.error(f"任务回调执行失败 {task.task_id}: {e}")
                                
                    except Exception as e:
                        # 任务执行失败
                        task.status = TaskStatus.FAILED
                        task.completed_at = datetime.now()
                        task.error = str(e)
                        
                        self.running_tasks.pop(task.task_id, None)
                        self.stats['total_failed'] += 1
                        
                        logger.error(f"任务执行失败 {task.task_id}: {e}")
                        
                        # 执行错误回调
                        if task.callback:
                            try:
                                task.callback(task.task_id, {'error': str(e)})
                            except Exception as cb_e:
                                logger.error(f"错误回调执行失败 {task.task_id}: {cb_e}")
                
                # 短暂休眠，避免占用过多CPU
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"任务处理循环出现异常: {e}")
                time.sleep(1.0)  # 出错时休眠更长时间
        
        logger.info("任务处理循环已停止")
    
    def _execute_task(self, task: EstimationTask) -> Dict[str, Any]:
        """执行单个任务"""
        try:
            logger.debug(f"开始执行任务: {task.task_id} ({task.task_type})")
            
            if task.task_type == 'project':
                return self.facade.advanced_estimate(**task.parameters)
            elif task.task_type == 'batch':
                return self.facade.mapsheet_estimation_batch(**task.parameters)
            elif task.task_type == 'mapsheet':
                return self.facade.mapsheet_estimation_single(**task.parameters)
            elif task.task_type == 'real_time':
                return self.facade.real_time_estimate(**task.parameters)
            else:
                raise ValueError(f"未知任务类型: {task.task_type}")
                
        except Exception as e:
            logger.error(f"任务执行异常 {task.task_id}: {e}")
            raise
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """清理已完成的任务"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        tasks_to_remove = []
        for task_id, task in self.completed_tasks.items():
            if task.completed_at and task.completed_at < cutoff_time:
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            self.completed_tasks.pop(task_id, None)
            self.all_tasks.pop(task_id, None)
        
        if tasks_to_remove:
            logger.info(f"已清理 {len(tasks_to_remove)} 个过期任务")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start_processing()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.stop_processing()
