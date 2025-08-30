# -*- coding: utf-8 -*-
"""
单一匹配结果处理模块 - 深度分析单个匹配结果
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import json

# 导入基础匹配结果类
try:
    from ..base_matcher import MatchResult
except ImportError:
    # 如果导入失败，使用本地定义
    from dataclasses import dataclass
    
    @dataclass
    class MatchResult:
        """基础匹配结果类"""
        matched_string: str = ""
        similarity_score: float = 0.0
        match_type: str = "none"
        confidence: float = 0.0
        is_matched: bool = False


class MatchType(Enum):
    """匹配类型枚举"""
    EXACT = "exact"      # 精确匹配
    FUZZY = "fuzzy"      # 模糊匹配  
    PATTERN = "pattern"  # 模式匹配
    HYBRID = "hybrid"    # 混合匹配
    NONE = "none"        # 无匹配


class ConfidenceLevel(Enum):
    """置信度等级枚举"""
    VERY_HIGH = "very_high"  # 0.9-1.0
    HIGH = "high"            # 0.7-0.9
    MEDIUM = "medium"        # 0.5-0.7
    LOW = "low"              # 0.3-0.5
    VERY_LOW = "very_low"    # 0.0-0.3


@dataclass
class SingleMatchResult:
    """
    单一匹配结果类 - 继承自基础 MatchResult，提供更详细的匹配信息
    """
    # 基础匹配结果信息
    matched_string: Optional[str] = None
    similarity_score: float = 0.0
    match_type: str = "none"
    confidence: float = 0.0
    
    # 扩展信息
    target_name: str = ""                                           # 目标名称
    original_target: str = ""                                       # 原始目标字符串
    match_position: Optional[int] = None                           # 匹配位置
    match_length: Optional[int] = None                             # 匹配长度
    preprocessing_applied: List[str] = field(default_factory=list) # 应用的预处理步骤
    metadata: Dict[str, Any] = field(default_factory=dict)        # 元数据
    
    def __post_init__(self):
        """初始化后处理"""
        # 设置匹配状态
        self.is_matched = self.matched_string is not None
        
        # 验证位置和长度参数
        if self.match_position is not None and self.match_length is not None:
            if self.match_position < 0:
                self.match_position = None
            if self.match_length <= 0:
                self.match_length = None

    @property
    def confidence_level(self) -> ConfidenceLevel:
        """获取置信度等级"""
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
    def match_type_enum(self) -> MatchType:
        """获取匹配类型枚举"""
        try:
            return MatchType(self.match_type.lower())
        except (ValueError, AttributeError):
            return MatchType.NONE

    @property
    def is_high_confidence(self) -> bool:
        """是否为高置信度匹配"""
        return self.confidence >= 0.7

    @property
    def match_span(self) -> Optional[tuple]:
        """获取匹配范围 (start, end)"""
        if self.match_position is not None and self.match_length is not None:
            return (self.match_position, self.match_position + self.match_length)
        return None

    def get_context(self, source_string: str, context_length: int = 10) -> str:
        """
        获取匹配上下文
        
        Args:
            source_string: 源字符串
            context_length: 上下文长度
            
        Returns:
            str: 包含上下文的字符串
        """
        if not source_string:
            return self.matched_string or ""
            
        if self.match_position is None or self.match_length is None:
            return self.matched_string or ""
        
        try:
            start = max(0, self.match_position - context_length)
            end = min(len(source_string), self.match_position + self.match_length + context_length)
            context = source_string[start:end]
            
            # 高亮匹配部分
            match_start = self.match_position - start
            match_end = match_start + self.match_length
            
            if 0 <= match_start < len(context) and match_end <= len(context):
                context = (context[:match_start] +
                          f"**{context[match_start:match_end]}**" +
                          context[match_end:])
            
            return context
        except (IndexError, TypeError) as e:
            # 如果发生错误，返回原始匹配字符串
            return self.matched_string or ""

    def validate(self) -> List[str]:
        """
        验证结果完整性
        
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 基础验证
        if not self.target_name:
            errors.append("目标名称不能为空")
            
        if self.is_matched and not self.matched_string:
            errors.append("已匹配但匹配字符串为空")
            
        if not self.is_matched and self.matched_string:
            errors.append("未匹配但匹配字符串不为空")
        
        # 分数验证
        if not (0.0 <= self.similarity_score <= 1.0):
            errors.append(f"相似度分数超出范围: {self.similarity_score}")
            
        if not (0.0 <= self.confidence <= 1.0):
            errors.append(f"置信度超出范围: {self.confidence}")
        
        # 位置验证
        if self.match_position is not None and self.match_position < 0:
            errors.append(f"匹配位置不能为负: {self.match_position}")
            
        if self.match_length is not None and self.match_length <= 0:
            errors.append(f"匹配长度必须为正: {self.match_length}")
        
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'target_name': self.target_name,
            'original_target': self.original_target,
            'matched_string': self.matched_string,
            'similarity_score': self.similarity_score,
            'match_type': self.match_type,
            'confidence': self.confidence,
            'confidence_level': self.confidence_level.value,
            'is_matched': self.is_matched,
            'match_position': self.match_position,
            'match_length': self.match_length,
            'match_span': self.match_span,
            'preprocessing_applied': self.preprocessing_applied,
            'metadata': self.metadata
        }

    def to_json(self, indent: int = 2) -> str:
        """转换为JSON"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def __str__(self) -> str:
        """字符串表示"""
        status = "匹配" if self.is_matched else "未匹配"
        return (f"SingleMatchResult({status} {self.target_name}: "
                f"'{self.matched_string}', "
                f"score={self.similarity_score:.3f}, "
                f"confidence={self.confidence_level.value})")


class SingleResultAnalyzer:
    """单一结果分析器"""

    @staticmethod
    def analyze_result(result: SingleMatchResult, source_string: str = "") -> Dict[str, Any]:
        """
        分析匹配结果
        
        Args:
            result: 匹配结果
            source_string: 源字符串
            
        Returns:
            Dict[str, Any]: 分析报告
        """
        analysis = {
            'basic_info': {
                'target_name': result.target_name,
                'is_matched': result.is_matched,
                'match_type': result.match_type,
                'confidence_level': result.confidence_level.value
            },
            'scores': {
                'similarity': result.similarity_score,
                'confidence': result.confidence,
                'is_high_confidence': result.is_high_confidence
            },
            'match_details': {
                'matched_string': result.matched_string,
                'original_target': result.original_target,
                'position': result.match_position,
                'length': result.match_length,
                'span': result.match_span
            },
            'preprocessing': result.preprocessing_applied,
            'metadata': result.metadata
        }
        
        # 添加上下文信息
        if source_string and result.match_position is not None:
            analysis['context'] = result.get_context(source_string)
        
        # 计算质量分数
        quality_score = SingleResultAnalyzer._calculate_quality_score(result)
        analysis['quality'] = {
            'score': quality_score,
            'level': SingleResultAnalyzer._get_quality_level(quality_score),
            'factors': SingleResultAnalyzer._get_quality_factors(result)
        }
        
        # 验证结果
        validation_errors = result.validate()
        analysis['validation'] = {
            'is_valid': len(validation_errors) == 0,
            'errors': validation_errors
        }
        
        return analysis

    @staticmethod
    def _calculate_quality_score(result: SingleMatchResult) -> float:
        """计算质量分数"""
        if not result.is_matched:
            return 0.0
        
        # 基础分数
        base_score = (result.similarity_score + result.confidence) / 2
        
        # 类型权重
        type_multiplier = {
            MatchType.EXACT: 1.0,
            MatchType.PATTERN: 0.95,
            MatchType.HYBRID: 0.9,
            MatchType.FUZZY: 0.85,
            MatchType.NONE: 0.0
        }
        multiplier = type_multiplier.get(result.match_type_enum, 0.8)
        
        # 位置加分
        position_bonus = 0.05 if result.match_position is not None else 0.0
        
        return min(1.0, base_score * multiplier + position_bonus)

    @staticmethod
    def _get_quality_level(score: float) -> str:
        """获取质量等级"""
        if score >= 0.9:
            return "优秀"
        elif score >= 0.7:
            return "良好"
        elif score >= 0.5:
            return "一般"
        elif score >= 0.3:
            return "较差"
        else:
            return "很差"

    @staticmethod
    def _get_quality_factors(result: SingleMatchResult) -> Dict[str, str]:
        """获取质量因子"""
        factors = {}
        
        if result.similarity_score >= 0.9:
            factors['similarity'] = "相似度很高"
        elif result.similarity_score >= 0.7:
            factors['similarity'] = "相似度较高"
        else:
            factors['similarity'] = "相似度较低"
        
        if result.confidence >= 0.8:
            factors['confidence'] = "置信度很高"
        elif result.confidence >= 0.6:
            factors['confidence'] = "置信度较高"
        else:
            factors['confidence'] = "置信度较低"
        
        if result.match_type_enum == MatchType.EXACT:
            factors['match_type'] = "精确匹配"
        elif result.match_type_enum == MatchType.FUZZY:
            factors['match_type'] = "模糊匹配"
        
        if result.match_position is not None:
            factors['position'] = "有位置信息"
        else:
            factors['position'] = "无位置信息"
        
        return factors

    @staticmethod
    def compare_results(result1: SingleMatchResult, result2: SingleMatchResult) -> Dict[str, Any]:
        """
        比较两个匹配结果
        
        Args:
            result1: 第一个结果
            result2: 第二个结果
            
        Returns:
            Dict[str, Any]: 比较报告
        """
        comparison = {
            'basic_comparison': {
                'both_matched': result1.is_matched and result2.is_matched,
                'neither_matched': not result1.is_matched and not result2.is_matched,
                'result1_better': result1.similarity_score > result2.similarity_score,
                'result2_better': result2.similarity_score > result1.similarity_score,
                'similar_scores': abs(result1.similarity_score - result2.similarity_score) < 0.1
            },
            'score_differences': {
                'similarity_diff': result1.similarity_score - result2.similarity_score,
                'confidence_diff': result1.confidence - result2.confidence
            },
            'type_comparison': {
                'result1_type': result1.match_type,
                'result2_type': result2.match_type,
                'same_type': result1.match_type == result2.match_type
            }
        }
        
        # 质量比较
        quality1 = SingleResultAnalyzer._calculate_quality_score(result1)
        quality2 = SingleResultAnalyzer._calculate_quality_score(result2)
        
        if quality1 > quality2:
            comparison['recommendation'] = 'result1'
            comparison['reason'] = f"结果1质量更高 ({quality1:.3f} vs {quality2:.3f})"
        elif quality2 > quality1:
            comparison['recommendation'] = 'result2'
            comparison['reason'] = f"结果2质量更高 ({quality2:.3f} vs {quality1:.3f})"
        else:
            comparison['recommendation'] = 'tie'
            comparison['reason'] = f"质量相当 ({quality1:.3f})"
        
        return comparison


class SingleResultExporter:
    """单一结果导出器"""

    @staticmethod
    def to_csv_row(result: SingleMatchResult) -> List[str]:
        """
        转换为CSV行数据
        
        Args:
            result: 匹配结果
            
        Returns:
            List[str]: CSV行数据
        """
        return [
            result.target_name,
            result.matched_string or '',
            str(result.similarity_score),
            result.match_type,
            str(result.confidence),
            result.confidence_level.value,
            str(result.is_matched),
            str(result.match_position) if result.match_position is not None else '',
            str(result.match_length) if result.match_length is not None else '',
            ';'.join(result.preprocessing_applied)
        ]

    @staticmethod
    def get_csv_headers() -> List[str]:
        """
        获取CSV表头
        
        Returns:
            List[str]: CSV表头
        """
        return [
            'target_name',
            'matched_string', 
            'similarity_score',
            'match_type',
            'confidence',
            'confidence_level',
            'is_matched',
            'match_position',
            'match_length',
            'preprocessing_applied'
        ]

    @staticmethod
    def to_markdown(result: SingleMatchResult, include_analysis: bool = True) -> str:
        """
        转换为Markdown格式
        
        Args:
            result: 匹配结果
            include_analysis: 是否包含分析信息
            
        Returns:
            str: Markdown格式的字符串
        """
        md = []
        
        # 标题
        status_symbol = "[匹配]" if result.is_matched else "[未匹配]"
        md.append(f"## {status_symbol} {result.target_name}")
        md.append("")
        
        # 基础信息
        md.append("### 基础信息")
        md.append(f"- **匹配状态**: {'已匹配' if result.is_matched else '未匹配'}")
        md.append(f"- **匹配字符串**: `{result.matched_string or 'N/A'}`")
        md.append(f"- **相似度分数**: {result.similarity_score:.3f}")
        md.append(f"- **置信度**: {result.confidence:.3f} ({result.confidence_level.value})")
        md.append(f"- **匹配类型**: {result.match_type}")
        md.append("")
        
        # 位置信息
        if result.match_position is not None:
            md.append("### 位置信息")
            md.append(f"- **匹配位置**: {result.match_position}")
            if result.match_length is not None:
                md.append(f"- **匹配长度**: {result.match_length}")
            md.append(f"- **匹配范围**: {result.match_span}")
            md.append("")
        
        # 预处理信息
        if result.preprocessing_applied:
            md.append("### 预处理步骤")
            for preproc in result.preprocessing_applied:
                md.append(f"- {preproc}")
            md.append("")
        
        # 质量分析
        if include_analysis:
            analysis = SingleResultAnalyzer.analyze_result(result)
            quality = analysis['quality']
            
            md.append("### 质量分析")
            md.append(f"- **质量分数**: {quality['score']:.3f}")
            md.append(f"- **质量等级**: {quality['level']}")
            md.append("")
            
            md.append("### 质量因子")
            for factor, description in quality['factors'].items():
                md.append(f"- **{factor}**: {description}")
            md.append("")
        
        return "\n".join(md)
