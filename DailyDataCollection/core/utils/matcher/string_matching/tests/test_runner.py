#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试运行器 - 统一管理和执行所有测试用例
"""

import unittest
import sys
import os
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import importlib.util
from pathlib import Path

from .base_test import BaseTestCase, TestResult


@dataclass
class TestModuleInfo:
    """测试模块信息"""
    name: str
    path: str
    test_classes: List[str]
    description: str = ""


class TestRunner:
    """测试运行器
    
    负责发现、加载和执行所有测试用例
    """
    
    def __init__(self, test_directory: str = None):
        """初始化测试运行器
        
        Args:
            test_directory: 测试目录路径
        """
        if test_directory is None:
            test_directory = os.path.dirname(os.path.abspath(__file__))
        
        self.test_directory = test_directory
        self.test_modules: List[TestModuleInfo] = []
        self.test_results: Dict[str, Any] = {}
        
    def discover_tests(self) -> List[TestModuleInfo]:
        """发现测试模块
        
        Returns:
            List[TestModuleInfo]: 测试模块列表
        """
        test_modules = []
        
        # 遍历测试目录
        for root, dirs, files in os.walk(self.test_directory):
            for file in files:
                if file.startswith('test_') and file.endswith('.py'):
                    module_path = os.path.join(root, file)
                    module_name = file[:-3]  # 移除.py后缀
                    
                    # 尝试加载模块并获取测试类
                    try:
                        test_classes = self._get_test_classes(module_path)
                        if test_classes:
                            test_modules.append(TestModuleInfo(
                                name=module_name,
                                path=module_path,
                                test_classes=test_classes,
                                description=f"测试模块: {module_name}"
                            ))
                    except Exception as e:
                        print(f"警告: 无法加载测试模块 {module_path}: {e}")
        
        self.test_modules = test_modules
        return test_modules
    
    def _get_test_classes(self, module_path: str) -> List[str]:
        """获取模块中的测试类
        
        Args:
            module_path: 模块路径
            
        Returns:
            List[str]: 测试类名列表
        """
        spec = importlib.util.spec_from_file_location("test_module", module_path)
        if spec is None:
            return []
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        test_classes = []
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, unittest.TestCase) and 
                attr != unittest.TestCase and
                attr != BaseTestCase):
                test_classes.append(attr_name)
        
        return test_classes
    
    def run_all_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """运行所有测试
        
        Args:
            verbose: 是否显示详细信息
            
        Returns:
            Dict[str, Any]: 测试结果汇总
        """
        if not self.test_modules:
            self.discover_tests()
        
        total_start_time = time.time()
        all_results = {}
        
        if verbose:
            print(f"🚀 开始运行测试套件")
            print(f"发现 {len(self.test_modules)} 个测试模块")
            print("=" * 60)
        
        for module_info in self.test_modules:
            if verbose:
                print(f"\n📋 运行模块: {module_info.name}")
                print("-" * 40)
            
            module_results = self._run_module_tests(module_info, verbose)
            all_results[module_info.name] = module_results
        
        total_end_time = time.time()
        total_time = total_end_time - total_start_time
        
        # 汇总结果
        summary = self._generate_summary(all_results, total_time)
        
        if verbose:
            self._print_summary(summary)
        
        self.test_results = {
            'summary': summary,
            'modules': all_results,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return self.test_results
    
    def _run_module_tests(self, module_info: TestModuleInfo, 
                         verbose: bool = True) -> Dict[str, Any]:
        """运行单个模块的测试
        
        Args:
            module_info: 模块信息
            verbose: 是否显示详细信息
            
        Returns:
            Dict[str, Any]: 模块测试结果
        """
        module_results = {
            'module_name': module_info.name,
            'test_classes': {},
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'execution_time': 0
        }
        
        # 加载模块
        spec = importlib.util.spec_from_file_location("test_module", module_info.path)
        if spec is None:
            module_results['errors'] = 1
            module_results['error_message'] = "无法加载模块"
            return module_results
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 运行每个测试类
        for class_name in module_info.test_classes:
            test_class = getattr(module, class_name)
            
            if verbose:
                print(f"  🧪 测试类: {class_name}")
            
            class_results = self._run_test_class(test_class, verbose)
            module_results['test_classes'][class_name] = class_results
            
            # 汇总统计
            module_results['total_tests'] += class_results.get('total_tests', 0)
            module_results['passed'] += class_results.get('passed', 0)
            module_results['failed'] += class_results.get('failed', 0)
            module_results['errors'] += class_results.get('errors', 0)
            module_results['execution_time'] += class_results.get('execution_time', 0)
        
        return module_results
    
    def _run_test_class(self, test_class, verbose: bool = True) -> Dict[str, Any]:
        """运行单个测试类
        
        Args:
            test_class: 测试类
            verbose: 是否显示详细信息
            
        Returns:
            Dict[str, Any]: 测试类结果
        """
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(test_class)
        
        # 使用自定义的测试结果收集器
        result = unittest.TestResult()
        
        start_time = time.time()
        suite.run(result)
        end_time = time.time()
        
        class_results = {
            'class_name': test_class.__name__,
            'total_tests': result.testsRun,
            'passed': result.testsRun - len(result.failures) - len(result.errors),
            'failed': len(result.failures),
            'errors': len(result.errors),
            'execution_time': end_time - start_time,
            'failures': [str(f[1]) for f in result.failures],
            'error_messages': [str(e[1]) for e in result.errors]
        }
        
        if verbose:
            status = "✅" if class_results['failed'] == 0 and class_results['errors'] == 0 else "❌"
            print(f"    {status} {class_results['total_tests']} 个测试 | "
                  f"通过: {class_results['passed']} | "
                  f"失败: {class_results['failed']} | "
                  f"错误: {class_results['errors']} | "
                  f"时间: {class_results['execution_time']:.3f}s")
        
        return class_results
    
    def _generate_summary(self, all_results: Dict[str, Any], 
                         total_time: float) -> Dict[str, Any]:
        """生成测试汇总
        
        Args:
            all_results: 所有测试结果
            total_time: 总执行时间
            
        Returns:
            Dict[str, Any]: 测试汇总
        """
        summary = {
            'total_modules': len(all_results),
            'total_tests': 0,
            'total_passed': 0,
            'total_failed': 0,
            'total_errors': 0,
            'total_time': total_time,
            'pass_rate': 0,
            'status': 'PASS'
        }
        
        for module_name, module_result in all_results.items():
            summary['total_tests'] += module_result.get('total_tests', 0)
            summary['total_passed'] += module_result.get('passed', 0)
            summary['total_failed'] += module_result.get('failed', 0)
            summary['total_errors'] += module_result.get('errors', 0)
        
        if summary['total_tests'] > 0:
            summary['pass_rate'] = (summary['total_passed'] / summary['total_tests']) * 100
        
        if summary['total_failed'] > 0 or summary['total_errors'] > 0:
            summary['status'] = 'FAIL'
        
        return summary
    
    def _print_summary(self, summary: Dict[str, Any]):
        """打印测试汇总
        
        Args:
            summary: 测试汇总数据
        """
        print(f"\n{'='*60}")
        print(f"🎯 测试套件执行完成")
        print(f"{'='*60}")
        
        status_icon = "✅" if summary['status'] == 'PASS' else "❌"
        print(f"总体状态: {status_icon} {summary['status']}")
        print(f"总模块数: {summary['total_modules']}")
        print(f"总测试数: {summary['total_tests']}")
        print(f"通过: {summary['total_passed']}")
        print(f"失败: {summary['total_failed']}")
        print(f"错误: {summary['total_errors']}")
        print(f"通过率: {summary['pass_rate']:.1f}%")
        print(f"总执行时间: {summary['total_time']:.3f}秒")
        print(f"{'='*60}\n")
    
    def run_specific_test(self, module_name: str, class_name: str = None, 
                         method_name: str = None, verbose: bool = True) -> Dict[str, Any]:
        """运行特定测试
        
        Args:
            module_name: 模块名
            class_name: 测试类名（可选）
            method_name: 测试方法名（可选）
            verbose: 是否显示详细信息
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        if not self.test_modules:
            self.discover_tests()
        
        # 查找指定模块
        target_module = None
        for module_info in self.test_modules:
            if module_info.name == module_name:
                target_module = module_info
                break
        
        if target_module is None:
            return {'error': f'未找到测试模块: {module_name}'}
        
        if verbose:
            print(f"🎯 运行特定测试: {module_name}")
            if class_name:
                print(f"  类: {class_name}")
            if method_name:
                print(f"  方法: {method_name}")
            print("-" * 40)
        
        # 加载并运行指定测试
        spec = importlib.util.spec_from_file_location("test_module", target_module.path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        loader = unittest.TestLoader()
        
        if method_name and class_name:
            # 运行特定方法
            suite = loader.loadTestsFromName(f'{class_name}.{method_name}', module)
        elif class_name:
            # 运行特定类
            test_class = getattr(module, class_name)
            suite = loader.loadTestsFromTestCase(test_class)
        else:
            # 运行整个模块
            suite = loader.loadTestsFromModule(module)
        
        result = unittest.TestResult()
        start_time = time.time()
        suite.run(result)
        end_time = time.time()
        
        test_result = {
            'module': module_name,
            'class': class_name,
            'method': method_name,
            'total_tests': result.testsRun,
            'passed': result.testsRun - len(result.failures) - len(result.errors),
            'failed': len(result.failures),
            'errors': len(result.errors),
            'execution_time': end_time - start_time,
            'failures': [str(f[1]) for f in result.failures],
            'error_messages': [str(e[1]) for e in result.errors]
        }
        
        if verbose:
            status = "✅" if test_result['failed'] == 0 and test_result['errors'] == 0 else "❌"
            print(f"{status} 执行完成:")
            print(f"  测试数: {test_result['total_tests']}")
            print(f"  通过: {test_result['passed']}")
            print(f"  失败: {test_result['failed']}")
            print(f"  错误: {test_result['errors']}")
            print(f"  时间: {test_result['execution_time']:.3f}s")
        
        return test_result
    
    def save_results(self, filepath: str):
        """保存测试结果到文件
        
        Args:
            filepath: 保存路径
        """
        import json
        
        if not self.test_results:
            print("警告: 没有可保存的测试结果")
            return
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"测试结果已保存到: {filepath}")


