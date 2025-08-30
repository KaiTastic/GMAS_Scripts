# -*- coding: utf-8 -*-
"""
多匹配结果测试模块
"""

import sys
import os
import unittest

# 添加父目录到路径以便导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from multi_result import (
    MultiMatchResult,
    ResultAnalyzer,
    ResultExporter
)

# 直接定义MatchResult类用于测试
from dataclasses import dataclass

@dataclass
class MatchResult:
    matched_string: str = ""
    similarity_score: float = 0.0
    match_type: str = "none"
    confidence: float = 0.0
    is_matched: bool = False


class TestMultiMatchResult(unittest.TestCase):
    """多匹配结果测试类"""

    def setUp(self):
        """设置测试数据"""
        # 创建基础匹配结果
        self.matches = {
            'city': MatchResult('北京', 0.95, 'exact', 0.90, True),
            'district': MatchResult('朝阳区', 0.88, 'fuzzy', 0.85, True),
            'street': MatchResult(None, 0.0, 'none', 0.0, False)
        }

        self.multi_result = MultiMatchResult(
            source_string="北京市朝阳区某某街道",
            matches=self.matches,
            overall_score=0.82,
            is_complete=False,
            missing_targets=['street'],
            metadata={"source": "address_parser", "timestamp": "2025-08-30"}
        )

    def test_multi_result_creation(self):
        """测试多结果创建"""
        self.assertIsNotNone(self.multi_result)
        self.assertEqual(self.multi_result.source_string, "北京市朝阳区某某街道")
        self.assertEqual(self.multi_result.overall_score, 0.82)
        self.assertFalse(self.multi_result.is_complete)
        self.assertEqual(len(self.multi_result.matches), 3)

    def test_match_queries(self):
        """测试匹配查询方法"""
        # 测试获取匹配值
        self.assertEqual(self.multi_result.get_matched_value('city'), '北京')
        self.assertEqual(self.multi_result.get_matched_value('district'), '朝阳区')
        self.assertIsNone(self.multi_result.get_matched_value('street'))
        self.assertIsNone(self.multi_result.get_matched_value('nonexistent'))

    def test_match_checks(self):
        """测试匹配检查方法"""
        # 测试是否匹配
        self.assertTrue(self.multi_result.has_match('city'))
        self.assertTrue(self.multi_result.has_match('district'))
        self.assertFalse(self.multi_result.has_match('street'))
        self.assertFalse(self.multi_result.has_match('nonexistent'))

    def test_match_scores(self):
        """测试匹配分数获取"""
        self.assertEqual(self.multi_result.get_match_score('city'), 0.95)
        self.assertEqual(self.multi_result.get_match_score('district'), 0.88)
        self.assertEqual(self.multi_result.get_match_score('street'), 0.0)
        self.assertEqual(self.multi_result.get_match_score('nonexistent'), 0.0)

    def test_target_lists(self):
        """测试目标列表获取"""
        matched_targets = self.multi_result.get_matched_targets()
        self.assertIn('city', matched_targets)
        self.assertIn('district', matched_targets)
        self.assertNotIn('street', matched_targets)
        self.assertEqual(len(matched_targets), 2)

        failed_targets = self.multi_result.get_failed_targets()
        self.assertIn('street', failed_targets)
        self.assertNotIn('city', failed_targets)
        self.assertEqual(len(failed_targets), 1)

    def test_summary(self):
        """测试结果摘要"""
        summary = self.multi_result.get_summary()
        self.assertIn('source', summary)
        self.assertIn('overall_score', summary)
        self.assertIn('is_complete', summary)
        self.assertIn('matched_count', summary)
        self.assertIn('total_targets', summary)
        self.assertIn('matched_values', summary)
        
        self.assertEqual(summary['matched_count'], 2)
        self.assertEqual(summary['total_targets'], 3)
        self.assertFalse(summary['is_complete'])

    def test_exports(self):
        """测试导出功能"""
        # 字典转换
        result_dict = self.multi_result.to_dict()
        self.assertIn('source_string', result_dict)
        self.assertIn('matches', result_dict)
        self.assertIn('overall_score', result_dict)
        
        # JSON导出
        json_str = self.multi_result.to_json()
        self.assertGreater(len(json_str), 0)
        
        # 字符串表示
        str_repr = str(self.multi_result)
        self.assertIn('MultiMatchResult', str_repr)
        self.assertIn('score=0.820', str_repr)

    def test_match_object_retrieval(self):
        """测试匹配对象获取"""
        city_match = self.multi_result.get_match('city')
        self.assertIsNotNone(city_match)
        self.assertEqual(city_match.matched_string, '北京')
        
        nonexistent_match = self.multi_result.get_match('nonexistent')
        self.assertIsNone(nonexistent_match)


