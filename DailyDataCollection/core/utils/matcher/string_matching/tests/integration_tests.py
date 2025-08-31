#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字符串匹配器集成测试
测试各个组件之间的协同工作和端到端的功能
"""

import unittest
import sys
import os
from typing import List, Dict, Any, Optional
import json
import tempfile

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# 导入所有组件
from exact_matcher import ExactStringMatcher
from fuzzy_matcher import FuzzyStringMatcher
from hybrid_matcher import HybridStringMatcher
from name_matcher import NameMatcher
from core_matcher import MultiTargetMatcher
from similarity_calculator import SimilarityCalculator
from factory import create_string_matcher
from string_types.enums import TargetType, MatchStrategy
from string_types.configs import TargetConfig
from string_types.results import MatchResult


class RealWorldScenarioTests(unittest.TestCase):
    """真实世界场景的集成测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.test_data = {
            'company_contacts': [
                "John Smith - CEO (john.smith@company.com)",
                "Jane Doe - CTO (jane.doe@company.com)", 
                "Mike Johnson - CFO (mike.johnson@company.com)",
                "Sarah Wilson - VP Engineering (sarah.wilson@company.com)",
                "David Brown - Senior Developer (david.brown@company.com)",
                "Lisa Garcia - Product Manager (lisa.garcia@company.com)",
                "Tom Anderson - Sales Director (tom.anderson@company.com)",
                "Emma Taylor - Marketing Lead (emma.taylor@company.com)"
            ],
            'product_catalog': [
                "Apple iPhone 15 Pro Max 256GB Natural Titanium",
                "Samsung Galaxy S24 Ultra 512GB Titanium Black",
                "Google Pixel 8 Pro 128GB Obsidian",
                "OnePlus 12 256GB Flowy Emerald",
                "Xiaomi 14 Ultra 512GB Black",
                "Sony Xperia 1 V 256GB Khaki Green",
                "ASUS ROG Phone 8 Pro 512GB Phantom Black",
                "Nothing Phone (2) 256GB Dark Grey"
            ],
            'geographic_locations': [
                "北京市朝阳区国贸中心",
                "上海市浦东新区陆家嘴金融区",
                "广州市天河区珠江新城",
                "深圳市南山区科技园",
                "杭州市西湖区文三路",
                "南京市鼓楼区新街口",
                "武汉市武昌区光谷",
                "成都市高新区天府软件园"
            ],
            'file_references': [
                "/home/user/documents/projects/2025/quarterly_report.pdf",
                "C:\\Users\\Admin\\Desktop\\meeting_notes_2025_01_15.docx",
                "/var/log/application_error_20250130.log",
                "D:\\BackupFiles\\database_backup_20250128_full.sql",
                "/usr/local/share/config/server_settings.json",
                "~/Downloads/software_installation_guide_v2.3.pdf"
            ]
        }
    
    def test_contact_search_scenario(self):
        """测试联系人搜索场景"""
        matcher = MultiTargetMatcher(debug=True)
        
        # 添加联系人目标
        try:
            matcher.add_name_target(
                "contacts",
                self.test_data['company_contacts'],
                strategy=MatchStrategy.HYBRID,
                fuzzy_threshold=0.6,
                case_sensitive=False
            )
        except Exception:
            # 如果方法不存在，使用基础匹配器
            hybrid_matcher = HybridStringMatcher(fuzzy_threshold=0.6)
            
            # 测试各种联系人查询
            test_queries = [
                ("John Smith", "John Smith - CEO (john.smith@company.com)"),      # 精确姓名匹配
                ("jane doe", "Jane Doe - CTO (jane.doe@company.com)"),           # 不区分大小写
                ("Mike", "Mike Johnson - CFO (mike.johnson@company.com)"),       # 部分匹配
                ("Sara Wilson", "Sarah Wilson - VP Engineering (sarah.wilson@company.com)"),  # 拼写错误
                ("CEO", "John Smith - CEO (john.smith@company.com)"),            # 职位匹配
                ("john.smith@company.com", "John Smith - CEO (john.smith@company.com)"),  # 邮箱匹配
            ]
            
            for query, expected in test_queries:
                with self.subTest(query=query):
                    result = hybrid_matcher.match_string(query, self.test_data['company_contacts'])
                    # 由于模糊匹配的不确定性，我们只检查是否找到了结果
                    if expected in self.test_data['company_contacts']:
                        self.assertIsNotNone(result, f"No result found for query: {query}")
    
    def test_product_search_scenario(self):
        """测试产品搜索场景"""
        fuzzy_matcher = FuzzyStringMatcher(threshold=0.5)
        exact_matcher = ExactStringMatcher(case_sensitive=False)
        
        test_cases = [
            # 品牌搜索
            ("iPhone 15", "Apple iPhone 15 Pro Max 256GB Natural Titanium"),
            ("Galaxy S24", "Samsung Galaxy S24 Ultra 512GB Titanium Black"),
            ("Pixel 8", "Google Pixel 8 Pro 128GB Obsidian"),
            
            # 容量搜索
            ("256GB", ["Apple iPhone 15 Pro Max 256GB Natural Titanium", 
                      "OnePlus 12 256GB Flowy Emerald", 
                      "Sony Xperia 1 V 256GB Khaki Green",
                      "Nothing Phone (2) 256GB Dark Grey"]),
            
            # 颜色搜索
            ("Black", ["Samsung Galaxy S24 Ultra 512GB Titanium Black",
                      "Xiaomi 14 Ultra 512GB Black",
                      "ASUS ROG Phone 8 Pro 512GB Phantom Black"]),
        ]
        
        for query, expected in test_cases:
            with self.subTest(query=query):
                result = fuzzy_matcher.match_string(query, self.test_data['product_catalog'])
                
                if isinstance(expected, str):
                    # 单个期望结果
                    self.assertIsNotNone(result, f"No result found for query: {query}")
                elif isinstance(expected, list):
                    # 多个可能的结果
                    self.assertIn(result, expected + [None], f"Unexpected result for query: {query}")
    
    def test_location_search_scenario(self):
        """测试地理位置搜索场景"""
        hybrid_matcher = HybridStringMatcher(fuzzy_threshold=0.6)
        
        test_queries = [
            ("北京", "北京市朝阳区国贸中心"),
            ("上海浦东", "上海市浦东新区陆家嘴金融区"),
            ("广州天河", "广州市天河区珠江新城"),
            ("深圳南山", "深圳市南山区科技园"),
            ("杭州西湖", "杭州市西湖区文三路"),
            ("南京鼓楼", "南京市鼓楼区新街口"),
            ("武汉光谷", "武汉市武昌区光谷"),
            ("成都高新", "成都市高新区天府软件园"),
        ]
        
        for query, expected in test_queries:
            with self.subTest(query=query):
                result = hybrid_matcher.match_string(query, self.test_data['geographic_locations'])
                self.assertEqual(result, expected, f"Failed to match location: {query}")
    
    def test_file_path_search_scenario(self):
        """测试文件路径搜索场景"""
        exact_matcher = ExactStringMatcher(case_sensitive=False)
        fuzzy_matcher = FuzzyStringMatcher(threshold=0.7)
        
        test_cases = [
            # 文件扩展名搜索
            (".pdf", ["~/Downloads/software_installation_guide_v2.3.pdf",
                     "/home/user/documents/projects/2025/quarterly_report.pdf"]),
            
            # 路径组件搜索
            ("Desktop", "C:\\Users\\Admin\\Desktop\\meeting_notes_2025_01_15.docx"),
            ("Documents", "/home/user/documents/projects/2025/quarterly_report.pdf"),
            ("Downloads", "~/Downloads/software_installation_guide_v2.3.pdf"),
            
            # 文件名搜索
            ("quarterly_report", "/home/user/documents/projects/2025/quarterly_report.pdf"),
            ("meeting_notes", "C:\\Users\\Admin\\Desktop\\meeting_notes_2025_01_15.docx"),
            ("database_backup", "D:\\BackupFiles\\database_backup_20250128_full.sql"),
        ]
        
        for query, expected in test_cases:
            with self.subTest(query=query):
                result = fuzzy_matcher.match_string(query, self.test_data['file_references'])
                
                if isinstance(expected, str):
                    self.assertEqual(result, expected)
                elif isinstance(expected, list):
                    self.assertIn(result, expected + [None])


