#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
边界条件和错误情况测试
测试各种边界条件、异常情况和错误处理
"""

import unittest
import sys
import os
from typing import List, Dict, Any, Optional
import random
import string

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# 导入要测试的模块
from exact_matcher import ExactStringMatcher
from fuzzy_matcher import FuzzyStringMatcher
from hybrid_matcher import HybridStringMatcher
from similarity_calculator import SimilarityCalculator
from factory import create_string_matcher


class TestBoundaryConditions(unittest.TestCase):
    """边界条件测试"""
    
    def setUp(self):
        self.exact_matcher = ExactStringMatcher()
        self.fuzzy_matcher = FuzzyStringMatcher(threshold=0.6)
        self.hybrid_matcher = HybridStringMatcher(fuzzy_threshold=0.6)
    
    def test_empty_inputs(self):
        """测试空输入的各种情况"""
        test_cases = [
            ("", []),           # 空查询，空候选列表
            ("", ["test"]),     # 空查询，非空候选列表
            ("test", []),       # 非空查询，空候选列表
            ("", [""]),         # 空查询，包含空字符串的候选列表
            ("test", [""]),     # 非空查询，包含空字符串的候选列表
        ]
        
        matchers = [
            ("Exact", self.exact_matcher),
            ("Fuzzy", self.fuzzy_matcher),
            ("Hybrid", self.hybrid_matcher)
        ]
        
        for matcher_name, matcher in matchers:
            for query, candidates in test_cases:
                with self.subTest(matcher=matcher_name, query=repr(query), candidates=repr(candidates)):
                    # 应该正常处理，不抛出异常
                    try:
                        result = matcher.match_string(query, candidates)
                        
                        # 空查询或空候选列表应该返回None
                        if not query or not candidates:
                            self.assertIsNone(result)
                        elif query == "" and "" in candidates:
                            # 精确匹配器应该匹配空字符串
                            if matcher_name == "Exact":
                                self.assertEqual(result, "")
                        
                    except Exception as e:
                        self.fail(f"{matcher_name} matcher failed with empty input: {e}")
    
    def test_none_inputs(self):
        """测试None输入"""
        test_cases = [
            (None, ["test"]),       # None查询
            ("test", None),         # None候选列表
            (None, None),           # 都是None
        ]
        
        matchers = [
            ("Exact", self.exact_matcher),
            ("Fuzzy", self.fuzzy_matcher),
            ("Hybrid", self.hybrid_matcher)
        ]
        
        for matcher_name, matcher in matchers:
            for query, candidates in test_cases:
                with self.subTest(matcher=matcher_name, query=query, candidates=candidates):
                    # 应该返回None或抛出适当的异常
                    try:
                        result = matcher.match_string(query, candidates)
                        self.assertIsNone(result)
                    except (TypeError, AttributeError, ValueError):
                        # 这些异常是可以接受的
                        pass
                    except Exception as e:
                        self.fail(f"{matcher_name} matcher raised unexpected exception with None input: {e}")
    
    def test_single_character_strings(self):
        """测试单字符字符串"""
        single_chars = list(string.ascii_letters + string.digits + "中日韩🌟")
        
        for matcher_name, matcher in [("Exact", self.exact_matcher), ("Fuzzy", self.fuzzy_matcher)]:
            for char in single_chars[:10]:  # 测试前10个字符
                with self.subTest(matcher=matcher_name, char=char):
                    # 自匹配应该成功
                    result = matcher.match_string(char, single_chars)
                    
                    if matcher_name == "Exact":
                        self.assertEqual(result, char)
                    else:
                        # 模糊匹配可能匹配相似字符
                        self.assertIsNotNone(result)
    
    def test_very_long_strings(self):
        """测试非常长的字符串"""
        # 生成不同长度的字符串
        lengths = [1000, 5000, 10000]
        
        for length in lengths:
            long_string = "a" * length
            slightly_different = "a" * (length - 1) + "b"
            candidates = [long_string, slightly_different]
            
            with self.subTest(length=length):
                # 精确匹配应该快速完成
                start_time = time.time()
                exact_result = self.exact_matcher.match_string(long_string, candidates)
                exact_time = time.time() - start_time
                
                self.assertEqual(exact_result, long_string)
                self.assertLess(exact_time, 1.0, f"Exact matching took too long for length {length}")
                
                # 模糊匹配可能较慢，但应该在合理时间内完成
                start_time = time.time()
                fuzzy_result = self.fuzzy_matcher.match_string(long_string, candidates)
                fuzzy_time = time.time() - start_time
                
                self.assertIsNotNone(fuzzy_result)
                self.assertLess(fuzzy_time, 10.0, f"Fuzzy matching took too long for length {length}")
    
    def test_duplicate_candidates(self):
        """测试重复候选项"""
        candidates_with_duplicates = ["apple", "banana", "apple", "cherry", "banana", "apple"]
        
        matchers = [
            ("Exact", self.exact_matcher),
            ("Fuzzy", self.fuzzy_matcher),
            ("Hybrid", self.hybrid_matcher)
        ]
        
        for matcher_name, matcher in matchers:
            with self.subTest(matcher=matcher_name):
                # 查询存在的项
                result = matcher.match_string("apple", candidates_with_duplicates)
                self.assertEqual(result, "apple")
                
                # 查询模糊匹配的项
                result = matcher.match_string("aple", candidates_with_duplicates)
                if matcher_name != "Exact":
                    self.assertEqual(result, "apple")
    
    def test_whitespace_variations(self):
        """测试空白字符变体"""
        whitespace_cases = [
            "test",
            " test",           # 前导空格
            "test ",           # 尾随空格
            " test ",          # 前后空格
            "te st",           # 中间空格
            "te  st",          # 多个空格
            "\ttest",          # 制表符
            "test\n",          # 换行符
            "\r\ntest\r\n",    # Windows换行符
        ]
        
        # 测试不同匹配器对空白字符的处理
        for matcher_name, matcher in [("Exact", self.exact_matcher), ("Fuzzy", self.fuzzy_matcher)]:
            for test_string in whitespace_cases:
                with self.subTest(matcher=matcher_name, string=repr(test_string)):
                    # 自匹配应该成功
                    result = matcher.match_string(test_string, whitespace_cases)
                    
                    if matcher_name == "Exact":
                        self.assertEqual(result, test_string)
                    else:
                        # 模糊匹配可能匹配相似的字符串
                        self.assertIsNotNone(result)
    
    def test_extreme_similarity_thresholds(self):
        """测试极端相似度阈值"""
        test_strings = ["apple", "aple", "ale", "xyz"]
        
        # 测试极端阈值
        extreme_thresholds = [0.0, 0.001, 0.999, 1.0]
        
        for threshold in extreme_thresholds:
            with self.subTest(threshold=threshold):
                try:
                    fuzzy_matcher = FuzzyStringMatcher(threshold=threshold)
                    hybrid_matcher = HybridStringMatcher(fuzzy_threshold=threshold)
                    
                    # 测试完全匹配
                    result = fuzzy_matcher.match_string("apple", test_strings)
                    if threshold <= 1.0:
                        self.assertEqual(result, "apple")
                    
                    # 测试部分匹配
                    result = fuzzy_matcher.match_string("aple", test_strings)
                    if threshold == 0.0:
                        # 阈值为0应该匹配任何字符串
                        self.assertIsNotNone(result)
                    elif threshold == 1.0:
                        # 阈值为1只应该精确匹配
                        self.assertIsNone(result)
                        
                except ValueError:
                    # 某些极端值可能被拒绝，这是可以接受的
                    pass


class TestErrorHandling(unittest.TestCase):
    """错误处理测试"""
    
    def test_invalid_threshold_values(self):
        """测试无效的阈值"""
        invalid_thresholds = [-1.0, -0.1, 1.1, 2.0, float('inf'), float('-inf'), float('nan')]
        
        for threshold in invalid_thresholds:
            with self.subTest(threshold=threshold):
                if threshold < 0 or threshold > 1 or not isinstance(threshold, (int, float)) or threshold != threshold:  # 检查NaN
                    # 应该抛出异常或使用默认值
                    with self.assertRaises((ValueError, TypeError)):
                        FuzzyStringMatcher(threshold=threshold)
                    with self.assertRaises((ValueError, TypeError)):
                        HybridStringMatcher(fuzzy_threshold=threshold)
    
    def test_invalid_matcher_types(self):
        """测试无效的匹配器类型"""
        invalid_types = [
            "invalid_type",
            "EXACT",  # 大小写错误
            "fuzzy_matcher",  # 名称错误
            123,      # 数字类型
            None,     # None类型
            [],       # 列表类型
        ]
        
        for invalid_type in invalid_types:
            with self.subTest(type=invalid_type):
                with self.assertRaises((ValueError, KeyError, TypeError, AttributeError)):
                    create_string_matcher(invalid_type)
    
    def test_malformed_candidate_lists(self):
        """测试格式错误的候选列表"""
        malformed_lists = [
            [None, "test", None],           # 包含None
            ["test", 123, "example"],       # 包含非字符串
            ["test", [], "example"],        # 包含列表
            ["test", {"key": "value"}],     # 包含字典
        ]
        
        matchers = [
            ("Exact", self.exact_matcher),
            ("Fuzzy", self.fuzzy_matcher),
        ]
        
        for matcher_name, matcher in matchers:
            for malformed_list in malformed_lists:
                with self.subTest(matcher=matcher_name, candidates=str(malformed_list)):
                    # 应该处理错误或跳过无效项
                    try:
                        result = matcher.match_string("test", malformed_list)
                        # 如果没有抛出异常，结果应该是合理的
                        self.assertIn(result, [None, "test"])
                    except (TypeError, AttributeError):
                        # 这些异常是可以接受的
                        pass
    
    def test_circular_references(self):
        """测试循环引用"""
        # 创建包含自引用的对象（如果可能）
        class SelfReferencingString:
            def __init__(self, value):
                self.value = value
                self.self_ref = self
            
            def __str__(self):
                return self.value
        
        try:
            circular_obj = SelfReferencingString("test")
            candidates = ["test", circular_obj, "example"]
            
            # 测试匹配器是否能处理这种情况
            for matcher_name, matcher in [("Exact", self.exact_matcher)]:
                with self.subTest(matcher=matcher_name):
                    try:
                        result = matcher.match_string("test", candidates)
                        # 应该能找到字符串"test"
                        self.assertEqual(result, "test")
                    except (RecursionError, TypeError):
                        # 这些错误是可以理解的
                        pass
        except Exception:
            # 如果创建循环引用失败，跳过这个测试
            self.skipTest("Could not create circular reference for testing")


class TestMemoryAndPerformance(unittest.TestCase):
    """内存和性能相关测试"""
    
    def test_memory_usage_with_large_datasets(self):
        """测试大数据集的内存使用"""
        import gc
        import psutil
        import os
        
        try:
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss
            
            # 创建大数据集
            large_dataset = [f"string_{i:06d}" for i in range(50000)]
            
            # 执行匹配操作
            matcher = ExactStringMatcher()
            for i in range(100):
                query = f"string_{i:06d}"
                result = matcher.match_string(query, large_dataset[:1000])  # 使用子集以控制时间
            
            # 强制垃圾回收
            gc.collect()
            
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            
            # 内存增长应该在合理范围内（不超过100MB）
            self.assertLess(memory_increase, 100 * 1024 * 1024, 
                          f"Memory usage increased by {memory_increase / 1024 / 1024:.1f}MB")
            
        except ImportError:
            self.skipTest("psutil not available for memory testing")
    
    def test_performance_degradation(self):
        """测试性能退化"""
        import time
        
        # 测试不同大小数据集的性能
        sizes = [100, 500, 1000, 2000]
        times = []
        
        matcher = FuzzyStringMatcher(threshold=0.8)  # 使用较高阈值
        
        for size in sizes:
            dataset = [f"test_string_{i}" for i in range(size)]
            query = "test_string_50"
            
            start_time = time.time()
            for _ in range(10):  # 重复10次取平均
                matcher.match_string(query, dataset)
            end_time = time.time()
            
            avg_time = (end_time - start_time) / 10
            times.append(avg_time)
        
        # 检查性能是否合理（不应该有指数级增长）
        for i in range(1, len(times)):
            size_ratio = sizes[i] / sizes[i-1]
            time_ratio = times[i] / times[i-1] if times[i-1] > 0 else float('inf')
            
            # 时间增长不应该远超过数据量增长
            self.assertLess(time_ratio, size_ratio * 2, 
                          f"Performance degraded too much: size ratio {size_ratio}, time ratio {time_ratio}")


class TestThreadSafety(unittest.TestCase):
    """线程安全测试"""
    
    def test_concurrent_matching(self):
        """测试并发匹配"""
        import threading
        import queue
        
        # 测试数据
        candidates = [f"candidate_{i}" for i in range(1000)]
        queries = [f"candidate_{i}" for i in range(0, 1000, 10)]  # 每10个取一个
        
        # 结果队列
        results_queue = queue.Queue()
        
        def worker(matcher, query_list):
            """工作线程函数"""
            local_results = []
            for query in query_list:
                try:
                    result = matcher.match_string(query, candidates)
                    local_results.append((query, result))
                except Exception as e:
                    local_results.append((query, f"ERROR: {e}"))
            results_queue.put(local_results)
        
        # 创建多个匹配器实例
        matchers = [
            ExactStringMatcher(),
            FuzzyStringMatcher(threshold=0.8),
            HybridStringMatcher(fuzzy_threshold=0.8)
        ]
        
        for matcher in matchers:
            matcher_name = matcher.__class__.__name__
            
            with self.subTest(matcher=matcher_name):
                # 创建多个线程
                threads = []
                num_threads = 4
                queries_per_thread = len(queries) // num_threads
                
                for i in range(num_threads):
                    start_idx = i * queries_per_thread
                    end_idx = start_idx + queries_per_thread if i < num_threads - 1 else len(queries)
                    thread_queries = queries[start_idx:end_idx]
                    
                    thread = threading.Thread(target=worker, args=(matcher, thread_queries))
                    threads.append(thread)
                    thread.start()
                
                # 等待所有线程完成
                for thread in threads:
                    thread.join(timeout=30)  # 30秒超时
                    self.assertFalse(thread.is_alive(), f"Thread timed out for {matcher_name}")
                
                # 收集结果
                all_results = []
                while not results_queue.empty():
                    all_results.extend(results_queue.get())
                
                # 验证结果
                self.assertGreater(len(all_results), 0, f"No results from {matcher_name}")
                
                # 检查是否有错误
                errors = [result for query, result in all_results if isinstance(result, str) and result.startswith("ERROR")]
                self.assertEqual(len(errors), 0, f"Errors in concurrent execution: {errors}")


if __name__ == '__main__':
    import time
    
    print("Running Boundary Conditions and Error Handling Tests...")
    print("=" * 70)
    
    unittest.main(verbosity=2)