class TestResultAnalyzer(unittest.TestCase):
    """结果分析器测试类"""

    def setUp(self):
        """设置测试数据"""
        # 创建多个测试结果
        self.results = []
        
        # 完全匹配的结果
        matches1 = {
            'city': MatchResult('北京', 0.95, 'exact', 0.90, True),
            'district': MatchResult('朝阳区', 0.90, 'exact', 0.88, True),
            'street': MatchResult('三里屯街', 0.85, 'fuzzy', 0.80, True)
        }
        result1 = MultiMatchResult(
            source_string="北京市朝阳区三里屯街",
            matches=matches1,
            overall_score=0.90,
            is_complete=True,
            missing_targets=[]
        )
        self.results.append(result1)
        
        # 部分匹配的结果
        matches2 = {
            'city': MatchResult('上海', 0.92, 'exact', 0.88, True),
            'district': MatchResult('黄浦区', 0.85, 'fuzzy', 0.82, True),
            'street': MatchResult(None, 0.0, 'none', 0.0, False)
        }
        result2 = MultiMatchResult(
            source_string="上海市黄浦区某某路",
            matches=matches2,
            overall_score=0.65,
            is_complete=False,
            missing_targets=['street']
        )
        self.results.append(result2)
        
        # 低分结果
        matches3 = {
            'city': MatchResult('广州', 0.60, 'fuzzy', 0.55, True),
            'district': MatchResult(None, 0.0, 'none', 0.0, False),
            'street': MatchResult(None, 0.0, 'none', 0.0, False)
        }
        result3 = MultiMatchResult(
            source_string="广州市某区某街道",
            matches=matches3,
            overall_score=0.30,
            is_complete=False,
            missing_targets=['district', 'street']
        )
        self.results.append(result3)

    def test_batch_analysis(self):
        """测试批量分析"""
        analysis = ResultAnalyzer.analyze_batch_results(self.results)
        
        # 检查摘要信息
        self.assertIn('summary', analysis)
        summary = analysis['summary']
        self.assertEqual(summary['total_count'], 3)
        self.assertEqual(summary['complete_count'], 1)
        self.assertAlmostEqual(summary['complete_rate'], 1/3, places=2)
        
        # 检查分数分布
        self.assertIn('score_distribution', analysis)
        distribution = analysis['score_distribution']
        self.assertIn('high', distribution)
        self.assertIn('medium', distribution)
        self.assertIn('low', distribution)
        
        # 检查目标统计
        self.assertIn('target_statistics', analysis)
        target_stats = analysis['target_statistics']
        self.assertIn('city', target_stats)
        self.assertIn('district', target_stats)
        self.assertIn('street', target_stats)
        
        # 检查最好和最差匹配
        self.assertIn('best_match', analysis)
        self.assertIn('worst_match', analysis)
        self.assertEqual(analysis['best_match']['score'], 0.90)
        self.assertEqual(analysis['worst_match']['score'], 0.30)

    def test_empty_batch_analysis(self):
        """测试空批次分析"""
        analysis = ResultAnalyzer.analyze_batch_results([])
        self.assertIn('summary', analysis)
        self.assertEqual(analysis['summary']['total_count'], 0)
        self.assertEqual(analysis['summary']['complete_count'], 0)
        self.assertEqual(analysis['summary']['complete_rate'], 0.0)
        self.assertIsNone(analysis['best_match'])
        self.assertIsNone(analysis['worst_match'])

    def test_pattern_finding(self):
        """测试模式识别"""
        patterns = ResultAnalyzer.find_patterns(self.results)
        
        self.assertIn('common_failures', patterns)
        self.assertIn('frequent_targets', patterns)
        self.assertIn('score_ranges', patterns)
        
        # 检查频繁目标
        frequent = patterns['frequent_targets']
        self.assertIn('city', frequent)
        self.assertEqual(frequent['city'], 3)  # 所有结果都有city
        self.assertEqual(frequent['district'], 2)  # 两个结果有district
        self.assertEqual(frequent['street'], 1)  # 一个结果有street

    def test_report_generation(self):
        """测试报告生成"""
        report = ResultAnalyzer.generate_report(self.results, include_patterns=True)
        
        self.assertIsInstance(report, str)
        self.assertIn("批量匹配结果分析报告", report)
        self.assertIn("总体统计", report)
        self.assertIn("目标匹配统计", report)
        self.assertIn("模式分析", report)


