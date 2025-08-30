# -*- coding: utf-8 -*-
"""
单一匹配结果处理模块 - 深度分析单个匹配结果
"""

from typing import Dict, Any, Optional, List
import json

# 直接导入具体类型，避免循环导入
from ..types.enums import MatchType, ConfidenceLevel
from ..types.results import SingleMatchResult, MatchResult
from ..types.validators import ValidationResult


class SingleResultAnalyzer:
    """
    单一匹配结果分析器 - 深度分析单个匹配结果
    """
    
    def __init__(self, result: SingleMatchResult):
        """初始化分析器
        
        Args:
            result: 要分析的单一匹配结果
        """
        self.result = result
    
    def analyze(self) -> Dict[str, Any]:
        """全面分析匹配结果
        
        Returns:
            Dict[str, Any]: 分析报告
        """
        analysis = {
            "basic_info": self._analyze_basic_info(),
            "quality_assessment": self._analyze_quality(),
            "confidence_analysis": self._analyze_confidence(),
            "position_analysis": self._analyze_position(),
            "recommendations": self._generate_recommendations()
        }
        
        return analysis
    
    def _analyze_basic_info(self) -> Dict[str, Any]:
        """分析基础信息"""
        return {
            "is_matched": self.result.is_matched,
            "matched_string": self.result.matched_string,
            "similarity_score": self.result.similarity_score,
            "match_type": self.result.match_type,
            "confidence": self.result.confidence,
            "target_name": self.result.target_name
        }
    
    def _analyze_quality(self) -> Dict[str, Any]:
        """分析匹配质量"""
        quality_score = (self.result.similarity_score * 0.7 + self.result.confidence * 0.3)
        
        if quality_score >= 0.9:
            quality_level = "excellent"
        elif quality_score >= 0.8:
            quality_level = "good"
        elif quality_score >= 0.6:
            quality_level = "fair"
        elif quality_score >= 0.4:
            quality_level = "poor"
        else:
            quality_level = "very_poor"
        
        return {
            "quality_score": quality_score,
            "quality_level": quality_level,
            "normalized_score": self.result.similarity_score * 100,
            "confidence_level": self.result.confidence_level.value
        }
    
    def _analyze_confidence(self) -> Dict[str, Any]:
        """分析置信度"""
        return {
            "confidence_value": self.result.confidence,
            "confidence_level": self.result.confidence_level.value,
            "is_high_confidence": self.result.confidence >= 0.7,
            "reliability": "high" if self.result.confidence >= 0.8 else 
                          "medium" if self.result.confidence >= 0.6 else "low"
        }
    
    def _analyze_position(self) -> Dict[str, Any]:
        """分析位置信息"""
        if self.result.match_position is not None and self.result.match_length is not None:
            return {
                "has_position_info": True,
                "position": self.result.match_position,
                "length": self.result.match_length,
                "end_position": self.result.match_position + self.result.match_length
            }
        else:
            return {
                "has_position_info": False,
                "position": None,
                "length": None
            }
    
    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if not self.result.is_matched:
            recommendations.append("未找到匹配，建议降低匹配阈值或扩大搜索范围")
        elif self.result.similarity_score < 0.7:
            recommendations.append("匹配分数较低，建议验证匹配结果的准确性")
        
        if self.result.confidence < 0.6:
            recommendations.append("置信度较低，建议使用多种匹配策略进行验证")
        
        if self.result.match_position is None:
            recommendations.append("缺少位置信息，建议在匹配过程中记录位置")
        
        if not self.result.preprocessing_applied:
            recommendations.append("未应用预处理，考虑使用文本标准化提高匹配效果")
        
        return recommendations


class SingleResultValidator:
    """
    单一匹配结果验证器
    """
    
    @staticmethod
    def validate(result: SingleMatchResult) -> ValidationResult:
        """验证单一匹配结果
        
        Args:
            result: 要验证的结果
            
        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        suggestions = []
        
        # 检查基本一致性
        if result.is_matched and result.matched_string is None:
            errors.append("匹配状态与匹配字符串不一致")
        
        # 检查分数范围
        if not 0.0 <= result.similarity_score <= 1.0:
            errors.append(f"相似度分数超出范围: {result.similarity_score}")
        
        if not 0.0 <= result.confidence <= 1.0:
            errors.append(f"置信度超出范围: {result.confidence}")
        
        # 检查位置参数
        if result.match_position is not None and result.match_position < 0:
            errors.append(f"匹配位置不能为负数: {result.match_position}")
        
        if result.match_length is not None and result.match_length <= 0:
            errors.append(f"匹配长度必须为正数: {result.match_length}")
        
        # 生成建议
        if result.similarity_score < 0.5:
            suggestions.append("相似度分数较低，考虑调整匹配策略")
        
        if result.confidence < 0.7:
            suggestions.append("置信度较低，建议进行人工验证")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            error_message="; ".join(errors) if errors else "",
            suggestions=suggestions,
            validated_value=result.matched_string if is_valid else None,
            metadata={"validation_timestamp": "2025-08-30"}
        )


class SingleResultExporter:
    """
    单一匹配结果导出器
    """
    
    @staticmethod
    def to_dict(result: SingleMatchResult, include_metadata: bool = True) -> Dict[str, Any]:
        """导出为字典"""
        return result.to_dict()
    
    @staticmethod
    def to_json(result: SingleMatchResult, include_metadata: bool = True, indent: int = 2) -> str:
        """导出为JSON"""
        data = SingleResultExporter.to_dict(result, include_metadata)
        return json.dumps(data, ensure_ascii=False, indent=indent)
    
    @staticmethod
    def to_summary(result: SingleMatchResult) -> str:
        """导出为摘要文本"""
        if result.is_matched:
            return f"匹配成功: '{result.matched_string}' (分数: {result.similarity_score:.3f}, 置信度: {result.confidence:.3f})"
        else:
            return f"匹配失败 (最佳分数: {result.similarity_score:.3f})"


# 导出接口
__all__ = [
    'MatchType',
    'ConfidenceLevel',
    'SingleMatchResult',
    'SingleResultAnalyzer',
    'SingleResultValidator', 
    'SingleResultExporter'
]
