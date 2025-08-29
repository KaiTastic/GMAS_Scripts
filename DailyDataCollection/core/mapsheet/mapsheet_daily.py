"""
图幅日文件处理模块

处理单个图幅的日文件，包括当前文件、历史文件和差异计算
"""

import os
import stat
import shutil
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

from ..data_models.observation_data import ObservationData
from ..file_handlers.kmz_handler import KMZFile
from ..utils.file_utils import list_fullpath_of_files_with_keywords

# 导入配置
try:
    from config import WORKSPACE, WECHAT_FOLDER, TRACEBACK_DATE, TRACEFORWARD_DAYS
    from config import DateType
except ImportError:
    WORKSPACE = ""
    WECHAT_FOLDER = ""
    TRACEBACK_DATE = "20240101"
    TRACEFORWARD_DAYS = 5
    # 如果无法导入DateType，我们需要从data_models导入
    try:
        from ..data_models.date_types import DateType
    except ImportError:
        DateType = None

# 创建 logger 实例
logger = logging.getLogger('Mapsheet Daily')
logger.setLevel(logging.ERROR)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class MapsheetDailyFile:
    """图幅日文件处理类，管理单个图幅的日常文件操作"""
    
    maps_info: Dict[int, Dict[str, Any]] = {}

    def __new__(cls, *args, **kwargs):
        """单例模式，确保图幅信息只初始化一次"""
        if not hasattr(cls, 'instance'):
            # 延迟导入以避免循环依赖
            from .current_date_files import CurrentDateFiles
            if CurrentDateFiles.maps_info:
                cls.maps_info = CurrentDateFiles.maps_info
            else:
                cls.maps_info = CurrentDateFiles.mapsInfo()
        cls.instance = super(MapsheetDailyFile, cls).__new__(cls)
        return cls.instance

    def __init__(self, mapsheetFileName: str, date):
        """
        初始化图幅日文件
        
        Args:
            mapsheetFileName: 图幅文件名称
            date: 日期对象
        """
        # 图幅的基本信息
        self.mapsheetFileName: str = mapsheetFileName
        self.sequence: Optional[int] = None
        self.sheetID: Optional[str] = None
        self.group: Optional[str] = None
        self.arabicName: Optional[str] = None
        self.romanName: Optional[str] = None
        self.latinName: Optional[str] = None
        self.teamNumber: Optional[str] = None
        self.teamleader: Optional[str] = None
        
        # 从 mapsheet_info 字典中获取图幅信息
        if not self.__mapsheetInfo():
            print(f"图幅文件名称{self.mapsheetFileName}未找到")
        
        # 当前日期
        self.currentDate = date
        # 当前日期的文件属性
        self.currentfilename: Optional[str] = None
        self.currentfilepath: Optional[str] = None
        self.currentPlacemarks: Optional[ObservationData] = None
        
        # 上一次提交的文件属性
        self.lastDate = None
        self.lastfilename: Optional[str] = None
        self.lastfilepath: Optional[str] = None
        self.lastPlacemarks: Optional[ObservationData] = None
        
        # 下一次提交的工作计划文件属性
        self.nextDate = None
        self.nextfilename: Optional[str] = None
        self.nextfilepath: Optional[str] = None
        self.nextPlacemarks: Optional[ObservationData] = None
        self.planPlacemarks: Optional[ObservationData] = None  # 计划数据的别名
        
        # 本日新增点数、线路数、点要素和线要素
        self.dailyincreasePointNum: Optional[int] = None
        self.dailyincreaseRouteNum: Optional[int] = None
        self.dailyincreasePoints: Dict = {}
        self.dailyincreaseRoutes: list = []
        
        # 包含的错误信息
        self.__errorMsg: Dict = {}
        
        # 截止当前日期的总点数、线路数
        self.currentTotalPointNum: Optional[int] = None
        self.currentTotalRouteNum: Optional[int] = None

        # 利用self.__mapsheetfiles获取图幅的文件路径
        self.__mapsheetfiles()

    def __mapsheetInfo(self) -> bool:
        """
        根据文件名从 mapsheet_info 字典中获取图幅信息
        
        Returns:
            bool: 是否成功获取图幅信息
        """
        if self.__class__.maps_info:
            for sequence, info in self.__class__.maps_info.items():
                if info['File Name'] == self.mapsheetFileName:
                    self.sequence = sequence
                    break
            else:
                print(f"文件名称未找到\n请查证是否文件名 '{self.mapsheetFileName}' 有误？\n文件名列表如下: ")
                print(json.dumps(self.__class__.maps_info, indent=4, ensure_ascii=False))
                print("程序退出")
                exit()
                
            self.sheetID = self.__class__.maps_info[self.sequence]['Sheet ID']
            self.group = self.__class__.maps_info[self.sequence]['Group']
            self.arabicName = self.__class__.maps_info[self.sequence]['Arabic Name']
            self.romanName = self.__class__.maps_info[self.sequence]['Roman Name']
            self.latinName = self.__class__.maps_info[self.sequence]['Latin Name']
            self.teamNumber = self.__class__.maps_info[self.sequence]['Team Number']
            self.teamleader = self.__class__.maps_info[self.sequence]['Leaders']

            return True
        return False

    @classmethod
    def getCurrentDateFile(cls, instance: 'MapsheetDailyFile') -> 'MapsheetDailyFile':
        """
        获取当天的文件
        
        Args:
            instance: MapsheetDailyFile实例
            
        Returns:
            MapsheetDailyFile: 类本身（用于链式调用）
        """
        file_path = os.path.join(
            WORKSPACE, 
            instance.currentDate.yyyymm_str, 
            instance.currentDate.yyyymmdd_str, 
            "Finished points", 
            f"{instance.mapsheetFileName}_finished_points_and_tracks_{instance.currentDate.yyyymmdd_str}.kmz"
        )
        
        # 列出微信聊天记录文件夹中包含指定日期、图幅名称和finished_points的文件
        folder = os.path.join(WECHAT_FOLDER)
        searchedFile_list = list_fullpath_of_files_with_keywords(
            folder, 
            [instance.currentDate.yyyymmdd_str, instance.mapsheetFileName, "finished_points_and_tracks", ".kmz"]
        )
        
        if len(searchedFile_list) >= 1:
            # 选择时间最新的文件
            fetched_file = max(searchedFile_list, key=os.path.getctime)
            
            # 如果工作文件夹中的文件存在
            if os.path.exists(file_path) and os.path.isfile(file_path):
                if KMZFile(filepath=file_path).hashMD5 != KMZFile(filepath=fetched_file).hashMD5:
                    # 将获取的文件拷贝至工作文件夹, 并进行了重命名
                    shutil.copy(fetched_file, file_path)
                    os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
                    instance.currentfilepath = file_path
                else:
                    instance.currentfilepath = file_path
                    os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
            else:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                shutil.copy(fetched_file, file_path)
                os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
                instance.currentfilepath = file_path
                
        if instance.currentfilepath:
            instance.currentfilename = os.path.basename(instance.currentfilepath)
            file = KMZFile(filepath=instance.currentfilepath)
            instance.currentPlacemarks = file.placemarks
            if file.errorMsg:  # errorMsg现在返回None或错误列表
                instance.__errorMsg[instance.currentfilename] = file.errorMsg
        return cls

    @classmethod
    def findlastFinished(cls, instance: 'MapsheetDailyFile') -> None:
        """
        查找上一次完成的文件
        
        Args:
            instance: MapsheetDailyFile实例
        """
        lastDate_datetime1 = instance.currentDate.date_datetime
        
        while lastDate_datetime1 > datetime.strptime(TRACEBACK_DATE, "%Y%m%d"):
            # Step 1: 在工作文件夹（当前日期）中直接查找
            lastDate_datetime2 = instance.currentDate.date_datetime
            
            while lastDate_datetime2 > datetime.strptime(TRACEBACK_DATE, "%Y%m%d"):
                lastDate_datetime2 -= timedelta(days=1)
                search_date_str = lastDate_datetime2.strftime("%Y%m%d")
                file_path = os.path.join(
                    WORKSPACE, 
                    lastDate_datetime1.strftime("%Y%m"), 
                    lastDate_datetime1.strftime("%Y%m%d"), 
                    "Finished points", 
                    f"{instance.mapsheetFileName}_finished_points_and_tracks_{search_date_str}.kmz"
                )
                
                if os.path.exists(file_path):
                    # 延迟导入以避免循环依赖
                    from ..data_models.date_types import DateType
                    instance.lastDate = DateType(date_datetime=lastDate_datetime2)
                    
                    # 如果当前日期的文件为None, 则需要将之前的文件拷贝至当前日期的文件夹
                    if instance.currentfilename is None:
                        dest = os.path.join(
                            WORKSPACE, 
                            instance.currentDate.yyyymm_str, 
                            instance.currentDate.yyyymmdd_str, 
                            "Finished points", 
                            os.path.basename(file_path)
                        )
                        if file_path != dest:
                            os.makedirs(os.path.dirname(dest), exist_ok=True)
                            shutil.copy(file_path, dest)
                            os.chmod(dest, stat.S_IWRITE | stat.S_IREAD)
                            instance.lastfilepath = dest
                    else:
                        # 需要清理当前文件夹中的之前的完成文件
                        fileTobeRemoved = os.path.join(
                            WORKSPACE, 
                            instance.currentDate.yyyymm_str, 
                            instance.currentDate.yyyymmdd_str, 
                            "Finished points", 
                            f"{instance.mapsheetFileName}_finished_points_and_tracks_{instance.lastDate}.kmz"
                        )
                        if os.path.exists(fileTobeRemoved) and os.path.isfile(fileTobeRemoved):
                            print("当日文件已经存在, 需要移除当日文件夹中的旧文件: ", fileTobeRemoved)
                            os.remove(fileTobeRemoved)
                        instance.lastfilepath = file_path
                    break
                    
            if instance.lastfilepath:
                break
            lastDate_datetime1 -= timedelta(days=1)

    def __mapsheetfiles(self) -> None:
        """获取图幅文件路径"""
        # 获取当前日期文件
        self.getCurrentDateFile(self)
        # 查找上一次完成的文件
        self.findlastFinished(self)
        
        # 处理文件信息
        if self.lastfilepath:
            self.lastfilename = os.path.basename(self.lastfilepath)
            file = KMZFile(filepath=self.lastfilepath)
            self.lastPlacemarks = file.placemarks
            if file.errorMsg:  # errorMsg现在返回None或错误列表
                self.__errorMsg[self.lastfilename] = file.errorMsg

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

        # 查找下一个计划文件
        self.findNextPlan(self)

    @property
    def errorMsg(self) -> Dict:
        """获取错误消息"""
        return self.__errorMsg

    @classmethod
    def findNextPlan(cls, instance: 'MapsheetDailyFile') -> None:
        """
        查找下一个计划文件
        
        findNextPlan 通常应是查找第二天的计划文件: 
                     或周五-周六休息, 周四会查找周六/周日的计划文件, 因此为了冗余日期, TRACEFORWARD_DAYS = 5, 即向前查找5天, 找到最近的一个计划文件
        
        Args:
            instance: MapsheetDailyFile实例
        """
        # 开始查找当前日期之后的计划文件
        date = instance.currentDate.date_datetime
        endDate = instance.currentDate.date_datetime + timedelta(days=TRACEFORWARD_DAYS)
        
        while date < endDate:
            date += timedelta(days=1)
            search_date_str = date.strftime("%Y%m%d")
            
            # 列出微信聊天记录文件夹中包含指定日期、图幅名称和plan_routes的文件
            searchedFile_list = list_fullpath_of_files_with_keywords(
                WECHAT_FOLDER, 
                [search_date_str, instance.mapsheetFileName, "plan_routes", ".kmz"]
            )
            
            if searchedFile_list:
                # 找到工作计划
                instance.nextDate = DateType(date_datetime=date)
                file_path = os.path.join(
                    WORKSPACE, 
                    instance.nextDate.yyyymm_str, 
                    instance.nextDate.yyyymmdd_str, 
                    "Planned routes", 
                    f"{instance.mapsheetFileName}_plan_routes_{instance.nextDate.yyyymmdd_str}.kmz"
                )
                
                # 选择时间最新的文件
                latestFile = max(searchedFile_list, key=os.path.getctime)
                
                if not os.path.exists(file_path):
                    # 创建目录并复制文件
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    shutil.copy(latestFile, file_path)
                    os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
                    instance.nextfilepath = file_path
                    break
                else:
                    # 检查文件是否需要更新
                    if KMZFile(filepath=file_path).hashMD5 != KMZFile(filepath=latestFile).hashMD5:
                        shutil.copy(latestFile, file_path)
                        os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
                        instance.nextfilepath = file_path
                        break
                    else:
                        instance.nextfilepath = file_path
                        break
        
        # 设置nextfilename和planPlacemarks
        if hasattr(instance, 'nextfilepath') and instance.nextfilepath:
            instance.nextfilename = os.path.basename(instance.nextfilepath)
            file = KMZFile(filepath=instance.nextfilepath)
            instance.planPlacemarks = file.placemarks
            if file.errorMsg:
                instance.__errorMsg[instance.nextfilename] = file.errorMsg

    def __str__(self) -> str:
        """字符串表示"""
        return (f"图幅: {self.mapsheetFileName}\n"
                f"序号: {self.sequence}\n"
                f"当前日期: {self.currentDate}\n"
                f"当前点数: {self.currentTotalPointNum}\n"
                f"日增点数: {self.dailyincreasePointNum}")
