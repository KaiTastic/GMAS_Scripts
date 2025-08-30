# -*- coding: utf-8 -*-
"""
Results 模块配置
"""

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class AnalyzerConfig:
    """分析器配置"""
    quality_weights: Dict[str, float] = None
    confidence_thresholds: Dict[str, float] = None
    context_length: int = 20
    batch_size: int = 1000
    enable_caching: bool = True
    
    def __post_init__(self):
        if self.quality_weights is None:
            self.quality_weights = {
                'similarity_score': 0.4,
                'confidence': 0.3,
                'match_type_bonus': 0.2,
                'consistency_check': 0.1
            }
        
        if self.confidence_thresholds is None:
            self.confidence_thresholds = {
                'very_high': 0.9,
                'high': 0.7,
                'medium': 0.5,
                'low': 0.3
            }

@dataclass 
class ExporterConfig:
    """导出器配置"""
    csv_encoding: str = 'utf-8'
    markdown_include_analysis: bool = True
    json_indent: int = 2
    excel_sheet_name: str = 'MatchResults'

# 默认配置实例
DEFAULT_ANALYZER_CONFIG = AnalyzerConfig()
DEFAULT_EXPORTER_CONFIG = ExporterConfig()
