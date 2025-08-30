# -*- coding: utf-8 -*-
"""
综合测试运行器
运行所有测试并生成报告
"""

import sys
import os
import unittest
from io import StringIO

# 添加父目录到路径以便导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

def run_all_tests():
    """运行所有测试"""
    print("Results 模块综合测试")
    print("=" * 80)
    
    # 发现并运行所有测试
    loader = unittest.TestLoader()
    suite = loader.discover('.', pattern='test_*.py')
    
    # 使用详细输出运行测试
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    print("\n" + "=" * 80)
    print("测试总结")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n成功率: {success_rate:.1f}%")
    
    return result.wasSuccessful()

def run_integration_test():
    """运行集成测试"""
    print("\n" + "=" * 80)
    print("集成测试")
    
    try:
        # 导入所有模块
        from single_result import SingleMatchResult, SingleResultAnalyzer, SingleResultExporter
        from multi_result import MultiMatchResult, ResultAnalyzer, ResultExporter
        from config import AnalyzerConfig, ExporterConfig
        
        # 定义MatchResult用于测试
        from dataclasses import dataclass
        
        @dataclass
        class MatchResult:
            matched_string: str = ""
            similarity_score: float = 0.0
            match_type: str = "none"
            confidence: float = 0.0
            is_matched: bool = False
        
        print("1. 所有模块导入成功")
        
        # 创建单一结果
        single_result = SingleMatchResult(
            matched_string="测试城市",
            similarity_score=0.90,
            match_type="exact",
            confidence=0.85,
            target_name="city",
            match_position=0,
            match_length=4
        )
        
        # 创建多结果
        matches = {
            'city': MatchResult('北京', 0.95, 'exact', 0.90, True),
            'district': MatchResult('朝阳区', 0.88, 'fuzzy', 0.85, True)
        }
        
        multi_result = MultiMatchResult(
            source_string="北京市朝阳区",
            matches=matches,
            overall_score=0.82,
            is_complete=True
        )
        
        print("2. 结果对象创建成功")
        
        # 测试分析功能
        single_analysis = SingleResultAnalyzer.analyze_result(single_result)
        batch_analysis = ResultAnalyzer.analyze_batch_results([multi_result])
        
        print("3. 分析功能正常")
        
        # 测试导出功能
        single_csv = SingleResultExporter.to_csv_row(single_result)
        single_md = SingleResultExporter.to_markdown(single_result)
        
        multi_csv = ResultExporter.to_csv_row(multi_result)
        multi_md = ResultExporter.to_markdown(multi_result)
        
        print("4. 导出功能正常")
        
        # 测试配置
        analyzer_config = AnalyzerConfig()
        exporter_config = ExporterConfig()
        
        print("5. 配置管理正常")
        
        print("\n集成测试通过！")
        return True
        
    except Exception as e:
        print(f"集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_performance_test():
    """运行性能测试"""
    print("\n" + "=" * 80)
    print("性能测试")
    
    # 定义MatchResult用于测试
    from dataclasses import dataclass
    
    @dataclass
    class MatchResult:
        matched_string: str = ""
        similarity_score: float = 0.0
        match_type: str = "none"
        confidence: float = 0.0
        is_matched: bool = False
    
    try:
        import time
        from multi_result import MultiMatchResult, ResultAnalyzer
        
        # 创建大量测试数据
        results = []
        print("创建测试数据...")
        
        start_time = time.time()
        for i in range(1000):
            matches = {
                'city': MatchResult(f'城市{i}', 0.8 + i*0.0001, 'exact', 0.75 + i*0.0001, True),
                'district': MatchResult(f'区{i}', 0.7 + i*0.0001, 'fuzzy', 0.65 + i*0.0001, True if i % 2 == 0 else False)
            }
            
            result = MultiMatchResult(
                source_string=f"测试地址{i}",
                matches=matches,
                overall_score=0.6 + i*0.0002,
                is_complete=i % 3 == 0
            )
            results.append(result)
        
        creation_time = time.time() - start_time
        print(f"创建1000个结果用时: {creation_time:.3f}秒")
        
        # 测试批量分析性能
        start_time = time.time()
        analysis = ResultAnalyzer.analyze_batch_results(results)
        analysis_time = time.time() - start_time
        print(f"批量分析用时: {analysis_time:.3f}秒")
        
        # 测试批量导出性能
        start_time = time.time()
        from multi_result import ResultExporter
        csv_data = ResultExporter.to_csv_batch(results)
        export_time = time.time() - start_time
        print(f"批量导出用时: {export_time:.3f}秒")
        
        print(f"总数据量: {len(results)} 个结果")
        print(f"分析结果: {analysis['summary']['total_count']} 总数, {analysis['summary']['complete_count']} 完整")
        print(f"导出数据: {len(csv_data)} 行")
        
        print("\n性能测试通过！")
        return True
        
    except Exception as e:
        print(f"性能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始运行 Results 模块全套测试")
    
    # 运行单元测试
    unit_test_success = run_all_tests()
    
    # 运行集成测试
    integration_test_success = run_integration_test()
    
    # 运行性能测试
    performance_test_success = run_performance_test()
    
    print("\n" + "=" * 80)
    print("最终测试报告")
    print(f"单元测试: {'通过' if unit_test_success else '失败'}")
    print(f"集成测试: {'通过' if integration_test_success else '失败'}")
    print(f"性能测试: {'通过' if performance_test_success else '失败'}")
    
    if unit_test_success and integration_test_success and performance_test_success:
        print("\n所有测试通过！Results 模块运行正常。")
        sys.exit(0)
    else:
        print("\n部分测试失败，请检查代码。")
        sys.exit(1)
