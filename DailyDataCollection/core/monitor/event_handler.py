"""
事件处理器模块 - 处理文件系统事件
"""

import os
from watchdog.events import FileSystemEventHandler
from ..data_models.date_types import DateType
from .file_validator import KMZFileValidator
# 临时注释，避免循环导入
from .mapsheet_monitor import MonitorMapSheetCollection
from display import MessageDisplay, MonitorDisplay


class FileEventHandler(FileSystemEventHandler):
    """
    文件系统事件处理器
    
    负责处理文件创建事件，验证文件并更新相应的图幅状态
    支持精确匹配和模糊匹配两种模式
    """
    
    def __init__(self, current_date: DateType, enable_fuzzy_matching: bool = True, fuzzy_threshold: float = 0.65):
        super().__init__()
        self.current_date = current_date
        self.enable_fuzzy_matching = enable_fuzzy_matching
        self.mapsheet_collection = MonitorMapSheetCollection(current_date)
        
        # 初始化文件验证器（支持模糊匹配）
        self.file_validator = KMZFileValidator(
            current_date=current_date,
            valid_mapsheet_names=self.mapsheet_collection.mapsheet_names,
            enable_fuzzy_matching=enable_fuzzy_matching,
            fuzzy_threshold=fuzzy_threshold
        )
    
    def on_created(self, event):
        """处理文件创建事件"""
        if event.is_directory:
            return
        
        filename = os.path.basename(event.src_path)
        filename_lower = filename.lower()
        
        # 只处理KMZ文件
        if not filename_lower.endswith('.kmz'):
            return
        
        MessageDisplay.show_file_detected(filename)
        
        # 基础验证
        if not self.file_validator.validate(filename_lower):
            return
        
        # 判断文件类型并处理（支持模糊匹配）
        if (self._is_finished_file(filename_lower) or 
            (self.enable_fuzzy_matching and self._is_finished_file_fuzzy(filename_lower))):
            self._handle_finished_file(filename_lower)
        elif (self._is_plan_file(filename_lower) or 
              (self.enable_fuzzy_matching and self._is_plan_file_fuzzy(filename_lower))):
            self._handle_plan_file(filename_lower)
        else:
            MessageDisplay.show_validation_error(filename_lower, 'invalid_name')
    
    def _handle_finished_file(self, filename: str):
        """处理完成点文件（支持模糊匹配）"""
        # 使用验证器的模糊匹配功能
        if not self.file_validator.validate_finished_file(filename, use_fuzzy=self.enable_fuzzy_matching):
            return
        
        # 查找匹配的图幅（支持模糊匹配）
        mapsheet_name = self.file_validator.extract_mapsheet_name(filename)
        if not mapsheet_name:
            MessageDisplay.show_validation_error(filename, 'no_valid_finished')
            return
        
        # 构建预期的文件名模式
        expected_pattern = f"{mapsheet_name.lower()}_finished_points_and_tracks_{self.current_date.yyyymmdd_str}"
        
        # 精确匹配或模糊匹配都认为有效
        if (expected_pattern in filename or 
            (self.enable_fuzzy_matching and self._fuzzy_match_finished_pattern(filename, mapsheet_name))):
            mapsheet = self.mapsheet_collection.get_mapsheet_by_name(mapsheet_name)
            if mapsheet:
                mapsheet.update_finished()
                self.mapsheet_collection.remove_from_collection(mapsheet_name)
                self._display_remaining_files()
        else:
            MessageDisplay.show_validation_error(filename, 'no_valid_finished')
    
    def _handle_plan_file(self, filename: str):
        """处理计划路线文件（支持模糊匹配）"""
        # 使用验证器的模糊匹配功能
        if not self.file_validator.validate_plan_file(filename, use_fuzzy=self.enable_fuzzy_matching):
            return
        
        # 查找匹配的图幅（支持模糊匹配）
        mapsheet_name = self.file_validator.extract_mapsheet_name(filename)
        if not mapsheet_name:
            MessageDisplay.show_validation_error(filename, 'no_valid_plan')
            return
        
        # 提取文件日期
        file_date = self.file_validator.extract_date(filename)
        if not file_date:
            return
        
        # 构建预期的文件名模式
        file_date_str = file_date.strftime('%Y%m%d')
        expected_pattern = f"{mapsheet_name.lower()}_plan_routes_{file_date_str}"
        
        # 精确匹配或模糊匹配都认为有效
        if (expected_pattern in filename or 
            (self.enable_fuzzy_matching and self._fuzzy_match_plan_pattern(filename, mapsheet_name, file_date_str))):
            mapsheet = self.mapsheet_collection.get_mapsheet_by_name(mapsheet_name)
            if mapsheet:
                mapsheet.update_plan()
        else:
            MessageDisplay.show_validation_error(filename, 'no_valid_plan')
    
    def _display_remaining_files(self):
        """显示剩余文件信息"""
        remaining_count = self.mapsheet_collection.get_remaining_count()
        total_planned = self.mapsheet_collection.planned_route_file_num
        MonitorDisplay.show_remaining_files(remaining_count, total_planned)
    
    def get_remaining_files(self):
        """获取剩余待收集的文件列表"""
        return self.mapsheet_collection.to_collect_names.copy()
    
    def is_collection_complete(self):
        """检查收集是否完成"""
        return self.mapsheet_collection.is_collection_complete()
    
    def is_all_collected(self):
        """检查是否所有文件都已收集（is_collection_complete的别名）"""
        return self.is_collection_complete()
    
    def get_planned_file_count(self):
        """获取计划文件总数"""
        return self.mapsheet_collection.planned_route_file_num
    
    def _is_finished_file(self, filename: str) -> bool:
        """检查是否是完成点文件（精确匹配）"""
        return '_finished_points_and_tracks_' in filename
    
    def _is_plan_file(self, filename: str) -> bool:
        """检查是否是计划路线文件（精确匹配）"""
        return '_plan_routes_' in filename
    
    def _is_finished_file_fuzzy(self, filename: str) -> bool:
        """检查是否是完成点文件（模糊匹配）"""
        patterns = ['finished_points_and_tracks', 'finished points and tracks', 
                   'finished_points', 'points_tracks', 'completed_points']
        best_match, similarity = self.file_validator._fuzzy_match_file_pattern(filename, patterns)
        return best_match is not None and similarity >= self.file_validator.fuzzy_threshold
    
    def _is_plan_file_fuzzy(self, filename: str) -> bool:
        """检查是否是计划路线文件（模糊匹配）"""
        patterns = ['plan_routes', 'plan routes', 'planned_routes', 
                   'route_plan', 'plan_route', 'routes_planned']
        best_match, similarity = self.file_validator._fuzzy_match_file_pattern(filename, patterns)
        return best_match is not None and similarity >= self.file_validator.fuzzy_threshold
    
    def _fuzzy_match_finished_pattern(self, filename: str, mapsheet_name: str) -> bool:
        """模糊匹配完成点文件模式"""
        # 检查文件名是否包含图幅名称和日期
        mapsheet_in_filename = mapsheet_name.lower() in filename
        date_in_filename = self.current_date.yyyymmdd_str in filename
        
        # 检查关键词
        keywords = ['finished', 'points', 'tracks', 'completed']
        keyword_matches = sum(1 for keyword in keywords if keyword in filename.replace('_', ' '))
        
        # 如果包含图幅名称、日期和至少2个关键词，则认为匹配成功
        return mapsheet_in_filename and date_in_filename and keyword_matches >= 2
    
    def _fuzzy_match_plan_pattern(self, filename: str, mapsheet_name: str, date_str: str) -> bool:
        """模糊匹配计划路线文件模式"""
        # 检查文件名是否包含图幅名称和日期
        mapsheet_in_filename = mapsheet_name.lower() in filename
        date_in_filename = date_str in filename
        
        # 检查关键词
        keywords = ['plan', 'route', 'planned', 'routes']
        keyword_matches = sum(1 for keyword in keywords if keyword in filename.replace('_', ' '))
        
        # 如果包含图幅名称、日期和至少1个关键词，则认为匹配成功
        return mapsheet_in_filename and date_in_filename and keyword_matches >= 1
