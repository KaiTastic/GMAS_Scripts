# -*- coding: utf-8 -*-
"""
混合字符串匹配器 - 结合精确匹配和模糊匹配
"""

from typing import List, Optional, Tuple

try:
    from .base_matcher import StringMatcher
    from .string_types.results import MatchResult
    from .exact_matcher import ExactStringMatcher
    from .fuzzy_matcher import FuzzyStringMatcher
except ImportError:
    # 处理独立运行的情况
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    from base_matcher import StringMatcher
    from string_types.results import MatchResult
    from exact_matcher import ExactStringMatcher
    from fuzzy_matcher import FuzzyStringMatcher


class HybridStringMatcher(StringMatcher):
    """混合字符串匹配器
    
    先尝试精确匹配，失败后尝试模糊匹配
    """
    
    def __init__(self, fuzzy_threshold: float = 0.65, case_sensitive: bool = False, debug: bool = False):
        """初始化混合匹配器
        
        Args:
            fuzzy_threshold: 模糊匹配阈值
            case_sensitive: 精确匹配是否区分大小写
            debug: 是否启用调试模式
        """
        super().__init__(debug)
        self.exact_matcher = ExactStringMatcher(case_sensitive, debug)
        self.fuzzy_matcher = FuzzyStringMatcher(fuzzy_threshold, debug)
        self.fuzzy_threshold = fuzzy_threshold
    
    def match_string(self, target: str, candidates: List[str]) -> Optional[str]:
        """混合匹配字符串
        
        Args:
            target: 目标字符串
            candidates: 候选字符串列表
            
        Returns:
            Optional[str]: 匹配到的字符串，未匹配到返回None
        """
        # 先尝试精确匹配
        exact_result = self.exact_matcher.match_string(target, candidates)
        if exact_result:
            self._log_debug(f"混合匹配(精确): '{target}' -> '{exact_result}'")
            return exact_result
        
        # 精确匹配失败，尝试模糊匹配
        fuzzy_result = self.fuzzy_matcher.match_string(target, candidates)
        if fuzzy_result:
            self._log_debug(f"混合匹配(模糊): '{target}' -> '{fuzzy_result}'")
            return fuzzy_result
        
        self._log_debug(f"混合匹配失败: '{target}'")
        return None
    
    def match_string_with_score(self, target: str, candidates: List[str]) -> Tuple[Optional[str], float]:
        """混合匹配字符串并返回分数
        
        Args:
            target: 目标字符串
            candidates: 候选字符串列表
            
        Returns:
            Tuple[Optional[str], float]: (匹配到的字符串, 分数)
        """
        # 先尝试精确匹配
        exact_result, exact_score = self.exact_matcher.match_string_with_score(target, candidates)
        if exact_result:
            return exact_result, exact_score
        
        # 精确匹配失败，尝试模糊匹配
        fuzzy_result, fuzzy_score = self.fuzzy_matcher.match_string_with_score(target, candidates)
        return fuzzy_result, fuzzy_score
    
    def match_with_result(self, target: str, candidates: List[str]) -> MatchResult:
        """混合匹配字符串并返回详细结果
        
        Args:
            target: 目标字符串
            candidates: 候选字符串列表
            
        Returns:
            MatchResult: 匹配结果对象
        """
        # 先尝试精确匹配
        exact_result = self.exact_matcher.match_with_result(target, candidates)
        if exact_result.is_matched:
            return exact_result
        
        # 精确匹配失败，尝试模糊匹配
        fuzzy_result = self.fuzzy_matcher.match_with_result(target, candidates)
        return fuzzy_result
    
    def match_with_strategy_info(self, target: str, candidates: List[str]) -> Tuple[Optional[str], float, str]:
        """混合匹配并返回使用的策略信息
        
        Args:
            target: 目标字符串
            candidates: 候选字符串列表
            
        Returns:
            Tuple[Optional[str], float, str]: (匹配结果, 分数, 策略类型)
        """
        # 先尝试精确匹配
        exact_result, exact_score = self.exact_matcher.match_string_with_score(target, candidates)
        if exact_result:
            return exact_result, exact_score, "exact"
        
        # 精确匹配失败，尝试模糊匹配
        fuzzy_result, fuzzy_score = self.fuzzy_matcher.match_string_with_score(target, candidates)
        if fuzzy_result:
            return fuzzy_result, fuzzy_score, "fuzzy"
        else:
            return None, fuzzy_score, "none"
    
    def match_with_fallback_threshold(self, target: str, candidates: List[str], 
                                    fallback_threshold: float = 0.4) -> Tuple[Optional[str], float]:
        """使用降级阈值的混合匹配
        
        如果正常模糊匹配失败，使用更低的阈值再次尝试
        
        Args:
            target: 目标字符串
            candidates: 候选字符串列表
            fallback_threshold: 降级阈值
            
        Returns:
            Tuple[Optional[str], float]: (匹配结果, 分数)
        """
        # 先进行正常的混合匹配
        result, score = self.match_string_with_score(target, candidates)
        if result:
            return result, score
        
        # 如果失败且分数在降级阈值以上，返回最佳匹配
        if score >= fallback_threshold:
            best_match = None
            best_score = 0.0
            
            for candidate in candidates:
                candidate_score = self.fuzzy_matcher.similarity_calculator.calculate_similarity(
                    target.lower(), candidate.lower()
                )
                if candidate_score > best_score:
                    best_score = candidate_score
                    best_match = candidate
            
            if best_score >= fallback_threshold:
                self._log_debug(f"降级阈值匹配: '{target}' -> '{best_match}' (分数: {best_score:.3f})")
                return best_match, best_score
        
        return None, score
    
    def get_fuzzy_threshold(self) -> float:
        """获取当前模糊匹配阈值
        
        Returns:
            float: 当前阈值
        """
        return self.fuzzy_threshold
    
    def set_fuzzy_threshold(self, threshold: float):
        """设置模糊匹配阈值
        
        Args:
            threshold: 新的阈值 (0.0-1.0)
        """
        self.fuzzy_threshold = threshold
        self.fuzzy_matcher.set_threshold(threshold)
        self._log_debug(f"混合匹配器阈值更新为: {threshold}")
    
    def get_exact_matcher(self) -> ExactStringMatcher:
        """获取精确匹配器实例
        
        Returns:
            ExactStringMatcher: 精确匹配器
        """
        return self.exact_matcher
    
    def get_fuzzy_matcher(self) -> FuzzyStringMatcher:
        """获取模糊匹配器实例
        
        Returns:
            FuzzyStringMatcher: 模糊匹配器
        """
        return self.fuzzy_matcher
