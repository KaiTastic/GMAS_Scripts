"""
图幅监控器模块 - 管理单个图幅和图幅集合的监控
"""

import os
from typing import List, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from DailyFileGenerator_compat import MapsheetDailyFile, CurrentDateFiles
from ..data_models.date_types import DateType
import config
from .display_manager import DisplayManager


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
    
    def update_finished(self):
        """在完成接收完成路线文件时,更新当前图幅的状态"""
        self.matchedFinishedFileCountNum += 1
        self.getCurrentDateFile(self)
        self.findlastFinished(self)
        self.dailyIncrease()
        self.soFarfinished()
        
        DisplayManager.display_mapsheet_update(
            self, 'finished', self.matchedFinishedFileCountNum
        )
    
    def update_plan(self):
        """在完成接收计划路线文件时,更新当前图幅的状态"""
        self.matchedPlanFileCountNum += 1
        self.findNextPlan(self)
        
        DisplayManager.display_mapsheet_update(
            self, 'plan', self.matchedPlanFileCountNum
        )
    
    def _check_has_plan(self):
        """检查当天的计划路线文件是否存在"""
        plan_file_path = os.path.join(
            config.WORKSPACE, 
            self.currentDate.yyyymm_str, 
            self.currentDate.yyyymmdd_str, 
            "Planned routes", 
            f"{self.mapsheetFileName}_plan_routes_{self.currentDate.yyyymmdd_str}.kmz"
        )
        
        self.fileToReceiveFlag = os.path.exists(plan_file_path)
        return self.fileToReceiveFlag


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
        cls._maps_info = CurrentDateFiles.mapsInfo()
    
    def _initialize_mapsheets(self):
        """初始化图幅列表"""
        for sequence in range(config.SEQUENCE_MIN, config.SEQUENCE_MAX + 1):
            mapsheet_filename = self._maps_info[sequence]['File Name']
            mapsheet = MonitorMapSheet(mapsheet_filename, self.current_date)
            
            # 添加到集合中
            self.mapsheet_collection.append(mapsheet)
            self.mapsheet_names.append(mapsheet_filename)
            
            # 检查是否需要接收
            if mapsheet.fileToReceiveFlag:
                self.planned_route_file_num += 1
                # 如果当前文件名为None，表示还未接收完成
                if mapsheet.currentfilename is None:
                    self.to_collect_names.append(mapsheet_filename)
    
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
