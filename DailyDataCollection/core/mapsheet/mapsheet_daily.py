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
from typing import Dict, Optional, Any, List
from pathlib import Path

from ..data_models.observation_data import ObservationData
from ..file_handlers.kmz_handler import KMZFile
from ..utils.file_utils import list_fullpath_of_files_with_keywords

# 使用系统配置模块
from config.config_manager import ConfigManager
from ..data_models.date_types import DateType


class MapsheetConfigError(Exception):
    """图幅配置错误"""
    pass


class MapsheetFileError(Exception):
    """图幅文件错误"""
    pass


# 获取配置实例
config_manager = ConfigManager()
config = config_manager.get_config()
platform_config = config_manager.get_platform_config()

# 配置常量
WORKSPACE = config_manager.get('system.workspace')
WECHAT_FOLDER = platform_config.get('wechat_folder', '')
TRACEBACK_DATE = config_manager.get('data_collection.traceback_date')
TRACEFORWARD_DAYS = config_manager.get('data_collection.traceforward_days')

# 常量
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0

# 获取logger
logger = logging.getLogger(__name__)


class FileOperationHelper:
    """文件操作助手类，统一处理文件操作"""
    
    # 文件哈希缓存，避免重复计算
    _hash_cache: Dict[str, str] = {}
    
    @staticmethod
    def get_file_hash(file_path: str) -> Optional[str]:
        """获取文件哈希值，使用缓存优化性能"""
        try:
            # 获取文件修改时间作为缓存键的一部分
            mtime = os.path.getmtime(file_path)
            cache_key = f"{file_path}:{mtime}"
            
            if cache_key in FileOperationHelper._hash_cache:
                return FileOperationHelper._hash_cache[cache_key]
            
            # 计算哈希值
            kmz_file = KMZFile(filepath=file_path)
            hash_value = kmz_file.hashMD5
            
            # 缓存结果
            FileOperationHelper._hash_cache[cache_key] = hash_value
            return hash_value
        except Exception as e:
            logger.warning(f"计算文件哈希失败 {file_path}: {e}")
            return None
    
    @staticmethod
    def safe_copy_file(source_file: str, dest_file: str, max_retries: int = DEFAULT_MAX_RETRIES) -> None:
        """安全地复制文件，包含重试机制和权限处理"""
        import time
        
        for attempt in range(max_retries):
            try:
                # 检查目标文件是否被占用，如果是则尝试删除
                if os.path.exists(dest_file):
                    try:
                        FileOperationHelper.set_file_permissions(dest_file)
                        os.remove(dest_file)
                    except PermissionError:
                        logger.warning(f"无法删除已存在的文件 {dest_file}，尝试重命名")
                        backup_name = f"{dest_file}.backup_{int(time.time())}"
                        try:
                            os.rename(dest_file, backup_name)
                        except PermissionError:
                            if attempt < max_retries - 1:
                                logger.warning(f"第 {attempt + 1} 次复制失败，等待{DEFAULT_RETRY_DELAY}秒后重试...")
                                time.sleep(DEFAULT_RETRY_DELAY)
                                continue
                            else:
                                raise MapsheetFileError(f"无法处理目标文件 {dest_file}")
                
                # 执行文件复制
                shutil.copy(source_file, dest_file)
                FileOperationHelper.set_file_permissions(dest_file)
                logger.info(f"成功复制文件: {source_file} -> {dest_file}")
                return
                
            except PermissionError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"第 {attempt + 1} 次复制失败 ({e})，等待{DEFAULT_RETRY_DELAY}秒后重试...")
                    time.sleep(DEFAULT_RETRY_DELAY)
                else:
                    raise MapsheetFileError(f"文件复制失败，已重试 {max_retries} 次: {e}")
            except Exception as e:
                raise MapsheetFileError(f"文件复制时发生未预期的错误: {e}")
    
    @staticmethod
    def set_file_permissions(file_path: str) -> None:
        """设置文件权限"""
        try:
            os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
        except PermissionError as e:
            logger.warning(f"无法设置文件权限 {file_path}: {e}")
        except Exception as e:
            logger.warning(f"设置文件权限时发生错误 {file_path}: {e}")

    @staticmethod
    def ensure_directory_exists(file_path: str) -> None:
        """确保目录存在"""
        directory = os.path.dirname(file_path)
        os.makedirs(directory, exist_ok=True)


