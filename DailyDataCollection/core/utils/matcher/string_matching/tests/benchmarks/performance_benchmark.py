#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能基准测试
"""

import time
import gc
import tracemalloc
import statistics
from typing import List, Dict, Any, Callable
from dataclasses import dataclass
from contextlib import contextmanager

# 直接导入，无兼容性处理
from ...core_matcher import MultiTargetMatcher
from ...targets.builder import TargetBuilder
from ..test_data.test_data_generator import TestDataGenerator


@dataclass
class PerformanceResult:
    """性能测试结果"""
    test_name: str
    data_size: int
    execution_time: float
    memory_peak: int
    memory_current: int
    throughput: float  # items per second
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "test_name": self.test_name,
            "data_size": self.data_size,
            "execution_time_seconds": round(self.execution_time, 4),
            "memory_peak_mb": round(self.memory_peak / 1024 / 1024, 2),
            "memory_current_mb": round(self.memory_current / 1024 / 1024, 2),
            "throughput_items_per_second": round(self.throughput, 2)
        }


class PerformanceBenchmark:
    """性能基准测试类"""
    
    def __init__(self):
        self.results: List[PerformanceResult] = []
        self.generator = TestDataGenerator()
    
    @contextmanager
    def measure_performance(self, test_name: str, data_size: int):
        """性能测量上下文管理器
        
        Args:
            test_name: 测试名称
            data_size: 数据大小
        """
        # 垃圾回收
        gc.collect()
        
        # 开始内存跟踪
        tracemalloc.start()
        
        # 记录开始时间
        start_time = time.perf_counter()
        
        try:
            yield
        finally:
            # 记录结束时间
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            
            # 获取内存使用情况
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            # 计算吞吐量
            throughput = data_size / execution_time if execution_time > 0 else 0
            
            # 创建结果
            result = PerformanceResult(
                test_name=test_name,
                data_size=data_size,
                execution_time=execution_time,
                memory_peak=peak,
                memory_current=current,
                throughput=throughput
            )
            
            self.results.append(result)
    
    def benchmark_basic_matching(self) -> None:
        """基础匹配性能测试"""
        data_sizes = [10, 50, 100, 500, 1000]
        
        for size in data_sizes:
            test_data = self.generator.generate_contact_data(size)
            
            with self.measure_performance(f"basic_matching_{size}", size):
                matcher = MultiTargetMatcher()
                
                # 创建目标
                targets = TargetBuilder().add_email().add_phone().add_name().build()
                
                # 批量匹配
                results = []
                for text in test_data:
                    result = matcher.match_targets(text, targets)
                    results.append(result)
    
    def benchmark_fuzzy_matching(self) -> None:
        """模糊匹配性能测试"""
        data_sizes = [10, 50, 100, 200]  # 模糊匹配更耗时，减少测试规模
        
        for size in data_sizes:
            test_data = self.generator.generate_multilingual_data(size)
            
            with self.measure_performance(f"fuzzy_matching_{size}", size):
                matcher = MultiTargetMatcher()
                
                # 创建模糊匹配目标
                targets = (TargetBuilder()
                          .add_name(fuzzy=True, threshold=0.8)
                          .add_email(fuzzy=True, threshold=0.8)
                          .build())
                
                # 批量匹配
                results = []
                for text in test_data:
                    result = matcher.match_targets(text, targets)
                    results.append(result)
    
    def benchmark_complex_targets(self) -> None:
        """复杂目标匹配性能测试"""
        data_sizes = [10, 50, 100, 200]
        
        for size in data_sizes:
            test_data = self.generator.generate_product_data(size)
            
            with self.measure_performance(f"complex_targets_{size}", size):
                matcher = MultiTargetMatcher()
                
                # 创建复杂目标组合
                targets = (TargetBuilder()
                          .add_email()
                          .add_phone()
                          .add_name(fuzzy=True, threshold=0.7)
                          .add_date()
                          .add_url()
                          .add_ip_address()
                          .add_version()
                          .add_price()
                          .build())
                
                # 批量匹配
                results = []
                for text in test_data:
                    result = matcher.match_targets(text, targets)
                    results.append(result)
    
    def benchmark_large_text(self) -> None:
        """大文本匹配性能测试"""
        # 生成长文本
        base_texts = self.generator.generate_contact_data(10)
        
        text_sizes = [1000, 5000, 10000, 20000]  # 文本长度
        
        for size in text_sizes:
            # 创建长文本
            long_text = " ".join(base_texts * (size // 100))[:size]
            
            with self.measure_performance(f"large_text_{size}", 1):
                matcher = MultiTargetMatcher()
                
                targets = (TargetBuilder()
                          .add_email()
                          .add_phone()
                          .add_name()
                          .build())
                
                # 单个长文本匹配
                result = matcher.match_targets(long_text, targets)
    
    def benchmark_memory_intensive(self) -> None:
        """内存密集型测试"""
        # 测试同时处理大量文本的内存使用
        data_sizes = [100, 500, 1000, 2000]
        
        for size in data_sizes:
            test_data = self.generator.generate_performance_test_data(size)
            
            with self.measure_performance(f"memory_intensive_{size}", size):
                matcher = MultiTargetMatcher()
                
                targets = (TargetBuilder()
                          .add_email()
                          .add_phone()
                          .add_name()
                          .add_date()
                          .build())
                
                # 批量处理并保存所有结果
                all_results = []
                for text in test_data:
                    result = matcher.match_targets(text, targets)
                    all_results.append(result)
                
                # 模拟后处理
                processed_count = sum(1 for r in all_results if r.matches)
    
    def run_all_benchmarks(self) -> None:
        """运行所有基准测试"""
        print("开始性能基准测试...")
        
        benchmark_methods = [
            ("基础匹配", self.benchmark_basic_matching),
            ("模糊匹配", self.benchmark_fuzzy_matching),
            ("复杂目标", self.benchmark_complex_targets),
            ("大文本处理", self.benchmark_large_text),
            ("内存密集型", self.benchmark_memory_intensive)
        ]
        
        for name, method in benchmark_methods:
            print(f"\n运行 {name} 基准测试...")
            try:
                method()
                print(f"✅ {name} 测试完成")
            except Exception as e:
                print(f"❌ {name} 测试失败: {e}")
    
    def analyze_results(self) -> Dict[str, Any]:
        """分析测试结果
        
        Returns:
            Dict[str, Any]: 分析结果
        """
        if not self.results:
            return {"error": "没有测试结果可分析"}
        
        # 按测试类型分组
        by_test_type = {}
        for result in self.results:
            test_type = result.test_name.split('_')[0]
            if test_type not in by_test_type:
                by_test_type[test_type] = []
            by_test_type[test_type].append(result)
        
        analysis = {
            "total_tests": len(self.results),
            "test_types": list(by_test_type.keys()),
            "performance_summary": {}
        }
        
        # 分析每种测试类型
        for test_type, results in by_test_type.items():
            execution_times = [r.execution_time for r in results]
            throughputs = [r.throughput for r in results]
            memory_peaks = [r.memory_peak for r in results]
            
            type_analysis = {
                "test_count": len(results),
                "avg_execution_time": statistics.mean(execution_times),
                "min_execution_time": min(execution_times),
                "max_execution_time": max(execution_times),
                "avg_throughput": statistics.mean(throughputs),
                "max_throughput": max(throughputs),
                "avg_memory_peak_mb": statistics.mean(memory_peaks) / 1024 / 1024,
                "max_memory_peak_mb": max(memory_peaks) / 1024 / 1024
            }
            
            analysis["performance_summary"][test_type] = type_analysis
        
        return analysis
    
    def print_results(self) -> None:
        """打印测试结果"""
        if not self.results:
            print("没有测试结果")
            return
        
        print("\n" + "="*80)
        print("性能基准测试结果")
        print("="*80)
        
        # 按测试类型分组打印
        by_test_type = {}
        for result in self.results:
            test_type = result.test_name.split('_')[0]
            if test_type not in by_test_type:
                by_test_type[test_type] = []
            by_test_type[test_type].append(result)
        
        for test_type, results in by_test_type.items():
            print(f"\n{test_type.upper()} 测试结果:")
            print("-" * 60)
            print(f"{'测试名称':<20} {'数据量':<8} {'执行时间(s)':<12} {'吞吐量':<12} {'内存峰值(MB)':<12}")
            print("-" * 60)
            
            for result in results:
                print(f"{result.test_name:<20} "
                      f"{result.data_size:<8} "
                      f"{result.execution_time:<12.4f} "
                      f"{result.throughput:<12.2f} "
                      f"{result.memory_peak/1024/1024:<12.2f}")
        
        # 打印分析结果
        analysis = self.analyze_results()
        print(f"\n总体分析:")
        print("-" * 40)
        for test_type, summary in analysis["performance_summary"].items():
            print(f"{test_type}:")
            print(f"  平均执行时间: {summary['avg_execution_time']:.4f}s")
            print(f"  平均吞吐量: {summary['avg_throughput']:.2f} items/s")
            print(f"  平均内存使用: {summary['avg_memory_peak_mb']:.2f} MB")
    
    def save_results(self, filename: str) -> None:
        """保存测试结果到文件
        
        Args:
            filename: 文件名
        """
        import json
        from datetime import datetime
        
        data = {
            "generated_at": datetime.now().isoformat(),
            "total_tests": len(self.results),
            "results": [result.to_dict() for result in self.results],
            "analysis": self.analyze_results()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"结果已保存到: {filename}")


def run_performance_benchmark():
    """运行性能基准测试的主函数"""
    benchmark = PerformanceBenchmark()
    
    try:
        # 运行所有基准测试
        benchmark.run_all_benchmarks()
        
        # 打印结果
        benchmark.print_results()
        
        # 保存结果
        benchmark.save_results("benchmark_results.json")
        
    except Exception as e:
        print(f"基准测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_performance_benchmark()
