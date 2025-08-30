# -*- coding: utf-8 -*-
"""
名称匹配器 - 专门用于文件名和图幅名称匹配的高级接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from .hybrid_matcher import HybridStringMatcher
from .exact_matcher import ExactStringMatcher
from .fuzzy_matcher import FuzzyStringMatcher


class NameMatcher(ABC):
    """名称匹配器抽象基类"""
    
    @abstractmethod
    def match_mapsheet_name(self, filename: str, valid_names: List[str]) -> Optional[str]:
        """匹配图幅名称
        
        Args:
            filename: 文件名
            valid_names: 有效的图幅名称列表
            
        Returns:
            Optional[str]: 匹配到的图幅名称，未匹配到返回None
        """
        pass
    
    @abstractmethod
    def match_file_pattern(self, filename: str, patterns: List[str]) -> Optional[str]:
        """匹配文件模式
        
        Args:
            filename: 文件名
            patterns: 文件模式列表
            
        Returns:
            Optional[str]: 匹配到的模式，未匹配到返回None
        """
        pass


class ExactNameMatcher(NameMatcher):
    """精确名称匹配器 - 只进行精确匹配"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.string_matcher = ExactStringMatcher(case_sensitive=False, debug=debug)
    
    def match_mapsheet_name(self, filename: str, valid_names: List[str]) -> Optional[str]:
        """精确匹配图幅名称"""
        filename_lower = filename.lower()
        
        for mapsheet_name in valid_names:
            if mapsheet_name.lower() in filename_lower:
                if self.debug:
                    print(f"精确匹配图幅名称: {filename} -> {mapsheet_name}")
                return mapsheet_name
        
        return None
    
    def match_file_pattern(self, filename: str, patterns: List[str]) -> Optional[str]:
        """精确匹配文件模式"""
        filename_lower = filename.lower()
        
        for pattern in patterns:
            pattern_clean = pattern.replace('_', ' ').strip().lower()
            if pattern_clean in filename_lower:
                if self.debug:
                    print(f"精确匹配文件模式: {filename} -> {pattern}")
                return pattern
        
        return None


class FuzzyNameMatcher(NameMatcher):
    """模糊名称匹配器 - 支持相似度匹配"""
    
    def __init__(self, fuzzy_threshold: float = 0.65, debug: bool = False):
        self.fuzzy_threshold = fuzzy_threshold
        self.debug = debug
        self.string_matcher = FuzzyStringMatcher(fuzzy_threshold, debug)
    
    def match_mapsheet_name(self, filename: str, valid_names: List[str]) -> Optional[str]:
        """模糊匹配图幅名称"""
        # 使用前缀偏向的模糊匹配，适合文件名场景
        best_match, best_similarity = self.string_matcher.match_with_prefix_bias(
            filename.lower(), [name.lower() for name in valid_names]
        )
        
        if best_match:
            # 找到原始大小写的名称
            for original_name in valid_names:
                if original_name.lower() == best_match:
                    if self.debug:
                        print(f"模糊匹配图幅名称: {filename} -> {original_name} (相似度: {best_similarity:.3f})")
                    return original_name
        
        if self.debug:
            print(f"图幅名称匹配失败: {filename} (最高相似度: {best_similarity:.3f} < {self.fuzzy_threshold})")
        
        return None
    
    def match_file_pattern(self, filename: str, patterns: List[str]) -> Optional[str]:
        """模糊匹配文件模式"""
        best_match = None
        best_similarity = 0.0
        
        for pattern in patterns:
            # 移除模式中的下划线进行更宽松的匹配
            pattern_clean = pattern.replace('_', ' ').strip()
            filename_clean = filename.replace('_', ' ')
            
            similarity = self.string_matcher.similarity_calculator.calculate_similarity(
                filename_clean.lower(), pattern_clean.lower()
            )
            
            # 检查是否包含模式的关键词
            pattern_words = pattern_clean.lower().split()
            filename_words = filename_clean.lower().split()
            
            word_matches = sum(1 for word in pattern_words 
                             if any(self.string_matcher.similarity_calculator.calculate_similarity(word, fw) > 0.7 
                                   for fw in filename_words))
            word_ratio = word_matches / len(pattern_words) if pattern_words else 0.0
            
            # 组合相似度: 字符串相似度(40%) + 关键词匹配(60%)
            combined_similarity = similarity * 0.4 + word_ratio * 0.6
            
            if combined_similarity > best_similarity:
                best_similarity = combined_similarity
                best_match = pattern
        
        if best_similarity >= self.fuzzy_threshold:
            if self.debug:
                print(f"模糊匹配文件模式: {filename} -> {best_match} (相似度: {best_similarity:.3f})")
            return best_match
        
        if self.debug:
            print(f"文件模式匹配失败: {filename} (最高相似度: {best_similarity:.3f} < {self.fuzzy_threshold})")
        
        return None


class HybridNameMatcher(NameMatcher):
    """混合名称匹配器 - 先尝试精确匹配，再尝试模糊匹配"""
    
    def __init__(self, fuzzy_threshold: float = 0.65, debug: bool = False):
        self.exact_matcher = ExactNameMatcher(debug)
        self.fuzzy_matcher = FuzzyNameMatcher(fuzzy_threshold, debug)
        self.fuzzy_threshold = fuzzy_threshold
        self.debug = debug
    
    def match_mapsheet_name(self, filename: str, valid_names: List[str]) -> Optional[str]:
        """混合匹配图幅名称 - 先精确后模糊"""
        # 先尝试精确匹配
        exact_result = self.exact_matcher.match_mapsheet_name(filename, valid_names)
        if exact_result:
            if self.debug:
                print(f"混合匹配(精确): {filename} -> {exact_result}")
            return exact_result
        
        # 精确匹配失败，尝试模糊匹配
        fuzzy_result = self.fuzzy_matcher.match_mapsheet_name(filename, valid_names)
        if fuzzy_result:
            if self.debug:
                print(f"混合匹配(模糊): {filename} -> {fuzzy_result}")
            return fuzzy_result
        
        if self.debug:
            print(f"混合匹配失败: {filename}")
        return None
    
    def match_file_pattern(self, filename: str, patterns: List[str]) -> Optional[str]:
        """混合匹配文件模式 - 先精确后模糊"""
        # 先尝试精确匹配
        exact_result = self.exact_matcher.match_file_pattern(filename, patterns)
        if exact_result:
            if self.debug:
                print(f"混合匹配(精确): {filename} -> {exact_result}")
            return exact_result
        
        # 精确匹配失败，尝试模糊匹配
        fuzzy_result = self.fuzzy_matcher.match_file_pattern(filename, patterns)
        if fuzzy_result:
            if self.debug:
                print(f"混合匹配(模糊): {filename} -> {fuzzy_result}")
            return fuzzy_result
        
        if self.debug:
            print(f"混合匹配失败: {filename}")
        return None
    
    def get_fuzzy_threshold(self) -> float:
        """获取模糊匹配阈值"""
        return self.fuzzy_threshold
    
    def set_fuzzy_threshold(self, threshold: float):
        """设置模糊匹配阈值"""
        self.fuzzy_threshold = threshold
        self.fuzzy_matcher.string_matcher.set_threshold(threshold)
