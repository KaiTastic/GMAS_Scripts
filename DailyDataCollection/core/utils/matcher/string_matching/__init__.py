# -*- coding: utf-8 -*-
"""
字符串匹配模块 - 简化版入口

模块结构：
- types/: 统一的类型定义（枚举、配置、结果、基础类型）
- targets/: 目标配置和构建系统
- results/: 结果处理、分析和导出
- validators/: 验证器和匹配规则
- tests/: 完整的测试框架
"""

# === 类型定义直接导入 ===
# 枚举类型
from .types.enums import TargetType, MatchType, MatchStrategy, ConfidenceLevel, ValidationLevel, ProcessingMode
# 配置类型
from .types.configs import TargetConfig, MatcherConfig, ValidatorConfig, BuilderConfig
# 结果类型  
from .types.results import MatchResult, SingleMatchResult, MultiMatchResult, BatchMatchResult, AnalysisReport
# 验证器类型
from .types.validators import Validator, ValidationResult, ValidationRule
# 基础类型
from .types.base import BaseConfig, BaseResult

# === 基础匹配组件 ===
from .similarity_calculator import SimilarityCalculator
from .base_matcher import StringMatcher
from .exact_matcher import ExactStringMatcher
from .fuzzy_matcher import FuzzyStringMatcher
from .hybrid_matcher import HybridStringMatcher
from .name_matcher import NameMatcher, ExactNameMatcher, FuzzyNameMatcher, HybridNameMatcher
from .factory import create_name_matcher, create_string_matcher, MatcherFactory

# === 多目标匹配组件 ===
from .core_matcher import MultiTargetMatcher

# === 目标和结果组件 ===
from .targets import create_target_config, TargetBuilder, PresetTargets, get_preset_target
from .results import ResultAnalyzer, ResultExporter
from .validators import get_validator

__all__ = [
    # === 类型定义 ===
    # 枚举类型
    'TargetType', 'MatchType', 'MatchStrategy', 'ConfidenceLevel', 'ValidationLevel', 'ProcessingMode',
    # 配置类型
    'TargetConfig', 'MatcherConfig', 'ValidatorConfig', 'BuilderConfig',
    # 结果类型
    'MatchResult', 'SingleMatchResult', 'MultiMatchResult', 'BatchMatchResult', 'AnalysisReport',
    # 验证器类型
    'Validator', 'ValidationResult', 'ValidationRule',
    # 基础类型
    'BaseConfig', 'BaseResult',
    
    # === 基础匹配组件 ===
    'SimilarityCalculator',
    'StringMatcher', 'ExactStringMatcher', 'FuzzyStringMatcher', 'HybridStringMatcher',
    'NameMatcher', 'ExactNameMatcher', 'FuzzyNameMatcher', 'HybridNameMatcher',
    'create_name_matcher', 'create_string_matcher', 'MatcherFactory',
    
    # === 多目标匹配组件 ===
    'MultiTargetMatcher',
    
    # === 目标和结果组件 ===
    'create_target_config', 'TargetBuilder', 'PresetTargets', 'get_preset_target',
    'ResultAnalyzer', 'ResultExporter', 'get_validator'
]