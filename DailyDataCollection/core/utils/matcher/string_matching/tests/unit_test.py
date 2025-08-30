# -*- coding: utf-8 -*-
"""
String Matching 模块单元测试

简化版单元测试，专注于核心功能验证
"""

import unittest
import sys
import os

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# 导入要测试的模块
from exact_matcher import ExactStringMatcher
from fuzzy_matcher import FuzzyStringMatcher
from hybrid_matcher import HybridStringMatcher
from similarity_calculator import SimilarityCalculator
from core_matcher import MultiTargetMatcher
from string_types.enums import TargetType, MatchStrategy
from string_types.configs import TargetConfig
from string_types.results import MatchResult


class TestExactMatcher(unittest.TestCase):
    """精确匹配器测试"""
    
    def setUp(self):
        self.matcher = ExactStringMatcher()
        self.test_patterns = ["图幅1", "图幅2", "示例图幅"]
    
    def test_exact_match_found(self):
        """测试找到精确匹配"""
        result = self.matcher.match_string("图幅1", self.test_patterns)
        self.assertEqual(result, "图幅1")
    
    def test_exact_match_not_found(self):
        """测试未找到精确匹配"""
        result = self.matcher.match_string("图幅3", self.test_patterns)
        self.assertIsNone(result)
    
    def test_case_sensitive_false(self):
        """测试不区分大小写"""
        matcher = ExactStringMatcher(case_sensitive=False)
        result = matcher.match_string("TEST", ["test", "example"])
        self.assertEqual(result, "test")
    
    def test_case_sensitive_true(self):
        """测试区分大小写"""
        matcher = ExactStringMatcher(case_sensitive=True)
        result = matcher.match_string("TEST", ["test", "example"])
        self.assertIsNone(result)
    
    def test_match_with_score(self):
        """测试带分数的匹配"""
        result, score = self.matcher.match_string_with_score("图幅1", self.test_patterns)
        self.assertEqual(result, "图幅1")
        self.assertEqual(score, 1.0)


class TestFuzzyMatcher(unittest.TestCase):
    """模糊匹配器测试"""
    
    def setUp(self):
        self.matcher = FuzzyStringMatcher(threshold=0.6)
        self.test_patterns = ["test", "example", "sample"]
    
    def test_fuzzy_match_found(self):
        """测试找到模糊匹配"""
        result = self.matcher.match_string("tset", self.test_patterns)
        self.assertEqual(result, "test")
    
    def test_fuzzy_match_threshold(self):
        """测试模糊匹配阈值"""
        # 相似度太低，应该找不到
        result = self.matcher.match_string("xyz", self.test_patterns)
        self.assertIsNone(result)
    
    def test_exact_match_preferred(self):
        """测试优先精确匹配"""
        result = self.matcher.match_string("test", self.test_patterns)
        self.assertEqual(result, "test")
    
    def test_match_with_score(self):
        """测试带分数的模糊匹配"""
        result, score = self.matcher.match_string_with_score("tset", self.test_patterns)
        self.assertEqual(result, "test")
        self.assertGreater(score, 0.6)
        self.assertLess(score, 1.0)


class TestHybridMatcher(unittest.TestCase):
    """混合匹配器测试"""
    
    def setUp(self):
        self.matcher = HybridStringMatcher(fuzzy_threshold=0.6)
        self.test_patterns = ["test", "example", "sample"]
    
    def test_exact_match_priority(self):
        """测试精确匹配优先"""
        result = self.matcher.match_string("test", ["test", "tset"])
        self.assertEqual(result, "test")
    
    def test_fallback_to_fuzzy(self):
        """测试回退到模糊匹配"""
        result = self.matcher.match_string("tset", self.test_patterns)
        self.assertEqual(result, "test")
    
    def test_no_match_found(self):
        """测试找不到匹配"""
        result = self.matcher.match_string("xyz", self.test_patterns)
        self.assertIsNone(result)