class MapsheetDailyFile:
    """图幅日文件处理类，管理单个图幅的日常文件操作"""
    
    # 类级别的图幅信息缓存
    _maps_info: Optional[Dict[int, Dict[str, Any]]] = None

    @classmethod
    def _load_maps_info(cls):
        """加载图幅信息，只加载一次"""
        if cls._maps_info is None:
            try:
                from .mapsheet_manager import mapsheet_manager
                cls._maps_info = mapsheet_manager.maps_info
            except ImportError as e:
                logger.error(f"无法导入图幅管理器: {e}")
                cls._maps_info = {}

    def __init__(self, mapsheetFileName: str, date):
        """
        初始化图幅日文件
        
        Args:
            mapsheetFileName: 图幅文件名称
            date: 日期对象
            
        Raises:
            MapsheetConfigError: 配置错误
            MapsheetFileError: 文件操作错误
        """
        # 加载图幅信息
        self._load_maps_info()
        
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
            raise MapsheetConfigError(f"图幅文件名称'{self.mapsheetFileName}'未找到")
        
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
        if self._maps_info:
            for sequence, info in self._maps_info.items():
                if info['File Name'] == self.mapsheetFileName:
                    self.sequence = sequence
                    break
            else:
                # 构造可用文件名列表
                available_files = [info['File Name'] for info in self._maps_info.values()]
                logger.error(f"文件名称'{self.mapsheetFileName}'未找到。可用的文件名: {available_files}")
                return False
                
            self.sheetID = self._maps_info[self.sequence]['Sheet ID']
            self.group = self._maps_info[self.sequence]['Group']
            self.arabicName = self._maps_info[self.sequence]['Arabic Name']
            self.romanName = self._maps_info[self.sequence]['Roman Name']
            self.latinName = self._maps_info[self.sequence]['Latin Name']
            self.teamNumber = self._maps_info[self.sequence]['Team Number']
            self.teamleader = self._maps_info[self.sequence]['Leaders']

            return True
        else:
            logger.error("图幅信息未加载")
            return False

    def _get_current_date_file(self) -> None:
        """
        获取当天的文件
        """
        file_path = os.path.join(
            WORKSPACE, 
            self.currentDate.yyyymm_str, 
            self.currentDate.yyyymmdd_str, 
            "Finished points", 
            f"{self.mapsheetFileName}_finished_points_and_tracks_{self.currentDate.yyyymmdd_str}.kmz"
        )
        
        # 列出微信聊天记录文件夹中包含指定日期、图幅名称和finished_points的文件
        folder = os.path.join(WECHAT_FOLDER)
        searchedFile_list = list_fullpath_of_files_with_keywords(
            folder, 
            [self.currentDate.yyyymmdd_str, self.mapsheetFileName, "finished_points_and_tracks", ".kmz"]
        )
        
        if len(searchedFile_list) >= 1:
            # 选择时间最新的文件
            fetched_file = max(searchedFile_list, key=os.path.getctime)
            
            # 如果工作文件夹中的文件存在
            if os.path.exists(file_path) and os.path.isfile(file_path):
                if self._files_are_different(file_path, fetched_file):
                    # 将获取的文件拷贝至工作文件夹, 并进行了重命名
                    self._safe_copy_file(fetched_file, file_path)
                    self.currentfilepath = file_path
                else:
                    self.currentfilepath = file_path
                    self._set_file_permissions(file_path)
            else:
                FileOperationHelper.ensure_directory_exists(file_path)
                self._safe_copy_file(fetched_file, file_path)
                self.currentfilepath = file_path
                
        if self.currentfilepath:
            self.currentfilename = os.path.basename(self.currentfilepath)
            try:
                file = KMZFile(filepath=self.currentfilepath)
                self.currentPlacemarks = file.placemarks
                if file.errorMsg:  # errorMsg现在返回None或错误列表
                    self.__errorMsg[self.currentfilename] = file.errorMsg
            except Exception as e:
                logger.error(f"加载当前文件数据失败 {self.currentfilepath}: {e}")
                raise MapsheetFileError(f"加载当前文件数据失败: {e}")
    
    @classmethod  
    def getCurrentDateFile(cls, instance: 'MapsheetDailyFile') -> 'MapsheetDailyFile':
        """向后兼容的方法"""
        instance._get_current_date_file()
        return cls

    @classmethod
    def _safe_copy_file(cls, source_file: str, dest_file: str, max_retries: int = DEFAULT_MAX_RETRIES):
        """安全地复制文件，包含重试机制和权限处理（向后兼容）"""
        FileOperationHelper.safe_copy_file(source_file, dest_file, max_retries)
    
    @classmethod
    def _set_file_permissions(cls, file_path: str):
        """设置文件权限（向后兼容）"""
        FileOperationHelper.set_file_permissions(file_path)

    def _find_last_finished_file(self) -> None:
        """查找上一次完成的文件"""
        traceback_date = datetime.strptime(TRACEBACK_DATE, "%Y%m%d").date()
        search_start_date = self.currentDate.date_datetime
        
        while search_start_date.date() > traceback_date:
            # 在工作文件夹中直接查找
            search_date = self.currentDate.date_datetime
            
            while search_date.date() > traceback_date:
                search_date -= timedelta(days=1)
                file_path = self._build_historical_file_path(search_date, "Finished points", "finished_points_and_tracks")
                
                if os.path.exists(file_path):
                    # 延迟导入以避免循环依赖
                    from ..data_models.date_types import DateType
                    self.lastDate = DateType(date_datetime=search_date)
                    self._handle_last_file_setup(file_path)
                    return
                    
            search_start_date -= timedelta(days=1)

    def _build_historical_file_path(self, date: datetime, folder_type: str, file_type: str) -> str:
        """构建历史文件路径"""
        return os.path.join(
            WORKSPACE,
            date.strftime("%Y%m"),
            date.strftime("%Y%m%d"),
            folder_type,
            f"{self.mapsheetFileName}_{file_type}_{date.strftime('%Y%m%d')}.kmz"
        )

    def _handle_last_file_setup(self, file_path: str) -> None:
        """处理上一次文件的设置"""
        if self.currentfilename is None:
            # 如果当前日期没有文件，将历史文件复制到当前日期文件夹
            dest = os.path.join(
                WORKSPACE, 
                self.currentDate.yyyymm_str, 
                self.currentDate.yyyymmdd_str, 
                "Finished points", 
                os.path.basename(file_path)
            )
            if file_path != dest:
                try:
                    FileOperationHelper.ensure_directory_exists(dest)
                    shutil.copy(file_path, dest)
                    FileOperationHelper.set_file_permissions(dest)
                    self.lastfilepath = dest
                except Exception as e:
                    logger.error(f"复制历史文件失败: {e}")
                    raise MapsheetFileError(f"复制历史文件失败: {e}")
        else:
            # 清理可能存在的旧文件
            self._cleanup_old_files()
            self.lastfilepath = file_path

    def _cleanup_old_files(self) -> None:
        """清理旧文件"""
        if self.lastDate:
            old_file = os.path.join(
                WORKSPACE,
                self.currentDate.yyyymm_str,
                self.currentDate.yyyymmdd_str,
                "Finished points",
                f"{self.mapsheetFileName}_finished_points_and_tracks_{self.lastDate}.kmz"
            )
            if os.path.exists(old_file):
                try:
                    os.remove(old_file)
                    logger.info(f"已移除旧文件: {old_file}")
                except Exception as e:
                    logger.warning(f"无法移除旧文件 {old_file}: {e}")

    @classmethod
    def findlastFinished(cls, instance: 'MapsheetDailyFile') -> None:
        """向后兼容的方法"""
        instance._find_last_finished_file()

    def _load_last_file_data(self) -> None:
        """加载上一次文件数据"""
        if self.lastfilepath:
            self.lastfilename = os.path.basename(self.lastfilepath)
            try:
                file = KMZFile(filepath=self.lastfilepath)
                self.lastPlacemarks = file.placemarks
                if file.errorMsg:  # errorMsg现在返回None或错误列表
                    self.__errorMsg[self.lastfilename] = file.errorMsg
            except Exception as e:
                logger.error(f"加载上一次文件数据失败 {self.lastfilepath}: {e}")
                raise MapsheetFileError(f"加载上一次文件数据失败: {e}")

    def _calculate_daily_statistics(self) -> None:
        """计算日增量和总数统计"""
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
            self.dailyincreasePoints = {}
            self.dailyincreaseRoutes = []

        # 设置总数
        if self.currentPlacemarks:
            self.currentTotalPointNum = self.currentPlacemarks.pointsCount
            self.currentTotalRouteNum = self.currentPlacemarks.routesCount
        else:
            self.currentTotalPointNum = 0
            self.currentTotalRouteNum = 0

    def __mapsheetfiles(self) -> None:
        """获取图幅文件路径 - 主要协调方法"""
        try:
            # 获取当前日期文件
            self._get_current_date_file()
            # 查找上一次完成的文件
            self._find_last_finished_file()
            # 加载上一次文件数据
            self._load_last_file_data()
            # 计算日增量和统计
            self._calculate_daily_statistics()
            # 查找下一个计划文件
            self._find_next_plan_file()
        except Exception as e:
            logger.error(f"处理图幅文件时发生错误: {e}")
            raise

    @property
    def errorMsg(self) -> Dict:
        """获取错误消息"""
        return self.__errorMsg

    def _find_next_plan_file(self) -> None:
        """
        查找下一个计划文件
        
        通常应是查找第二天的计划文件: 
        或周五-周六休息, 周四会查找周六/周日的计划文件, 
        因此为了冗余日期, TRACEFORWARD_DAYS = 5, 即向前查找5天, 找到最近的一个计划文件
        """
        start_date = self.currentDate.date_datetime
        end_date = start_date + timedelta(days=TRACEFORWARD_DAYS)
        search_date = start_date
        
        while search_date < end_date:
            search_date += timedelta(days=1)
            searched_files = self._search_plan_files_for_date(search_date)
            
            if searched_files:
                self._handle_plan_file_synchronization(searched_files, search_date)
                break

    def _search_plan_files_for_date(self, date: datetime) -> list:
        """搜索指定日期的计划文件"""
        search_date_str = date.strftime("%Y%m%d")
        return list_fullpath_of_files_with_keywords(
            WECHAT_FOLDER, 
            [search_date_str, self.mapsheetFileName, "plan_routes", ".kmz"]
        )

    def _handle_plan_file_synchronization(self, searched_files: list, date: datetime) -> None:
        """处理计划文件同步"""
        try:
            self.nextDate = DateType(date_datetime=date)
            file_path = self._build_historical_file_path(date, "Planned routes", "plan_routes")
            
            # 选择时间最新的文件
            latest_file = max(searched_files, key=os.path.getctime)
            
            if not os.path.exists(file_path):
                # 创建目录并复制文件
                FileOperationHelper.ensure_directory_exists(file_path)
                FileOperationHelper.safe_copy_file(latest_file, file_path)
            elif self._files_are_different(file_path, latest_file):
                # 检查文件是否需要更新
                FileOperationHelper.safe_copy_file(latest_file, file_path)
            
            self.nextfilepath = file_path
            self._load_plan_file_data()
            
        except Exception as e:
            logger.error(f"处理计划文件同步失败: {e}")
            raise MapsheetFileError(f"处理计划文件同步失败: {e}")

    def _files_are_different(self, file1: str, file2: str) -> bool:
        """检查两个文件是否不同，使用缓存优化性能"""
        try:
            hash1 = FileOperationHelper.get_file_hash(file1)
            hash2 = FileOperationHelper.get_file_hash(file2)
            
            if hash1 is None or hash2 is None:
                return True  # 如果无法获取哈希，假设不同
            
            return hash1 != hash2
        except Exception as e:
            logger.warning(f"比较文件时出错: {e}")
            return True  # 如果无法比较，假设不同

    def _load_plan_file_data(self) -> None:
        """加载计划文件数据"""
        if hasattr(self, 'nextfilepath') and self.nextfilepath:
            try:
                self.nextfilename = os.path.basename(self.nextfilepath)
                file = KMZFile(filepath=self.nextfilepath)
                self.planPlacemarks = file.placemarks
                if file.errorMsg:
                    self.__errorMsg[self.nextfilename] = file.errorMsg
            except Exception as e:
                logger.error(f"加载计划文件数据失败 {self.nextfilepath}: {e}")
                raise MapsheetFileError(f"加载计划文件数据失败: {e}")

    @classmethod
    def findNextPlan(cls, instance: 'MapsheetDailyFile') -> None:
        """向后兼容的方法"""
        instance._find_next_plan_file()

    def __str__(self) -> str:
        """字符串表示"""
        return (f"图幅: {self.mapsheetFileName}\n"
                f"序号: {self.sequence}\n"
                f"当前日期: {self.currentDate}\n"
                f"当前点数: {self.currentTotalPointNum}\n"
                f"日增点数: {self.dailyincreasePointNum}")

    def __repr__(self) -> str:
        """开发者友好的字符串表示"""
        return (f"MapsheetDailyFile(mapsheetFileName='{self.mapsheetFileName}', "
                f"date={self.currentDate}, sequence={self.sequence})")
