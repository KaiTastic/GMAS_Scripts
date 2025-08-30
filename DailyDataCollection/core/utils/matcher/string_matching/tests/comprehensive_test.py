# -*- coding: utf-8 -*-
"""
String Matching 模块综合功能测试

这个脚本测试模块的核心功能，验证各种匹配器和类型系统是否正常工作
"""

import sys
import os
from typing import List, Dict, Any

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)


class ComprehensiveTest:
    """综合功能测试器"""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def run_test(self, test_name: str, test_func):
        """运行单个测试"""
        try:
            result = test_func()
            if result:
                print(f"[通过] {test_name}")
                self.passed += 1
                self.results.append((test_name, True, None))
            else:
                print(f"[失败] {test_name}: 返回False")
                self.failed += 1
                self.results.append((test_name, False, "返回False"))
        except Exception as e:
            print(f"[错误] {test_name}: {e}")
            self.failed += 1
            self.results.append((test_name, False, str(e)))
    
    def test_basic_imports(self):
        """测试基础导入"""
        try:
            from string_types.enums import TargetType, MatchType, MatchStrategy
            from string_types.configs import TargetConfig
            from string_types.results import MatchResult
            from base_matcher import StringMatcher
            from exact_matcher import ExactStringMatcher
            from fuzzy_matcher import FuzzyStringMatcher
            from hybrid_matcher import HybridStringMatcher
            return True
        except Exception:
            return False
    
    def test_exact_matcher(self):
        """测试精确匹配器"""
        try:
            from exact_matcher import ExactStringMatcher
            
            matcher = ExactStringMatcher()
            
            # 测试精确匹配成功
            result = matcher.match_string("test", ["test", "example", "sample"])
            if result != "test":
                return False
            
            # 测试精确匹配失败
            result = matcher.match_string("notfound", ["test", "example", "sample"])
            if result is not None:
                return False
            
            # 测试带分数的匹配
            result, score = matcher.match_string_with_score("test", ["test", "example"])
            if result != "test" or score != 1.0:
                return False
            
            return True
        except Exception:
            return False
    
    def test_fuzzy_matcher(self):
        """测试模糊匹配器"""
        try:
            from fuzzy_matcher import FuzzyStringMatcher
            
            matcher = FuzzyStringMatcher(threshold=0.6)
            
            # 测试模糊匹配成功
            result = matcher.match_string("test", ["tset", "example", "sample"])
            if result != "tset":  # tset 应该与 test 相似
                return False
            
            # 测试模糊匹配失败
            result = matcher.match_string("xyz", ["abc", "def", "ghi"])
            if result is not None:
                return False
            
            # 测试带分数的匹配
            result, score = matcher.match_string_with_score("test", ["tset", "example"])
            if result != "tset" or score <= 0.6:
                return False
            
            return True
        except Exception:
            return False
    
    def test_hybrid_matcher(self):
        """测试混合匹配器"""
        try:
            from hybrid_matcher import HybridStringMatcher
            
            matcher = HybridStringMatcher(fuzzy_threshold=0.6)
            
            # 测试精确匹配优先
            result = matcher.match_string("test", ["test", "tset", "example"])
            if result != "test":
                return False
            
            # 测试回退到模糊匹配
            result = matcher.match_string("tset", ["test", "example", "sample"])
            if result != "test":  # 应该找到 test 作为 tset 的模糊匹配
                return False
            
            return True
        except Exception:
            return False
    
    def test_similarity_calculator(self):
        """测试相似度计算器"""
        try:
            from similarity_calculator import SimilarityCalculator
            
            calc = SimilarityCalculator()
            
            # 测试相同字符串
            similarity = calc.calculate_similarity("test", "test")
            if similarity != 1.0:
                return False
            
            # 测试完全不同的字符串
            similarity = calc.calculate_similarity("abc", "xyz")
            if similarity >= 0.5:  # 应该很低
                return False
            
            # 测试相似字符串
            similarity = calc.calculate_similarity("test", "tset")
            if similarity <= 0.5:  # 应该较高
                return False
            
            return True
        except Exception:
            return False
    
    def test_factory_functions(self):
        """测试工厂函数"""
        try:
            from factory import create_string_matcher
            
            # 创建精确匹配器
            exact_matcher = create_string_matcher("exact")
            if exact_matcher.__class__.__name__ != "ExactStringMatcher":
                return False
            
            # 创建模糊匹配器
            fuzzy_matcher = create_string_matcher("fuzzy", fuzzy_threshold=0.7)
            if fuzzy_matcher.__class__.__name__ != "FuzzyStringMatcher":
                return False
            
            # 创建混合匹配器
            hybrid_matcher = create_string_matcher("hybrid")
            if hybrid_matcher.__class__.__name__ != "HybridStringMatcher":
                return False
            
            return True
        except Exception:
            return False
    
    def test_name_matcher(self):
        """测试名称匹配器"""
        try:
            from name_matcher import ExactNameMatcher, FuzzyNameMatcher, HybridNameMatcher
            
            test_names = ["图幅1", "图幅2", "示例图幅"]
            filename = "示例图幅_20250830.pdf"
            
            # 测试精确名称匹配器
            exact_matcher = ExactNameMatcher()
            result = exact_matcher.match_mapsheet_name(filename, test_names)
            if result != "示例图幅":
                return False
            
            # 测试模糊名称匹配器
            fuzzy_matcher = FuzzyNameMatcher()
            result = fuzzy_matcher.match_mapsheet_name("示例图幅测试.pdf", test_names)
            if result != "示例图幅":
                return False
            
            return True
        except Exception:
            return False
    
    def test_core_matcher(self):
        """测试核心多目标匹配器"""
        try:
            from core_matcher import MultiTargetMatcher
            from string_types.enums import TargetType, MatchStrategy
            from string_types.configs import TargetConfig
            
            # 创建多目标匹配器
            matcher = MultiTargetMatcher()
            
            # 添加名称目标
            name_config = TargetConfig(
                target_type=TargetType.NAME,
                patterns=["图幅1", "图幅2"],
                matcher_strategy=MatchStrategy.EXACT
            )
            matcher.add_target("names", name_config)
            
            # 验证目标已添加
            if "names" not in matcher.targets:
                return False
            
            return True
        except Exception:
            return False
    
    def test_type_system(self):
        """测试类型系统"""
        try:
            from string_types.enums import TargetType, MatchType, MatchStrategy
            from string_types.configs import TargetConfig
            from string_types.results import MatchResult
            
            # 创建配置实例
            config = TargetConfig(
                target_type=TargetType.NAME,
                patterns=["test"],
                matcher_strategy=MatchStrategy.FUZZY,
                fuzzy_threshold=0.8
            )
            
            # 验证配置属性
            if config.target_type != TargetType.NAME:
                return False
            if config.matcher_strategy != MatchStrategy.FUZZY:
                return False
            if config.fuzzy_threshold != 0.8:
                return False
            
            # 创建结果实例
            result = MatchResult(
                matched_string="test",
                similarity_score=0.95,
                match_type=MatchType.FUZZY
            )
            
            # 验证结果属性
            if not result.is_matched:
                return False
            if result.matched_string != "test":
                return False
            
            return True
        except Exception:
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("开始String Matching模块综合功能测试")
        print("=" * 60)
        
        # 运行所有测试
        self.run_test("基础导入测试", self.test_basic_imports)
        self.run_test("精确匹配器测试", self.test_exact_matcher)
        self.run_test("模糊匹配器测试", self.test_fuzzy_matcher)
        self.run_test("混合匹配器测试", self.test_hybrid_matcher)
        self.run_test("相似度计算器测试", self.test_similarity_calculator)
        self.run_test("工厂函数测试", self.test_factory_functions)
        self.run_test("名称匹配器测试", self.test_name_matcher)
        self.run_test("核心匹配器测试", self.test_core_matcher)
        self.run_test("类型系统测试", self.test_type_system)
        
        # 生成报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        print("\n" + "=" * 60)
        print("综合功能测试报告")
        print("=" * 60)
        print(f"总测试数: {total}")
        print(f"通过: {self.passed}")
        print(f"失败: {self.failed}")
        print(f"成功率: {success_rate:.1f}%")
        
        if self.failed > 0:
            print("\n失败的测试:")
            for name, passed, error in self.results:
                if not passed:
                    print(f"  - {name}: {error}")
        
        print(f"\n模块状态: {'健康' if success_rate >= 80 else '需要修复'}")
        return success_rate >= 80


def main():
    """主函数"""
    tester = ComprehensiveTest()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
