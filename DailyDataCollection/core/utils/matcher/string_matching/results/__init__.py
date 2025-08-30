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

# 添加基础匹配结果类的导入
try:
    from ..base_matcher import MatchResult
except ImportError:
    # 如果无法导入，提供一个简单的替代实现
    from dataclasses import dataclass
    from typing import Optional
    
    @dataclass
    class MatchResult:
        matched_string: Optional[str] = None
        similarity_score: float = 0.0
        match_type: str = "none"
        confidence: float = 0.0
        is_matched: bool = False

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