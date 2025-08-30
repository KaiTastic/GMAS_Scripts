# -*- coding: utf-8 -*-
"""
枚举类型定义
"""

from enum import Enum


class TargetType(Enum):
    """目标类型枚举"""
    NAME = "name"           # 名称
    DATE = "date"           # 日期
    FILE_EXTENSION = "ext"  # 文件后缀
    NUMBER = "number"       # 数字
    EMAIL = "email"         # 邮箱
    PHONE = "phone"         # 电话
    URL = "url"            # 网址
    IP_ADDRESS = "ip"      # IP地址
    CUSTOM = "custom"       # 自定义


class MatchType(Enum):
    """匹配类型枚举"""
    NONE = "none"           # 无匹配
    EXACT = "exact"         # 精确匹配
    FUZZY = "fuzzy"         # 模糊匹配
    PARTIAL = "partial"     # 部分匹配
    REGEX = "regex"         # 正则匹配
    PATTERN = "pattern"     # 模式匹配
    HYBRID = "hybrid"       # 混合匹配


class MatchStrategy(Enum):
    """匹配策略枚举"""
    EXACT = "exact"         # 精确匹配策略
    FUZZY = "fuzzy"         # 模糊匹配策略
    HYBRID = "hybrid"       # 混合匹配策略
    REGEX_ONLY = "regex"    # 仅正则匹配
    NAME_SPECIFIC = "name"  # 名称专用匹配


class ValidationLevel(Enum):
    """验证级别枚举"""
    NONE = "none"           # 无验证
    BASIC = "basic"         # 基础验证
    STRICT = "strict"       # 严格验证
    CUSTOM = "custom"       # 自定义验证


class ProcessingMode(Enum):
    """处理模式枚举"""
    SINGLE = "single"       # 单个处理
    BATCH = "batch"         # 批量处理
    STREAMING = "streaming" # 流式处理


class ConfidenceLevel(Enum):
    """置信度等级枚举（来自 results 模块）"""
    VERY_HIGH = "very_high"  # 0.9-1.0
    HIGH = "high"            # 0.7-0.9
    MEDIUM = "medium"        # 0.5-0.7
    LOW = "low"              # 0.3-0.5
    VERY_LOW = "very_low"    # 0.0-0.3


class ValidatorType(Enum):
    """验证器类型枚举"""
    DATE = "date"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    NUMBER = "number"
    LENGTH = "length"
    REGEX = "regex"
    CUSTOM = "custom"


class AnalysisLevel(Enum):
    """分析级别枚举"""
    BASIC = "basic"         # 基础分析
    DETAILED = "detailed"   # 详细分析
    COMPREHENSIVE = "comprehensive"  # 全面分析