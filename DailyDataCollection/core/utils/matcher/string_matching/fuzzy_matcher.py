# -*- coding: utf-8 -*-
"""
模糊字符串匹配器 - 支持相似度匹配
"""

from typing import List, Optional, Tuple

try:
    from .base_matcher import StringMatcher
    from .string_types.results import MatchResult
    from .similarity_calculator import SimilarityCalculator
except ImportError:
    # 处理独立运行的情况
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    from base_matcher import StringMatcher
    from string_types.results import MatchResult
    from similarity_calculator import SimilarityCalculator


class FuzzyStringMatcher(StringMatcher):
    """模糊字符串匹配器
    
    支持基于相似度的模糊匹配
    """
    
    def __init__(self, threshold: float = 0.65, debug: bool = False):
        """初始化模糊匹配器
        
        Args:
            threshold: 相似度阈值 (0.0-1.0)
            debug: 是否启用调试模式
        """
        super().__init__(debug)
        self.threshold = threshold
        self.similarity_calculator = SimilarityCalculator()
    
    def match_string(self, target: str, candidates: List[str]) -> Optional[str]:
        """模糊匹配字符串
        
        Args:
            target: 目标字符串
            candidates: 候选字符串列表
            
        Returns:
            Optional[str]: 匹配到的字符串，未匹配到返回None
        """
        matched, _ = self.match_string_with_score(target, candidates)
        return matched
    
    def match_string_with_score(self, target: str, candidates: List[str]) -> Tuple[Optional[str], float]:
        """模糊匹配字符串并返回相似度分数
        
        Args:
            target: 目标字符串
            candidates: 候选字符串列表
            
        Returns:
            Tuple[Optional[str], float]: (匹配到的字符串, 相似度分数)
        """
        if not target or not candidates:
            return None, 0.0
        
        best_match = None
        best_similarity = 0.0
        
        target_lower = target.lower()
        
        for candidate in candidates:
            similarity = self.similarity_calculator.calculate_similarity(
                target_lower, candidate.lower()
            )
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = candidate
        
        if best_similarity >= self.threshold:
            self._log_debug(f"模糊匹配成功: '{target}' -> '{best_match}' (相似度: {best_similarity:.3f})")
            return best_match, best_similarity
        else:
            self._log_debug(f"模糊匹配失败: '{target}' (最高相似度: {best_similarity:.3f} < {self.threshold})")
            return None, best_similarity
    
    def match_with_result(self, target: str, candidates: List[str]) -> MatchResult:
        """模糊匹配字符串并返回详细结果
        
        Args:
            target: 目标字符串
            candidates: 候选字符串列表
            
        Returns:
            MatchResult: 匹配结果对象
        """
        matched, score = self.match_string_with_score(target, candidates)
        
        if matched:
            return MatchResult(
                matched_string=matched,
                similarity_score=score,
                match_type="fuzzy",
                confidence=score
            )
        else:
            return MatchResult(
                matched_string=None,
                similarity_score=score,
                match_type="none",
                confidence=0.0
            )
    
    def match_with_prefix_bias(self, target: str, candidates: List[str], 
                              prefix_weight: float = 0.7) -> Tuple[Optional[str], float]:
        """带前缀偏向的模糊匹配
        
        对前缀匹配给予更高权重，适用于文件名等场景
        
        Args:
            target: 目标字符串
            candidates: 候选字符串列表
            prefix_weight: 前缀权重 (0.0-1.0)
            
        Returns:
            Tuple[Optional[str], float]: (匹配到的字符串, 相似度分数)
        """
        if not target or not candidates:
            return None, 0.0
        
        best_match = None
        best_similarity = 0.0
        
        target_lower = target.lower()
        
        for candidate in candidates:
            candidate_lower = candidate.lower()
            
            # 计算前缀相似度和整体相似度
            prefix_sim, overall_sim = self.similarity_calculator.calculate_prefix_similarity(
                target_lower, candidate_lower
            )
            
            # 加权组合
            combined_similarity = (prefix_sim * prefix_weight) + (overall_sim * (1 - prefix_weight))
            
            if combined_similarity > best_similarity:
                best_similarity = combined_similarity
                best_match = candidate
        
        if best_similarity >= self.threshold:
            self._log_debug(f"前缀偏向模糊匹配成功: '{target}' -> '{best_match}' (相似度: {best_similarity:.3f})")
            return best_match, best_similarity
        else:
            self._log_debug(f"前缀偏向模糊匹配失败: '{target}' (最高相似度: {best_similarity:.3f} < {self.threshold})")
            return None, best_similarity
    
    def get_all_matches_above_threshold(self, target: str, candidates: List[str]) -> List[Tuple[str, float]]:
        """获取所有超过阈值的匹配结果
        
        Args:
            target: 目标字符串
            candidates: 候选字符串列表
            
        Returns:
            List[Tuple[str, float]]: 匹配结果列表 [(候选字符串, 相似度)]
        """
        if not target or not candidates:
            return []
        
        matches = []
        target_lower = target.lower()
        
        for candidate in candidates:
            similarity = self.similarity_calculator.calculate_similarity(
                target_lower, candidate.lower()
            )
            
            if similarity >= self.threshold:
                matches.append((candidate, similarity))
        
        # 按相似度降序排列
        matches.sort(key=lambda x: x[1], reverse=True)
        
        self._log_debug(f"找到 {len(matches)} 个超过阈值的匹配: '{target}'")
        return matches
    
    def set_threshold(self, threshold: float):
        """设置相似度阈值
        
        Args:
            threshold: 新的相似度阈值 (0.0-1.0)
        """
        if 0.0 <= threshold <= 1.0:
            self.threshold = threshold
            self._log_debug(f"相似度阈值更新为: {threshold}")
        else:
            raise ValueError(f"阈值必须在0.0-1.0之间，得到: {threshold}")
