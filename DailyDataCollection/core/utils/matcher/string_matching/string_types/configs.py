# -*- coding: utf-8 -*-
"""
配置类型定义
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable

try:
    from .enums import TargetType, MatchStrategy, ValidationLevel, ValidatorType
    from .base import BaseConfig
except ImportError:
    # 处理独立运行的情况
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    from enums import TargetType, MatchStrategy, ValidationLevel, ValidatorType
    from base import BaseConfig


@dataclass
class TargetConfig(BaseConfig):
    """目标配置类（新版本，功能完整）"""
    target_type: TargetType = TargetType.CUSTOM
    patterns: List[str] = field(default_factory=list)
    matcher_strategy: MatchStrategy = MatchStrategy.HYBRID
    fuzzy_threshold: float = 0.65
    case_sensitive: bool = False
    required: bool = True
    weight: float = 1.0
    min_score: float = 0.0
    max_score: float = 1.0
    
    # 处理函数
    preprocessor: Optional[Callable[[str], str]] = None
    postprocessor: Optional[Callable[[str], str]] = None
    validator: Optional[Callable[[str], bool]] = None
    
    # 正则相关
    regex_pattern: Optional[str] = None
    regex_flags: int = 0
    
    # 验证配置
    validation_level: ValidationLevel = ValidationLevel.BASIC
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    
    # 来自 targets/config.py 的额外字段
    max_length: Optional[int] = None
    normalize: bool = True
    
    def validate(self) -> bool:
        """验证配置的有效性"""
        if not self.patterns and not self.regex_pattern:
            return False
        if not 0 <= self.fuzzy_threshold <= 1:
            return False
        if not 0 <= self.weight <= 10:
            return False
        if not 0 <= self.min_score <= self.max_score <= 1:
            return False
        if self.max_length is not None and self.max_length <= 0:
            return False
        return True


@dataclass
class MatcherConfig(BaseConfig):
    """匹配器配置类"""
    strategy: MatchStrategy = MatchStrategy.HYBRID
    global_fuzzy_threshold: float = 0.65
    global_case_sensitive: bool = False
    enable_caching: bool = True
    cache_size: int = 1000
    debug_mode: bool = False
    parallel_processing: bool = False
    max_workers: int = 4
    timeout_seconds: float = 30.0
    
    def validate(self) -> bool:
        """验证配置的有效性"""
        if not 0 <= self.global_fuzzy_threshold <= 1:
            return False
        if self.cache_size < 0:
            return False
        if self.max_workers < 1:
            return False
        if self.timeout_seconds <= 0:
            return False
        return True


@dataclass
class ValidatorConfig(BaseConfig):
    """验证器配置类"""
    validation_level: ValidationLevel = ValidationLevel.BASIC
    validator_type: ValidatorType = ValidatorType.CUSTOM
    strict_mode: bool = False
    ignore_case: bool = True
    trim_whitespace: bool = True
    min_length: int = 0
    max_length: int = 1000
    allowed_chars: Optional[str] = None
    forbidden_chars: Optional[str] = None
    regex_validators: List[str] = field(default_factory=list)
    custom_validators: List[Callable[[str], bool]] = field(default_factory=list)
    
    # 日期验证器特有配置
    date_formats: List[str] = field(default_factory=lambda: [
        "%Y%m%d", "%Y-%m-%d", "%Y/%m/%d",
        "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y"
    ])
    
    # 数字验证器特有配置
    allow_negative: bool = True
    allow_decimal: bool = True
    decimal_places: Optional[int] = None
    
    # URL验证器特有配置
    require_protocol: bool = True
    allowed_protocols: List[str] = field(default_factory=lambda: ["http", "https", "ftp"])
    
    def validate(self) -> bool:
        """验证配置的有效性"""
        if self.min_length < 0 or self.max_length < 0:
            return False
        if self.min_length > self.max_length:
            return False
        if self.decimal_places is not None and self.decimal_places < 0:
            return False
        return True


@dataclass
class BuilderConfig(BaseConfig):
    """构建器配置类 - 来自 targets/builder.py"""
    auto_normalize: bool = True
    auto_validate: bool = True
    strict_validation: bool = False
    default_weight: float = 1.0
    default_threshold: float = 0.65
    enable_preprocessing: bool = True
    enable_postprocessing: bool = True
    
    def validate(self) -> bool:
        """验证配置的有效性"""
        if not 0 <= self.default_weight <= 10:
            return False
        if not 0 <= self.default_threshold <= 1:
            return False
        return True


@dataclass
class ProcessingConfig(BaseConfig):
    """处理配置类"""
    batch_size: int = 100
    max_retries: int = 3
    retry_delay: float = 1.0
    enable_progress_tracking: bool = True
    log_level: str = "INFO"
    output_format: str = "json"
    
    def validate(self) -> bool:
        """验证配置的有效性"""
        if self.batch_size <= 0:
            return False
        if self.max_retries < 0:
            return False
        if self.retry_delay < 0:
            return False
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            return False
        if self.output_format not in ["json", "xml", "csv", "yaml"]:
            return False
        return True


# 导出接口
__all__ = [
    'TargetConfig',
    'MatcherConfig', 
    'ValidatorConfig',
    'BuilderConfig',
    'ProcessingConfig'
]