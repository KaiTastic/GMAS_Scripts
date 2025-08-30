# -*- coding: utf-8 -*-
"""
Results 模块 - 字符串匹配结果处理系统
提供单一结果深度分析和多结果批量处理功能
"""

from .single_result import (
    SingleMatchResult,
    SingleResultAnalyzer,
    SingleResultExporter,
    MatchType,
    ConfidenceLevel
)

from .multi_result import (
    MultiMatchResult,
    ResultAnalyzer,
    ResultExporter
)

from .config import (
    AnalyzerConfig,
    ExporterConfig,
    DEFAULT_ANALYZER_CONFIG,
    DEFAULT_EXPORTER_CONFIG
)

# 直接导入统一类型定义，无向后兼容
from ..types.results import MatchResult

__all__ = [
    # 基础结果类
    'MatchResult',
    # 单一结果处理类
    'SingleMatchResult',
    'SingleResultAnalyzer', 
    'SingleResultExporter',
    'MatchType',
    'ConfidenceLevel',
    # 多结果处理类
    'MultiMatchResult',
    'ResultAnalyzer',
    'ResultExporter',
    # 配置类
    'AnalyzerConfig',
    'ExporterConfig',
    'DEFAULT_ANALYZER_CONFIG',
    'DEFAULT_EXPORTER_CONFIG'
] 