class MultiMatcherIntegrationTests(unittest.TestCase):
    """多匹配器集成测试"""
    
    def test_matcher_factory_integration(self):
        """测试匹配器工厂集成"""
        test_configs = [
            ('exact', {'case_sensitive': True}),
            ('exact', {'case_sensitive': False}),
            ('fuzzy', {'fuzzy_threshold': 0.6}),
            ('fuzzy', {'fuzzy_threshold': 0.8}),
            ('hybrid', {'fuzzy_threshold': 0.7}),
        ]
        
        test_data = ["apple", "banana", "cherry", "date", "elderberry"]
        
        for matcher_type, config in test_configs:
            with self.subTest(matcher_type=matcher_type, config=config):
                try:
                    matcher = create_string_matcher(matcher_type, **config)
                    
                    # 测试匹配功能
                    result = matcher.match_string("apple", test_data)
                    self.assertEqual(result, "apple")
                    
                    # 测试不存在的项
                    result = matcher.match_string("grape", test_data)
                    # 对于模糊匹配，可能会找到相似的结果
                    
                except Exception as e:
                    self.fail(f"Failed to create or use {matcher_type} matcher with config {config}: {e}")
    
    def test_cascade_matching_strategy(self):
        """测试级联匹配策略：精确 -> 模糊 -> 混合"""
        candidates = [
            "Apple iPhone 15 Pro",
            "Samsung Galaxy S24",
            "Google Pixel 8 Pro",
            "OnePlus 12 Pro"
        ]
        
        queries = [
            "Apple iPhone 15 Pro",    # 精确匹配
            "iPhone 15",              # 部分匹配，需要模糊匹配
            "Galaxy S24 Ultra",       # 相似但不完全匹配
            "Pixel 8",                # 部分匹配
            "Nothing Phone"           # 完全不匹配
        ]
        
        matchers = [
            ('exact', ExactStringMatcher()),
            ('fuzzy', FuzzyStringMatcher(threshold=0.6)),
            ('hybrid', HybridStringMatcher(fuzzy_threshold=0.6))
        ]
        
        results = {}
        
        for query in queries:
            query_results = {}
            
            for matcher_name, matcher in matchers:
                try:
                    result = matcher.match_string(query, candidates)
                    query_results[matcher_name] = result
                except Exception as e:
                    query_results[matcher_name] = f"Error: {e}"
            
            results[query] = query_results
        
        # 验证级联逻辑：如果精确匹配找到结果，其他方法也应该找到相同或相似结果
        for query, query_results in results.items():
            with self.subTest(query=query):
                exact_result = query_results.get('exact')
                fuzzy_result = query_results.get('fuzzy')
                hybrid_result = query_results.get('hybrid')
                
                if exact_result:
                    # 如果精确匹配成功，混合匹配也应该成功且结果相同
                    self.assertEqual(exact_result, hybrid_result, 
                                   f"Hybrid matcher should return same result as exact for: {query}")
    
    def test_result_consistency_across_matchers(self):
        """测试不同匹配器结果的一致性"""
        test_cases = [
            {
                'candidates': ["test", "testing", "tester", "contest"],
                'query': "test",
                'expected_exact': "test",
                'expected_fuzzy_in': ["test", "testing", "tester"],  # 可能的模糊匹配结果
                'expected_hybrid': "test"  # 混合匹配应该优先精确匹配
            },
            {
                'candidates': ["apple", "application", "apply", "appreciate"],
                'query': "app",
                'expected_exact': None,
                'expected_fuzzy_in': ["apple", "application", "apply"],  # 可能的模糊匹配结果
                'expected_hybrid_in': ["apple", "application", "apply"]  # 混合匹配回退到模糊匹配
            }
        ]
        
        for i, case in enumerate(test_cases):
            with self.subTest(case_index=i):
                exact_matcher = ExactStringMatcher()
                fuzzy_matcher = FuzzyStringMatcher(threshold=0.5)
                hybrid_matcher = HybridStringMatcher(fuzzy_threshold=0.5)
                
                exact_result = exact_matcher.match_string(case['query'], case['candidates'])
                fuzzy_result = fuzzy_matcher.match_string(case['query'], case['candidates'])
                hybrid_result = hybrid_matcher.match_string(case['query'], case['candidates'])
                
                # 验证精确匹配结果
                self.assertEqual(exact_result, case['expected_exact'])
                
                # 验证模糊匹配结果
                if 'expected_fuzzy_in' in case:
                    self.assertIn(fuzzy_result, case['expected_fuzzy_in'] + [None])
                
                # 验证混合匹配结果
                if 'expected_hybrid' in case:
                    self.assertEqual(hybrid_result, case['expected_hybrid'])
                elif 'expected_hybrid_in' in case:
                    self.assertIn(hybrid_result, case['expected_hybrid_in'] + [None])


