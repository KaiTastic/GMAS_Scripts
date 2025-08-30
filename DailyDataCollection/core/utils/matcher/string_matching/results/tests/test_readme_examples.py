# -*- coding: utf-8 -*-
"""
README 文档示例验证测试
验证文档中的代码示例是否正确工作
"""

import sys
import os
import unittest

# 添加父目录到路径以便导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from single_result import SingleMatchResult, SingleResultAnalyzer, SingleResultExporter
from multi_result import MultiMatchResult, ResultAnalyzer, ResultExporter

# 直接定义MatchResult类用于测试
from dataclasses import dataclass

@dataclass
class MatchResult:
    matched_string: str = ""
    similarity_score: float = 0.0
    match_type: str = "none"
    confidence: float = 0.0
    is_matched: bool = False


class TestReadmeExamples(unittest.TestCase):
    """README 示例测试类"""

    def test_single_result_examples(self):
        """测试单一结果示例"""
        # 1. 创建单一结果（文档示例）
        result = SingleMatchResult(
            matched_string="北京市",
            similarity_score=0.95,
            match_type="exact", 
            confidence=0.90,
            target_name="city",
            original_target="beijing",
            match_position=0,
            match_length=3,
            preprocessing_applied=["normalize", "clean"],
            metadata={"source": "user_input", "timestamp": "2025-08-30"}
        )
        
        self.assertIsNotNone(result)
        
        # 2. 智能属性访问（文档示例）
        self.assertEqual(result.confidence_level.value, "very_high")
        self.assertEqual(result.match_type_enum.value, "exact")
        self.assertTrue(result.is_high_confidence)
        self.assertEqual(result.match_span, (0, 3))
        
        # 3. 上下文分析（文档示例）
        source_text = "北京市是中国的首都"
        context = result.get_context(source_text, context_length=5)
        expected_context = "**北京市**是中国的首"
        self.assertEqual(context, expected_context)
        
        # 4. 结果验证（文档示例）
        validation_errors = result.validate()
        self.assertEqual(len(validation_errors), 0)  # 应该通过验证
        
        # 5. 质量分析（文档示例）
        analysis = SingleResultAnalyzer.analyze_result(result)
        self.assertEqual(analysis['quality']['level'], "优秀")
        self.assertIsInstance(analysis['quality']['score'], float)
        
        # 6. 结果导出（文档示例）
        csv_row = SingleResultExporter.to_csv_row(result)
        markdown = SingleResultExporter.to_markdown(result)
        self.assertGreater(len(csv_row), 0)
        self.assertGreater(len(markdown), 0)

    def test_multi_result_examples(self):
        """测试多结果示例"""        
        # 创建测试数据
        matches = {
            'city': MatchResult('北京', 0.95, 'exact', 0.90, True),
            'district': MatchResult('朝阳区', 0.88, 'fuzzy', 0.85, True),
            'street': MatchResult(None, 0.0, 'none', 0.0, False)
        }

        multi_result = MultiMatchResult(
            source_string="北京市朝阳区某某街道",
            matches=matches,
            overall_score=0.82,
            is_complete=False,
            missing_targets=['street']
        )
        
        # 测试查询方法
        self.assertEqual(multi_result.get_matched_value('city'), '北京')
        self.assertTrue(multi_result.has_match('district'))
        self.assertEqual(multi_result.get_match_score('street'), 0.0)

    def test_error_handling_examples(self):
        """测试错误处理示例"""
        # 测试空字符串上下文
        result = SingleMatchResult(
            matched_string="test",
            match_position=0,
            match_length=4
        )
        
        context = result.get_context("", context_length=5)
        self.assertEqual(context, "test")
        
        # 测试无效位置
        result2 = SingleMatchResult(
            matched_string="test",
            match_position=None,
            match_length=None
        )
        
        context2 = result2.get_context("some text", context_length=5)
        self.assertEqual(context2, "test")

    def test_configuration_examples(self):
        """测试配置示例"""
        from config import AnalyzerConfig, ExporterConfig
        
        # 测试分析器配置
        config = AnalyzerConfig(
            quality_weights={
                'similarity_score': 0.4,
                'confidence': 0.3,
                'match_type_bonus': 0.2,
                'consistency_check': 0.1
            },
            context_length=20,
            batch_size=1000
        )
        
        self.assertEqual(config.context_length, 20)
        self.assertEqual(config.batch_size, 1000)
        
        # 测试导出器配置
        export_config = ExporterConfig(
            csv_encoding='utf-8',
            markdown_include_analysis=True,
            json_indent=2
        )
        
        self.assertEqual(export_config.csv_encoding, 'utf-8')
        self.assertTrue(export_config.markdown_include_analysis)

    def test_batch_analysis_examples(self):
        """测试批量分析示例"""        
        # 创建多个结果
        results = []
        for i in range(3):
            matches = {
                'city': MatchResult(f'城市{i}', 0.9 - i*0.1, 'exact', 0.85 - i*0.1, True),
                'district': MatchResult(f'区{i}', 0.8 - i*0.1, 'fuzzy', 0.75 - i*0.1, i < 2)
            }
            
            result = MultiMatchResult(
                source_string=f"测试地址{i}",
                matches=matches,
                overall_score=0.8 - i*0.1,
                is_complete=i < 2
            )
            results.append(result)
        
        # 批量分析
        analysis = ResultAnalyzer.analyze_batch_results(results)
        
        self.assertEqual(analysis['summary']['total_count'], 3)
        self.assertIn('target_statistics', analysis)
        self.assertIn('best_match', analysis)
        self.assertIn('worst_match', analysis)


