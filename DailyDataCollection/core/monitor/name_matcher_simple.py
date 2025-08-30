# -*- coding: utf-8 -*-
"""简化版名称匹配器 - 用于测试"""

from abc import ABC, abstractmethod
from typing import List, Optional


class NameMatcher(ABC):
    """名称匹配器抽象基类"""
    
    @abstractmethod
    def match_mapsheet_name(self, filename: str, valid_names: List[str]) -> Optional[str]:
        pass
    
    @abstractmethod
    def match_file_pattern(self, filename: str, patterns: List[str]) -> Optional[str]:
        pass


class HybridNameMatcher(NameMatcher):
    """简化的混合名称匹配器"""
    
    def __init__(self, fuzzy_threshold: float = 0.65, debug: bool = False):
        self.fuzzy_threshold = fuzzy_threshold
        self.debug = debug
    
    def match_mapsheet_name(self, filename: str, valid_names: List[str]) -> Optional[str]:
        """简单匹配图幅名称"""
        filename_lower = filename.lower()
        for name in valid_names:
            if name.lower() in filename_lower:
                return name
        return None
    
    def match_file_pattern(self, filename: str, patterns: List[str]) -> Optional[str]:
        """简单匹配文件模式"""
        filename_lower = filename.lower()
        for pattern in patterns:
            pattern_clean = pattern.replace('_', ' ').strip().lower()
            if pattern_clean in filename_lower:
                return pattern
        return None
