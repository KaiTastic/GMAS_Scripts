"""
监控管理器模块 - 协调整个监控流程
"""

import os
import time
from datetime import datetime
from typing import Optional, Callable
from watchdog.observers import Observer

from ..data_models.date_types import DateType
import config
from .event_handler import FileEventHandler
from .display_manager import DisplayManager

# 导入编码修复器
try:
    from ..utils.encoding_fixer import safe_print
except ImportError:
    safe_print = print


class MonitorManager:
    """
    监控管理器
    
    协调文件监控的整个流程，包括：
    - 启动文件系统监控
    - 管理监控循环
    - 处理超时和完成逻辑
    - 支持模糊匹配配置
    """
    
    def __init__(self, current_date: DateType, enable_fuzzy_matching: bool = True, fuzzy_threshold: float = 0.65):
        self.current_date = current_date
        self.enable_fuzzy_matching = enable_fuzzy_matching
        self.fuzzy_threshold = fuzzy_threshold
        self.event_handler = FileEventHandler(
            current_date, 
            enable_fuzzy_matching=enable_fuzzy_matching,
            fuzzy_threshold=fuzzy_threshold
        )
        self.observer = None
        
    def start_monitoring(self, 
                        executor: Optional[Callable] = None, 
                        end_time: Optional[datetime] = None):
        """
        启动监控服务
        
        Args:
            executor: 完成后要执行的回调函数
            end_time: 监控结束时间
        """
        wechat_path = os.path.join(config.WECHAT_FOLDER, self.current_date.yyyy_mm_str)
        
        # 启动文件系统监控
        self.observer = Observer()
        self.observer.schedule(self.event_handler, wechat_path, recursive=True)
        self.observer.start()
        
        try:
            if self.event_handler.get_planned_file_count() > 0:
                self._monitor_planned_files(executor)
            else:
                self._monitor_plan_mode(executor, end_time)
        except KeyboardInterrupt:
            safe_print("\n用户中断监控...")
        finally:
            self._stop_monitoring()
    
    def _monitor_planned_files(self, executor: Optional[Callable] = None):
        """监控计划文件模式"""
        # 首次显示待接收文件列表
        remaining_files = self.event_handler.get_remaining_files()
        if remaining_files:
            DisplayManager.display_remaining_files(
                len(remaining_files), 
                self.event_handler.get_planned_file_count()
            )
            safe_print(f"当前待接收的文件列表: {remaining_files}")
        
        # 监控循环
        while not self.event_handler.is_collection_complete():
            current_time = datetime.now()
            
            # 定期显示状态
            if self._should_display_status(current_time):
                remaining_files = self.event_handler.get_remaining_files()
                DisplayManager.display_monitoring_status(current_time, remaining_files)
                DisplayManager.display_remaining_files(
                    len(remaining_files), 
                    self.event_handler.get_planned_file_count()
                )
                
                # 催促模式
                if self._should_enter_urgent_mode(current_time, remaining_files):
                    DisplayManager.display_urgent_mode(
                        remaining_files, 
                        self.event_handler.mapsheet_collection.mapsheet_collection
                    )
            
            time.sleep(config.MONITOR_TIME_INTERVAL_SECOND)
            print(".", end="", flush=True)
        
        # 完成收集
        DisplayManager.display_completion_message()
        if executor:
            executor()
    
    def _monitor_plan_mode(self, 
                          executor: Optional[Callable] = None, 
                          end_time: Optional[datetime] = None):
        """监控计划模式（无待接收完成点）"""
        if not end_time:
            end_time = datetime.now().replace(hour=20, minute=30, second=0, microsecond=0)
        
        DisplayManager.display_plan_mode_start(end_time)
        
        # 监控循环
        while datetime.now() <= end_time:
            current_time = datetime.now()
            
            # 定期显示状态
            if self._should_display_status(current_time):
                DisplayManager.display_monitoring_status(current_time, [])
            
            time.sleep(config.MONITOR_TIME_INTERVAL_SECOND)
            print(".", end="", flush=True)
        
        # 超时退出
        DisplayManager.display_timeout_message(end_time)
        if executor:
            executor()
    
    def _should_display_status(self, current_time: datetime) -> bool:
        """判断是否应该显示状态"""
        return (
            current_time.minute % config.MONITOR_STATUS_INTERVAL_MINUTE == 0 and 
            0 <= current_time.second < config.MONITOR_TIME_INTERVAL_SECOND
        )
    
    def _should_enter_urgent_mode(self, current_time: datetime, remaining_files: list) -> bool:
        """判断是否进入催促模式"""
        return (
            (current_time.hour >= 19 and current_time.minute >= 0) or 
            len(remaining_files) <= 5
        )
    
    def _stop_monitoring(self):
        """停止监控"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
    
    def get_monitoring_status(self) -> dict:
        """获取当前监控状态"""
        return {
            'current_date': self.current_date.yyyymmdd_str,
            'planned_files': self.event_handler.get_planned_file_count(),
            'remaining_files': len(self.event_handler.get_remaining_files()),
            'remaining_file_list': self.event_handler.get_remaining_files(),
            'is_complete': self.event_handler.is_collection_complete()
        }
