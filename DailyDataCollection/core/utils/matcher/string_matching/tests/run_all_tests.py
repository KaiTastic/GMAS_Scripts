#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字符串匹配器测试套件运行器
统一运行所有测试并生成详细报告
"""

import unittest
import sys
import os
import time
import json
from typing import Dict, List, Any
from io import StringIO
import traceback

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

# 导入所有测试模块
try:
    import comprehensive_matcher_tests
    import performance_tests
    import integration_tests
    import dataset_tests
    import unit_test
    import test_romanization
    import test_enhanced_romanization  # 新增增强版测试导入
except ImportError as e:
    print(f"Warning: Failed to import some test modules: {e}")


class TestReporter:
    """测试报告生成器"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.error_tests = 0
        self.skipped_tests = 0
    
    def start_testing(self):
        """开始测试"""
        self.start_time = time.time()
        print("=" * 80)
        print("STRING MATCHER TEST SUITE")
        print("=" * 80)
        print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    def end_testing(self):
        """结束测试"""
        self.end_time = time.time()
        self.generate_summary_report()
    
    def record_test_result(self, test_name: str, result: unittest.TestResult):
        """记录测试结果"""
        self.test_results[test_name] = {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0,
            'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100 if result.testsRun > 0 else 0,
            'failure_details': result.failures,
            'error_details': result.errors
        }
        
        self.total_tests += result.testsRun
        self.passed_tests += result.testsRun - len(result.failures) - len(result.errors)
        self.failed_tests += len(result.failures)
        self.error_tests += len(result.errors)
        if hasattr(result, 'skipped'):
            self.skipped_tests += len(result.skipped)
    
    def generate_summary_report(self):
        """生成汇总报告"""
        execution_time = self.end_time - self.start_time if self.start_time else 0
        
        print("\n" + "=" * 80)
        print("TEST EXECUTION SUMMARY")
        print("=" * 80)
        print(f"Total execution time: {execution_time:.2f} seconds")
        print(f"Total tests run: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Errors: {self.error_tests}")
        print(f"Skipped: {self.skipped_tests}")
        print(f"Overall success rate: {self.passed_tests / self.total_tests * 100:.1f}%" if self.total_tests > 0 else "N/A")
        
        print("\n" + "-" * 80)
        print("DETAILED RESULTS BY TEST MODULE")
        print("-" * 80)
        
        for test_name, results in self.test_results.items():
            print(f"\n{test_name}:")
            print(f"  Tests run: {results['tests_run']}")
            print(f"  Success rate: {results['success_rate']:.1f}%")
            print(f"  Failures: {results['failures']}")
            print(f"  Errors: {results['errors']}")
            print(f"  Skipped: {results['skipped']}")
            
            if results['failures'] > 0:
                print(f"  Failure details:")
                for i, (test, traceback_str) in enumerate(results['failure_details'][:3]):  # 只显示前3个
                    print(f"    {i+1}. {test}: {traceback_str.split('AssertionError:')[-1].strip() if 'AssertionError:' in traceback_str else 'See details'}")
            
            if results['errors'] > 0:
                print(f"  Error details:")
                for i, (test, traceback_str) in enumerate(results['error_details'][:3]):  # 只显示前3个
                    error_msg = traceback_str.split('\n')[-2] if '\n' in traceback_str else traceback_str
                    print(f"    {i+1}. {test}: {error_msg}")
        
        # 生成JSON报告
        self.generate_json_report()
        
        print(f"\n" + "=" * 80)
        print("TEST SUITE COMPLETED")
        print("=" * 80)
    
    def generate_json_report(self):
        """生成JSON格式的详细报告"""
        report_data = {
            'execution_summary': {
                'start_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.start_time)),
                'end_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.end_time)),
                'execution_time_seconds': self.end_time - self.start_time,
                'total_tests': self.total_tests,
                'passed_tests': self.passed_tests,
                'failed_tests': self.failed_tests,
                'error_tests': self.error_tests,
                'skipped_tests': self.skipped_tests,
                'overall_success_rate': self.passed_tests / self.total_tests * 100 if self.total_tests > 0 else 0
            },
            'test_modules': {}
        }
        
        for test_name, results in self.test_results.items():
            report_data['test_modules'][test_name] = {
                'tests_run': results['tests_run'],
                'success_rate': results['success_rate'],
                'failures': results['failures'],
                'errors': results['errors'],
                'skipped': results['skipped']
            }
        
        # 保存到文件
        try:
            report_filename = f"test_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            print(f"Detailed JSON report saved to: {report_filename}")
        except Exception as e:
            print(f"Failed to save JSON report: {e}")


