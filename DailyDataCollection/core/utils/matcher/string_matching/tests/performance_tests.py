#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字符串匹配器性能基准测试
测试不同匹配器在各种数据集大小和复杂度下的性能
"""

import unittest
import time
import statistics
import sys
import os
from typing import List, Dict, Any, Tuple
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


class PerformanceTestDataGenerator:
    """性能测试数据生成器"""
    
    @staticmethod
    def generate_random_strings(count: int, min_length: int = 5, max_length: int = 20) -> List[str]:
        """生成随机字符串列表"""
        strings = []
        for _ in range(count):
            length = random.randint(min_length, max_length)
            chars = string.ascii_letters + string.digits
            random_string = ''.join(random.choice(chars) for _ in range(length))
            strings.append(random_string)
        return strings
    
    @staticmethod
    def generate_similar_strings(base_string: str, count: int, similarity_level: float = 0.8) -> List[str]:
        """基于基础字符串生成相似字符串"""
        similar_strings = [base_string]  # 包含原始字符串
        
        for _ in range(count - 1):
            chars = list(base_string)
            changes = max(1, int(len(chars) * (1 - similarity_level)))
            
            # 随机修改字符
            for _ in range(changes):
                if chars:
                    index = random.randint(0, len(chars) - 1)
                    chars[index] = random.choice(string.ascii_letters)
            
            similar_strings.append(''.join(chars))
        
        return similar_strings
    
    @staticmethod
    def generate_chinese_strings(count: int) -> List[str]:
        """生成中文字符串列表"""
        # 常用中文字符范围
        chinese_chars = []
        for i in range(0x4e00, 0x9fff):  # 中文字符Unicode范围
            if i % 100 == 0:  # 取样，避免生成太多字符
                chinese_chars.append(chr(i))
        
        strings = []
        for _ in range(count):
            length = random.randint(2, 8)
            chinese_string = ''.join(random.choice(chinese_chars) for _ in range(length))
            strings.append(chinese_string)
        
        return strings
    
    @staticmethod
    def generate_mixed_strings(count: int) -> List[str]:
        """生成混合类型字符串（英文、数字、中文、特殊字符）"""
        patterns = [
            lambda: ''.join(random.choice(string.ascii_letters) for _ in range(random.randint(5, 15))),
            lambda: ''.join(random.choice(string.digits) for _ in range(random.randint(8, 12))),
            lambda: f"user{random.randint(1, 1000)}@example.com",
            lambda: f"file_{random.randint(1, 100)}.txt",
            lambda: f"v{random.randint(1, 10)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
        ]
        
        strings = []
        for _ in range(count):
            pattern = random.choice(patterns)
            strings.append(pattern())
        
        return strings


class BenchmarkResult:
    """基准测试结果"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.execution_times: List[float] = []
        self.memory_usage: List[float] = []
        self.success_rate: float = 0.0
        self.total_operations: int = 0
    
    def add_execution_time(self, time_seconds: float):
        """添加执行时间"""
        self.execution_times.append(time_seconds)
    
    def calculate_statistics(self) -> Dict[str, float]:
        """计算统计信息"""
        if not self.execution_times:
            return {}
        
        return {
            'avg_time': statistics.mean(self.execution_times),
            'min_time': min(self.execution_times),
            'max_time': max(self.execution_times),
            'median_time': statistics.median(self.execution_times),
            'std_dev': statistics.stdev(self.execution_times) if len(self.execution_times) > 1 else 0.0,
            'operations_per_second': self.total_operations / sum(self.execution_times) if sum(self.execution_times) > 0 else 0,
            'success_rate': self.success_rate
        }


