# -*- coding: utf-8 -*-
"""
统一类型系统 - 无循环导入版本

仅导出类型定义，不依赖主模块的任何组件。
"""

# 基础类型（无依赖）
from .base import BaseConfig, BaseResult

# 枚举类型（无依赖）
from .enums import (
    TargetType, MatchType, MatchStrategy, ValidationLevel, ProcessingMode,
    ConfidenceLevel, ValidatorType, AnalysisLevel
)

# 结果类型（仅依赖base和enums）
from .results import (
    MatchResult, MultiMatchResult, AnalysisReport, 
    SingleMatchResult, BatchMatchResult
)

# 配置类型（仅依赖base和enums）
from .configs import (
    TargetConfig, MatcherConfig, ValidatorConfig, 
    BuilderConfig, ProcessingConfig
)

# 验证器类型（仅依赖base）
from .validators import (
    Validator, ValidationResult, ValidatorDefinition, 
    ValidationRule, ValidationSchema
)

# 导出所有25个类型
__all__ = [
    # 基础类型 (2个)
    'BaseConfig', 'BaseResult',
    
    # 枚举类型 (8个)
    'TargetType', 'MatchType', 'MatchStrategy', 'ValidationLevel', 'ProcessingMode',
    'ConfidenceLevel', 'ValidatorType', 'AnalysisLevel',
    
    # 结果类型 (5个)
    'MatchResult', 'MultiMatchResult', 'AnalysisReport', 
    'SingleMatchResult', 'BatchMatchResult',
    
    # 配置类型 (5个)
    'TargetConfig', 'MatcherConfig', 'ValidatorConfig', 
    'BuilderConfig', 'ProcessingConfig',
    
    # 验证器类型 (5个)
    'Validator', 'ValidationResult', 'ValidatorDefinition', 
    'ValidationRule', 'ValidationSchema'
]

# 清理版本信息
__version__ = "2.0.0-cleaned"
__status__ = "No aliases, no backward compatibility"