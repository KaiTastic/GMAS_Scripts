# -*- coding: utf-8 -*-
"""
String Matching 模块一致性检查工具

检查模块中的各种不一致问题：
- API 接口一致性
- 类设计一致性  
- 方法签名一致性
- 导入语句一致性
- 命名约定一致性
- 类型系统一致性
"""

import sys
import os
import inspect
import ast
from typing import Dict, List, Set, Any, Optional, Tuple
from pathlib import Path

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)


class ConsistencyChecker:
    """模块一致性检查器"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.module_path = current_dir
        
    def log_issue(self, category: str, message: str):
        """记录问题"""
        self.issues.append((category, message))
        print(f"[问题] {category}: {message}")
        
    def log_warning(self, category: str, message: str):
        """记录警告"""
        self.warnings.append((category, message))
        print(f"[警告] {category}: {message}")
    
    def check_api_consistency(self):
        """检查API接口一致性"""
        print("\n=== 检查API接口一致性 ===")
        
        try:
            # 导入所有匹配器类
            from base_matcher import StringMatcher
            from exact_matcher import ExactStringMatcher
            from fuzzy_matcher import FuzzyStringMatcher
            from hybrid_matcher import HybridStringMatcher
            from name_matcher import NameMatcher, ExactNameMatcher, FuzzyNameMatcher, HybridNameMatcher
            
            # 检查StringMatcher子类
            string_matchers = [ExactStringMatcher, FuzzyStringMatcher, HybridStringMatcher]
            expected_methods = ['match_string', 'match_string_with_score']
            
            for matcher_class in string_matchers:
                for method_name in expected_methods:
                    if not hasattr(matcher_class, method_name):
                        self.log_issue("API一致性", f"{matcher_class.__name__} 缺少方法 {method_name}")
                    else:
                        # 检查方法签名
                        method = getattr(matcher_class, method_name)
                        signature = inspect.signature(method)
                        params = list(signature.parameters.keys())
                        
                        if method_name == 'match_string':
                            expected_params = ['self', 'target', 'candidates']
                            if params != expected_params:
                                self.log_warning("API一致性", 
                                    f"{matcher_class.__name__}.{method_name} 参数不一致: {params} vs {expected_params}")
                        
                        elif method_name == 'match_string_with_score':
                            expected_params = ['self', 'target', 'candidates']
                            if params != expected_params:
                                self.log_warning("API一致性", 
                                    f"{matcher_class.__name__}.{method_name} 参数不一致: {params} vs {expected_params}")
            
            # 检查NameMatcher子类
            name_matchers = [ExactNameMatcher, FuzzyNameMatcher, HybridNameMatcher]
            expected_name_methods = ['match_mapsheet_name', 'match_file_pattern']
            
            for matcher_class in name_matchers:
                for method_name in expected_name_methods:
                    if not hasattr(matcher_class, method_name):
                        self.log_warning("API一致性", f"{matcher_class.__name__} 缺少方法 {method_name}")
                        
        except Exception as e:
            self.log_issue("API一致性", f"检查失败: {e}")
    
    def check_class_inheritance(self):
        """检查类继承一致性"""
        print("\n=== 检查类继承一致性 ===")
        
        try:
            from base_matcher import StringMatcher
            from exact_matcher import ExactStringMatcher
            from fuzzy_matcher import FuzzyStringMatcher
            from hybrid_matcher import HybridStringMatcher
            from name_matcher import NameMatcher, ExactNameMatcher, FuzzyNameMatcher, HybridNameMatcher
            
            # 检查StringMatcher继承关系
            string_matcher_classes = [ExactStringMatcher, FuzzyStringMatcher, HybridStringMatcher]
            for cls in string_matcher_classes:
                if not issubclass(cls, StringMatcher):
                    self.log_issue("继承一致性", f"{cls.__name__} 没有继承 StringMatcher")
                else:
                    # 检查是否正确实现了抽象方法
                    abstract_methods = ['match_string', 'match_string_with_score']
                    for method in abstract_methods:
                        if not hasattr(cls, method):
                            self.log_issue("继承一致性", f"{cls.__name__} 没有实现抽象方法 {method}")
            
            # 检查NameMatcher继承关系
            name_matcher_classes = [ExactNameMatcher, FuzzyNameMatcher, HybridNameMatcher]
            for cls in name_matcher_classes:
                if not issubclass(cls, NameMatcher):
                    self.log_issue("继承一致性", f"{cls.__name__} 没有继承 NameMatcher")
                    
        except Exception as e:
            self.log_issue("继承一致性", f"检查失败: {e}")
    
    def check_constructor_consistency(self):
        """检查构造函数一致性"""
        print("\n=== 检查构造函数一致性 ===")
        
        try:
            from exact_matcher import ExactStringMatcher
            from fuzzy_matcher import FuzzyStringMatcher
            from hybrid_matcher import HybridStringMatcher
            
            constructors = {}
            classes = [ExactStringMatcher, FuzzyStringMatcher, HybridStringMatcher]
            
            for cls in classes:
                init_method = cls.__init__
                signature = inspect.signature(init_method)
                params = list(signature.parameters.keys())
                constructors[cls.__name__] = params
                
            # 检查debug参数是否都有
            for cls_name, params in constructors.items():
                if 'debug' not in params:
                    self.log_warning("构造函数一致性", f"{cls_name} 构造函数缺少 debug 参数")
                    
            # 检查模糊匹配相关参数
            fuzzy_classes = ['FuzzyStringMatcher', 'HybridStringMatcher']
            for cls_name in fuzzy_classes:
                if cls_name in constructors:
                    params = constructors[cls_name]
                    has_threshold = any('threshold' in param for param in params)
                    if not has_threshold:
                        self.log_warning("构造函数一致性", f"{cls_name} 构造函数缺少阈值参数")
                        
        except Exception as e:
            self.log_issue("构造函数一致性", f"检查失败: {e}")
    
    def check_import_consistency(self):
        """检查导入语句一致性"""
        print("\n=== 检查导入语句一致性 ===")
        
        # 检查主要文件的导入模式
        main_files = [
            'base_matcher.py',
            'exact_matcher.py', 
            'fuzzy_matcher.py',
            'hybrid_matcher.py',
            'core_matcher.py',
            'factory.py'
        ]
        
        import_patterns = {}
        
        for file_name in main_files:
            file_path = os.path.join(self.module_path, file_name)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    tree = ast.parse(content)
                    imports = []
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imports.append(f"import {alias.name}")
                        elif isinstance(node, ast.ImportFrom):
                            module = node.module or ""
                            for alias in node.names:
                                imports.append(f"from {module} import {alias.name}")
                    
                    import_patterns[file_name] = imports
                    
                except Exception as e:
                    self.log_warning("导入一致性", f"解析 {file_name} 失败: {e}")
        
        # 检查string_types导入是否一致
        string_types_imports = {}
        for file_name, imports in import_patterns.items():
            string_types_refs = [imp for imp in imports if 'string_types' in imp]
            if string_types_refs:
                string_types_imports[file_name] = string_types_refs
        
        # 检查是否有不一致的导入模式
        if len(set(str(sorted(imports)) for imports in string_types_imports.values())) > 1:
            self.log_warning("导入一致性", "不同文件的 string_types 导入模式不一致")
            for file_name, imports in string_types_imports.items():
                print(f"  {file_name}: {imports}")
    
    def check_naming_consistency(self):
        """检查命名约定一致性"""
        print("\n=== 检查命名约定一致性 ===")
        
        try:
            # 检查类名约定
            from exact_matcher import ExactStringMatcher
            from fuzzy_matcher import FuzzyStringMatcher  
            from hybrid_matcher import HybridStringMatcher
            from name_matcher import ExactNameMatcher, FuzzyNameMatcher, HybridNameMatcher
            
            # 所有匹配器类名都应该以Matcher结尾
            matcher_classes = [
                ExactStringMatcher, FuzzyStringMatcher, HybridStringMatcher,
                ExactNameMatcher, FuzzyNameMatcher, HybridNameMatcher
            ]
            
            for cls in matcher_classes:
                if not cls.__name__.endswith('Matcher'):
                    self.log_issue("命名一致性", f"类名 {cls.__name__} 不符合Matcher后缀约定")
            
            # 检查方法命名约定
            expected_methods = {
                'match_string': ['exact_matcher', 'fuzzy_matcher', 'hybrid_matcher'],
                'match_mapsheet_name': ['name_matcher'],
                'calculate_similarity': ['similarity_calculator']
            }
            
            # 检查是否使用了下划线命名约定
            for cls in matcher_classes:
                for method_name in dir(cls):
                    if not method_name.startswith('_') and hasattr(cls, method_name):
                        method = getattr(cls, method_name)
                        if callable(method):
                            # 检查方法名是否使用下划线
                            if '-' in method_name or ' ' in method_name:
                                self.log_issue("命名一致性", f"{cls.__name__}.{method_name} 使用了非标准分隔符")
                                
        except Exception as e:
            self.log_issue("命名一致性", f"检查失败: {e}")
    
    def check_type_system_consistency(self):
        """检查类型系统一致性"""
        print("\n=== 检查类型系统一致性 ===")
        
        try:
            # 检查枚举值的使用一致性
            from string_types.enums import TargetType, MatchType, MatchStrategy
            from string_types.configs import TargetConfig
            from string_types.results import MatchResult
            
            # 检查枚举值命名约定
            target_types = [item for item in dir(TargetType) if not item.startswith('_')]
            match_types = [item for item in dir(MatchType) if not item.startswith('_')]
            match_strategies = [item for item in dir(MatchStrategy) if not item.startswith('_')]
            
            # 检查是否都使用大写命名
            for enum_name, items in [
                ('TargetType', target_types),
                ('MatchType', match_types), 
                ('MatchStrategy', match_strategies)
            ]:
                for item in items:
                    if not item.isupper():
                        self.log_warning("类型一致性", f"{enum_name}.{item} 不符合大写命名约定")
            
            # 检查配置类的默认值一致性
            config = TargetConfig()
            default_values = {
                'fuzzy_threshold': 0.65,
                'case_sensitive': False,
                'required': True
            }
            
            for attr, expected_default in default_values.items():
                if hasattr(config, attr):
                    actual_default = getattr(config, attr)
                    if actual_default != expected_default:
                        self.log_warning("类型一致性", 
                            f"TargetConfig.{attr} 默认值不一致: {actual_default} vs {expected_default}")
                            
        except Exception as e:
            self.log_issue("类型一致性", f"检查失败: {e}")
    
    def check_file_structure_consistency(self):
        """检查文件结构一致性"""
        print("\n=== 检查文件结构一致性 ===")
        
        # 检查是否存在重复的types目录
        types_paths = []
        for root, dirs, files in os.walk(self.module_path):
            if 'types' in dirs:
                types_paths.append(os.path.join(root, 'types'))
            if 'string_types' in dirs:
                types_paths.append(os.path.join(root, 'string_types'))
        
        if len(types_paths) > 1:
            self.log_warning("文件结构", f"发现多个类型目录: {types_paths}")
        
        # 检查是否存在孤立的pyc文件
        for root, dirs, files in os.walk(self.module_path):
            py_files = [f[:-3] for f in files if f.endswith('.py')]
            pyc_files = [f[:-4] for f in files if f.endswith('.pyc')]
            
            for pyc_file in pyc_files:
                if pyc_file not in py_files and not pyc_file.startswith('__'):
                    self.log_warning("文件结构", f"发现孤立的pyc文件: {os.path.join(root, pyc_file + '.pyc')}")
        
        # 检查__init__.py文件的存在性
        required_init_dirs = ['string_types', 'targets', 'results', 'validators', 'tests']
        for dir_name in required_init_dirs:
            dir_path = os.path.join(self.module_path, dir_name)
            init_path = os.path.join(dir_path, '__init__.py')
            if os.path.exists(dir_path) and not os.path.exists(init_path):
                self.log_warning("文件结构", f"目录 {dir_name} 缺少 __init__.py 文件")
    
    def check_factory_consistency(self):
        """检查工厂函数一致性"""
        print("\n=== 检查工厂函数一致性 ===")
        
        try:
            from factory import create_string_matcher, create_name_matcher, MatcherFactory
            
            # 检查create_string_matcher支持的类型
            supported_types = ['exact', 'fuzzy', 'hybrid']
            for matcher_type in supported_types:
                try:
                    matcher = create_string_matcher(matcher_type)
                    expected_class_name = f"{matcher_type.title()}StringMatcher"
                    if matcher.__class__.__name__ != expected_class_name:
                        self.log_warning("工厂一致性", 
                            f"create_string_matcher('{matcher_type}') 返回了 {matcher.__class__.__name__}，期望 {expected_class_name}")
                except Exception as e:
                    self.log_issue("工厂一致性", f"create_string_matcher('{matcher_type}') 失败: {e}")
            
            # 检查create_name_matcher支持的类型
            name_matcher_types = ['exact', 'fuzzy', 'hybrid']
            for matcher_type in name_matcher_types:
                try:
                    matcher = create_name_matcher(matcher_type)
                    expected_class_name = f"{matcher_type.title()}NameMatcher"
                    if matcher.__class__.__name__ != expected_class_name:
                        self.log_warning("工厂一致性",
                            f"create_name_matcher('{matcher_type}') 返回了 {matcher.__class__.__name__}，期望 {expected_class_name}")
                except Exception as e:
                    self.log_issue("工厂一致性", f"create_name_matcher('{matcher_type}') 失败: {e}")
                    
        except Exception as e:
            self.log_issue("工厂一致性", f"检查失败: {e}")
    
    def check_method_return_consistency(self):
        """检查方法返回值一致性"""
        print("\n=== 检查方法返回值一致性 ===")
        
        try:
            from exact_matcher import ExactStringMatcher
            from fuzzy_matcher import FuzzyStringMatcher
            from hybrid_matcher import HybridStringMatcher
            
            test_candidates = ["test", "example", "sample"]
            
            # 测试所有匹配器的返回值类型一致性
            matchers = [
                ExactStringMatcher(),
                FuzzyStringMatcher(),
                HybridStringMatcher()
            ]
            
            for matcher in matchers:
                # 测试match_string返回值
                result = matcher.match_string("test", test_candidates)
                if result is not None and not isinstance(result, str):
                    self.log_issue("返回值一致性", 
                        f"{matcher.__class__.__name__}.match_string 返回值类型不是str或None: {type(result)}")
                
                # 测试match_string_with_score返回值
                result, score = matcher.match_string_with_score("test", test_candidates)
                if result is not None and not isinstance(result, str):
                    self.log_issue("返回值一致性",
                        f"{matcher.__class__.__name__}.match_string_with_score 返回的结果类型不是str或None: {type(result)}")
                if not isinstance(score, (int, float)):
                    self.log_issue("返回值一致性",
                        f"{matcher.__class__.__name__}.match_string_with_score 返回的分数类型不是数值: {type(score)}")
                        
        except Exception as e:
            self.log_issue("返回值一致性", f"检查失败: {e}")
    
    def run_all_checks(self):
        """运行所有一致性检查"""
        print("开始 String Matching 模块一致性检查")
        print("=" * 60)
        
        # 运行所有检查
        self.check_api_consistency()
        self.check_class_inheritance()
        self.check_constructor_consistency()
        self.check_import_consistency()
        self.check_naming_consistency()
        self.check_type_system_consistency()
        self.check_file_structure_consistency()
        self.check_factory_consistency()
        self.check_method_return_consistency()
        
        # 生成报告
        self.generate_report()
    
    def generate_report(self):
        """生成一致性检查报告"""
        total_issues = len(self.issues)
        total_warnings = len(self.warnings)
        
        print("\n" + "=" * 60)
        print("一致性检查报告")
        print("=" * 60)
        print(f"发现问题: {total_issues}")
        print(f"发现警告: {total_warnings}")
        
        if self.issues:
            print("\n严重问题:")
            for i, (category, message) in enumerate(self.issues, 1):
                print(f"{i}. [{category}] {message}")
        
        if self.warnings:
            print("\n警告信息:")
            for i, (category, message) in enumerate(self.warnings, 1):
                print(f"{i}. [{category}] {message}")
        
        if total_issues == 0 and total_warnings == 0:
            print("\n✅ 模块一致性良好，未发现严重问题！")
        elif total_issues == 0:
            print(f"\n⚠️  模块基本一致，有 {total_warnings} 个轻微警告")
        else:
            print(f"\n❌ 发现 {total_issues} 个一致性问题需要修复")
        
        return total_issues == 0


def main():
    """主函数"""
    checker = ConsistencyChecker()
    success = checker.run_all_checks()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
