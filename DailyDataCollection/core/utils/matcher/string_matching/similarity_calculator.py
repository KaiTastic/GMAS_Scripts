# -*- coding: utf-8 -*-
"""
相似度计算器 - 提供各种字符串相似度计算算法
"""

from difflib import SequenceMatcher
from typing import Tuple


class SimilarityCalculator:
    """字符串相似度计算器
    
    提供多种相似度计算算法的组合，用于字符串匹配
    """
    
    @staticmethod
    def calculate_similarity(str1: str, str2: str) -> float:
        """计算两个字符串的综合相似度
        
        使用多种算法的组合来提高匹配准确性:
        1. SequenceMatcher (编辑距离) - 60%
        2. 字符集重叠度 - 25%
        3. 长度相似度惩罚 - 15%
        
        Args:
            str1: 第一个字符串
            str2: 第二个字符串
            
        Returns:
            float: 相似度分数 (0.0-1.0)
        """
        if not str1 or not str2:
            return 0.0
        
        # 1. 序列匹配器 (基于最长公共子序列)
        sequence_similarity = SequenceMatcher(None, str1, str2).ratio()
        
        # 2. 字符集重叠度
        char_overlap = SimilarityCalculator._calculate_char_overlap(str1, str2)
        
        # 3. 长度相似度 (长度差异的惩罚)
        length_similarity = SimilarityCalculator._calculate_length_similarity(str1, str2)
        
        # 组合权重: 序列匹配(60%) + 字符重叠(25%) + 长度相似(15%)
        combined_similarity = (
            sequence_similarity * 0.6 + 
            char_overlap * 0.25 + 
            length_similarity * 0.15
        )
        
        return combined_similarity
    
    @staticmethod
    def _calculate_char_overlap(str1: str, str2: str) -> float:
        """计算字符集重叠度
        
        Args:
            str1: 第一个字符串
            str2: 第二个字符串
            
        Returns:
            float: 字符重叠度 (0.0-1.0)
        """
        set1, set2 = set(str1), set(str2)
        if not (set1 | set2):
            return 0.0
        return len(set1 & set2) / len(set1 | set2)
    
    @staticmethod
    def _calculate_length_similarity(str1: str, str2: str) -> float:
        """计算长度相似度
        
        Args:
            str1: 第一个字符串
            str2: 第二个字符串
            
        Returns:
            float: 长度相似度 (0.0-1.0)
        """
        if not str1 and not str2:
            return 1.0
        if not str1 or not str2:
            return 0.0
        
        max_length = max(len(str1), len(str2))
        length_diff = abs(len(str1) - len(str2))
        return 1.0 - (length_diff / max_length)
    
    @staticmethod
    def calculate_weighted_similarity(str1: str, str2: str, 
                                    sequence_weight: float = 0.6,
                                    char_weight: float = 0.25,
                                    length_weight: float = 0.15) -> float:
        """计算自定义权重的相似度
        
        Args:
            str1: 第一个字符串
            str2: 第二个字符串
            sequence_weight: 序列匹配权重
            char_weight: 字符重叠权重
            length_weight: 长度相似权重
            
        Returns:
            float: 加权相似度分数 (0.0-1.0)
        """
        if not str1 or not str2:
            return 0.0
        
        # 标准化权重
        total_weight = sequence_weight + char_weight + length_weight
        if total_weight <= 0:
            return 0.0
        
        sequence_weight /= total_weight
        char_weight /= total_weight
        length_weight /= total_weight
        
        # 计算各种相似度
        sequence_similarity = SequenceMatcher(None, str1, str2).ratio()
        char_overlap = SimilarityCalculator._calculate_char_overlap(str1, str2)
        length_similarity = SimilarityCalculator._calculate_length_similarity(str1, str2)
        
        # 加权组合
        weighted_similarity = (
            sequence_similarity * sequence_weight + 
            char_overlap * char_weight + 
            length_similarity * length_weight
        )
        
        return weighted_similarity
    
    @staticmethod
    def calculate_prefix_similarity(str1: str, str2: str, prefix_length: int = None) -> Tuple[float, float]:
        """计算前缀相似度和整体相似度
        
        Args:
            str1: 第一个字符串
            str2: 第二个字符串
            prefix_length: 前缀长度，如果为None则使用较短字符串的长度
            
        Returns:
            Tuple[float, float]: (前缀相似度, 整体相似度)
        """
        if not str1 or not str2:
            return 0.0, 0.0
        
        # 计算整体相似度
        overall_similarity = SimilarityCalculator.calculate_similarity(str1, str2)
        
        # 计算前缀相似度
        if prefix_length is None:
            prefix_length = min(len(str1), len(str2))
        
        prefix1 = str1[:prefix_length]
        prefix2 = str2[:prefix_length]
        prefix_similarity = SimilarityCalculator.calculate_similarity(prefix1, prefix2)
        
        return prefix_similarity, overall_similarity
