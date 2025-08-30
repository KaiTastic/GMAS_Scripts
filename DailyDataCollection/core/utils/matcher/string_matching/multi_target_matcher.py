# -*- coding: utf-8 -*-
"""
多目标字符串匹配器 - 支持同时匹配多种类型的目标信息
"""

from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
from datetime import datetime

from .base_matcher import StringMatcher, MatchResult
from .factory import create_string_matcher


class TargetType(Enum):
    """目标类型枚举"""
    NAME = "name"           # 名称
    DATE = "date"           # 日期
    FILE_EXTENSION = "ext"  # 文件后缀
    NUMBER = "number"       # 数字
    CUSTOM = "custom"       # 自定义


@dataclass
class TargetConfig:
    """目标配置类"""
    target_type: TargetType
    patterns: List[str]                    # 目标模式列表
    matcher_type: str = "hybrid"           # 匹配器类型
    fuzzy_threshold: float = 0.65          # 模糊匹配阈值
    case_sensitive: bool = False           # 是否区分大小写
    required: bool = True                  # 是否必需匹配
    weight: float = 1.0                    # 权重
    preprocessor: Optional[callable] = None # 预处理函数
    validator: Optional[callable] = None    # 验证函数
    regex_pattern: Optional[str] = None     # 正则表达式模式
    min_score: float = 0.0                 # 最小匹配分数


@dataclass
class MultiMatchResult:
    """多目标匹配结果"""
    source_string: str                                          # 源字符串
    matches: Dict[str, MatchResult] = field(default_factory=dict)  # 匹配结果字典
    overall_score: float = 0.0                                  # 整体匹配分数
    is_complete: bool = False                                   # 是否完整匹配
    missing_targets: List[str] = field(default_factory=list)    # 缺失的目标
    
    def get_match(self, target_name: str) -> Optional[MatchResult]:
        """获取指定目标的匹配结果"""
        return self.matches.get(target_name)
    
    def get_matched_value(self, target_name: str) -> Optional[str]:
        """获取指定目标的匹配值"""
        match = self.get_match(target_name)
        return match.matched_string if match else None
    
    def has_match(self, target_name: str) -> bool:
        """检查是否匹配了指定目标"""
        match = self.get_match(target_name)
        return match is not None and match.is_matched


