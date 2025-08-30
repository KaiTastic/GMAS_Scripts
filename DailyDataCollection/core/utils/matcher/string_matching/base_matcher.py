# -*- coding: utf-8 -*-
"""
基础字符串匹配器 - 定义字符串匹配的接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple


class StringMatcher(ABC):
    """字符串匹配器抽象基类
    
    定义了字符串匹配的通用接口
    """
    
    def __init__(self, debug: bool = False):
        """初始化匹配器
        
        Args:
            debug: 是否启用调试模式
        """
        self.debug = debug
    
    @abstractmethod
    def match_string(self, target: str, candidates: List[str]) -> Optional[str]:
        """匹配字符串
        
        Args:
            target: 目标字符串
            candidates: 候选字符串列表
            
        Returns:
            Optional[str]: 匹配到的字符串，未匹配到返回None
        """
        pass
    
    @abstractmethod
    def match_string_with_score(self, target: str, candidates: List[str]) -> Tuple[Optional[str], float]:
        """匹配字符串并返回相似度分数
        
        Args:
            target: 目标字符串
            candidates: 候选字符串列表
            
        Returns:
            Tuple[Optional[str], float]: (匹配到的字符串, 相似度分数)
        """
        pass
    
    def match_multiple(self, targets: List[str], candidates: List[str]) -> List[Optional[str]]:
        """批量匹配多个字符串
        
        Args:
            targets: 目标字符串列表
            candidates: 候选字符串列表
            
        Returns:
            List[Optional[str]]: 匹配结果列表
        """
        results = []
        for target in targets:
            result = self.match_string(target, candidates)
            results.append(result)
        return results
    
    def _log_debug(self, message: str):
        """输出调试信息
        
        Args:
            message: 调试信息
        """
        if self.debug:
            print(f"[{self.__class__.__name__}] {message}")


class MatchResult:
    """匹配结果类
    
    封装匹配结果的详细信息
    """
    
    def __init__(self, matched_string: Optional[str] = None, 
                 similarity_score: float = 0.0,
                 match_type: str = "none",
                 confidence: float = 0.0):
        """初始化匹配结果
        
        Args:
            matched_string: 匹配到的字符串
            similarity_score: 相似度分数
            match_type: 匹配类型 (exact, fuzzy, none)
            confidence: 置信度
        """
        self.matched_string = matched_string
        self.similarity_score = similarity_score
        self.match_type = match_type
        self.confidence = confidence
        self.is_matched = matched_string is not None
    
    def __str__(self) -> str:
        """字符串表示"""
        if self.is_matched:
            return f"MatchResult(match='{self.matched_string}', score={self.similarity_score:.3f}, type={self.match_type})"
        else:
            return f"MatchResult(no_match, best_score={self.similarity_score:.3f})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return self.__str__()
