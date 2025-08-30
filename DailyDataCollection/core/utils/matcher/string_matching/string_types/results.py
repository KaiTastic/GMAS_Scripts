# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, Tuple

try:
    from .enums import MatchType, ConfidenceLevel, AnalysisLevel
    from .base import BaseResult
except ImportError:
    # 处理独立运行的情况
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    from enums import MatchType, ConfidenceLevel, AnalysisLevel
    from base import BaseResult


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
        result = {
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
        
        # 如果是 SingleMatchResult 类型，添加额外字段
        if hasattr(self, 'target_name'):
            result['target_name'] = getattr(self, 'target_name', '')
            
        return result
    
    def __str__(self) -> str:
        """字符串表示"""
        if self.is_matched:
            return f"MatchResult(match='{self.matched_string}', score={self.similarity_score:.3f}, type={self.match_type.value})"
        else:
            return f"MatchResult(no_match, best_score={self.similarity_score:.3f})"
    
    def to_json(self, indent: int = 2) -> str:
        """转换为JSON格式"""
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass
class SingleMatchResult(MatchResult):
    """单一目标匹配结果（扩展版）"""
    target_name: str = ""
    preprocessing_applied: bool = False
    postprocessing_applied: bool = False
    validation_passed: bool = True
    error_message: Optional[str] = None
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
            
    @property
    def confidence_level(self) -> ConfidenceLevel:
        """置信度等级属性"""
        return self.get_confidence_level()
    
    @property
    def match_type_enum(self) -> MatchType:
        """匹配类型枚举属性"""
        return self.match_type
    
    @property
    def is_high_confidence(self) -> bool:
        """是否高置信度"""
        return self.confidence >= 0.7
    
    @property
    def match_span(self) -> Optional[Tuple[int, int]]:
        """匹配范围"""
        if self.match_position is not None and self.match_length is not None:
            return (self.match_position[0], self.match_position[0] + self.match_length)
        return self.match_position
        
    def get_context(self, source_text: str, context_length: int = 10) -> str:
        """获取匹配上下文
        
        Args:
            source_text: 源文本
            context_length: 上下文长度
            
        Returns:
            str: 带标记的上下文
        """
        if not source_text or self.match_position is None:
            return self.matched_string or ""
        
        start, end = self.match_position
        # 验证位置的有效性
        if (start < 0 or end > len(source_text) or start > end or 
            start >= len(source_text) or end < 0):
            return self.matched_string or ""
        
        # 计算上下文范围
        context_start = max(0, start - context_length)
        context_end = min(len(source_text), end + context_length)
        
        # 构建上下文
        before = source_text[context_start:start]
        matched = source_text[start:end]
        after = source_text[end:context_end]
        
        return f"{before}**{matched}**{after}"
    
    def validate(self) -> List[str]:
        """验证结果
        
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 检查分数范围
        if not 0.0 <= self.similarity_score <= 1.0:
            errors.append(f"相似度分数超出范围: {self.similarity_score}")
        
        if not 0.0 <= self.confidence <= 1.0:
            errors.append(f"置信度超出范围: {self.confidence}")
        
        # 检查目标名称
        if not self.target_name:
            errors.append("目标名称不能为空")
        
        # 检查位置参数
        if self.match_position is not None:
            if isinstance(self.match_position, (tuple, list)) and len(self.match_position) >= 2:
                if self.match_position[0] < 0:
                    errors.append(f"匹配位置不能为负数: {self.match_position[0]}")
            elif isinstance(self.match_position, int) and self.match_position < 0:
                errors.append(f"匹配位置不能为负数: {self.match_position}")
        
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'matched_string': self.matched_string,
            'similarity_score': self.similarity_score,
            'match_type': self.match_type.value if hasattr(self.match_type, 'value') else str(self.match_type),
            'confidence': self.confidence,
            'source_pattern': self.source_pattern,
            'match_position': self.match_position,
            'alternatives': self.alternatives,
            'is_matched': self.is_matched,
            'timestamp': self.timestamp.isoformat(),
            'processing_time': self.processing_time,
            'metadata': self.metadata,
            'target_name': self.target_name
        }
    
    def to_json(self, indent: int = 2) -> str:
        """转换为JSON格式"""
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

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
    
    def get_match_score(self, target_name: str) -> float:
        """获取指定目标的匹配分数"""
        match = self.get_match(target_name)
        return match.similarity_score if match else 0.0
    
    def get_matched_targets(self) -> List[str]:
        """获取所有匹配的目标列表"""
        return [name for name, match in self.matches.items() if match.is_matched]
    
    def get_summary(self) -> Dict[str, Any]:
        """获取结果摘要"""
        return {
            'source': self.source_string,
            'total_targets': len(self.matches),
            'matched_targets': self.match_count,
            'matched_count': self.match_count,  # 测试期望的字段名
            'completion_rate': self.match_count / len(self.matches) if self.matches else 0.0,
            'overall_score': self.overall_score,
            'is_complete': self.is_complete,
            'missing_targets': self.missing_targets
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
