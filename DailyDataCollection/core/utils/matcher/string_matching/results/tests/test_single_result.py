# -*- coding: utf-8 -*-
"""
单一匹配结果测试模块
合并了所有单一结果相关的测试
"""

import sys
import os
import unittest

# 添加父目录到路径以便导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from ..single_result import (
    SingleMatchResult,
    SingleResultAnalyzer, 
    SingleResultExporter
)
from ..config import AnalyzerConfig, ExporterConfig
from ...types.enums import MatchType, ConfidenceLevel


class TestSingleMatchResult(unittest.TestCase):
    """单一匹配结果测试类"""

    def setUp(self):
        """设置测试数据"""
        self.result = SingleMatchResult(
            matched_string="北京市",
            similarity_score=0.95,
            match_type=MatchType.EXACT, 
            confidence=0.90,
            target_name="city",
            match_position=(0, 3),
            match_length=3,
            preprocessing_applied=True,
            metadata={"source": "user_input", "timestamp": "2025-08-30"}
        )

    def test_result_creation(self):
        """测试结果创建"""
        self.assertIsNotNone(self.result)
        self.assertEqual(self.result.matched_string, "北京市")
        self.assertEqual(self.result.similarity_score, 0.95)
        self.assertEqual(self.result.match_type, MatchType.EXACT)
        self.assertEqual(self.result.confidence, 0.90)
        self.assertTrue(self.result.is_matched)

    def test_smart_properties(self):
        """测试智能属性访问"""
        self.assertEqual(self.result.confidence_level.value, "very_high")
        self.assertEqual(self.result.match_type_enum.value, "exact")
        self.assertTrue(self.result.is_high_confidence)
        self.assertEqual(self.result.match_span, (0, 3))

    def test_context_analysis(self):
        """测试上下文分析"""
        source_text = "北京市是中国的首都"
        context = self.result.get_context(source_text, context_length=5)
        expected_context = "**北京市**是中国的首"
        self.assertEqual(context, expected_context)

    def test_context_error_handling(self):
        """测试上下文分析的错误处理"""
        # 测试空字符串上下文
        context = self.result.get_context("", context_length=5)
        self.assertEqual(context, "北京市")
        
        # 测试无效位置的结果
        result_no_pos = SingleMatchResult(
            matched_string="test",
            match_position=None,
            match_length=None
        )
        context2 = result_no_pos.get_context("some text", context_length=5)
        self.assertEqual(context2, "test")

    def test_validation(self):
        """测试结果验证"""
        validation_errors = self.result.validate()
        self.assertEqual(len(validation_errors), 0)  # 应该通过验证
        
        # 测试无效数据
        invalid_result = SingleMatchResult(
            matched_string="test",
            similarity_score=1.5,  # 超出范围
            confidence=-0.1,  # 超出范围
            target_name="",  # 空名称
            match_position=-1  # 负位置
        )
        
        errors = invalid_result.validate()
        self.assertGreater(len(errors), 0)

    def test_quality_analysis(self):
        """测试质量分析"""
        analysis = SingleResultAnalyzer.analyze_result(self.result)
        self.assertIn('quality', analysis)
        self.assertEqual(analysis['quality']['level'], "优秀")
        self.assertIsInstance(analysis['quality']['score'], float)
        self.assertGreaterEqual(analysis['quality']['score'], 0.0)
        self.assertLessEqual(analysis['quality']['score'], 1.0)

    def test_result_comparison(self):
        """测试结果比较"""
        result2 = SingleMatchResult(
            matched_string="上海市",
            similarity_score=0.80,
            match_type="fuzzy",
            confidence=0.75,
            target_name="city"
        )
        
        comparison = SingleResultAnalyzer.compare_results(self.result, result2)
        self.assertIn('basic_comparison', comparison)
        self.assertIn('recommendation', comparison)
        self.assertEqual(comparison['recommendation'], 'result1')

    def test_exports(self):
        """测试结果导出"""
        # CSV导出测试
        csv_row = SingleResultExporter.to_csv_row(self.result)
        self.assertGreater(len(csv_row), 0)
        self.assertEqual(len(csv_row), len(SingleResultExporter.get_csv_headers()))
        
        # Markdown导出测试
        markdown = SingleResultExporter.to_markdown(self.result)
        self.assertGreater(len(markdown), 0)
        self.assertIn("北京市", markdown)
        self.assertIn("[匹配]", markdown)  # 无emoji版本
        
        # JSON导出测试
        json_str = self.result.to_json()
        self.assertGreater(len(json_str), 0)
        
        # 字典转换测试
        result_dict = self.result.to_dict()
        self.assertIn('target_name', result_dict)
        self.assertIn('matched_string', result_dict)

    def test_enums(self):
        """测试枚举类型"""
        # 测试匹配类型枚举
        self.assertIn(MatchType.EXACT, MatchType)
        self.assertIn(MatchType.FUZZY, MatchType)
        self.assertIn(MatchType.PATTERN, MatchType)
        self.assertIn(MatchType.HYBRID, MatchType)
        self.assertIn(MatchType.NONE, MatchType)
        
        # 测试置信度等级枚举
        self.assertIn(ConfidenceLevel.VERY_HIGH, ConfidenceLevel)
        self.assertIn(ConfidenceLevel.HIGH, ConfidenceLevel)
        self.assertIn(ConfidenceLevel.MEDIUM, ConfidenceLevel)
        self.assertIn(ConfidenceLevel.LOW, ConfidenceLevel)
        self.assertIn(ConfidenceLevel.VERY_LOW, ConfidenceLevel)


