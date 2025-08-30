#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试基类 - 为所有测试用例提供公共功能
"""

import unittest
import time
import traceback
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json


class TestResult(Enum):
    """测试结果枚举"""
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    SKIP = "SKIP"


@dataclass
class TestCaseResult:
    """单个测试用例结果"""
    test_name: str
    result: TestResult
    execution_time: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    expected: Optional[Any] = None
    actual: Optional[Any] = None


class BaseTestCase(unittest.TestCase):
    """测试基类
    
    提供通用的测试功能和断言方法
    """
    
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.test_results: List[TestCaseResult] = []
        self.start_time = None
        self.end_time = None
        
    def setUp(self):
        """测试前设置"""
        self.start_time = time.time()
        
    def tearDown(self):
        """测试后清理"""
        self.end_time = time.time()
        
    def run_test_case(self, test_name: str, test_func: Callable, 
                      expected_result: Any = None, **kwargs) -> TestCaseResult:
        """运行单个测试用例
        
        Args:
            test_name: 测试用例名称
            test_func: 测试函数
            expected_result: 期望结果
            **kwargs: 测试函数参数
            
        Returns:
            TestCaseResult: 测试结果
        """
        start_time = time.time()
        result = TestResult.PASS
        error_message = None
        actual_result = None
        details = {}
        
        try:
            # 执行测试函数
            actual_result = test_func(**kwargs)
            
            # 如果提供了期望结果，进行比较
            if expected_result is not None:
                if actual_result != expected_result:
                    result = TestResult.FAIL
                    error_message = f"期望结果: {expected_result}, 实际结果: {actual_result}"
                    
        except AssertionError as e:
            result = TestResult.FAIL
            error_message = str(e)
            
        except Exception as e:
            result = TestResult.ERROR
            error_message = f"{type(e).__name__}: {str(e)}"
            details['traceback'] = traceback.format_exc()
            
        execution_time = time.time() - start_time
        
        test_result = TestCaseResult(
            test_name=test_name,
            result=result,
            execution_time=execution_time,
            error_message=error_message,
            details=details,
            expected=expected_result,
            actual=actual_result
        )
        
        self.test_results.append(test_result)
        return test_result
    
    def assert_fuzzy_match(self, actual: float, expected: float, 
                          tolerance: float = 0.01, message: str = ""):
        """断言模糊匹配分数
        
        Args:
            actual: 实际分数
            expected: 期望分数
            tolerance: 容差
            message: 错误消息
        """
        if abs(actual - expected) > tolerance:
            fail_msg = f"分数差异过大: 期望 {expected}, 实际 {actual}, 容差 {tolerance}"
            if message:
                fail_msg = f"{message}: {fail_msg}"
            self.fail(fail_msg)
            
    def assert_match_result(self, result, expected_matches: Dict[str, str], 
                           min_score: float = 0.5):
        """断言匹配结果
        
        Args:
            result: 匹配结果对象
            expected_matches: 期望的匹配字典
            min_score: 最小分数要求
        """
        # 检查总分数
        self.assertGreaterEqual(result.overall_score, min_score, 
                               f"整体分数过低: {result.overall_score}")
        
        # 检查期望的匹配项
        for target_name, expected_value in expected_matches.items():
            actual_value = result.get_matched_value(target_name)
            self.assertEqual(actual_value, expected_value, 
                           f"目标 {target_name} 匹配错误: 期望 {expected_value}, 实际 {actual_value}")
    
    def assert_target_config(self, config, expected_type, expected_patterns: List[str]):
        """断言目标配置
        
        Args:
            config: 目标配置对象
            expected_type: 期望的目标类型
            expected_patterns: 期望的模式列表
        """
        self.assertEqual(config.target_type, expected_type, 
                        f"目标类型错误: 期望 {expected_type}, 实际 {config.target_type}")
        
        for pattern in expected_patterns:
            self.assertIn(pattern, config.patterns, 
                         f"模式 {pattern} 不在配置中")
    
    def get_test_summary(self) -> Dict[str, Any]:
        """获取测试总结
        
        Returns:
            Dict[str, Any]: 测试总结信息
        """
        total_tests = len(self.test_results)
        if total_tests == 0:
            return {"total": 0, "summary": "无测试用例"}
            
        pass_count = sum(1 for r in self.test_results if r.result == TestResult.PASS)
        fail_count = sum(1 for r in self.test_results if r.result == TestResult.FAIL)
        error_count = sum(1 for r in self.test_results if r.result == TestResult.ERROR)
        skip_count = sum(1 for r in self.test_results if r.result == TestResult.SKIP)
        
        total_time = sum(r.execution_time for r in self.test_results)
        avg_time = total_time / total_tests if total_tests > 0 else 0
        
        return {
            "total": total_tests,
            "pass": pass_count,
            "fail": fail_count,
            "error": error_count,
            "skip": skip_count,
            "pass_rate": (pass_count / total_tests) * 100,
            "total_time": total_time,
            "average_time": avg_time,
            "details": self.test_results
        }
    
    def print_test_results(self):
        """打印测试结果"""
        summary = self.get_test_summary()
        
        print(f"\n{'='*60}")
        print(f"测试总结 - {self.__class__.__name__}")
        print(f"{'='*60}")
        print(f"总用例数: {summary['total']}")
        print(f"通过: {summary['pass']} | 失败: {summary['fail']} | 错误: {summary['error']} | 跳过: {summary['skip']}")
        print(f"通过率: {summary['pass_rate']:.1f}%")
        print(f"总执行时间: {summary['total_time']:.4f}秒")
        print(f"平均执行时间: {summary['average_time']:.4f}秒")
        
        print(f"\n详细结果:")
        print(f"{'-'*60}")
        
        for i, result in enumerate(self.test_results, 1):
            status_icon = {
                TestResult.PASS: "✅",
                TestResult.FAIL: "❌", 
                TestResult.ERROR: "💥",
                TestResult.SKIP: "⏭️"
            }.get(result.result, "❓")
            
            print(f"{i:2d}. {status_icon} {result.test_name} ({result.execution_time:.4f}s)")
            
            if result.error_message:
                print(f"    错误: {result.error_message}")
                
            if result.expected is not None and result.actual is not None:
                print(f"    期望: {result.expected}")
                print(f"    实际: {result.actual}")
                
        print(f"{'='*60}\n")
    
    def save_test_results(self, filepath: str):
        """保存测试结果到文件
        
        Args:
            filepath: 保存路径
        """
        summary = self.get_test_summary()
        
        # 转换结果为可序列化的格式
        serializable_results = []
        for result in self.test_results:
            serializable_results.append({
                "test_name": result.test_name,
                "result": result.result.value,
                "execution_time": result.execution_time,
                "error_message": result.error_message,
                "details": result.details,
                "expected": str(result.expected) if result.expected is not None else None,
                "actual": str(result.actual) if result.actual is not None else None
            })
        
        summary["details"] = serializable_results
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
            
        print(f"测试结果已保存到: {filepath}")


class PerformanceTestCase(BaseTestCase):
    """性能测试基类"""
    
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.performance_thresholds = {
            'execution_time': 1.0,  # 秒
            'memory_usage': 100,    # MB
            'accuracy': 0.8         # 准确率
        }
    
    def benchmark_function(self, func: Callable, iterations: int = 100, 
                          **kwargs) -> Dict[str, float]:
        """性能基准测试
        
        Args:
            func: 要测试的函数
            iterations: 迭代次数
            **kwargs: 函数参数
            
        Returns:
            Dict[str, float]: 性能指标
        """
        times = []
        
        for _ in range(iterations):
            start_time = time.time()
            func(**kwargs)
            end_time = time.time()
            times.append(end_time - start_time)
        
        return {
            'min_time': min(times),
            'max_time': max(times),
            'avg_time': sum(times) / len(times),
            'total_time': sum(times),
            'iterations': iterations
        }
    
    def assert_performance(self, metrics: Dict[str, float], 
                          max_avg_time: float = None):
        """断言性能指标
        
        Args:
            metrics: 性能指标
            max_avg_time: 最大平均时间
        """
        if max_avg_time is not None:
            self.assertLessEqual(metrics['avg_time'], max_avg_time,
                               f"平均执行时间过长: {metrics['avg_time']:.4f}s > {max_avg_time}s")