class TestResultExporter(unittest.TestCase):
    """结果导出器测试类"""

    def setUp(self):
        """设置测试数据"""
        matches = {
            'city': MatchResult('北京', 0.95, 'exact', 0.90, True),
            'district': MatchResult('朝阳区', 0.88, 'fuzzy', 0.85, True)
        }
        
        self.multi_result = MultiMatchResult(
            source_string="北京市朝阳区",
            matches=matches,
            overall_score=0.82,
            is_complete=True,
            missing_targets=[]
        )

    def test_csv_export(self):
        """测试CSV导出"""
        # 测试单个结果导出
        csv_row = ResultExporter.to_csv_row(self.multi_result)
        self.assertIsInstance(csv_row, list)
        self.assertGreater(len(csv_row), 0)
        
        # 测试表头
        headers = ResultExporter.get_csv_headers()
        self.assertIsInstance(headers, list)
        self.assertIn('source_string', headers)
        self.assertIn('overall_score', headers)

    def test_batch_csv_export(self):
        """测试批量CSV导出"""
        results = [self.multi_result]
        csv_data = ResultExporter.to_csv_batch(results)
        
        self.assertIsInstance(csv_data, list)
        self.assertGreater(len(csv_data), 1)  # 至少有表头和一行数据

    def test_markdown_export(self):
        """测试Markdown导出"""
        markdown = ResultExporter.to_markdown(self.multi_result)
        
        self.assertIsInstance(markdown, str)
        self.assertGreater(len(markdown), 0)
        self.assertIn("北京市朝阳区", markdown)

    def test_json_export(self):
        """测试JSON导出"""
        json_str = ResultExporter.to_json(self.multi_result)
        
        self.assertIsInstance(json_str, str)
        self.assertGreater(len(json_str), 0)
        
        # 验证是否为有效JSON
        import json
        data = json.loads(json_str)
        self.assertIn('source_string', data)


def run_multi_result_examples():
    """运行多结果示例测试（向后兼容）"""
    print("\n验证多结果示例...")
    
    try:
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
        assert multi_result.get_matched_value('city') == '北京'
        assert multi_result.has_match('district') == True
        assert multi_result.get_match_score('street') == 0.0
        
        print("多结果示例验证通过")
        return True
        
    except Exception as e:
        print(f"多结果测试失败: {e}")
        return False


if __name__ == "__main__":
    print("开始多匹配结果测试")
    print("=" * 60)
    
    # 运行unittest
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 60)
    print("运行兼容性测试")
    
    # 运行示例测试
    run_multi_result_examples()
