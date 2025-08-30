# -*- coding: utf-8 -*-
"""
String Matching 模块健康检查脚本

检查模块的完整性、导入依赖、API一致性等问题
"""

import sys
import os
import importlib.util
from pathlib import Path
from typing import List, Dict, Any

# 添加当前目录到路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))


class ModuleHealthChecker:
    """模块健康检查器"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.success_count = 0
        self.total_checks = 0
        
    def log_issue(self, message: str):
        """记录问题"""
        self.issues.append(message)
        print(f"[错误] {message}")
        
    def log_warning(self, message: str):
        """记录警告"""
        self.warnings.append(message)
        print(f"[警告] {message}")
        
    def log_success(self, message: str):
        """记录成功"""
        self.success_count += 1
        print(f"[成功] {message}")
    
    def check_import(self, module_name: str, import_path: str = None) -> bool:
        """检查模块导入"""
        self.total_checks += 1
        try:
            if import_path:
                spec = importlib.util.spec_from_file_location(module_name, import_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:
                module = importlib.import_module(module_name)
            self.log_success(f"导入模块: {module_name}")
            return True
        except Exception as e:
            self.log_issue(f"导入模块失败 {module_name}: {e}")
            return False
    
    def check_core_modules(self):
        """检查核心模块"""
        print("\n=== 检查核心模块 ===")
        
        core_modules = [
            'types',
            'base_matcher', 
            'exact_matcher',
            'fuzzy_matcher',
            'hybrid_matcher',
            'name_matcher',
            'similarity_calculator',
            'factory',
            'core_matcher'
        ]
        
        for module in core_modules:
            self.check_import(module)
    
    def check_submodules(self):
        """检查子模块"""
        print("\n=== 检查子模块 ===")
        
        submodules = [
            'targets',
            'results', 
            'validators'
        ]
        
        for module in submodules:
            self.check_import(module)
    
    def check_types_system(self):
        """检查类型系统"""
        print("\n=== 检查类型系统 ===")
        
        try:
            from string_types.enums import TargetType, MatchType, MatchStrategy
            from string_types.configs import TargetConfig
            from string_types.results import MatchResult
            self.log_success("类型系统导入成功")
        except Exception as e:
            self.log_issue(f"类型系统导入失败: {e}")
    
    def check_basic_functionality(self):
        """检查基本功能"""
        print("\n=== 检查基本功能 ===")
        
        try:
            # 测试精确匹配器
            from exact_matcher import ExactStringMatcher
            matcher = ExactStringMatcher()
            self.log_success("精确匹配器创建成功")
            
            # 测试模糊匹配器
            from fuzzy_matcher import FuzzyStringMatcher
            fuzzy_matcher = FuzzyStringMatcher()
            self.log_success("模糊匹配器创建成功")
            
            # 测试核心匹配器
            from core_matcher import MultiTargetMatcher
            multi_matcher = MultiTargetMatcher()
            self.log_success("多目标匹配器创建成功")
            
        except Exception as e:
            self.log_issue(f"基本功能测试失败: {e}")
    
    def check_api_consistency(self):
        """检查API一致性"""
        print("\n=== 检查API一致性 ===")
        
        try:
            from base_matcher import StringMatcher
            from exact_matcher import ExactStringMatcher
            from fuzzy_matcher import FuzzyStringMatcher
            
            # 检查基础接口
            required_methods = ['match_string', 'match_string_with_score']
            
            for matcher_class in [ExactStringMatcher, FuzzyStringMatcher]:
                for method in required_methods:
                    if hasattr(matcher_class, method):
                        self.log_success(f"{matcher_class.__name__} 有方法 {method}")
                    else:
                        self.log_issue(f"{matcher_class.__name__} 缺少方法 {method}")
                        
        except Exception as e:
            self.log_issue(f"API一致性检查失败: {e}")
    
    def check_test_structure(self):
        """检查测试结构"""
        print("\n=== 检查测试结构 ===")
        
        test_dirs = ['tests/unit', 'tests/integration', 'tests/benchmarks']
        test_files = [
            'tests/unit/test_base_matcher.py',
            'tests/unit/test_core_matcher.py',
            'tests/integration/test_end_to_end.py'
        ]
        
        for test_dir in test_dirs:
            if os.path.exists(test_dir):
                self.log_success(f"测试目录存在: {test_dir}")
            else:
                self.log_warning(f"测试目录不存在: {test_dir}")
        
        for test_file in test_files:
            if os.path.exists(test_file):
                self.log_success(f"测试文件存在: {test_file}")
            else:
                self.log_warning(f"测试文件不存在: {test_file}")
    
    def run_full_check(self):
        """运行完整检查"""
        print("开始 String Matching 模块健康检查...")
        print("=" * 50)
        
        self.check_core_modules()
        self.check_submodules()
        self.check_types_system()
        self.check_basic_functionality()
        self.check_api_consistency()
        self.check_test_structure()
        
        # 生成报告
        self.generate_report()
    
    def generate_report(self):
        """生成检查报告"""
        print("\n" + "=" * 50)
        print("健康检查报告")
        print("=" * 50)
        print(f"总检查项: {self.total_checks}")
        print(f"成功: {self.success_count}")
        print(f"问题: {len(self.issues)}")
        print(f"警告: {len(self.warnings)}")
        
        if self.issues:
            print("\n发现的问题:")
            for i, issue in enumerate(self.issues, 1):
                print(f"{i}. {issue}")
        
        if self.warnings:
            print("\n警告信息:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"{i}. {warning}")
        
        health_score = (self.success_count / max(self.total_checks, 1)) * 100
        print(f"\n模块健康评分: {health_score:.1f}%")
        
        if health_score >= 80:
            print("模块状态: 良好")
        elif health_score >= 60:
            print("模块状态: 一般，需要注意")
        else:
            print("模块状态: 较差，需要修复")


def main():
    """主函数"""
    checker = ModuleHealthChecker()
    checker.run_full_check()


if __name__ == "__main__":
    main()
