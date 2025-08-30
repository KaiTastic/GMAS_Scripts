# -*- coding: utf-8 -*-
"""
向后兼容层 - 提供旧版本功能的便捷访问

此模块为已移入deprecated文件夹的功能提供兼容性接口，
帮助用户平滑迁移到新的模块化架构。
"""

import warnings
from typing import Optional, List, Dict, Any

# 导入新版本组件
from .core_matcher import MultiTargetMatcher as NewMultiTargetMatcher
from .targets import TargetType, TargetBuilder, PresetTargets
from .results import MultiMatchResult

# 导入旧版本组件
from .multi_target_matcher import (
    MultiTargetMatcher as OriginalMultiTargetMatcher,
    TargetType as OriginalTargetType,
    TargetConfig as OriginalTargetConfig
)


def create_legacy_matcher(debug: bool = False) -> OriginalMultiTargetMatcher:
    """
    创建配置好的旧版本匹配器
    
    Args:
        debug: 是否启用调试模式
        
    Returns:
        配置好的旧版本多目标匹配器
        
    Example:
        >>> matcher = create_legacy_matcher()
        >>> matcher.add_name_target("person", ["john", "jane"])
        >>> result = matcher.match_string("john_document.pdf")
    """
    warnings.warn(
        "create_legacy_matcher is deprecated. "
        "Please migrate to the new MultiTargetMatcher API.",
        DeprecationWarning,
        stacklevel=2
    )
    
    return OriginalMultiTargetMatcher(debug=debug)


def create_modern_matcher_from_legacy_config(
    legacy_matcher: OriginalMultiTargetMatcher
) -> NewMultiTargetMatcher:
    """
    从旧版本匹配器配置创建新版本匹配器
    
    Args:
        legacy_matcher: 已配置的旧版本匹配器
        
    Returns:
        等效配置的新版本匹配器
    """
    warnings.warn(
        "This is a migration helper function. "
        "Please consider using the new API directly.",
        DeprecationWarning,
        stacklevel=2
    )
    
    new_matcher = NewMultiTargetMatcher()
    
    # 迁移目标配置 (这里简化实现，实际需要根据具体配置来迁移)
    # 注意：这是一个示例实现，可能需要根据实际的配置结构进行调整
    
    return new_matcher


def run_simple_test():
    """运行简单测试演示"""
    warnings.warn(
        "This function uses deprecated code. "
        "Please use the new test framework in tests/ folder.",
        DeprecationWarning,
        stacklevel=2
    )
    
    try:
        from .deprecated.simple_test import test_basic_functionality
        test_basic_functionality()
    except ImportError as e:
        print(f"无法导入deprecated测试: {e}")
        print("请检查deprecated文件夹中的文件是否完整")


def run_complete_demo():
    """运行完整演示"""
    warnings.warn(
        "This function uses deprecated code. "
        "Please use refactored_multi_target_demo.py for the latest features.",
        DeprecationWarning,
        stacklevel=2
    )
    
    try:
        from .deprecated.complete_demo import main as complete_demo_main
        complete_demo_main()
    except ImportError as e:
        print(f"无法导入完整演示: {e}")
        print("请检查deprecated文件夹中的文件是否完整")


def run_legacy_demo():
    """运行旧版本演示"""
    warnings.warn(
        "This function uses deprecated code. "
        "Please use refactored_multi_target_demo.py for the latest features.",
        DeprecationWarning,
        stacklevel=2
    )
    
    try:
        from .deprecated.multi_target_demo import main as legacy_demo_main
        legacy_demo_main()
    except ImportError as e:
        print(f"无法导入旧版演示: {e}")
        print("请检查deprecated文件夹中的文件是否完整")


def run_performance_comparison():
    """运行性能对比测试"""
    warnings.warn(
        "Performance comparison uses both old and new code. "
        "Consider using the benchmark tools in tests/benchmarks/ for detailed analysis.",
        DeprecationWarning,
        stacklevel=2
    )
    
    try:
        from .deprecated.performance_comparison import main as perf_main
        perf_main()
    except ImportError as e:
        print(f"无法导入性能对比: {e}")
        print("请检查deprecated文件夹中的文件是否完整")


class LegacyMatcherWrapper:
    """
    旧版本匹配器的包装类，提供向后兼容的接口
    同时引导用户迁移到新版本
    """
    
    def __init__(self, debug: bool = False):
        warnings.warn(
            "LegacyMatcherWrapper is deprecated. "
            "Please migrate to MultiTargetMatcher for better performance and features.",
            DeprecationWarning,
            stacklevel=2
        )
        
        self._legacy_matcher = OriginalMultiTargetMatcher(debug=debug)
        self._migration_suggestions = []
    
    def add_name_target(self, name: str, names: List[str], **kwargs):
        """添加名称目标 (兼容旧版本接口)"""
        self._migration_suggestions.append(
            f"Consider using TargetBuilder.name('{name}').with_names({names}) for better configuration"
        )
        return self._legacy_matcher.add_name_target(name, names, **kwargs)
    
    def add_date_target(self, name: str, **kwargs):
        """添加日期目标 (兼容旧版本接口)"""
        self._migration_suggestions.append(
            f"Consider using get_preset_target(PresetTargets.DATE) for standardized date matching"
        )
        return self._legacy_matcher.add_date_target(name, **kwargs)
    
    def match_string(self, text: str):
        """匹配字符串 (兼容旧版本接口)"""
        return self._legacy_matcher.match_string(text)
    
    def print_migration_suggestions(self):
        """打印迁移建议"""
        if self._migration_suggestions:
            print("\n🔄 迁移建议:")
            for i, suggestion in enumerate(self._migration_suggestions, 1):
                print(f"  {i}. {suggestion}")
            print("\n💡 查看 refactored_multi_target_demo.py 了解新API的用法")


# 便捷函数别名
create_legacy = create_legacy_matcher
demo_simple = run_simple_test  
demo_complete = run_complete_demo
demo_legacy = run_legacy_demo
benchmark = run_performance_comparison


# 兼容性导出
__all__ = [
    'create_legacy_matcher',
    'create_modern_matcher_from_legacy_config',
    'run_simple_test',
    'run_complete_demo', 
    'run_legacy_demo',
    'run_performance_comparison',
    'LegacyMatcherWrapper',
    # 便捷别名
    'create_legacy',
    'demo_simple',
    'demo_complete',
    'demo_legacy',
    'benchmark'
]
