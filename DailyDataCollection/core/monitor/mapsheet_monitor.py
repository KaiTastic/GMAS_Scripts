"""
图幅监控器模块 - 管理单个图幅和图幅集合的监控
"""

import os
from typing import List, Optional

from ..mapsheet.mapsheet_daily import MapsheetDailyFile
from ..mapsheet.mapsheet_manager import mapsheet_manager
from ..data_models.date_types import DateType
from config.config_manager import ConfigManager
from display import MonitorDisplay


class MonitorMapSheet(MapsheetDailyFile):
    """
    单个图幅监控器
    
    继承自MapsheetDailyFile类,主要用于监视图幅文件的变化
    
    属性:
        fileToReceiveFlag: bool - 表示当天是否有已有计划路线
        matchedFinishedFileCountNum: int - 表示当天接收到的完成路线数量
        matchedPlanFileCountNum: int - 表示当天接收到的计划路线数量
    """
    
    def __init__(self, mapsheet_filename: str, current_date: DateType):
        super().__init__(mapsheet_filename, current_date)
        
        # 检查是否有当日计划
        self.fileToReceiveFlag: bool = False
        self._check_has_plan()
        
        # 记录当天接收到的文件数量
        self.matchedFinishedFileCountNum: int = 0
        self.matchedPlanFileCountNum: int = 0
        
        # 监控状态：检查该图幅的文件是否已完成收集
        # 如果当前文件已存在，则标记为已完成
        self.finished: bool = bool(self.currentfilepath and os.path.exists(self.currentfilepath))
    
    def update_finished(self):
        """在完成接收完成路线文件时,更新当前图幅的状态"""
        self.matchedFinishedFileCountNum += 1
        self.getCurrentDateFile(self)
        self.findlastFinished(self)
        
        # 重新计算增量和总数 - 替代原来的 dailyIncrease() 和 soFarfinished()
        self._update_point_calculations()
        
        # 标记为已完成收集
        self.finished = True
        
        MonitorDisplay.show_mapsheet_update(
            self, 'finished', self.matchedFinishedFileCountNum
        )
    
    def update_plan(self):
        """在完成接收计划路线文件时,更新当前图幅的状态"""
        self.matchedPlanFileCountNum += 1
        self.findNextPlan(self)
        
        MonitorDisplay.show_mapsheet_update(
            self, 'plan', self.matchedPlanFileCountNum
        )
    
    def _check_has_plan(self):
        """检查当天的计划路线文件是否存在"""
        config = mapsheet_manager._config_manager.get_config()
        plan_file_path = os.path.join(
            config['paths']['workspace'], 
            self.currentDate.yyyymm_str, 
            self.currentDate.yyyymmdd_str, 
            "Planned routes", 
            f"{self.mapsheetFileName}_plan_routes_{self.currentDate.yyyymmdd_str}.kmz"
        )
        
        self.fileToReceiveFlag = os.path.exists(plan_file_path)
        return self.fileToReceiveFlag

    def _update_point_calculations(self):
        """更新点数计算 - 计算日增量和当前总数"""
        from ..file_handlers.kmz_handler import KMZFile
        
        # 处理当前文件
        if self.currentfilepath:
            file = KMZFile(filepath=self.currentfilepath)
            self.currentPlacemarks = file.placemarks
            if file.errorMsg:
                if not hasattr(self, '_MonitorMapSheet__errorMsg'):
                    self._MonitorMapSheet__errorMsg = {}
                self._MonitorMapSheet__errorMsg[os.path.basename(self.currentfilepath)] = file.errorMsg

        # 处理上一次文件
        if self.lastfilepath:
            self.lastfilename = os.path.basename(self.lastfilepath)
            file = KMZFile(filepath=self.lastfilepath)
            self.lastPlacemarks = file.placemarks
            if file.errorMsg:
                if not hasattr(self, '_MonitorMapSheet__errorMsg'):
                    self._MonitorMapSheet__errorMsg = {}
                self._MonitorMapSheet__errorMsg[self.lastfilename] = file.errorMsg

        # 计算增量
        if self.currentPlacemarks and self.lastPlacemarks:
            dailyincrease = self.currentPlacemarks - self.lastPlacemarks
            self.dailyincreasePointNum = dailyincrease.pointsCount
            self.dailyincreaseRouteNum = dailyincrease.routesCount
            self.dailyincreasePoints = dailyincrease.points
            self.dailyincreaseRoutes = dailyincrease.routes
        elif self.currentPlacemarks and not self.lastPlacemarks:
            self.dailyincreasePointNum = self.currentPlacemarks.pointsCount
            self.dailyincreaseRouteNum = self.currentPlacemarks.routesCount
            self.dailyincreasePoints = self.currentPlacemarks.points
            self.dailyincreaseRoutes = self.currentPlacemarks.routes
        else:
            self.dailyincreasePointNum = 0
            self.dailyincreaseRouteNum = 0

        # 设置总数
        if self.currentPlacemarks:
            self.currentTotalPointNum = self.currentPlacemarks.pointsCount
            self.currentTotalRouteNum = self.currentPlacemarks.routesCount
        else:
            self.currentTotalPointNum = 0
            self.currentTotalRouteNum = 0