class TestSimilarityCalculator(unittest.TestCase):
    """相似度计算器测试"""
    
    def test_identical_strings(self):
        """测试相同字符串"""
        similarity = SimilarityCalculator.calculate_similarity("test", "test")
        self.assertEqual(similarity, 1.0)
    
    def test_different_strings(self):
        """测试不同字符串"""
        similarity = SimilarityCalculator.calculate_similarity("abc", "xyz")
        self.assertLess(similarity, 0.5)
    
    def test_similar_strings(self):
        """测试相似字符串"""
        similarity = SimilarityCalculator.calculate_similarity("test", "tset")
        self.assertGreater(similarity, 0.5)
        self.assertLess(similarity, 1.0)
    
    def test_calculate_similarity_method(self):
        """测试相似度计算方法"""
        # 替代levenshtein_distance测试
        similarity = SimilarityCalculator.calculate_similarity("kitten", "sitting")
        self.assertGreater(similarity, 0.0)
        self.assertLess(similarity, 1.0)


class TestCoreTypes(unittest.TestCase):
    """核心类型测试"""
    
    def test_target_config_creation(self):
        """测试目标配置创建"""
        config = TargetConfig(
            target_type=TargetType.NAME,
            patterns=["test"],
            matcher_strategy=MatchStrategy.FUZZY,
            fuzzy_threshold=0.8
        )
        
        self.assertEqual(config.target_type, TargetType.NAME)
        self.assertEqual(config.patterns, ["test"])
        self.assertEqual(config.matcher_strategy, MatchStrategy.FUZZY)
        self.assertEqual(config.fuzzy_threshold, 0.8)
    
    def test_match_result_creation(self):
        """测试匹配结果创建"""
        from string_types.enums import MatchType
        
        result = MatchResult(
            matched_string="test",
            similarity_score=0.95,
            confidence=0.9,
            match_type=MatchType.FUZZY
        )
        
        self.assertEqual(result.matched_string, "test")
        self.assertEqual(result.similarity_score, 0.95)
        self.assertEqual(result.confidence, 0.9)
        self.assertTrue(result.is_matched)
    
    def test_match_result_no_match(self):
        """测试无匹配结果"""
        result = MatchResult()
        self.assertFalse(result.is_matched)


class TestMultiTargetMatcher(unittest.TestCase):
    """多目标匹配器测试"""
    
    def test_create_matcher(self):
        """测试创建多目标匹配器"""
        matcher = MultiTargetMatcher()
        self.assertIsInstance(matcher, MultiTargetMatcher)
        self.assertEqual(len(matcher.targets), 0)
    
    def test_add_target(self):
        """测试添加目标"""
        matcher = MultiTargetMatcher()
        config = TargetConfig(
            target_type=TargetType.NAME,
            patterns=["test"],
            matcher_strategy=MatchStrategy.EXACT
        )
        
        matcher.add_target("test_target", config)
        self.assertIn("test_target", matcher.targets)
        self.assertEqual(matcher.targets["test_target"], config)
    
    def test_add_multiple_targets(self):
        """测试添加多个目标"""
        matcher = MultiTargetMatcher()
        
        targets = {
            "names": TargetConfig(target_type=TargetType.NAME, patterns=["图幅1"]),
            "numbers": TargetConfig(target_type=TargetType.NUMBER, patterns=["123"])
        }
        
        matcher.add_targets(targets)
        self.assertEqual(len(matcher.targets), 2)
        self.assertIn("names", matcher.targets)
        self.assertIn("numbers", matcher.targets)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    test_classes = [
        TestExactMatcher,
        TestFuzzyMatcher, 
        TestHybridMatcher,
        TestSimilarityCalculator,
        TestCoreTypes,
        TestMultiTargetMatcher
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回测试结果
    return result.wasSuccessful()


if __name__ == "__main__":
    print("String Matching 模块单元测试")
    print("=" * 50)
    
    success = run_tests()
    
    print("\n" + "=" * 50)
    print(f"测试结果: {'全部通过' if success else '有测试失败'}")
    
    exit(0 if success else 1)
