# -*- coding: utf-8 -*-
"""
精确字符串匹配器 - 只进行精确匹配
"""

from typing import List, Optional, Tuple
from .base_matcher import StringMatcher, MatchResult


class ExactStringMatcher(StringMatcher):
    """精确字符串匹配器
    
    只进行精确的字符串匹配，不进行模糊匹配
    """
    
    def __init__(self, case_sensitive: bool = False, debug: bool = False):
        """初始化精确匹配器
        
        Args:
            case_sensitive: 是否区分大小写
            debug: 是否启用调试模式
        """
        super().__init__(debug)
        self.case_sensitive = case_sensitive
    
    def match_string(self, target: str, candidates: List[str]) -> Optional[str]:
        """精确匹配字符串
        
        Args:
            target: 目标字符串
            candidates: 候选字符串列表
            
        Returns:
            Optional[str]: 匹配到的字符串，未匹配到返回None
        """
        target_processed = target if self.case_sensitive else target.lower()
        
        for candidate in candidates:
            candidate_processed = candidate if self.case_sensitive else candidate.lower()
            
            # 检查目标字符串是否包含在候选字符串中
            if target_processed in candidate_processed or candidate_processed in target_processed:
                self._log_debug(f"精确匹配成功: '{target}' -> '{candidate}'")
                return candidate
        
        self._log_debug(f"精确匹配失败: '{target}'")
        return None
    
    def match_string_with_score(self, target: str, candidates: List[str]) -> Tuple[Optional[str], float]:
        """精确匹配字符串并返回分数
        
        Args:
            target: 目标字符串
            candidates: 候选字符串列表
            
        Returns:
            Tuple[Optional[str], float]: (匹配到的字符串, 分数)
        """
        matched = self.match_string(target, candidates)
        score = 1.0 if matched else 0.0
        return matched, score
    
    def match_with_result(self, target: str, candidates: List[str]) -> MatchResult:
        """匹配字符串并返回详细结果
        
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
                match_type="exact",
                confidence=1.0
            )
        else:
            return MatchResult(
                matched_string=None,
                similarity_score=0.0,
                match_type="none",
                confidence=0.0
            )
    
    def match_substring(self, target: str, candidates: List[str]) -> Optional[str]:
        """子字符串匹配
        
        检查目标字符串是否是任何候选字符串的子字符串
        
        Args:
            target: 目标字符串
            candidates: 候选字符串列表
            
        Returns:
            Optional[str]: 匹配到的字符串，未匹配到返回None
        """
        target_processed = target if self.case_sensitive else target.lower()
        
        for candidate in candidates:
            candidate_processed = candidate if self.case_sensitive else candidate.lower()
            
            if target_processed in candidate_processed:
                self._log_debug(f"子字符串匹配成功: '{target}' 在 '{candidate}' 中")
                return candidate
        
        self._log_debug(f"子字符串匹配失败: '{target}'")
        return None
    
    def match_exact_equals(self, target: str, candidates: List[str]) -> Optional[str]:
        """完全相等匹配
        
        只有完全相等的字符串才匹配
        
        Args:
            target: 目标字符串
            candidates: 候选字符串列表
            
        Returns:
            Optional[str]: 匹配到的字符串，未匹配到返回None
        """
        target_processed = target if self.case_sensitive else target.lower()
        
        for candidate in candidates:
            candidate_processed = candidate if self.case_sensitive else candidate.lower()
            
            if target_processed == candidate_processed:
                self._log_debug(f"完全匹配成功: '{target}' == '{candidate}'")
                return candidate
        
        self._log_debug(f"完全匹配失败: '{target}'")
        return None
