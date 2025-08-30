# -*- coding: utf-8 -*-
"""
重构后的多目标匹配器核心模块 - 简化的主要匹配逻辑
"""

from typing import Dict, List, Optional, Tuple
import re

try:
    from .base_matcher import StringMatcher
    from .string_types.results import MatchResult
    from .factory import create_string_matcher
    from .targets.config import TargetConfig
    from .targets.builder import TargetBuilder
    from .results.multi_result import MultiMatchResult, ResultAnalyzer
except ImportError:
    # 处理独立运行的情况
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    from base_matcher import StringMatcher
    from string_types.results import MatchResult
    from factory import create_string_matcher
    from targets.config import TargetConfig
    from targets.builder import TargetBuilder
    from results.multi_result import MultiMatchResult, ResultAnalyzer


class MultiTargetMatcher:
    """多目标字符串匹配器 (重构版)
    
    重构后的版本专注于核心匹配逻辑，
    具体的目标构建和结果分析委托给专门的模块
    """
    
    def __init__(self, targets: Optional[List[TargetConfig]] = None, debug: bool = False):
        """初始化多目标匹配器
        
        Args:
            targets: 可选的目标配置列表
            debug: 是否启用调试模式
        """
        self.debug = debug
        self.targets: Dict[str, TargetConfig] = {}
        self.matchers: Dict[str, StringMatcher] = {}
        self._target_builder = TargetBuilder()
        
        # 如果提供了目标列表，则添加它们
        if targets:
            for i, target in enumerate(targets):
                target_name = f"{target.target_type.value}_{i}"
                self.add_target(target_name, target)
        
    def add_target(self, name: str, config: TargetConfig) -> 'MultiTargetMatcher':
        """添加目标配置
        
        Args:
            name: 目标名称
            config: 目标配置
            
        Returns:
            MultiTargetMatcher: 返回自身以支持链式调用
        """
        # 暂时注释掉验证，因为方法还未实现
        # if not config.is_valid_for_type():
        #     raise ValueError(f"Invalid configuration for target '{name}' of type {config.target_type}")
        
        self.targets[name] = config
        
        # 创建对应的匹配器
        self.matchers[name] = create_string_matcher(
            matcher_type=config.matcher_strategy.value,
            fuzzy_threshold=config.fuzzy_threshold,
            case_sensitive=config.case_sensitive,
            debug=self.debug
        )
        
        self._log_debug(f"添加目标: {name}, 类型: {config.target_type.value}")
        return self
    
    def add_targets(self, targets: Dict[str, TargetConfig]) -> 'MultiTargetMatcher':
        """批量添加目标配置
        
        Args:
            targets: 目标配置字典
            
        Returns:
            MultiTargetMatcher: 返回自身以支持链式调用
        """
        for name, config in targets.items():
            self.add_target(name, config)
        return self
    
    # 便捷方法 - 委托给TargetBuilder
    def add_name_target(self, name: str, names: List[str], **kwargs) -> 'MultiTargetMatcher':
        """添加名称匹配目标"""
        targets = self._target_builder.create_name_target(name, names, **kwargs)
        return self.add_targets(targets)
    
    def add_date_target(self, name: str, **kwargs) -> 'MultiTargetMatcher':
        """添加日期匹配目标"""
        targets = self._target_builder.create_date_target(name, **kwargs)
        return self.add_targets(targets)
    
    def add_extension_target(self, name: str, extensions: List[str], **kwargs) -> 'MultiTargetMatcher':
        """添加文件扩展名匹配目标"""
        targets = self._target_builder.create_extension_target(name, extensions, **kwargs)
        return self.add_targets(targets)
    
    def add_number_target(self, name: str, **kwargs) -> 'MultiTargetMatcher':
        """添加数字匹配目标"""
        targets = self._target_builder.create_number_target(name, **kwargs)
        return self.add_targets(targets)
    
    def add_email_target(self, name: str, **kwargs) -> 'MultiTargetMatcher':
        """添加邮箱匹配目标"""
        targets = self._target_builder.create_email_target(name, **kwargs)
        return self.add_targets(targets)
    
    def add_phone_target(self, name: str, **kwargs) -> 'MultiTargetMatcher':
        """添加电话号码匹配目标"""
        targets = self._target_builder.create_phone_target(name, **kwargs)
        return self.add_targets(targets)
    
    def add_url_target(self, name: str, **kwargs) -> 'MultiTargetMatcher':
        """添加URL匹配目标"""
        targets = self._target_builder.create_url_target(name, **kwargs)
        return self.add_targets(targets)
    
    def add_custom_target(self, name: str, patterns: List[str], **kwargs) -> 'MultiTargetMatcher':
        """添加自定义匹配目标"""
        targets = self._target_builder.create_custom_target(name, patterns, **kwargs)
        return self.add_targets(targets)
    
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
            
            self._log_debug(f"目标 '{target_name}' 匹配结果: {match_result.matched_string} "
                           f"(分数: {match_result.similarity_score:.3f})")
        
        # 计算整体分数和完整性
        result.overall_score = self._calculate_overall_score(result)
        _, result.missing_targets = self._check_completeness(result)
        
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
                         min_overall_score: float = 0.5,
                         max_results: Optional[int] = None) -> List[MultiMatchResult]:
        """查找最佳匹配
        
        Args:
            texts: 要匹配的文本列表
            min_overall_score: 最小整体分数阈值
            max_results: 最大结果数量
            
        Returns:
            List[MultiMatchResult]: 按分数排序的匹配结果列表
        """
        results = self.match_multiple(texts)
        
        # 过滤并排序
        filtered_results = [r for r in results if r.overall_score >= min_overall_score]
        filtered_results.sort(key=lambda x: x.overall_score, reverse=True)
        
        if max_results is not None:
            filtered_results = filtered_results[:max_results]
        
        return filtered_results
    
    def analyze_results(self, results: List[MultiMatchResult]) -> str:
        """分析匹配结果
        
        Args:
            results: 匹配结果列表
            
        Returns:
            str: 分析报告
        """
        return ResultAnalyzer.generate_report(results)
    
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
        
        # 长度检查
        if config.max_length and len(processed_text) > config.max_length:
            return MatchResult(match_type="none")
        
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
        if not config.patterns:
            return MatchResult(match_type="none")
        
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
        try:
            match = re.search(pattern, text)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        except re.error as e:
            self._log_debug(f"正则表达式错误: {e}")
        return None
    
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
    
    # 目标管理方法
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
            if name in self.matchers:
                del self.matchers[name]
            self._log_debug(f"移除目标: {name}")
            return True
        return False
    
    def clear_targets(self):
        """清空所有目标"""
        self.targets.clear()
        self.matchers.clear()
        self._log_debug("清空所有目标")
    
    def get_target_config(self, name: str) -> Optional[TargetConfig]:
        """获取目标配置
        
        Args:
            name: 目标名称
            
        Returns:
            Optional[TargetConfig]: 目标配置
        """
        return self.targets.get(name)
    
    def update_target_config(self, name: str, **changes) -> bool:
        """更新目标配置
        
        Args:
            name: 目标名称
            **changes: 要修改的配置项
            
        Returns:
            bool: 是否成功更新
        """
        if name not in self.targets:
            return False
        
        # 创建新配置
        old_config = self.targets[name]
        try:
            new_config = old_config.copy(**changes)
            
            # 更新配置
            self.targets[name] = new_config
            
            # 重新创建匹配器
            self.matchers[name] = create_string_matcher(
                matcher_type=new_config.matcher_type,
                fuzzy_threshold=new_config.fuzzy_threshold,
                case_sensitive=new_config.case_sensitive,
                debug=self.debug
            )
            
            self._log_debug(f"更新目标配置: {name}")
            return True
            
        except Exception as e:
            self._log_debug(f"更新目标配置失败: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, int]:
        """获取匹配器统计信息"""
        return {
            'total_targets': len(self.targets),
            'required_targets': sum(1 for config in self.targets.values() if config.required),
            'optional_targets': sum(1 for config in self.targets.values() if not config.required),
            'exact_matchers': sum(1 for config in self.targets.values() if config.matcher_type == 'exact'),
            'fuzzy_matchers': sum(1 for config in self.targets.values() if config.matcher_type == 'fuzzy'),
            'hybrid_matchers': sum(1 for config in self.targets.values() if config.matcher_type == 'hybrid'),
        }
