"""
文件验证器模块 - 负责KMZ文件的验证逻辑
使用策略模式支持不同的名称匹配策略
"""

import os
import re
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List, Optional
from ..data_models.date_types import DateType
from ..utils.matcher.string_matching import NameMatcher, HybridNameMatcher, ExactNameMatcher, FuzzyNameMatcher

# 导入编码修复器
try:
    from ..utils.encoding_fixer import safe_print
except ImportError:
    safe_print = print


class FileValidator(ABC):
    """文件验证器基类"""
    
    @abstractmethod
    def validate(self, filename: str, **kwargs) -> bool:
        """验证文件是否符合要求"""
        pass


class KMZFileValidator(FileValidator):
    """KMZ文件验证器 - 使用策略模式支持不同的匹配策略"""
    
    def __init__(self, current_date: DateType, valid_mapsheet_names: List[str], 
                 name_matcher: NameMatcher = None, 
                 enable_fuzzy_matching: bool = True, 
                 fuzzy_threshold: float = 0.65,
                 debug: bool = False):
        """
        初始化文件验证器
        
        Args:
            current_date: 当前日期
            valid_mapsheet_names: 有效的图幅名称列表
            name_matcher: 名称匹配器，如果为None则根据enable_fuzzy_matching自动选择
            enable_fuzzy_matching: 是否启用模糊匹配（仅在name_matcher为None时有效）
            fuzzy_threshold: 模糊匹配阈值（仅在name_matcher为None时有效）
            debug: 是否启用调试模式
        """
        self.current_date = current_date
        self.valid_mapsheet_names = valid_mapsheet_names
        self.debug = debug
        
        # 如果没有提供匹配器，则根据配置自动创建
        if name_matcher is None:
            if enable_fuzzy_matching:
                self.name_matcher = HybridNameMatcher(fuzzy_threshold, debug)
            else:
                self.name_matcher = ExactNameMatcher()
        else:
            self.name_matcher = name_matcher
        
        # 保持向后兼容性的属性
        self.enable_fuzzy_matching = enable_fuzzy_matching
        self.fuzzy_threshold = fuzzy_threshold
    
    def validate(self, filename: str, **kwargs) -> bool:
        """综合验证KMZ文件"""
        filename_lower = filename.lower()
        
        return (
            self._validate_extension(filename_lower) and
            self._validate_date(filename_lower) and
            self._validate_mapsheet_name(filename_lower)
        )
    
    def _validate_extension(self, filename: str) -> bool:
        """验证文件扩展名"""
        return filename.endswith('.kmz')
    
    def _validate_date(self, filename: str) -> bool:
        """验证文件名中的日期信息"""
        date_match = re.search(r'\d{8}', filename)
        if not date_match:
            safe_print(f"文件名日期格式错误(不正确/不足8位): {filename}")
            return False
        
        try:
            file_date = datetime.strptime(date_match.group(), "%Y%m%d")
        except ValueError:
            safe_print(f"文件名中的日期不合法: {filename}")
            return False
        
        # 文件日期应该大于等于当前日期
        if file_date.date() >= self.current_date.date_datetime.date():
            return True
        else:
            safe_print(f"无法从文件名匹配到有效日期（日期格式错误/日期不为当天/日期不为下一天): {filename}")
            return False
    
    def _validate_mapsheet_name(self, filename: str) -> bool:
        """验证文件名中的图幅信息 - 使用名称匹配器"""
        # 使用名称匹配器进行匹配
        matched_mapsheet = self.name_matcher.match_mapsheet_name(filename, self.valid_mapsheet_names)
        
        if matched_mapsheet:
            if self.debug:
                safe_print(f"图幅匹配成功: {filename} -> {matched_mapsheet}")
            return True
        else:
            if self.debug:
                safe_print(f"文件名中没有包含有效的图幅名称: {filename}")
            return False
    
    def validate_finished_file(self, filename: str, use_fuzzy: bool = None) -> bool:
        """验证完成点文件
        
        Args:
            filename: 文件名
            use_fuzzy: 是否使用模糊匹配，None表示使用实例默认设置
        """
        if use_fuzzy is None:
            use_fuzzy = self.enable_fuzzy_matching
            
        if use_fuzzy:
            return self.validate_finished_file_fuzzy(filename)
        
        # 原有的精确匹配逻辑
        if not self.validate(filename):
            return False
        
        if '_finished_points_and_tracks_' not in filename:
            return False
        
        return self._validate_finished_date(filename)
    
    def validate_plan_file(self, filename: str, use_fuzzy: bool = None) -> bool:
        """验证计划路线文件
        
        Args:
            filename: 文件名
            use_fuzzy: 是否使用模糊匹配，None表示使用实例默认设置
        """
        if use_fuzzy is None:
            use_fuzzy = self.enable_fuzzy_matching
            
        if use_fuzzy:
            return self.validate_plan_file_fuzzy(filename)
        
        # 原有的精确匹配逻辑
        if not self.validate(filename):
            return False
        
        if '_plan_routes_' not in filename:
            return False
        
        return self._validate_plan_date(filename)
    
    def extract_mapsheet_name(self, filename: str) -> Optional[str]:
        """从文件名中提取图幅名称 - 使用名称匹配器"""
        # 使用名称匹配器进行匹配
        matched_mapsheet = self.name_matcher.match_mapsheet_name(filename, self.valid_mapsheet_names)
        
        if self.debug and matched_mapsheet:
            safe_print(f"提取图幅名称: {filename} -> {matched_mapsheet}")
        
        return matched_mapsheet
    
    def extract_date(self, filename: str) -> Optional[datetime]:
        """从文件名中提取日期"""
        date_match = re.search(r'\d{8}', filename)
        if date_match:
            try:
                return datetime.strptime(date_match.group(), "%Y%m%d")
            except ValueError:
                pass
        return None
    
    def validate_finished_file_fuzzy(self, filename: str) -> bool:
        """验证完成点文件 - 使用名称匹配器"""
        if not self.validate(filename):
            return False
        
        # 定义完成点文件的模式
        finished_patterns = [
            '_finished_points_and_tracks_', 
            'finished points and tracks', 
            'finished_points', 
            'points_tracks', 
            'completed_points'
        ]
        
        # 使用名称匹配器进行模式匹配
        matched_pattern = self.name_matcher.match_file_pattern(filename, finished_patterns)
        
        if matched_pattern:
            if self.debug:
                safe_print(f"完成点文件模式匹配成功: {filename} -> {matched_pattern}")
            return self._validate_finished_date(filename)
        
        return False
    
    def validate_plan_file_fuzzy(self, filename: str) -> bool:
        """验证计划路线文件 - 使用名称匹配器"""
        if not self.validate(filename):
            return False
        
        # 定义计划路线文件的模式
        plan_patterns = [
            '_plan_routes_', 
            'plan routes', 
            'planned_routes', 
            'route_plan', 
            'plan_route', 
            'routes_planned'
        ]
        
        # 使用名称匹配器进行模式匹配
        matched_pattern = self.name_matcher.match_file_pattern(filename, plan_patterns)
        
        if matched_pattern:
            if self.debug:
                safe_print(f"计划路线文件模式匹配成功: {filename} -> {matched_pattern}")
            return self._validate_plan_date(filename)
        
        return False
    
    def _validate_finished_date(self, filename: str) -> bool:
        """验证完成点文件的日期"""
        date_match = re.search(r'\d{8}', filename)
        if date_match:
            file_date = datetime.strptime(date_match.group(), "%Y%m%d")
            if file_date.date() != self.current_date.date_datetime.date():
                safe_print(f"无法从完成点文件名中匹配出有效日期（格式错误/日期不为当天): {filename}")
                return False
        return True
    
    def _validate_plan_date(self, filename: str) -> bool:
        """验证计划路线文件的日期"""
        date_match = re.search(r'\d{8}', filename)
        if date_match:
            file_date = datetime.strptime(date_match.group(), "%Y%m%d")
            if file_date.date() <= self.current_date.date_datetime.date():
                safe_print(f"无法从计划路线文件名中匹配出有效日期（格式错误/日期不为下一天): {filename}")
                return False
        return True
    
    # 为了向后兼容，保留这些方法的引用
    def _fuzzy_match_mapsheet(self, filename: str):
        """向后兼容方法 - 已废弃，请使用name_matcher"""
        import warnings
        warnings.warn("_fuzzy_match_mapsheet已废弃，请使用name_matcher", DeprecationWarning)
        if hasattr(self.name_matcher, '_fuzzy_match_mapsheet'):
            return self.name_matcher._fuzzy_match_mapsheet(filename, self.valid_mapsheet_names)
        return None, 0.0
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """向后兼容方法 - 已废弃，请使用name_matcher"""
        import warnings
        warnings.warn("_calculate_similarity已废弃，请使用name_matcher", DeprecationWarning)
        if hasattr(self.name_matcher, '_calculate_similarity'):
            return self.name_matcher._calculate_similarity(str1, str2)
        return 0.0
    
    def _fuzzy_match_file_pattern(self, filename: str, patterns: List[str]):
        """向后兼容方法 - 已废弃，请使用name_matcher"""
        import warnings
        warnings.warn("_fuzzy_match_file_pattern已废弃，请使用name_matcher", DeprecationWarning)
        if hasattr(self.name_matcher, '_fuzzy_match_file_pattern'):
            return self.name_matcher._fuzzy_match_file_pattern(filename, patterns)
        return None, 0.0