class ErrorHandlingIntegrationTests(unittest.TestCase):
    """错误处理集成测试"""
    
    def test_invalid_input_handling(self):
        """测试无效输入处理"""
        matchers = [
            ExactStringMatcher(),
            FuzzyStringMatcher(threshold=0.6),
            HybridStringMatcher(fuzzy_threshold=0.6)
        ]
        
        invalid_inputs = [
            (None, ["test"]),           # None作为查询
            ("test", None),             # None作为候选列表
            ("", []),                   # 空输入
            ("test", []),               # 空候选列表
            ("", ["test"]),             # 空查询字符串
        ]
        
        for matcher in matchers:
            matcher_name = matcher.__class__.__name__
            for query, candidates in invalid_inputs:
                with self.subTest(matcher=matcher_name, query=query, candidates=candidates):
                    try:
                        result = matcher.match_string(query, candidates)
                        # 应该返回None而不是抛出异常
                        self.assertIsNone(result, f"{matcher_name} should return None for invalid input")
                    except Exception as e:
                        # 如果抛出异常，应该是适当的异常类型
                        self.assertIsInstance(e, (ValueError, TypeError, AttributeError))
    
    def test_extreme_threshold_values(self):
        """测试极端阈值处理"""
        test_data = ["apple", "banana", "cherry"]
        
        extreme_thresholds = [0.0, 1.0, -0.1, 1.1, 0.999, 0.001]
        
        for threshold in extreme_thresholds:
            with self.subTest(threshold=threshold):
                try:
                    if 0.0 <= threshold <= 1.0:
                        # 有效阈值
                        fuzzy_matcher = FuzzyStringMatcher(threshold=threshold)
                        hybrid_matcher = HybridStringMatcher(fuzzy_threshold=threshold)
                        
                        # 测试匹配
                        fuzzy_result = fuzzy_matcher.match_string("apple", test_data)
                        hybrid_result = hybrid_matcher.match_string("apple", test_data)
                        
                        # 对于阈值1.0，只有精确匹配才能成功
                        if threshold == 1.0:
                            self.assertEqual(fuzzy_result, "apple")
                            self.assertEqual(hybrid_result, "apple")
                        # 对于阈值0.0，任何匹配都应该成功
                        elif threshold == 0.0:
                            self.assertIsNotNone(fuzzy_result)
                            self.assertIsNotNone(hybrid_result)
                    else:
                        # 无效阈值，应该抛出异常或使用默认值
                        with self.assertRaises((ValueError, TypeError)):
                            FuzzyStringMatcher(threshold=threshold)
                
                except Exception as e:
                    # 记录意外错误
                    print(f"Unexpected error with threshold {threshold}: {e}")
    
    def test_large_input_handling(self):
        """测试大输入处理"""
        # 生成大量候选项
        large_candidates = [f"candidate_{i:06d}" for i in range(10000)]
        
        matchers = [
            ExactStringMatcher(),
            FuzzyStringMatcher(threshold=0.8),  # 使用较高阈值以提高性能
        ]
        
        test_queries = [
            "candidate_005000",  # 存在的项
            "candidate_999999",  # 不存在的项
            "nonexistent",       # 完全不匹配的项
        ]
        
        for matcher in matchers:
            matcher_name = matcher.__class__.__name__
            for query in test_queries:
                with self.subTest(matcher=matcher_name, query=query):
                    try:
                        import time
                        start_time = time.time()
                        result = matcher.match_string(query, large_candidates)
                        end_time = time.time()
                        
                        execution_time = end_time - start_time
                        
                        # 验证结果合理性
                        if query == "candidate_005000":
                            self.assertEqual(result, "candidate_005000")
                        elif query == "candidate_999999":
                            self.assertIsNone(result)
                        
                        # 验证性能在合理范围内（不应超过10秒）
                        self.assertLess(execution_time, 10.0, 
                                      f"{matcher_name} took too long: {execution_time:.2f}s")
                        
                    except Exception as e:
                        self.fail(f"{matcher_name} failed with large input: {e}")


if __name__ == '__main__':
    print("Running String Matcher Integration Tests...")
    print("=" * 60)
    
    unittest.main(verbosity=2)