class TestStringMatcherPerformance(unittest.TestCase):
    """字符串匹配器性能测试"""
    
    def setUp(self):
        self.exact_matcher = ExactStringMatcher()
        self.fuzzy_matcher = FuzzyStringMatcher(threshold=0.6)
        self.hybrid_matcher = HybridStringMatcher(fuzzy_threshold=0.6)
        self.results: Dict[str, BenchmarkResult] = {}
    
    def benchmark_matcher(self, matcher, test_name: str, queries: List[str], 
                         candidates: List[str], iterations: int = 1) -> BenchmarkResult:
        """对匹配器进行基准测试"""
        result = BenchmarkResult(test_name)
        successful_matches = 0
        
        for _ in range(iterations):
            start_time = time.time()
            
            for query in queries:
                match = matcher.match_string(query, candidates)
                if match is not None:
                    successful_matches += 1
            
            end_time = time.time()
            execution_time = end_time - start_time
            result.add_execution_time(execution_time)
        
        result.total_operations = len(queries) * iterations
        result.success_rate = successful_matches / result.total_operations if result.total_operations > 0 else 0.0
        
        return result
    
    def test_small_dataset_performance(self):
        """测试小数据集性能（100个候选项，10个查询）"""
        candidates = PerformanceTestDataGenerator.generate_random_strings(100)
        queries = random.sample(candidates, 10)  # 从候选中随机选择，确保有匹配
        
        # 添加一些不匹配的查询
        queries.extend(PerformanceTestDataGenerator.generate_random_strings(5))
        
        # 测试各种匹配器
        matchers = [
            (self.exact_matcher, "Exact_Small"),
            (self.fuzzy_matcher, "Fuzzy_Small"),
            (self.hybrid_matcher, "Hybrid_Small")
        ]
        
        for matcher, name in matchers:
            with self.subTest(matcher=name):
                result = self.benchmark_matcher(matcher, name, queries, candidates, iterations=5)
                self.results[name] = result
                
                stats = result.calculate_statistics()
                print(f"\n{name} Performance (Small Dataset):")
                print(f"  Average time: {stats['avg_time']:.4f}s")
                print(f"  Operations/sec: {stats['operations_per_second']:.2f}")
                print(f"  Success rate: {stats['success_rate']:.2%}")
    
    def test_medium_dataset_performance(self):
        """测试中等数据集性能（1000个候选项，50个查询）"""
        candidates = PerformanceTestDataGenerator.generate_random_strings(1000)
        queries = random.sample(candidates, 30)  # 30个匹配查询
        queries.extend(PerformanceTestDataGenerator.generate_random_strings(20))  # 20个不匹配查询
        
        matchers = [
            (self.exact_matcher, "Exact_Medium"),
            (self.fuzzy_matcher, "Fuzzy_Medium"),
            (self.hybrid_matcher, "Hybrid_Medium")
        ]
        
        for matcher, name in matchers:
            with self.subTest(matcher=name):
                result = self.benchmark_matcher(matcher, name, queries, candidates, iterations=3)
                self.results[name] = result
                
                stats = result.calculate_statistics()
                print(f"\n{name} Performance (Medium Dataset):")
                print(f"  Average time: {stats['avg_time']:.4f}s")
                print(f"  Operations/sec: {stats['operations_per_second']:.2f}")
                print(f"  Success rate: {stats['success_rate']:.2%}")
    
    def test_large_dataset_performance(self):
        """测试大数据集性能（5000个候选项，100个查询）"""
        candidates = PerformanceTestDataGenerator.generate_random_strings(5000)
        queries = random.sample(candidates, 60)  # 60个匹配查询
        queries.extend(PerformanceTestDataGenerator.generate_random_strings(40))  # 40个不匹配查询
        
        matchers = [
            (self.exact_matcher, "Exact_Large"),
            (self.fuzzy_matcher, "Fuzzy_Large"),
            (self.hybrid_matcher, "Hybrid_Large")
        ]
        
        for matcher, name in matchers:
            with self.subTest(matcher=name):
                result = self.benchmark_matcher(matcher, name, queries, candidates, iterations=2)
                self.results[name] = result
                
                stats = result.calculate_statistics()
                print(f"\n{name} Performance (Large Dataset):")
                print(f"  Average time: {stats['avg_time']:.4f}s")
                print(f"  Operations/sec: {stats['operations_per_second']:.2f}")
                print(f"  Success rate: {stats['success_rate']:.2%}")
    
    def test_chinese_text_performance(self):
        """测试中文文本性能"""
        candidates = PerformanceTestDataGenerator.generate_chinese_strings(500)
        queries = random.sample(candidates, 20)
        queries.extend(PerformanceTestDataGenerator.generate_chinese_strings(10))
        
        matchers = [
            (self.exact_matcher, "Exact_Chinese"),
            (self.fuzzy_matcher, "Fuzzy_Chinese"),
            (self.hybrid_matcher, "Hybrid_Chinese")
        ]
        
        for matcher, name in matchers:
            with self.subTest(matcher=name):
                result = self.benchmark_matcher(matcher, name, queries, candidates, iterations=3)
                self.results[name] = result
                
                stats = result.calculate_statistics()
                print(f"\n{name} Performance (Chinese Text):")
                print(f"  Average time: {stats['avg_time']:.4f}s")
                print(f"  Operations/sec: {stats['operations_per_second']:.2f}")
                print(f"  Success rate: {stats['success_rate']:.2%}")
    
    def test_similar_strings_performance(self):
        """测试相似字符串性能（模糊匹配的最佳情况）"""
        base_strings = PerformanceTestDataGenerator.generate_random_strings(10)
        candidates = []
        
        # 为每个基础字符串生成相似变体
        for base in base_strings:
            similar = PerformanceTestDataGenerator.generate_similar_strings(base, 50, 0.8)
            candidates.extend(similar)
        
        # 查询是基础字符串的轻微变体
        queries = []
        for base in base_strings[:5]:  # 使用前5个基础字符串
            variants = PerformanceTestDataGenerator.generate_similar_strings(base, 4, 0.7)
            queries.extend(variants)
        
        matchers = [
            (self.fuzzy_matcher, "Fuzzy_Similar"),
            (self.hybrid_matcher, "Hybrid_Similar")
        ]
        
        for matcher, name in matchers:
            with self.subTest(matcher=name):
                result = self.benchmark_matcher(matcher, name, queries, candidates, iterations=3)
                self.results[name] = result
                
                stats = result.calculate_statistics()
                print(f"\n{name} Performance (Similar Strings):")
                print(f"  Average time: {stats['avg_time']:.4f}s")
                print(f"  Operations/sec: {stats['operations_per_second']:.2f}")
                print(f"  Success rate: {stats['success_rate']:.2%}")
    
    def test_worst_case_performance(self):
        """测试最坏情况性能（完全不匹配的字符串）"""
        candidates = PerformanceTestDataGenerator.generate_random_strings(1000)
        queries = PerformanceTestDataGenerator.generate_random_strings(50)  # 完全不同的字符串
        
        matchers = [
            (self.exact_matcher, "Exact_WorstCase"),
            (self.fuzzy_matcher, "Fuzzy_WorstCase"),
            (self.hybrid_matcher, "Hybrid_WorstCase")
        ]
        
        for matcher, name in matchers:
            with self.subTest(matcher=name):
                result = self.benchmark_matcher(matcher, name, queries, candidates, iterations=3)
                self.results[name] = result
                
                stats = result.calculate_statistics()
                print(f"\n{name} Performance (Worst Case):")
                print(f"  Average time: {stats['avg_time']:.4f}s")
                print(f"  Operations/sec: {stats['operations_per_second']:.2f}")
                print(f"  Success rate: {stats['success_rate']:.2%}")


