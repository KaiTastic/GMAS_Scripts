# -*- coding: utf-8 -*-
"""
匹配器工厂 - 提供创建各种匹配器的便捷方法
"""

from typing import Union

try:
    from .base_matcher import StringMatcher
    from .exact_matcher import ExactStringMatcher
    from .fuzzy_matcher import FuzzyStringMatcher
    from .hybrid_matcher import HybridStringMatcher
    from .name_matcher import NameMatcher, ExactNameMatcher, FuzzyNameMatcher, HybridNameMatcher
except ImportError:
    # 处理独立运行的情况
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    from base_matcher import StringMatcher
    from exact_matcher import ExactStringMatcher
    from fuzzy_matcher import FuzzyStringMatcher
    from hybrid_matcher import HybridStringMatcher
    from name_matcher import NameMatcher, ExactNameMatcher, FuzzyNameMatcher, HybridNameMatcher


def create_string_matcher(matcher_type: str = "hybrid", 
                         fuzzy_threshold: float = 0.65,
                         case_sensitive: bool = False,
                         debug: bool = False) -> StringMatcher:
    """创建字符串匹配器
    
    Args:
        matcher_type: 匹配器类型 ("exact", "fuzzy", "hybrid")
        fuzzy_threshold: 模糊匹配阈值 (仅用于fuzzy和hybrid)
        case_sensitive: 是否区分大小写 (仅用于exact和hybrid)
        debug: 是否启用调试模式
        
    Returns:
        StringMatcher: 字符串匹配器实例
        
    Raises:
        ValueError: 无效的匹配器类型
    """
    matcher_type = matcher_type.lower()
    
    if matcher_type == "exact":
        return ExactStringMatcher(case_sensitive=case_sensitive, debug=debug)
    elif matcher_type == "fuzzy":
        return FuzzyStringMatcher(threshold=fuzzy_threshold, debug=debug)
    elif matcher_type == "hybrid":
        return HybridStringMatcher(fuzzy_threshold=fuzzy_threshold, 
                                 case_sensitive=case_sensitive, 
                                 debug=debug)
    else:
        raise ValueError(f"不支持的匹配器类型: {matcher_type}. 支持的类型: exact, fuzzy, hybrid")


def create_name_matcher(matcher_type: str = "hybrid", 
                       fuzzy_threshold: float = 0.65, 
                       debug: bool = False) -> NameMatcher:
    """创建名称匹配器
    
    Args:
        matcher_type: 匹配器类型 ("exact", "fuzzy", "hybrid")
        fuzzy_threshold: 模糊匹配阈值 (仅用于fuzzy和hybrid)
        debug: 是否启用调试模式
        
    Returns:
        NameMatcher: 名称匹配器实例
        
    Raises:
        ValueError: 无效的匹配器类型
    """
    matcher_type = matcher_type.lower()
    
    if matcher_type == "exact":
        return ExactNameMatcher(debug=debug)
    elif matcher_type == "fuzzy":
        return FuzzyNameMatcher(fuzzy_threshold=fuzzy_threshold, debug=debug)
    elif matcher_type == "hybrid":
        return HybridNameMatcher(fuzzy_threshold=fuzzy_threshold, debug=debug)
    else:
        raise ValueError(f"不支持的名称匹配器类型: {matcher_type}. 支持的类型: exact, fuzzy, hybrid")

class MatcherFactory:
    """匹配器工厂类
    
    提供创建和配置各种匹配器的静态方法
    """
    
    # 预定义的配置
    STRICT_CONFIG = {
        "fuzzy_threshold": 0.8,
        "case_sensitive": True,
        "debug": False
    }
    
    RELAXED_CONFIG = {
        "fuzzy_threshold": 0.5,
        "case_sensitive": False, 
        "debug": False
    }
    
    DEFAULT_CONFIG = {
        "fuzzy_threshold": 0.65,
        "case_sensitive": False,
        "debug": False
    }
    
    @staticmethod
    def create_strict_matcher(matcher_type: str = "hybrid") -> Union[StringMatcher, NameMatcher]:
        """创建严格配置的匹配器
        
        Args:
            matcher_type: 匹配器类型
            
        Returns:
            匹配器实例
        """
        config = MatcherFactory.STRICT_CONFIG
        return create_string_matcher(matcher_type, **config)
    
    @staticmethod
    def create_relaxed_matcher(matcher_type: str = "hybrid") -> Union[StringMatcher, NameMatcher]:
        """创建宽松配置的匹配器
        
        Args:
            matcher_type: 匹配器类型
            
        Returns:
            匹配器实例
        """
        config = MatcherFactory.RELAXED_CONFIG
        return create_string_matcher(matcher_type, **config)
    
    @staticmethod
    def create_debug_matcher(matcher_type: str = "hybrid", 
                           fuzzy_threshold: float = 0.65) -> Union[StringMatcher, NameMatcher]:
        """创建调试模式的匹配器
        
        Args:
            matcher_type: 匹配器类型
            fuzzy_threshold: 模糊匹配阈值
            
        Returns:
            匹配器实例
        """
        return create_string_matcher(matcher_type, fuzzy_threshold=fuzzy_threshold, debug=True)
    
    @staticmethod
    def create_file_name_matcher(fuzzy_threshold: float = 0.65, debug: bool = False) -> NameMatcher:
        """创建专门用于文件名匹配的匹配器
        
        Args:
            fuzzy_threshold: 模糊匹配阈值
            debug: 是否启用调试模式
            
        Returns:
            NameMatcher: 文件名匹配器
        """
        return HybridNameMatcher(fuzzy_threshold, debug)
    
    @staticmethod
    def get_config_options() -> dict:
        """获取所有预定义配置选项
        
        Returns:
            dict: 配置选项字典
        """
        return {
            "strict": MatcherFactory.STRICT_CONFIG,
            "relaxed": MatcherFactory.RELAXED_CONFIG,
            "default": MatcherFactory.DEFAULT_CONFIG
        }