def main():
    """主函数 - 命令行运行测试"""
    import argparse
    
    parser = argparse.ArgumentParser(description='多目标字符串匹配器测试运行器')
    parser.add_argument('--module', '-m', help='运行特定模块')
    parser.add_argument('--class', '-c', dest='test_class', help='运行特定测试类')
    parser.add_argument('--method', help='运行特定测试方法')
    parser.add_argument('--output', '-o', help='保存结果到文件')
    parser.add_argument('--quiet', '-q', action='store_true', help='静默模式')
    parser.add_argument('--discover', '-d', action='store_true', help='仅发现测试，不运行')
    
    args = parser.parse_args()
    
    # 创建测试运行器
    runner = TestRunner()
    
    if args.discover:
        # 仅发现测试
        modules = runner.discover_tests()
        print(f"发现 {len(modules)} 个测试模块:")
        for module in modules:
            print(f"  📋 {module.name} ({len(module.test_classes)} 个测试类)")
            for class_name in module.test_classes:
                print(f"    🧪 {class_name}")
        return
    
    verbose = not args.quiet
    
    if args.module:
        # 运行特定测试
        results = runner.run_specific_test(
            args.module, 
            args.test_class, 
            args.method, 
            verbose
        )
    else:
        # 运行所有测试
        results = runner.run_all_tests(verbose)
    
    # 保存结果
    if args.output:
        runner.save_results(args.output)
    
    # 返回退出码
    if isinstance(results, dict) and 'summary' in results:
        exit_code = 0 if results['summary']['status'] == 'PASS' else 1
    else:
        exit_code = 0 if results.get('failed', 0) == 0 and results.get('errors', 0) == 0 else 1
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
