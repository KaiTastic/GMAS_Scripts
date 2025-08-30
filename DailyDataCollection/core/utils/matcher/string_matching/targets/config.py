# -*- coding: utf-8 -*-
"""
目标配置模块 - 使用统一类型定义
"""

# 直接导入具体类型，避免循环导入
try:
    from ..string_types.enums import TargetType, MatchStrategy, ValidationLevel
    from ..string_types.configs import TargetConfig, BuilderConfig
except ImportError:
    # 处理独立运行的情况
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)
    
    from string_types.enums import TargetType, MatchStrategy, ValidationLevel
    from string_types.configs import TargetConfig, BuilderConfig

def create_target_config(**kwargs):
    """创建目标配置的便利函数"""
    return TargetConfig(**kwargs)

# 导出接口
__all__ = [
    'TargetType',
    'TargetConfig',
    'BuilderConfig',
    'create_target_config',
    'MatchStrategy', 
    'BuilderConfig',
    'ValidationLevel'
]
