#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础匹配器单元测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ...base_matcher import StringMatcher, MatchResult
from ...exact_matcher import ExactStringMatcher
from ...fuzzy_matcher import FuzzyStringMatcher
from ...hybrid_matcher import HybridStringMatcher
from ...similarity_calculator import SimilarityCalculator
from ..base_test import BaseTestCase


class TestBaseMatcher(BaseTestCase):
    """基础匹配器测试类"""
    
    def setUp(self):
        """测试前设置"""
        super().setUp()
        self.test_patterns = ["test", "example", "sample"]
        self.test_text = "This is a test example for matching"
        
    def test_exact_matcher_creation(self):
        """测试精确匹配器创建"""
        def test_func():
            matcher = ExactStringMatcher()
            return isinstance(matcher, ExactStringMatcher)
        
        result = self.run_test_case(
            "exact_matcher_creation",
            test_func,
            expected_result=True
        )
        self.assertEqual(result.result.value, "PASS")
    
    def test_exact_match_success(self):
        """测试精确匹配成功"""
        def test_func():
            matcher = ExactStringMatcher()
            result = matcher.match("test")
            return result.matched_string
        
        self.run_test_case(
            "exact_match_success",
            test_func,
            expected_result="test"
        )
    
    def test_exact_match_case_sensitive(self):
        """测试精确匹配大小写敏感"""
        def test_func():
            matcher = ExactStringMatcher(case_sensitive=True)
            result = matcher.match("test")
            return result.matched_string
        
        self.run_test_case(
            "exact_match_case_sensitive",
            test_func,
            expected_result=None
        )
    
    def test_exact_match_case_insensitive(self):
        """测试精确匹配大小写不敏感"""
        def test_func():
            matcher = ExactStringMatcher(case_sensitive=False)
            result = matcher.match("test")
            return result.matched_string
        
        self.run_test_case(
            "exact_match_case_insensitive",
            test_func,
            expected_result="test"
        )
    
    def test_fuzzy_matcher_creation(self):
        """测试模糊匹配器创建"""
        def test_func():
            matcher = FuzzyStringMatcher(threshold=0.8)
            return isinstance(matcher, FuzzyStringMatcher)
        
        self.run_test_case(
            "fuzzy_matcher_creation",
            test_func,
            expected_result=True
        )
    
    def test_fuzzy_match_similar_strings(self):
        """测试模糊匹配相似字符串"""
        def test_func():
            matcher = FuzzyStringMatcher(threshold=0.6)
            result = matcher.match("helo")  # 缺少一个字母
            return result.similarity_score > 0.6
        
        self.run_test_case(
            "fuzzy_match_similar_strings",
            test_func,
            expected_result=True
        )
    
    def test_fuzzy_match_threshold(self):
        """测试模糊匹配阈值"""
        def test_func():
            matcher = FuzzyStringMatcher(threshold=0.9)
            result = matcher.match("helo")  # 相似度不够高
            return result.matched_string is None
        
        self.run_test_case(
            "fuzzy_match_threshold",
            test_func,
            expected_result=True
        )
    
    def test_hybrid_matcher_creation(self):
        """测试混合匹配器创建"""
        def test_func():
            matcher = HybridStringMatcher(fuzzy_threshold=0.7)
            return isinstance(matcher, HybridStringMatcher)
        
        self.run_test_case(
            "hybrid_matcher_creation",
            test_func,
            expected_result=True
        )
    
    def test_hybrid_match_exact_priority(self):
        """测试混合匹配精确优先"""
        def test_func():
            matcher = HybridStringMatcher(fuzzy_threshold=0.5)
            result = matcher.match("test")
            return result.similarity_score == 1.0
        
        self.run_test_case(
            "hybrid_match_exact_priority",
            test_func,
            expected_result=True
        )
    
    def test_hybrid_match_fuzzy_fallback(self):
        """测试混合匹配模糊回退"""
        def test_func():
            matcher = HybridStringMatcher(fuzzy_threshold=0.6)
            result = matcher.match("tset")  # 字母顺序错误但相似
            return 0.6 <= result.similarity_score < 1.0
        
        self.run_test_case(
            "hybrid_match_fuzzy_fallback",
            test_func,
            expected_result=True
        )
    
    def test_similarity_calculator(self):
        """测试相似度计算器"""
        def test_func():
            calc = SimilarityCalculator()
            similarity = calc.calculate_similarity("hello", "helo")
            return 0.7 <= similarity <= 0.9
        
        self.run_test_case(
            "similarity_calculator",
            test_func,
            expected_result=True
        )
    
    def test_match_result_properties(self):
        """测试匹配结果属性"""
        def test_func():
            result = MatchResult("test", "original text", 0.85, 10, 14)
            return (result.matched_string == "test" and 
                   result.similarity_score == 0.85 and
                   result.start_position == 10 and
                   result.end_position == 14)
        
        self.run_test_case(
            "match_result_properties",
            test_func,
            expected_result=True
        )
    
    def test_empty_patterns(self):
        """测试空模式列表"""
        def test_func():
            matcher = ExactStringMatcher()
            result = matcher.match("any text")
            return result.matched_string is None
        
        self.run_test_case(
            "empty_patterns",
            test_func,
            expected_result=True
        )
    
    def test_empty_text(self):
        """测试空文本"""
        def test_func():
            matcher = ExactStringMatcher()
            result = matcher.match("")
            return result.matched_string is None
        
        self.run_test_case(
            "empty_text",
            test_func,
            expected_result=True
        )
    
    def test_special_characters(self):
        """测试特殊字符"""
        def test_func():
            special_patterns = ["@#$", "123", "test@example.com"]
            matcher = ExactStringMatcher()
            result = matcher.match("Contact test@example.com for info")
            return result.matched_string == "test@example.com"
        
        self.run_test_case(
            "special_characters",
            test_func,
            expected_result=True
        )
    
    def test_unicode_support(self):
        """测试Unicode支持"""
        def test_func():
            unicode_patterns = ["测试", "例子", "中文"]
            matcher = ExactStringMatcher()
            result = matcher.match("这是一个测试例子")
            return result.matched_string in ["测试", "例子"]
        
        self.run_test_case(
            "unicode_support",
            test_func,
            expected_result=True
        )