class MonitorMapSheetCollection:
    """
    图幅集合监控器
    
    单例模式的容器类，管理所有需要监控的图幅
    """
    
    _instance = None
    _maps_info = None
    
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance') or cls._instance is None:
            cls._load_maps_info()
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, current_date: DateType):
        # 避免重复初始化
        if hasattr(self, '_initialized'):
            return
        
        self.current_date = current_date
        self.mapsheet_collection: List[MonitorMapSheet] = []
        self.mapsheet_names: List[str] = []
        self.to_collect_names: List[str] = []
        self.planned_route_file_num: int = 0
        
        self._initialize_mapsheets()
        self._initialized = True
    
    @classmethod
    def _load_maps_info(cls):
        """加载图幅信息"""
        cls._maps_info = mapsheet_manager.maps_info
    
    def _initialize_mapsheets(self):
        """初始化图幅列表 - 使用统一的图幅管理器"""
        # 使用图幅管理器创建图幅对象集合
        mapsheets = mapsheet_manager.create_mapsheet_collection(MonitorMapSheet, self.current_date)
        
        for mapsheet in mapsheets:
            # 添加到集合中
            self.mapsheet_collection.append(mapsheet)
            self.mapsheet_names.append(mapsheet.mapsheetFileName)
            
            # 检查是否需要接收
            if mapsheet.fileToReceiveFlag:
                self.planned_route_file_num += 1
                # 如果当前文件名为None，表示还未接收完成
                if mapsheet.currentfilename is None:
                    self.to_collect_names.append(mapsheet.mapsheetFileName)
    
    def get_mapsheet_by_name(self, mapsheet_name: str) -> Optional[MonitorMapSheet]:
        """根据图幅名称获取图幅对象"""
        for mapsheet in self.mapsheet_collection:
            if mapsheet.mapsheetFileName == mapsheet_name:
                return mapsheet
        return None
    
    def remove_from_collection(self, mapsheet_name: str) -> bool:
        """从待收集列表中移除图幅"""
        if mapsheet_name in self.to_collect_names:
            self.to_collect_names.remove(mapsheet_name)
            return True
        return False
    
    def get_remaining_count(self) -> int:
        """获取剩余待接收文件数量"""
        return len(self.to_collect_names)
    
    def is_collection_complete(self) -> bool:
        """检查是否完成所有收集"""
        return len(self.to_collect_names) == 0
    
    def get_team_info_for_mapsheet(self, mapsheet_name: str) -> Optional[dict]:
        """获取图幅对应的团队信息"""
        mapsheet = self.get_mapsheet_by_name(mapsheet_name)
        if mapsheet:
            return {
                'team_number': mapsheet.teamNumber,
                'team_leader': mapsheet.teamleader,
                'roman_name': mapsheet.romanName
            }
        return None
