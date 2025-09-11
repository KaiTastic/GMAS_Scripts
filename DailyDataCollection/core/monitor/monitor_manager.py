"""
监控管理器模块
=============

协调整个监控流程，负责文件系统监控、事件处理和状态显示。

该模块提供了监控微信文件夹中KMZ文件变化的核心功能，
支持实时监控、状态显示和自动完成检测。

.. note::
   本模块依赖于watchdog库进行文件系统监控

.. version:: 1.0
.. author:: GMAS Team
"""

import os
import time
from datetime import datetime
from typing import Optional, Callable
from watchdog.observers import Observer

from ..data_models.date_types import DateType
from config import ConfigManager
from .event_handler import FileEventHandler
from display import MonitorDisplay

# 初始化配置
config_manager = ConfigManager()
config = config_manager.get_all_config()


class MonitorManager:
    """
    监控管理器
    ==========
    
    负责协调文件监控、事件处理和显示管理的核心类。
    
    该类封装了整个监控流程的逻辑，包括：
    
    * 文件系统监控的启动和停止
    * 事件处理器的管理
    * 状态显示的协调
    * 监控模式的控制（实时监控/定时监控）
    
    :ivar current_date: 当前监控的日期
    :type current_date: DateType
    :ivar enable_fuzzy_matching: 是否启用模糊匹配
    :type enable_fuzzy_matching: bool
    :ivar fuzzy_threshold: 模糊匹配的阈值
    :type fuzzy_threshold: float
    :ivar event_handler: 文件事件处理器
    :type event_handler: FileEventHandler
    :ivar observer: 文件系统观察者
    :type observer: Optional[Observer]
    
    .. seealso::
       :class:`FileEventHandler` 文件事件处理器
       :class:`MonitorDisplay` 监控显示器
    """
    
    def __init__(self, current_date: DateType, enable_fuzzy_matching: bool = True, fuzzy_threshold: float = 0.65):
        """
        初始化监控管理器
        
        :param current_date: 当前监控日期，用于确定监控的目标文件
        :type current_date: DateType
        :param enable_fuzzy_matching: 是否启用模糊匹配功能，默认为True
        :type enable_fuzzy_matching: bool
        :param fuzzy_threshold: 模糊匹配的相似度阈值，范围0-1，默认0.65
        :type fuzzy_threshold: float
        
        :raises ValueError: 当fuzzy_threshold不在有效范围内时
        
        .. note::
           模糊匹配阈值建议设置在0.6-0.8之间，过低会产生误匹配，过高会漏掉相似文件
        """
        self.current_date = current_date
        self.enable_fuzzy_matching = enable_fuzzy_matching
        self.fuzzy_threshold = fuzzy_threshold
        
        # 初始化组件
        self.event_handler = FileEventHandler(current_date, enable_fuzzy_matching, fuzzy_threshold)
        self.observer = None
    
    def start_monitoring(self, executor: Optional[Callable] = None, end_time: Optional[datetime] = None):
        """
        启动文件监控
        
        启动对微信文件夹的实时监控，监控指定日期的KMZ文件变化。
        支持两种模式：持续监控模式和定时监控模式。
        
        :param executor: 监控完成后要执行的回调函数，可选
        :type executor: Optional[Callable]
        :param end_time: 监控结束时间，如果为None则持续监控直到完成
        :type end_time: Optional[datetime]
        
        :raises OSError: 当无法创建监控目录时
        :raises PermissionError: 当没有权限访问监控目录时
        
        .. warning::
           如果监控目录不存在，系统会尝试自动创建
           
        .. note::
           监控会在以下情况下结束：
           
           * 所有计划文件都已收集完成
           * 达到指定的结束时间（如果设置了end_time）
           * 用户手动中断（Ctrl+C）
        """
        wechat_path = os.path.join(config['paths']['wechat_folder'], self.current_date.yyyy_mm_str)
        
        # 检查并创建监控目录：可能当天是当月第一天，微信尚未自动创建此文件夹
        if not os.path.exists(wechat_path):
            print(f"监控目录不存在，正在创建: {wechat_path}")
            try:
                os.makedirs(wechat_path, exist_ok=True)
                print(f"成功创建监控目录: {wechat_path}")
            except Exception as e:
                print(f"创建监控目录失败: {e}")
                return
        
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
        """
        持续监控直到所有文件收集完成
        
        在实时监控模式下持续运行，直到所有计划的文件都被收集完成。
        会定期显示收集状态，并在必要时进入催促模式。
        
        :param executor: 监控完成后要执行的回调函数，可选
        :type executor: Optional[Callable]
        
        .. note::
           监控过程中会：
           
           * 每隔一定时间间隔显示收集状态
           * 在晚上19点后或剩余文件<=5个时进入催促模式
           * 显示进度指示点（.）表示系统正在运行
        """
        while not self.event_handler.is_all_collected():
            current_time = datetime.now()
            
            if self._should_display_status(current_time):
                remaining_files = self.event_handler.get_remaining_files()
                planned_count, total_count, planned_unfinished_count = MonitorDisplay.get_planned_mapsheets_count(
                    self.event_handler.mapsheet_collection.mapsheet_collection
                )
                MonitorDisplay.show_status(
                    "实时监控模式",
                    f"有当日计划的图幅: {planned_count}/{total_count} | 待收集文件数: {planned_unfinished_count}",
                    self.event_handler.mapsheet_collection.mapsheet_collection
                )
                
                # 检查是否需要进入催促模式
                if self._should_enter_urgent_mode(current_time, remaining_files):
                    MonitorDisplay.show_urgent_mode(
                        remaining_files, 
                        self.event_handler.mapsheet_collection.mapsheet_collection
                    )
            
            time.sleep(config['monitoring']['time_interval_seconds'])
            print(".", end="", flush=True)
        
        # 完成收集
        MonitorDisplay.show_completion()
        if executor:
            executor()
    
    def monitor_with_timeout(self, end_time: datetime, executor=None):
        """
        带超时的监控模式
        
        在指定时间内进行监控，到达结束时间或所有文件收集完成时停止。
        适用于定时任务或有时间限制的监控场景。
        
        :param end_time: 监控结束的时间点
        :type end_time: datetime
        :param executor: 监控完成后要执行的回调函数，可选
        :type executor: Optional[Callable]
        
        .. note::
           监控会在以下条件之一满足时结束：
           
           * 达到指定的结束时间
           * 所有计划文件都已收集完成
        """
        while datetime.now() < end_time and not self.event_handler.is_all_collected():
            if self._should_display_status(datetime.now()):
                planned_count, total_count, planned_unfinished_count = MonitorDisplay.get_planned_mapsheets_count(
                    self.event_handler.mapsheet_collection.mapsheet_collection
                )
                MonitorDisplay.show_status(
                    "监控模式 - 定时检查",
                    f"有当日计划的图幅: {planned_count}/{total_count} | 待收集文件数: {planned_unfinished_count}",
                    self.event_handler.mapsheet_collection.mapsheet_collection
                )
            
            time.sleep(config['monitoring']['time_interval_seconds'])
            print(".", end="", flush=True)
        
        # 超时退出
        MonitorDisplay.show_timeout(end_time)
        if executor:
            executor()
    
    def _should_display_status(self, current_time: datetime) -> bool:
        """
        判断是否应该显示状态信息
        
        根据当前时间和配置的状态显示间隔，判断是否需要显示监控状态。
        
        :param current_time: 当前时间
        :type current_time: datetime
        :return: 如果应该显示状态则返回True，否则返回False
        :rtype: bool
        
        .. note::
           状态显示的时机由配置文件中的status_interval_minutes参数控制
        """
        return (
            current_time.minute % config['monitoring']['status_interval_minutes'] == 0 and 
            0 <= current_time.second < config['monitoring']['time_interval_seconds']
        )
    
    def _should_enter_urgent_mode(self, current_time: datetime, remaining_files: list) -> bool:
        """
        判断是否应该进入催促模式
        
        根据当前时间和剩余文件数量，判断是否需要进入催促模式。
        催促模式会显示更详细的提醒信息，用于提醒用户及时上传文件。
        
        :param current_time: 当前时间
        :type current_time: datetime
        :param remaining_files: 剩余待收集的文件列表
        :type remaining_files: list
        :return: 如果应该进入催促模式则返回True，否则返回False
        :rtype: bool
        
        .. note::
           催促模式的触发条件：
           
           * 时间晚于19:00
           * 剩余文件数量<=5个
        """
        return (
            (current_time.hour >= 19 and current_time.minute >= 0) or 
            len(remaining_files) <= 5
        )
    
    def stop_monitoring(self):
        """
        停止文件监控
        
        安全地停止文件系统监控，确保观察者线程正确退出。
        
        .. note::
           该方法会检查观察者状态，只有在观察者仍在运行时才执行停止操作
        """
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
    
    def _display_initial_status(self):
        """
        显示监控启动时的初始状态
        
        在监控开始时显示当前的收集状态，包括：
        
        * 待收集文件数量
        * 计划收集文件总数
        * 各图幅的收集状态
        
        如果所有文件已收集完成，则显示完成消息；
        否则显示详细的状态信息并开始实时监控。
        """
        
        # 统计有当日计划的图幅数量
        planned_mapsheets = [ms for ms in self.event_handler.mapsheet_collection.mapsheet_collection if ms.fileToReceiveFlag]
        planned_files = self.event_handler.mapsheet_collection.planned_route_file_num
        remaining_files = self.event_handler.get_remaining_files()
        remaining_count = len(remaining_files)

        # 显示详细状态信息
        MonitorDisplay.show_status(
            "监控系统初始化",
            f"待收集文件数/计划收集文件数:{remaining_count}/{planned_files}",
            self.event_handler.mapsheet_collection.mapsheet_collection
        )
        
        if remaining_count > 0:

            print("="*60)
            print("开始实时监控文件变化...\n")

        else:
            print("\n 所有计划文件已收集完成!")
        
