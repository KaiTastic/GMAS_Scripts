"""
监控管理器模块 - 协调整个监控流程
"""

import os
import time
from datetime import datetime
from typing import Optional, Callable
from watchdog.observers import Observer

from ..data_models.date_types import DateType
from config import ConfigManager
from .event_handler import FileEventHandler
from .display_manager import DisplayManager

# 初始化配置
config_manager = ConfigManager()
config = config_manager.get_config()


class MonitorManager:
    """
    监控管理器
    
    负责协调文件监控、事件处理和显示管理
    """
    
    def __init__(self, current_date: DateType, enable_fuzzy_matching: bool = True, fuzzy_threshold: float = 0.65):
        """
        初始化监控管理器
        
        Args:
            current_date: 当前监控日期
            enable_fuzzy_matching: 是否启用模糊匹配
            fuzzy_threshold: 模糊匹配阈值
        """
        self.current_date = current_date
        self.enable_fuzzy_matching = enable_fuzzy_matching
        self.fuzzy_threshold = fuzzy_threshold
        
        # 初始化组件
        self.event_handler = FileEventHandler(current_date, enable_fuzzy_matching, fuzzy_threshold)
        self.display_manager = DisplayManager()
        self.observer = None
    
    def start_monitoring(self, executor: Optional[Callable] = None, end_time: Optional[datetime] = None):
        """
        启动监控
        
        Args:
            executor: 完成后要执行的回调函数
            end_time: 监控结束时间
        """
        wechat_path = os.path.join(config['paths']['wechat_folder'], self.current_date.yyyy_mm_str)
        
        # 显示初始的待收集文件列表
        self._display_initial_status()
        
        # 启动文件系统监控
        self.observer = Observer()
        self.observer.schedule(self.event_handler, wechat_path, recursive=True)
        self.observer.start()
        
        try:
            if end_time:
                self.monitor_with_timeout(end_time, executor)
            else:
                self.monitor_until_completion(executor)
        except KeyboardInterrupt:
            print("\n用户中断监控...")
        finally:
            self.observer.stop()
            self.observer.join()
    
    def monitor_until_completion(self, executor: Optional[Callable] = None):
        """监控直到所有文件收集完成"""
        while not self.event_handler.is_all_collected():
            current_time = datetime.now()
            
            if self._should_display_status(current_time):
                remaining_files = self.event_handler.get_remaining_files()
                self.display_manager.display_status(
                    "实时监控模式",
                    f"当前待接收的文件数量/当日计划数量: {len(remaining_files)}/{len(self.event_handler.mapsheet_collection.mapsheet_collection)}",
                    self.event_handler.mapsheet_collection.mapsheet_collection
                )
                
                # 检查是否需要进入催促模式
                if self._should_enter_urgent_mode(current_time, remaining_files):
                    DisplayManager.display_urgent_mode(
                        remaining_files, 
                        self.event_handler.mapsheet_collection.mapsheet_collection
                    )
            
            time.sleep(config['monitoring']['time_interval_seconds'])
            print(".", end="", flush=True)
        
        # 完成收集
        DisplayManager.display_completion_message()
        if executor:
            executor()
    
    def monitor_with_timeout(self, end_time: datetime, executor=None):
        """带超时的监控模式"""
        while datetime.now() < end_time and not self.event_handler.is_all_collected():
            if self._should_display_status(datetime.now()):
                self.display_manager.display_status(
                    "监控模式 - 定时检查",
                    "",
                    self.event_handler.mapsheet_collection.mapsheet_collection
                )
            
            time.sleep(config['monitoring']['time_interval_seconds'])
            print(".", end="", flush=True)
        
        # 超时退出
        DisplayManager.display_timeout_message(end_time)
        if executor:
            executor()
    
    def _should_display_status(self, current_time: datetime) -> bool:
        """判断是否应该显示状态"""
        return (
            current_time.minute % config['monitoring']['status_interval_minutes'] == 0 and 
            0 <= current_time.second < config['monitoring']['time_interval_seconds']
        )
    
    def _should_enter_urgent_mode(self, current_time: datetime, remaining_files: list) -> bool:
        """判断是否进入催促模式"""
        return (
            (current_time.hour >= 19 and current_time.minute >= 0) or 
            len(remaining_files) <= 5
        )
    
    def stop_monitoring(self):
        """停止监控"""
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
    
    def _display_initial_status(self):
        """显示监控启动时的初始状态"""
        print("\n" + "="*60)
        print("监控系统状态初始化")
        print("="*60)
        
        total_mapsheets = len(self.event_handler.mapsheet_collection.mapsheet_collection)
        planned_files = self.event_handler.mapsheet_collection.planned_route_file_num
        remaining_files = self.event_handler.get_remaining_files()
        remaining_count = len(remaining_files)
        
        print(f"总图幅数量: {total_mapsheets}")
        print(f"计划收集文件数: {planned_files}")
        print(f"待收集文件数: {remaining_count}")
        
        if remaining_count > 0:
            print(f"\n待收集的文件列表:")
            for i, filename in enumerate(remaining_files, 1):
                # 获取对应的团队信息
                team_info = self.event_handler.mapsheet_collection.get_team_info_for_mapsheet(filename)
                if team_info:
                    print(f"  {i:2d}. {filename} (团队: {team_info['team_number']}, 负责人: {team_info['team_leader']})")
                else:
                    print(f"  {i:2d}. {filename}")
        else:
            print("\n✅ 所有计划文件已收集完成!")
        
        print("="*60)
        print("开始实时监控文件变化...\n")