class TestSuiteRunner:
    """测试套件运行器"""
    
    def __init__(self):
        self.reporter = TestReporter()
        self.test_modules = [
            ('Unit Tests', unit_test),
            ('Comprehensive Tests', comprehensive_matcher_tests), 
            ('Dataset Tests', dataset_tests),
            ('Romanization Tests', test_romanization),
            ('Enhanced Romanization Tests', test_enhanced_romanization),  # 新增增强版测试
            ('Integration Tests', integration_tests),
            ('Performance Tests', performance_tests),
        ]
    
    def run_test_module(self, module_name: str, test_module) -> unittest.TestResult:
        """运行单个测试模块"""
        print(f"\n{'-' * 60}")
        print(f"Running {module_name}")
        print(f"{'-' * 60}")
        
        # 创建测试套件
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(test_module)
        
        # 运行测试
        stream = StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=2)
        result = runner.run(suite)
        
        # 显示结果
        output = stream.getvalue()
        print(output)
        
        return result
    
    def run_all_tests(self):
        """运行所有测试"""
        self.reporter.start_testing()
        
        for module_name, test_module in self.test_modules:
            try:
                result = self.run_test_module(module_name, test_module)
                self.reporter.record_test_result(module_name, result)
                
            except Exception as e:
                print(f"Error running {module_name}: {e}")
                traceback.print_exc()
                
                # 创建一个表示错误的结果
                error_result = unittest.TestResult()
                error_result.testsRun = 1
                error_result.errors = [(f"{module_name}_error", str(e))]
                self.reporter.record_test_result(f"{module_name} (ERROR)", error_result)
        
        self.reporter.end_testing()
    
    def run_specific_tests(self, test_names: List[str]):
        """运行指定的测试"""
        self.reporter.start_testing()
        
        available_tests = {name: module for name, module in self.test_modules}
        
        for test_name in test_names:
            if test_name in available_tests:
                try:
                    result = self.run_test_module(test_name, available_tests[test_name])
                    self.reporter.record_test_result(test_name, result)
                except Exception as e:
                    print(f"Error running {test_name}: {e}")
            else:
                print(f"Test module '{test_name}' not found. Available tests: {list(available_tests.keys())}")
        
        self.reporter.end_testing()
    
    def run_quick_tests(self):
        """运行快速测试（跳过性能测试）"""
        quick_modules = [
            ('Unit Tests', unit_test),
            ('Comprehensive Tests', comprehensive_matcher_tests),
            ('Dataset Tests', dataset_tests),
            ('Romanization Tests', test_romanization),
        ]
        
        self.reporter.start_testing()
        
        for module_name, test_module in quick_modules:
            try:
                result = self.run_test_module(module_name, test_module)
                self.reporter.record_test_result(module_name, result)
            except Exception as e:
                print(f"Error running {module_name}: {e}")
                
        self.reporter.end_testing()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='String Matcher Test Suite Runner')
    parser.add_argument('--quick', action='store_true', 
                       help='Run quick tests only (skip performance tests)')
    parser.add_argument('--tests', nargs='+', 
                       help='Run specific test modules')
    parser.add_argument('--list', action='store_true',
                       help='List available test modules')
    
    args = parser.parse_args()
    
    runner = TestSuiteRunner()
    
    if args.list:
        print("Available test modules:")
        for name, _ in runner.test_modules:
            print(f"  - {name}")
        return
    
    if args.tests:
        runner.run_specific_tests(args.tests)
    elif args.quick:
        runner.run_quick_tests()
    else:
        runner.run_all_tests()


if __name__ == '__main__':
    main()