class TestConfiguration(unittest.TestCase):
    """配置测试类"""

    def test_analyzer_config(self):
        """测试分析器配置"""
        config = AnalyzerConfig()
        self.assertEqual(config.context_length, 20)
        self.assertEqual(config.batch_size, 1000)
        self.assertTrue(config.enable_caching)
        self.assertIsInstance(config.quality_weights, dict)
        self.assertIsInstance(config.confidence_thresholds, dict)

    def test_exporter_config(self):
        """测试导出器配置"""
        config = ExporterConfig()
        self.assertEqual(config.csv_encoding, 'utf-8')
        self.assertTrue(config.markdown_include_analysis)
        self.assertEqual(config.json_indent, 2)
        self.assertEqual(config.excel_sheet_name, 'MatchResults')


def run_basic_functionality_test():
    """运行基本功能测试（非unittest版本，用于向后兼容）"""
    print("运行基本功能测试...")
    
    try:
        # 测试模块导入
        print("1. 模块导入成功")
        
        # 创建测试结果
        result = SingleMatchResult(
            matched_string="北京市",
            similarity_score=0.95,
            match_type="exact", 
            confidence=0.90,
            target_name="city",
            original_target="beijing",
            match_position=0,
            match_length=3
        )
        print("2. 单一结果创建成功")
        
        # 测试属性访问
        assert result.confidence_level.value == "very_high"
        assert result.match_type_enum.value == "exact"
        assert result.is_high_confidence == True
        assert result.match_span == (0, 3)
        print("3. 属性访问正常")
        
        # 测试验证
        validation_errors = result.validate()
        assert len(validation_errors) == 0
        print("4. 结果验证通过")
        
        # 测试导出
        csv_row = SingleResultExporter.to_csv_row(result)
        markdown = SingleResultExporter.to_markdown(result)
        assert len(csv_row) > 0
        assert len(markdown) > 0
        print("5. 结果导出成功")
        
        # 测试配置
        config = AnalyzerConfig()
        assert config.context_length == 20
        print("6. 配置创建成功")
        
        print("\n所有基本功能测试通过！")
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("开始单一匹配结果测试")
    print("=" * 60)
    
    # 运行unittest
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 60)
    print("运行兼容性测试")
    
    # 运行基本功能测试
    run_basic_functionality_test()