class TestSimilarityCalculatorPerformance(unittest.TestCase):
    """相似度计算器性能测试"""
    
    def test_similarity_calculation_performance(self):
        """测试相似度计算性能"""
        test_cases = [
            ("Short strings", 
             PerformanceTestDataGenerator.generate_random_strings(100, 5, 10),
             PerformanceTestDataGenerator.generate_random_strings(100, 5, 10)),
            ("Medium strings", 
             PerformanceTestDataGenerator.generate_random_strings(50, 20, 50),
             PerformanceTestDataGenerator.generate_random_strings(50, 20, 50)),
            ("Long strings", 
             PerformanceTestDataGenerator.generate_random_strings(20, 100, 200),
             PerformanceTestDataGenerator.generate_random_strings(20, 100, 200)),
        ]
        
        for test_name, strings1, strings2 in test_cases:
            with self.subTest(test_name=test_name):
                start_time = time.time()
                
                total_comparisons = 0
                for s1 in strings1:
                    for s2 in strings2:
                        SimilarityCalculator.calculate_similarity(s1, s2)
                        total_comparisons += 1
                
                end_time = time.time()
                total_time = end_time - start_time
                
                print(f"\nSimilarity Calculator Performance ({test_name}):")
                print(f"  Total comparisons: {total_comparisons}")
                print(f"  Total time: {total_time:.4f}s")
                print(f"  Comparisons/sec: {total_comparisons / total_time:.2f}")
                print(f"  Average time per comparison: {total_time / total_comparisons * 1000:.4f}ms")


class TestScalabilityAnalysis(unittest.TestCase):
    """可扩展性分析测试"""
    
    def test_dataset_size_scaling(self):
        """测试数据集大小的扩展性"""
        dataset_sizes = [100, 500, 1000, 2000, 5000]
        query_count = 50
        
        fuzzy_matcher = FuzzyStringMatcher(threshold=0.6)
        
        results = []
        
        for size in dataset_sizes:
            candidates = PerformanceTestDataGenerator.generate_random_strings(size)
            queries = random.sample(candidates, min(query_count, size // 2))
            queries.extend(PerformanceTestDataGenerator.generate_random_strings(
                query_count - len(queries)))
            
            start_time = time.time()
            
            for query in queries:
                fuzzy_matcher.match_string(query, candidates)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            results.append({
                'dataset_size': size,
                'execution_time': execution_time,
                'time_per_query': execution_time / len(queries),
                'queries_per_second': len(queries) / execution_time
            })
            
            print(f"\nDataset Size: {size}")
            print(f"  Execution time: {execution_time:.4f}s")
            print(f"  Time per query: {execution_time / len(queries) * 1000:.2f}ms")
            print(f"  Queries per second: {len(queries) / execution_time:.2f}")
        
        # 分析时间复杂度
        print("\nScalability Analysis:")
        for i in range(1, len(results)):
            prev = results[i-1]
            curr = results[i]
            size_ratio = curr['dataset_size'] / prev['dataset_size']
            time_ratio = curr['execution_time'] / prev['execution_time']
            complexity_factor = time_ratio / size_ratio
            
            print(f"  {prev['dataset_size']} -> {curr['dataset_size']}: "
                  f"Time ratio = {time_ratio:.2f}, Size ratio = {size_ratio:.2f}, "
                  f"Complexity factor = {complexity_factor:.2f}")


if __name__ == '__main__':
    print("Starting String Matcher Performance Benchmarks...")
    print("=" * 60)
    
    # 运行性能测试
    unittest.main(verbosity=2)