class MultiTargetMatcher:
    """多目标字符串匹配器
    
    支持同时匹配多种类型的目标信息，如名称、日期、文件后缀等
    """
    
    def __init__(self, debug: bool = False):
        """初始化多目标匹配器
        
        Args:
            debug: 是否启用调试模式
        """
        self.debug = debug
        self.targets: Dict[str, TargetConfig] = {}
        self.matchers: Dict[str, StringMatcher] = {}
        
    def add_target(self, name: str, config: TargetConfig) -> 'MultiTargetMatcher':
        """添加目标配置
        
        Args:
            name: 目标名称
            config: 目标配置
            
        Returns:
            MultiTargetMatcher: 返回自身以支持链式调用
        """
        self.targets[name] = config
        
        # 创建对应的匹配器
        self.matchers[name] = create_string_matcher(
            matcher_type=config.matcher_type,
            fuzzy_threshold=config.fuzzy_threshold,
            case_sensitive=config.case_sensitive,
            debug=self.debug
        )
        
        self._log_debug(f"添加目标: {name}, 类型: {config.target_type.value}")
        return self
    
    def add_name_target(self, name: str, names: List[str], 
                       matcher_type: str = "hybrid", 
                       fuzzy_threshold: float = 0.65,
                       required: bool = True,
                       weight: float = 1.0) -> 'MultiTargetMatcher':
        """添加名称匹配目标
        
        Args:
            name: 目标名称
            names: 候选名称列表
            matcher_type: 匹配器类型
            fuzzy_threshold: 模糊匹配阈值
            required: 是否必需
            weight: 权重
        """
        config = TargetConfig(
            target_type=TargetType.NAME,
            patterns=names,
            matcher_type=matcher_type,
            fuzzy_threshold=fuzzy_threshold,
            required=required,
            weight=weight
        )
        return self.add_target(name, config)
    
    def add_date_target(self, name: str, date_formats: List[str] = None,
                       fuzzy_threshold: float = 0.8,
                       required: bool = True,
                       weight: float = 1.0) -> 'MultiTargetMatcher':
        """添加日期匹配目标
        
        Args:
            name: 目标名称
            date_formats: 日期格式列表，如 ["YYYYMMDD", "YYYY-MM-DD"]
            fuzzy_threshold: 模糊匹配阈值
            required: 是否必需
            weight: 权重
        """
        if date_formats is None:
            date_formats = [
                r"\d{8}",           # YYYYMMDD
                r"\d{4}-\d{2}-\d{2}", # YYYY-MM-DD
                r"\d{4}/\d{2}/\d{2}", # YYYY/MM/DD
                r"\d{2}-\d{2}-\d{4}", # DD-MM-YYYY
                r"\d{2}/\d{2}/\d{4}"  # DD/MM/YYYY
            ]
        
        config = TargetConfig(
            target_type=TargetType.DATE,
            patterns=date_formats,
            matcher_type="fuzzy",
            fuzzy_threshold=fuzzy_threshold,
            required=required,
            weight=weight,
            regex_pattern=r"(\d{4}[-/]?\d{2}[-/]?\d{2}|\d{2}[-/]?\d{2}[-/]?\d{4})",
            validator=self._validate_date
        )
        return self.add_target(name, config)
    
    def add_extension_target(self, name: str, extensions: List[str],
                           case_sensitive: bool = False,
                           required: bool = False,
                           weight: float = 0.5) -> 'MultiTargetMatcher':
        """添加文件扩展名匹配目标
        
        Args:
            name: 目标名称
            extensions: 扩展名列表，如 [".txt", ".pdf", ".docx"]
            case_sensitive: 是否区分大小写
            required: 是否必需
            weight: 权重
        """
        # 确保扩展名以点开头
        normalized_exts = []
        for ext in extensions:
            if not ext.startswith('.'):
                ext = '.' + ext
            normalized_exts.append(ext)
        
        config = TargetConfig(
            target_type=TargetType.FILE_EXTENSION,
            patterns=normalized_exts,
            matcher_type="exact",
            case_sensitive=case_sensitive,
            required=required,
            weight=weight,
            regex_pattern=r"\.([a-zA-Z0-9]+)$"
        )
        return self.add_target(name, config)
    
    def add_number_target(self, name: str, number_patterns: List[str] = None,
                         fuzzy_threshold: float = 0.9,
                         required: bool = False,
                         weight: float = 0.8) -> 'MultiTargetMatcher':
        """添加数字匹配目标
        
        Args:
            name: 目标名称
            number_patterns: 数字模式列表
            fuzzy_threshold: 模糊匹配阈值
            required: 是否必需
            weight: 权重
        """
        if number_patterns is None:
            number_patterns = [
                r"\d+",             # 整数
                r"\d+\.\d+",        # 小数
                r"\d{1,3}(,\d{3})*", # 带逗号的数字
            ]
        
        config = TargetConfig(
            target_type=TargetType.NUMBER,
            patterns=number_patterns,
            matcher_type="fuzzy",
            fuzzy_threshold=fuzzy_threshold,
            required=required,
            weight=weight,
            regex_pattern=r"(\d+(?:[.,]\d+)*)",
            validator=self._validate_number
        )
        return self.add_target(name, config)
    
    def add_custom_target(self, name: str, patterns: List[str],
                         matcher_type: str = "hybrid",
                         fuzzy_threshold: float = 0.65,
                         case_sensitive: bool = False,
                         required: bool = True,
                         weight: float = 1.0,
                         regex_pattern: Optional[str] = None,
                         validator: Optional[callable] = None) -> 'MultiTargetMatcher':
        """添加自定义匹配目标
        
        Args:
            name: 目标名称
            patterns: 模式列表
            matcher_type: 匹配器类型
            fuzzy_threshold: 模糊匹配阈值
            case_sensitive: 是否区分大小写
            required: 是否必需
            weight: 权重
            regex_pattern: 正则表达式模式
            validator: 验证函数
        """
        config = TargetConfig(
            target_type=TargetType.CUSTOM,
            patterns=patterns,
            matcher_type=matcher_type,
            fuzzy_threshold=fuzzy_threshold,
            case_sensitive=case_sensitive,
            required=required,
            weight=weight,
            regex_pattern=regex_pattern,
            validator=validator
        )
        return self.add_target(name, config)
    
    def match_string(self, text: str) -> MultiMatchResult:
        """匹配单个字符串
        
        Args:
            text: 要匹配的文本
            
        Returns:
            MultiMatchResult: 匹配结果
        """
        result = MultiMatchResult(source_string=text)
        
        self._log_debug(f"开始匹配文本: '{text}'")
        
        # 对每个目标进行匹配
        for target_name, target_config in self.targets.items():
            match_result = self._match_single_target(text, target_name, target_config)
            result.matches[target_name] = match_result
            
            self._log_debug(f"目标 '{target_name}' 匹配结果: {match_result.matched_string} (分数: {match_result.similarity_score:.3f})")
        
        # 计算整体分数和完整性
        result.overall_score = self._calculate_overall_score(result)
        result.is_complete, result.missing_targets = self._check_completeness(result)
        
        return result
    
    def match_multiple(self, texts: List[str]) -> List[MultiMatchResult]:
        """批量匹配多个字符串
        
        Args:
            texts: 要匹配的文本列表
            
        Returns:
            List[MultiMatchResult]: 匹配结果列表
        """
        results = []
        for text in texts:
            result = self.match_string(text)
            results.append(result)
        return results
    
    def find_best_matches(self, texts: List[str], 
                         min_overall_score: float = 0.5) -> List[MultiMatchResult]:
        """查找最佳匹配
        
        Args:
            texts: 要匹配的文本列表
            min_overall_score: 最小整体分数阈值
            
        Returns:
            List[MultiMatchResult]: 按分数排序的匹配结果列表
        """
        results = self.match_multiple(texts)
        
        # 过滤并排序
        filtered_results = [r for r in results if r.overall_score >= min_overall_score]
        filtered_results.sort(key=lambda x: x.overall_score, reverse=True)
        
        return filtered_results
    
    def _match_single_target(self, text: str, target_name: str, 
                           config: TargetConfig) -> MatchResult:
        """匹配单个目标
        
        Args:
            text: 要匹配的文本
            target_name: 目标名称
            config: 目标配置
            
        Returns:
            MatchResult: 匹配结果
        """
        # 预处理
        processed_text = text
        if config.preprocessor:
            processed_text = config.preprocessor(text)
        
        # 正则表达式匹配
        if config.regex_pattern:
            regex_match = self._regex_match(processed_text, config.regex_pattern)
            if regex_match:
                # 验证匹配结果
                if config.validator and not config.validator(regex_match):
                    return MatchResult(match_type="none")
                
                return MatchResult(
                    matched_string=regex_match,
                    similarity_score=1.0,
                    match_type="exact",
                    confidence=0.9
                )
        
        # 使用字符串匹配器
        matcher = self.matchers[target_name]
        matched_string, score = matcher.match_string_with_score(processed_text, config.patterns)
        
        # 检查最小分数要求
        if score < config.min_score:
            matched_string = None
            score = 0.0
        
        # 验证匹配结果
        if matched_string and config.validator and not config.validator(matched_string):
            matched_string = None
            score = 0.0
        
        match_type = "none"
        if matched_string:
            match_type = "exact" if score >= 0.95 else "fuzzy"
        
        return MatchResult(
            matched_string=matched_string,
            similarity_score=score,
            match_type=match_type,
            confidence=score * 0.8 + 0.2 if matched_string else 0.0
        )
    
    def _regex_match(self, text: str, pattern: str) -> Optional[str]:
        """正则表达式匹配
        
        Args:
            text: 要匹配的文本
            pattern: 正则表达式模式
            
        Returns:
            Optional[str]: 匹配到的字符串
        """
        match = re.search(pattern, text)
        if match:
            return match.group(1) if match.groups() else match.group(0)
        return None
    
    def _validate_date(self, date_str: str) -> bool:
        """验证日期字符串
        
        Args:
            date_str: 日期字符串
            
        Returns:
            bool: 是否有效
        """
        # 常见日期格式
        date_formats = [
            "%Y%m%d", "%Y-%m-%d", "%Y/%m/%d",
            "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y",
            "%d.%m.%Y", "%Y.%m.%d"
        ]
        
        for fmt in date_formats:
            try:
                datetime.strptime(date_str, fmt)
                return True
            except ValueError:
                continue
        return False
    
    def _validate_number(self, number_str: str) -> bool:
        """验证数字字符串
        
        Args:
            number_str: 数字字符串
            
        Returns:
            bool: 是否有效
        """
        try:
            # 移除逗号并尝试转换为数字
            cleaned = number_str.replace(',', '')
            float(cleaned)
            return True
        except ValueError:
            return False
    
    def _calculate_overall_score(self, result: MultiMatchResult) -> float:
        """计算整体匹配分数
        
        Args:
            result: 匹配结果
            
        Returns:
            float: 整体分数
        """
        total_weight = 0.0
        weighted_score = 0.0
        
        for target_name, match_result in result.matches.items():
            config = self.targets[target_name]
            weight = config.weight
            score = match_result.similarity_score if match_result.is_matched else 0.0
            
            total_weight += weight
            weighted_score += score * weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _check_completeness(self, result: MultiMatchResult) -> Tuple[bool, List[str]]:
        """检查匹配完整性
        
        Args:
            result: 匹配结果
            
        Returns:
            Tuple[bool, List[str]]: (是否完整, 缺失的目标列表)
        """
        missing_targets = []
        
        for target_name, config in self.targets.items():
            if config.required:
                match_result = result.matches.get(target_name)
                if not match_result or not match_result.is_matched:
                    missing_targets.append(target_name)
        
        is_complete = len(missing_targets) == 0
        return is_complete, missing_targets
    
    def _log_debug(self, message: str):
        """输出调试信息
        
        Args:
            message: 调试信息
        """
        if self.debug:
            print(f"[MultiTargetMatcher] {message}")
    
    def get_target_names(self) -> List[str]:
        """获取所有目标名称"""
        return list(self.targets.keys())
    
    def remove_target(self, name: str) -> bool:
        """移除目标
        
        Args:
            name: 目标名称
            
        Returns:
            bool: 是否成功移除
        """
        if name in self.targets:
            del self.targets[name]
            del self.matchers[name]
            self._log_debug(f"移除目标: {name}")
            return True
        return False
    
    def clear_targets(self):
        """清空所有目标"""
        self.targets.clear()
        self.matchers.clear()
        self._log_debug("清空所有目标")