def run_readme_examples_legacy():
    """运行README示例（向后兼容的非unittest版本）"""
    print("验证 README 文档示例...")
    
    success_count = 0
    total_tests = 6
    
    try:        
        # 1. 创建单一结果（文档示例）
        result = SingleMatchResult(
            matched_string="北京市",
            similarity_score=0.95,
            match_type="exact", 
            confidence=0.90,
            target_name="city",
            original_target="beijing",
            match_position=0,
            match_length=3,
            preprocessing_applied=["normalize", "clean"],
            metadata={"source": "user_input", "timestamp": "2025-08-30"}
        )
        print("1. 结果创建成功")
        success_count += 1
        
        # 2. 智能属性访问（文档示例）
        assert result.confidence_level.value == "very_high"
        assert result.match_type_enum.value == "exact"
        assert result.is_high_confidence == True
        assert result.match_span == (0, 3)
        print("2. 智能属性验证通过")
        success_count += 1
        
        # 3. 上下文分析（文档示例）
        source_text = "北京市是中国的首都"
        context = result.get_context(source_text, context_length=5)
        expected_context = "**北京市**是中国的首"
        assert context == expected_context
        print("3. 上下文分析验证通过")
        success_count += 1
        
        # 4. 结果验证（文档示例）
        validation_errors = result.validate()
        assert len(validation_errors) == 0  # 应该通过验证
        print("4. 结果验证通过")
        success_count += 1
        
        # 5. 质量分析（文档示例）
        analysis = SingleResultAnalyzer.analyze_result(result)
        assert analysis['quality']['level'] == "优秀"
        assert isinstance(analysis['quality']['score'], float)
        print("5. 质量分析验证通过")
        success_count += 1
        
        # 6. 结果导出（文档示例）
        csv_row = SingleResultExporter.to_csv_row(result)
        markdown = SingleResultExporter.to_markdown(result)
        assert len(csv_row) > 0
        assert len(markdown) > 0
        print("6. 结果导出验证通过")
        success_count += 1
        
    except Exception as e:
        print(f"测试失败: {e}")
        return False
    
    print(f"\nREADME 示例验证完成: {success_count}/{total_tests} 通过！")
    return success_count == total_tests


if __name__ == "__main__":
    print("开始README示例验证测试")
    print("=" * 60)
    
    # 运行unittest
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 60)
    print("运行兼容性测试")
    
    # 运行传统示例测试
    success = run_readme_examples_legacy()
    if success:
        print("\n所有README示例验证成功！")
    else:
        print("\n部分README示例验证失败")
