#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结果分析器单元测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ...results.multi_result import MultiMatchResult, ResultAnalyzer, ResultExporter
from ...base_matcher import MatchResult
from ..base_test import BaseTestCase


class TestResultAnalyzer(BaseTestCase):
    """结果分析器测试类"""
    
    def setUp(self):
        """测试前设置"""
        super().setUp()
        
        # 创建测试数据
        self.sample_results = []
        
        # 创建一个完整匹配的结果
        result1 = MultiMatchResult("Contact john@example.com at +1-555-123-4567")
        result1.matches = {
            "email": MatchResult("john@example.com", "Contact john@example.com at +1-555-123-4567", 1.0, 8, 25),
            "phone": MatchResult("+1-555-123-4567", "Contact john@example.com at +1-555-123-4567", 1.0, 29, 44)
        }
        result1.overall_score = 1.0
        result1.is_complete = True
        self.sample_results.append(result1)
        
        # 创建一个部分匹配的结果
        result2 = MultiMatchResult("Email: jane@company.org")
        result2.matches = {
            "email": MatchResult("jane@company.org", "Email: jane@company.org", 1.0, 7, 23)
        }
        result2.overall_score = 0.5
        result2.is_complete = False
        result2.missing_targets = ["phone"]
        self.sample_results.append(result2)
        
        # 创建一个无匹配的结果
        result3 = MultiMatchResult("No contact information")
        result3.overall_score = 0.0
        result3.is_complete = False
        result3.missing_targets = ["email", "phone"]
        self.sample_results.append(result3)
    
    def test_result_analyzer_creation(self):
        """测试结果分析器创建"""
        def test_func():
            analyzer = ResultAnalyzer(self.sample_results)
            return isinstance(analyzer, ResultAnalyzer)
        
        self.run_test_case(
            "result_analyzer_creation",
            test_func,
            expected_result=True
        )
    
    def test_calculate_statistics(self):
        """测试统计计算"""
        def test_func():
            analyzer = ResultAnalyzer(self.sample_results)
            stats = analyzer.calculate_statistics()
            
            return (stats["total_results"] == 3 and
                   stats["complete_matches"] == 1 and
                   stats["average_score"] > 0.4)
        
        self.run_test_case(
            "calculate_statistics",
            test_func,
            expected_result=True
        )
    
    def test_analyze_patterns(self):
        """测试模式分析"""
        def test_func():
            analyzer = ResultAnalyzer(self.sample_results)
            patterns = analyzer.analyze_patterns()
            
            # 应该识别出常见的失败模式
            return len(patterns.get("common_failures", [])) > 0
        
        self.run_test_case(
            "analyze_patterns",
            test_func,
            expected_result=True
        )
    
    def test_get_best_matches(self):
        """测试获取最佳匹配"""
        def test_func():
            analyzer = ResultAnalyzer(self.sample_results)
            best_matches = analyzer.get_best_matches(min_score=0.7)
            
            # 应该只返回高分匹配
            return len(best_matches) == 1 and best_matches[0].overall_score >= 0.7
        
        self.run_test_case(
            "get_best_matches",
            test_func,
            expected_result=True
        )
    
    def test_get_worst_matches(self):
        """测试获取最差匹配"""
        def test_func():
            analyzer = ResultAnalyzer(self.sample_results)
            worst_matches = analyzer.get_worst_matches(max_score=0.3)
            
            # 应该返回低分匹配
            return len(worst_matches) == 1 and worst_matches[0].overall_score <= 0.3
        
        self.run_test_case(
            "get_worst_matches",
            test_func,
            expected_result=True
        )
    
    def test_generate_report(self):
        """测试生成报告"""
        def test_func():
            analyzer = ResultAnalyzer(self.sample_results)
            report = analyzer.generate_report()
            
            return (isinstance(report, dict) and
                   "statistics" in report and
                   "patterns" in report and
                   "best_matches" in report)
        
        self.run_test_case(
            "generate_report",
            test_func,
            expected_result=True
        )
    
    def test_target_success_rates(self):
        """测试目标成功率"""
        def test_func():
            analyzer = ResultAnalyzer(self.sample_results)
            success_rates = analyzer.get_target_success_rates()
            
            # email目标应该有更高的成功率
            email_rate = success_rates.get("email", 0)
            phone_rate = success_rates.get("phone", 0)
            
            return email_rate > phone_rate
        
        self.run_test_case(
            "target_success_rates",
            test_func,
            expected_result=True
        )
    
    def test_score_distribution(self):
        """测试分数分布"""
        def test_func():
            analyzer = ResultAnalyzer(self.sample_results)
            distribution = analyzer.get_score_distribution()
            
            return (isinstance(distribution, dict) and
                   "high_scores" in distribution and
                   "medium_scores" in distribution and
                   "low_scores" in distribution)
        
        self.run_test_case(
            "score_distribution",
            test_func,
            expected_result=True
        )
    
    def test_result_exporter_creation(self):
        """测试结果导出器创建"""
        def test_func():
            exporter = ResultExporter(self.sample_results)
            return isinstance(exporter, ResultExporter)
        
        self.run_test_case(
            "result_exporter_creation",
            test_func,
            expected_result=True
        )
    
    def test_to_csv_format(self):
        """测试CSV格式导出"""
        def test_func():
            exporter = ResultExporter(self.sample_results)
            csv_data = exporter.to_csv()
            
            # 检查CSV头部和数据行
            lines = csv_data.strip().split('\n')
            return len(lines) == 4  # 1 header + 3 data rows
        
        self.run_test_case(
            "to_csv_format",
            test_func,
            expected_result=True
        )
    
    def test_to_json_format(self):
        """测试JSON格式导出"""
        def test_func():
            exporter = ResultExporter(self.sample_results)
            json_data = exporter.to_json()
            
            import json
            try:
                parsed = json.loads(json_data)
                return len(parsed) == 3
            except:
                return False
        
        self.run_test_case(
            "to_json_format",
            test_func,
            expected_result=True
        )
    
    def test_to_dict_format(self):
        """测试字典格式导出"""
        def test_func():
            exporter = ResultExporter(self.sample_results)
            dict_data = exporter.to_dict()
            
            return (isinstance(dict_data, list) and
                   len(dict_data) == 3 and
                   all(isinstance(item, dict) for item in dict_data))
        
        self.run_test_case(
            "to_dict_format",
            test_func,
            expected_result=True
        )
    
    def test_multi_match_result_methods(self):
        """测试多目标匹配结果方法"""
        def test_func():
            result = self.sample_results[0]  # 完整匹配的结果
            
            # 测试获取匹配值
            email = result.get_matched_value("email")
            phone = result.get_matched_value("phone")
            
            return (email == "john@example.com" and
                   phone == "+1-555-123-4567")
        
        self.run_test_case(
            "multi_match_result_methods",
            test_func,
            expected_result=True
        )
    
    def test_has_match_method(self):
        """测试has_match方法"""
        def test_func():
            result = self.sample_results[1]  # 部分匹配的结果
            
            has_email = result.has_match("email")
            has_phone = result.has_match("phone")
            
            return has_email and not has_phone
        
        self.run_test_case(
            "has_match_method",
            test_func,
            expected_result=True
        )
    
    def test_get_match_method(self):
        """测试get_match方法"""
        def test_func():
            result = self.sample_results[0]
            
            email_match = result.get_match("email")
            nonexistent_match = result.get_match("nonexistent")
            
            return (email_match is not None and
                   nonexistent_match is None)
        
        self.run_test_case(
            "get_match_method",
            test_func,
            expected_result=True
        )
    
    def test_empty_results_handling(self):
        """测试空结果处理"""
        def test_func():
            analyzer = ResultAnalyzer([])
            stats = analyzer.calculate_statistics()
            
            return stats["total_results"] == 0
        
        self.run_test_case(
            "empty_results_handling",
            test_func,
            expected_result=True
        )
    
    def test_single_result_analysis(self):
        """测试单个结果分析"""
        def test_func():
            analyzer = ResultAnalyzer([self.sample_results[0]])
            report = analyzer.generate_report()
            
            return (report["statistics"]["total_results"] == 1 and
                   report["statistics"]["complete_matches"] == 1)
        
        self.run_test_case(
            "single_result_analysis",
            test_func,
            expected_result=True
        )
    
    def test_custom_target_analysis(self):
        """测试自定义目标分析"""
        def test_func():
            # 创建包含自定义目标的结果
            result = MultiMatchResult("Version 2.1.0 released")
            result.matches = {
                "version": MatchResult("2.1.0", "Version 2.1.0 released", 1.0, 8, 13)
            }
            result.overall_score = 1.0
            result.is_complete = True
            
            analyzer = ResultAnalyzer([result])
            success_rates = analyzer.get_target_success_rates()
            
            return success_rates.get("version", 0) == 1.0
        
        self.run_test_case(
            "custom_target_analysis",
            test_func,
            expected_result=True
        )
