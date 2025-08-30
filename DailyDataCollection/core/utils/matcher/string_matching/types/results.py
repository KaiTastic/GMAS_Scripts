# -*- coding: utf-8 -*-
"""
结果类型定义
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, Tuple
from core.utils.matcher.string_matching.types.enums import MatchType, ConfidenceLevel, AnalysisLevel
from core.utils.matcher.string_matching.types.base import BaseResult


@dataclass
class MatchResult(BaseResult):
    """单个匹配结果"""
    matched_string: Optional[str] = None
    similarity_score: float = 0.0
    match_type: MatchType = MatchType.NONE
    confidence: float = 0.0
    source_pattern: Optional[str] = None
    match_position: Optional[Tuple[int, int]] = None  # (start, end)
    alternatives: List[str] = field(default_factory=list)
    
    @property
    def is_matched(self) -> bool:
        """是否匹配成功"""
        return (self.matched_string is not None and 
                self.match_type != MatchType.NONE and 
                self.similarity_score > 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'matched_string': self.matched_string,
            'similarity_score': self.similarity_score,
            'match_type': self.match_type.value,
            'confidence': self.confidence,
            'source_pattern': self.source_pattern,
            'match_position': self.match_position,
            'alternatives': self.alternatives,
            'is_matched': self.is_matched,
            'timestamp': self.timestamp.isoformat(),
            'processing_time': self.processing_time,
            'metadata': self.metadata
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        if self.is_matched:
            return f"MatchResult(match='{self.matched_string}', score={self.similarity_score:.3f}, type={self.match_type.value})"
        else:
            return f"MatchResult(no_match, best_score={self.similarity_score:.3f})"


@dataclass
class SingleMatchResult(MatchResult):
    """单一目标匹配结果（扩展版）"""
    target_name: str = ""
    preprocessing_applied: bool = False
    postprocessing_applied: bool = False
    validation_passed: bool = True
    error_message: Optional[str] = None
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    match_length: Optional[int] = None
    context_before: Optional[str] = None
    context_after: Optional[str] = None
    
    def get_confidence_level(self) -> ConfidenceLevel:
        """根据置信度值确定级别"""
        if self.confidence >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif self.confidence >= 0.7:
            return ConfidenceLevel.HIGH
        elif self.confidence >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif self.confidence >= 0.3:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW


@dataclass
class MultiMatchResult(BaseResult):
    """多目标匹配结果"""
    source_string: str = ""
    matches: Dict[str, MatchResult] = field(default_factory=dict)
    overall_score: float = 0.0
    completeness_ratio: float = 0.0
    weighted_score: float = 0.0
    missing_targets: List[str] = field(default_factory=list)
    extra_matches: List[str] = field(default_factory=list)
    
    @property
    def is_complete(self) -> bool:
        """是否完全匹配"""
        return len(self.missing_targets) == 0
    
    @property
    def match_count(self) -> int:
        """匹配数量"""
        return sum(1 for match in self.matches.values() if match.is_matched)
    
    def get_match(self, target_name: str) -> Optional[MatchResult]:
        """获取指定目标的匹配结果"""
        return self.matches.get(target_name)
    
    def get_matched_value(self, target_name: str) -> Optional[str]:
        """获取指定目标的匹配值"""
        match = self.get_match(target_name)
        return match.matched_string if match and match.is_matched else None
    
    def has_match(self, target_name: str) -> bool:
        """检查是否匹配了指定目标"""
        match = self.get_match(target_name)
        return match is not None and match.is_matched
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'source_string': self.source_string,
            'matches': {name: match.to_dict() for name, match in self.matches.items()},
            'overall_score': self.overall_score,
            'completeness_ratio': self.completeness_ratio,
            'weighted_score': self.weighted_score,
            'missing_targets': self.missing_targets,
            'extra_matches': self.extra_matches,
            'is_complete': self.is_complete,
            'match_count': self.match_count,
            'timestamp': self.timestamp.isoformat(),
            'processing_time': self.processing_time,
            'metadata': self.metadata
        }


@dataclass
class BatchMatchResult(BaseResult):
    """批量匹配结果"""
    source_strings: List[str] = field(default_factory=list)
    results: List[MultiMatchResult] = field(default_factory=list)
    success_count: int = 0
    failure_count: int = 0
    total_processed: int = 0
    average_score: float = 0.0
    processing_summary: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        return self.success_count / self.total_processed if self.total_processed > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'source_strings': self.source_strings,
            'results': [result.to_dict() for result in self.results],
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'total_processed': self.total_processed,
            'average_score': self.average_score,
            'success_rate': self.success_rate,
            'processing_summary': self.processing_summary,
            'timestamp': self.timestamp.isoformat(),
            'processing_time': self.processing_time,
            'metadata': self.metadata
        }


@dataclass
class AnalysisReport(BaseResult):
    """分析报告"""
    total_processed: int = 0
    successful_matches: int = 0
    failed_matches: int = 0
    average_score: float = 0.0
    best_score: float = 0.0
    worst_score: float = 0.0
    score_distribution: Dict[str, int] = field(default_factory=dict)
    target_statistics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    analysis_level: AnalysisLevel = AnalysisLevel.BASIC
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        return self.successful_matches / self.total_processed if self.total_processed > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'total_processed': self.total_processed,
            'successful_matches': self.successful_matches,
            'failed_matches': self.failed_matches,
            'average_score': self.average_score,
            'best_score': self.best_score,
            'worst_score': self.worst_score,
            'success_rate': self.success_rate,
            'score_distribution': self.score_distribution,
            'target_statistics': self.target_statistics,
            'performance_metrics': self.performance_metrics,
            'recommendations': self.recommendations,
            'analysis_level': self.analysis_level.value,
            'timestamp': self.timestamp.isoformat(),
            'processing_time': self.processing_time,
            'metadata': self.metadata
        }


# 导出接口
__all__ = [
    'MatchResult',
    'SingleMatchResult', 
    'MultiMatchResult',
    'BatchMatchResult',
    'AnalysisReport'
]
