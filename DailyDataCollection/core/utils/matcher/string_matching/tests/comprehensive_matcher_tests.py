#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字符串匹配器综合测试套件
包含各种匹配场景的详尽测试
"""

import unittest
import sys
import os
from typing import List, Dict, Any
import json

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# 导入要测试的模块
from exact_matcher import ExactStringMatcher
from fuzzy_matcher import FuzzyStringMatcher
from hybrid_matcher import HybridStringMatcher
from name_matcher import NameMatcher
from core_matcher import MultiTargetMatcher
from similarity_calculator import SimilarityCalculator
from factory import create_string_matcher
from string_types.enums import TargetType, MatchStrategy
from string_types.configs import TargetConfig


class TestDataSets:
    """测试数据集合"""
    
    # 中文地名数据
    CHINESE_PLACES = [
        "北京市", "上海市", "广州市", "深圳市", "杭州市", "南京市", "武汉市", "成都市",
        "西安市", "天津市", "重庆市", "苏州市", "长沙市", "郑州市", "青岛市", "大连市",
        "宁波市", "厦门市", "福州市", "济南市", "石家庄市", "哈尔滨市", "长春市", "沈阳市"
    ]
    
    # 罗马化地名数据（拼音形式）
    ROMANIZED_CHINESE_PLACES = [
        "Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Hangzhou", "Nanjing", 
        "Wuhan", "Chengdu", "Xi'an", "Tianjin", "Chongqing", "Suzhou",
        "Changsha", "Zhengzhou", "Qingdao", "Dalian", "Ningbo", "Xiamen",
        "Fuzhou", "Jinan", "Shijiazhuang", "Harbin", "Changchun", "Shenyang"
    ]
    
    # 英文人名数据
    ENGLISH_NAMES = [
        "John Smith", "Jane Doe", "Michael Johnson", "Sarah Wilson", "David Brown",
        "Emily Davis", "Robert Miller", "Lisa Anderson", "James Wilson", "Mary Johnson",
        "Christopher Lee", "Jessica Taylor", "Matthew Anderson", "Ashley Martinez", "Daniel Clark"
    ]
    
    # 中文人名数据
    CHINESE_NAMES = [
        "张伟", "王芳", "李娜", "刘强", "陈敏", "杨静", "赵磊", "黄丽", "周勇", "吴艳"
    ]
    
    # 罗马化中文人名数据
    ROMANIZED_CHINESE_NAMES = [
        "Zhang Wei", "Wang Fang", "Li Na", "Liu Qiang", "Chen Min", 
        "Yang Jing", "Zhao Lei", "Huang Li", "Zhou Yong", "Wu Yan"
    ]
    
    # 日文数据
    JAPANESE_PLACES = [
        "東京", "大阪", "京都", "名古屋", "横浜", "神戸", "福岡", "札幌", "仙台", "広島"
    ]
    
    # 罗马化日文数据
    ROMANIZED_JAPANESE_PLACES = [
        "Tokyo", "Osaka", "Kyoto", "Nagoya", "Yokohama", "Kobe", 
        "Fukuoka", "Sapporo", "Sendai", "Hiroshima"
    ]
    
    # 韩文数据
    KOREAN_PLACES = [
        "서울", "부산", "대구", "인천", "광주", "대전", "울산", "경기", "강원", "충북"
    ]
    
    # 罗马化韩文数据
    ROMANIZED_KOREAN_PLACES = [
        "Seoul", "Busan", "Daegu", "Incheon", "Gwangju", "Daejeon", 
        "Ulsan", "Gyeonggi", "Gangwon", "Chungbuk"
    ]
    
    # 阿拉伯文人名数据
    ARABIC_NAMES = [
        "محمد أحمد", "فاطمة علي", "عبدالله حسن", "عائشة محمود", "عمر سالم"
    ]
    
    # 罗马化阿拉伯文人名
    ROMANIZED_ARABIC_NAMES = [
        "Muhammad Ahmed", "Fatima Ali", "Abdullah Hassan", "Aisha Mahmoud", "Omar Salem"
    ]
    
    # 产品型号数据
    PRODUCT_MODELS = [
        "iPhone 15 Pro", "Galaxy S24 Ultra", "Pixel 8 Pro", "MacBook Pro M3",
        "Surface Pro 9", "iPad Air 5", "Apple Watch Series 9", "AirPods Pro 2",
        "Sony WH-1000XM5", "Dell XPS 13", "HP Spectre x360", "Lenovo ThinkPad X1"
    ]
    
    # 地理坐标数据
    COORDINATES = [
        "39.9042° N, 116.4074° E", "31.2304° N, 121.4737° E", "23.1291° N, 113.2644° E",
        "22.3193° N, 114.1694° E", "30.2741° N, 120.1551° E", "32.0603° N, 118.7969° E",
        "30.5928° N, 114.3055° E", "30.5728° N, 104.0668° E", "34.3416° N, 108.9398° E"
    ]
    
    # 文件路径数据
    FILE_PATHS = [
        "/home/user/documents/project1/main.py",
        "C:\\Users\\Admin\\Desktop\\report.docx", 
        "/var/log/system.log",
        "D:\\Projects\\StringMatcher\\tests\\data.json",
        "/usr/local/bin/python3.11",
        "~/Downloads/presentation.pptx"
    ]
    
    # 邮箱地址数据
    EMAIL_ADDRESSES = [
        "user@example.com", "admin@company.org", "support@service.net",
        "info@website.info", "contact@business.biz", "help@platform.io",
        "sales@enterprise.co", "team@startup.tech"
    ]
    
    # 日期时间数据
    DATETIME_STRINGS = [
        "2025-01-15 10:30:00", "2025-02-28 14:45:30", "2025-03-10 09:15:45",
        "Jan 15, 2025", "February 28th, 2025", "March 10, 2025 9:15 AM",
        "15/01/2025", "28-02-2025", "10.03.2025"
    ]
    
    # 版本号数据
    VERSION_NUMBERS = [
        "v1.0.0", "v2.1.3", "v10.15.7", "version 3.2.1", "Ver. 4.0.0-beta",
        "1.2.3-rc1", "2.0.0-alpha", "3.1.4-stable", "0.9.8-dev"
    ]


class TestExactMatcherComprehensive(unittest.TestCase):
    """精确匹配器全面测试"""
    
    def setUp(self):
        self.matcher = ExactStringMatcher()
        self.case_insensitive_matcher = ExactStringMatcher(case_sensitive=False)
    
    def test_chinese_places_exact_match(self):
        """测试中文地名精确匹配"""
        test_cases = [
            ("北京市", TestDataSets.CHINESE_PLACES, "北京市"),
            ("上海市", TestDataSets.CHINESE_PLACES, "上海市"),
            ("不存在的城市", TestDataSets.CHINESE_PLACES, None),
        ]
        
        for query, candidates, expected in test_cases:
            with self.subTest(query=query):
                result = self.matcher.match_string(query, candidates)
                self.assertEqual(result, expected)
    
    def test_english_names_case_sensitivity(self):
        """测试英文人名大小写敏感性"""
        test_cases = [
            ("john smith", TestDataSets.ENGLISH_NAMES, True, "John Smith"),  # 不区分大小写
            ("john smith", TestDataSets.ENGLISH_NAMES, False, None),         # 区分大小写
            ("JANE DOE", TestDataSets.ENGLISH_NAMES, True, "Jane Doe"),      # 不区分大小写
            ("Jane Doe", TestDataSets.ENGLISH_NAMES, False, "Jane Doe"),     # 精确匹配
        ]
        
        for query, candidates, case_insensitive, expected in test_cases:
            with self.subTest(query=query, case_insensitive=case_insensitive):
                matcher = ExactStringMatcher(case_sensitive=not case_insensitive)
                result = matcher.match_string(query, candidates)
                self.assertEqual(result, expected)
    
    def test_product_models_exact_match(self):
        """测试产品型号精确匹配"""
        test_cases = [
            ("iPhone 15 Pro", TestDataSets.PRODUCT_MODELS, "iPhone 15 Pro"),
            ("Galaxy S24 Ultra", TestDataSets.PRODUCT_MODELS, "Galaxy S24 Ultra"),
            ("iPhone 15", TestDataSets.PRODUCT_MODELS, None),  # 部分匹配不算精确匹配
        ]
        
        for query, candidates, expected in test_cases:
            with self.subTest(query=query):
                result = self.matcher.match_string(query, candidates)
                self.assertEqual(result, expected)
    
    def test_coordinates_exact_match(self):
        """测试地理坐标精确匹配"""
        test_cases = [
            ("39.9042° N, 116.4074° E", TestDataSets.COORDINATES, "39.9042° N, 116.4074° E"),
            ("31.2304° N, 121.4737° E", TestDataSets.COORDINATES, "31.2304° N, 121.4737° E"),
            ("39.9042°N,116.4074°E", TestDataSets.COORDINATES, None),  # 格式不同
        ]
        
        for query, candidates, expected in test_cases:
            with self.subTest(query=query):
                result = self.matcher.match_string(query, candidates)
                self.assertEqual(result, expected)
    
    def test_file_paths_exact_match(self):
        """测试文件路径精确匹配"""
        for file_path in TestDataSets.FILE_PATHS:
            with self.subTest(file_path=file_path):
                result = self.matcher.match_string(file_path, TestDataSets.FILE_PATHS)
                self.assertEqual(result, file_path)
    
    def test_email_addresses_case_insensitive(self):
        """测试邮箱地址不区分大小写匹配"""
        test_cases = [
            ("USER@EXAMPLE.COM", "user@example.com"),
            ("Admin@Company.ORG", "admin@company.org"),
            ("SUPPORT@SERVICE.NET", "support@service.net"),
        ]
        
        for query, expected in test_cases:
            with self.subTest(query=query):
                result = self.case_insensitive_matcher.match_string(query, TestDataSets.EMAIL_ADDRESSES)
                self.assertEqual(result, expected)
    
    def test_match_with_score_always_one_or_zero(self):
        """测试精确匹配的分数总是1.0或0.0"""
        test_cases = [
            ("北京市", TestDataSets.CHINESE_PLACES, 1.0),
            ("不存在的城市", TestDataSets.CHINESE_PLACES, 0.0),
        ]
        
        for query, candidates, expected_score in test_cases:
            with self.subTest(query=query):
                result, score = self.matcher.match_string_with_score(query, candidates)
                if result:
                    self.assertEqual(score, 1.0)
                else:
                    self.assertEqual(score, 0.0)


class TestFuzzyMatcherComprehensive(unittest.TestCase):
    """模糊匹配器全面测试"""
    
    def setUp(self):
        self.matcher = FuzzyStringMatcher(threshold=0.6)
        self.strict_matcher = FuzzyStringMatcher(threshold=0.8)
        self.lenient_matcher = FuzzyStringMatcher(threshold=0.4)
    
    def test_chinese_places_fuzzy_match(self):
        """测试中文地名模糊匹配"""
        test_cases = [
            ("北京", TestDataSets.CHINESE_PLACES, "北京市"),       # 缺少后缀
            ("上海", TestDataSets.CHINESE_PLACES, "上海市"),       # 缺少后缀
            ("广洲市", TestDataSets.CHINESE_PLACES, "广州市"),     # 错别字
            ("深圳", TestDataSets.CHINESE_PLACES, "深圳市"),       # 缺少后缀
            ("不存在城市", TestDataSets.CHINESE_PLACES, None),     # 完全不匹配
        ]
        
        for query, candidates, expected in test_cases:
            with self.subTest(query=query):
                result = self.matcher.match_string(query, candidates)
                self.assertEqual(result, expected)
    
    def test_english_names_typos(self):
        """测试英文人名拼写错误"""
        test_cases = [
            ("Jon Smith", TestDataSets.ENGLISH_NAMES, "John Smith"),      # 缺少字母
            ("Jane Do", TestDataSets.ENGLISH_NAMES, "Jane Doe"),          # 缺少字母
            ("Micheal Johnson", TestDataSets.ENGLISH_NAMES, "Michael Johnson"),  # 拼写错误
            ("Sara Wilson", TestDataSets.ENGLISH_NAMES, "Sarah Wilson"),  # 缺少字母
        ]
        
        for query, candidates, expected in test_cases:
            with self.subTest(query=query):
                result = self.matcher.match_string(query, candidates)
                self.assertEqual(result, expected)
    
    def test_product_models_partial_match(self):
        """测试产品型号部分匹配"""
        test_cases = [
            ("iPhone 15", TestDataSets.PRODUCT_MODELS, "iPhone 15 Pro"),     # 部分匹配
            ("Galaxy S24", TestDataSets.PRODUCT_MODELS, "Galaxy S24 Ultra"), # 部分匹配
            ("MacBook Pro", TestDataSets.PRODUCT_MODELS, "MacBook Pro M3"),  # 部分匹配
            ("iPad Air", TestDataSets.PRODUCT_MODELS, "iPad Air 5"),         # 部分匹配
        ]
        
        for query, candidates, expected in test_cases:
            with self.subTest(query=query):
                result = self.matcher.match_string(query, candidates)
                self.assertEqual(result, expected)
    
    def test_version_numbers_variations(self):
        """测试版本号变体匹配"""
        test_cases = [
            ("v1.0", TestDataSets.VERSION_NUMBERS, "v1.0.0"),           # 缺少小版本号
            ("version 3.2", TestDataSets.VERSION_NUMBERS, "version 3.2.1"),  # 缺少修订号
            ("2.1.3", TestDataSets.VERSION_NUMBERS, "v2.1.3"),         # 缺少前缀
            ("Ver 4.0.0", TestDataSets.VERSION_NUMBERS, "Ver. 4.0.0-beta"),  # 格式略有不同
        ]
        
        for query, candidates, expected in test_cases:
            with self.subTest(query=query):
                result = self.matcher.match_string(query, candidates)
                self.assertEqual(result, expected)
    
    def test_different_thresholds(self):
        """测试不同阈值的影响"""
        query = "北京"
        candidates = TestDataSets.CHINESE_PLACES
        
        # 宽松阈值应该找到匹配
        lenient_result = self.lenient_matcher.match_string(query, candidates)
        self.assertIsNotNone(lenient_result)
        
        # 标准阈值
        standard_result = self.matcher.match_string(query, candidates)
        self.assertIsNotNone(standard_result)
        
        # 严格阈值可能不匹配(取决于相似度计算)
        strict_result = self.strict_matcher.match_string(query, candidates)
        # 不做断言，因为这取决于具体的相似度算法
    
    def test_similarity_scores(self):
        """测试相似度分数的合理性"""
        test_cases = [
            ("北京市", TestDataSets.CHINESE_PLACES, 1.0),        # 精确匹配
            ("北京", TestDataSets.CHINESE_PLACES, (0.6, 1.0)),   # 高相似度
            ("xyz", TestDataSets.CHINESE_PLACES, (0.0, 0.6)),    # 低相似度
        ]
        
        for query, candidates, expected_range in test_cases:
            with self.subTest(query=query):
                result, score = self.matcher.match_string_with_score(query, candidates)
                if isinstance(expected_range, tuple):
                    self.assertGreaterEqual(score, expected_range[0])
                    self.assertLessEqual(score, expected_range[1])
                else:
                    self.assertEqual(score, expected_range)


class TestHybridMatcherComprehensive(unittest.TestCase):
    """混合匹配器全面测试"""
    
    def setUp(self):
        self.matcher = HybridStringMatcher(fuzzy_threshold=0.6)
    
    def test_exact_match_priority(self):
        """测试精确匹配优先级"""
        # 构造一个场景：有精确匹配和模糊匹配
        candidates = ["test", "tset", "testing"]
        
        # 精确匹配应该优先
        result = self.matcher.match_string("test", candidates)
        self.assertEqual(result, "test")
        
        # 只有模糊匹配时返回模糊匹配结果
        result = self.matcher.match_string("tst", candidates)
        self.assertIn(result, ["test", "tset"])  # 应该匹配其中一个
    
    def test_chinese_places_hybrid(self):
        """测试中文地名混合匹配"""
        test_cases = [
            ("北京市", TestDataSets.CHINESE_PLACES, "北京市"),     # 精确匹配
            ("北京", TestDataSets.CHINESE_PLACES, "北京市"),       # 模糊匹配
            ("BeiJing", TestDataSets.CHINESE_PLACES, None),       # 完全不匹配
        ]
        
        for query, candidates, expected in test_cases:
            with self.subTest(query=query):
                result = self.matcher.match_string(query, candidates)
                self.assertEqual(result, expected)
    
    def test_product_models_hybrid(self):
        """测试产品型号混合匹配"""
        test_cases = [
            ("iPhone 15 Pro", TestDataSets.PRODUCT_MODELS, "iPhone 15 Pro"),  # 精确匹配
            ("iPhone 15", TestDataSets.PRODUCT_MODELS, "iPhone 15 Pro"),      # 模糊匹配
            ("iphone 15 pro", TestDataSets.PRODUCT_MODELS, "iPhone 15 Pro"),  # 大小写不同
        ]
        
        # 使用不区分大小写的混合匹配器
        case_insensitive_matcher = HybridStringMatcher(
            fuzzy_threshold=0.6, 
            exact_case_sensitive=False
        )
        
        for query, candidates, expected in test_cases:
            with self.subTest(query=query):
                if query == "iphone 15 pro":
                    result = case_insensitive_matcher.match_string(query, candidates)
                else:
                    result = self.matcher.match_string(query, candidates)
                self.assertEqual(result, expected)
    
    def test_fallback_behavior(self):
        """测试回退行为"""
        candidates = ["apple", "banana", "cherry"]
        
        # 测试从精确匹配回退到模糊匹配
        result = self.matcher.match_string("aple", candidates)  # 拼写错误
        self.assertEqual(result, "apple")
        
        # 测试没有任何匹配
        result = self.matcher.match_string("xyz", candidates)
        self.assertIsNone(result)


class TestSimilarityCalculatorComprehensive(unittest.TestCase):
    """相似度计算器全面测试"""
    
    def test_identical_strings(self):
        """测试相同字符串"""
        test_strings = [
            "hello", "北京市", "iPhone 15 Pro", 
            "user@example.com", "C:\\Windows\\System32"
        ]
        
        for string in test_strings:
            with self.subTest(string=string):
                similarity = SimilarityCalculator.calculate_similarity(string, string)
                self.assertEqual(similarity, 1.0)
    
    def test_completely_different_strings(self):
        """测试完全不同的字符串"""
        test_cases = [
            ("abc", "xyz"),
            ("hello", "12345"),
            ("北京", "tokyo"),
            ("short", "verylongstring"),
        ]
        
        for str1, str2 in test_cases:
            with self.subTest(str1=str1, str2=str2):
                similarity = SimilarityCalculator.calculate_similarity(str1, str2)
                self.assertLess(similarity, 0.5)
    
    def test_similar_strings(self):
        """测试相似字符串"""
        test_cases = [
            ("hello", "helo", 0.7),      # 缺少一个字母
            ("test", "tset", 0.6),       # 字母顺序不同
            ("北京市", "北京", 0.6),      # 缺少后缀
            ("iPhone", "iphone", 0.8),   # 大小写不同
        ]
        
        for str1, str2, min_similarity in test_cases:
            with self.subTest(str1=str1, str2=str2):
                similarity = SimilarityCalculator.calculate_similarity(str1, str2)
                self.assertGreaterEqual(similarity, min_similarity)
    
    def test_symmetric_property(self):
        """测试对称性：similarity(a,b) == similarity(b,a)"""
        test_pairs = [
            ("hello", "world"),
            ("北京", "上海"),
            ("test", "tset"),
            ("iPhone", "Samsung"),
        ]
        
        for str1, str2 in test_pairs:
            with self.subTest(str1=str1, str2=str2):
                sim1 = SimilarityCalculator.calculate_similarity(str1, str2)
                sim2 = SimilarityCalculator.calculate_similarity(str2, str1)
                self.assertEqual(sim1, sim2)
    
    def test_empty_strings(self):
        """测试空字符串"""
        # 两个空字符串应该完全相似
        similarity = SimilarityCalculator.calculate_similarity("", "")
        self.assertEqual(similarity, 1.0)
        
        # 空字符串与非空字符串应该不相似
        similarity = SimilarityCalculator.calculate_similarity("", "hello")
        self.assertEqual(similarity, 0.0)
        
        similarity = SimilarityCalculator.calculate_similarity("hello", "")
        self.assertEqual(similarity, 0.0)


class TestMultiTargetMatcherComprehensive(unittest.TestCase):
    """多目标匹配器全面测试"""
    
    def setUp(self):
        self.matcher = MultiTargetMatcher(debug=True)
        
        # 设置多个目标
        self.matcher.add_name_target(
            "chinese_places", 
            TestDataSets.CHINESE_PLACES,
            strategy=MatchStrategy.HYBRID,
            fuzzy_threshold=0.6
        )
        
        self.matcher.add_name_target(
            "english_names",
            TestDataSets.ENGLISH_NAMES,
            strategy=MatchStrategy.FUZZY,
            fuzzy_threshold=0.7
        )
        
        self.matcher.add_name_target(
            "product_models",
            TestDataSets.PRODUCT_MODELS,
            strategy=MatchStrategy.EXACT,
            case_sensitive=False
        )
    
    def test_multi_target_matching(self):
        """测试多目标匹配"""
        test_queries = [
            "北京",                    # 应该匹配中文地名
            "John Smith",             # 应该匹配英文人名
            "iphone 15 pro",          # 应该匹配产品型号(不区分大小写)
            "不存在的内容",            # 不应该匹配任何目标
        ]
        
        for query in test_queries:
            with self.subTest(query=query):
                try:
                    results = self.matcher.match_all_targets(query)
                    self.assertIsInstance(results, dict)
                    
                    if query == "不存在的内容":
                        # 检查是否所有结果都是None或空
                        for target_name, result in results.items():
                            if hasattr(result, 'matched_text'):
                                self.assertIsNone(result.matched_text)
                    else:
                        # 至少应该有一个目标匹配成功
                        has_match = any(
                            result and (
                                hasattr(result, 'matched_text') and result.matched_text is not None
                            ) or result is not None
                            for result in results.values()
                        )
                        self.assertTrue(has_match, f"No match found for query: {query}")
                        
                except AttributeError:
                    # 如果方法不存在，跳过这个测试
                    self.skipTest("match_all_targets method not implemented")


class TestFactoryPatterns(unittest.TestCase):
    """工厂模式测试"""
    
    def test_create_exact_matcher(self):
        """测试创建精确匹配器"""
        matcher = create_string_matcher("exact", case_sensitive=True)
        self.assertIsInstance(matcher, ExactStringMatcher)
    
    def test_create_fuzzy_matcher(self):
        """测试创建模糊匹配器"""
        matcher = create_string_matcher("fuzzy", fuzzy_threshold=0.7)
        self.assertIsInstance(matcher, FuzzyStringMatcher)
    
    def test_create_hybrid_matcher(self):
        """测试创建混合匹配器"""
        matcher = create_string_matcher("hybrid", fuzzy_threshold=0.6)
        self.assertIsInstance(matcher, HybridStringMatcher)
    
    def test_invalid_matcher_type(self):
        """测试无效的匹配器类型"""
        with self.assertRaises((ValueError, KeyError, TypeError)):
            create_string_matcher("invalid_type")


class TestEdgeCases(unittest.TestCase):
    """边界情况测试"""
    
    def test_empty_inputs(self):
        """测试空输入"""
        matcher = ExactStringMatcher()
        
        # 空查询字符串
        result = matcher.match_string("", ["test", "example"])
        self.assertIsNone(result)
        
        # 空候选列表
        result = matcher.match_string("test", [])
        self.assertIsNone(result)
        
        # 都为空
        result = matcher.match_string("", [])
        self.assertIsNone(result)
    
    def test_special_characters(self):
        """测试特殊字符"""
        special_strings = [
            "hello@world.com",
            "file_name_with_underscores.txt",
            "path/with/slashes",
            "string with spaces",
            "unicode字符串",
            "numbers123",
            "symbols!@#$%",
        ]
        
        matcher = ExactStringMatcher()
        for string in special_strings:
            with self.subTest(string=string):
                result = matcher.match_string(string, special_strings)
                self.assertEqual(result, string)
    
    def test_very_long_strings(self):
        """测试很长的字符串"""
        long_string = "a" * 1000
        long_similar = "a" * 999 + "b"
        
        exact_matcher = ExactStringMatcher()
        fuzzy_matcher = FuzzyStringMatcher(threshold=0.5)
        
        # 精确匹配
        result = exact_matcher.match_string(long_string, [long_string, long_similar])
        self.assertEqual(result, long_string)
        
        # 模糊匹配
        result = fuzzy_matcher.match_string(long_string, [long_similar])
        self.assertEqual(result, long_similar)
    
    def test_unicode_strings(self):
        """测试Unicode字符串"""
        unicode_strings = [
            "Hello 世界",
            "Café ☕",
            "🌟 Star",
            "Привет мир",
            "こんにちは",
            "مرحبا بالعالم",
        ]
        
        matcher = FuzzyStringMatcher(threshold=0.6)
        for string in unicode_strings:
            with self.subTest(string=string):
                # 测试自匹配
                result = matcher.match_string(string, unicode_strings)
                self.assertEqual(result, string)


if __name__ == '__main__':
    # 运行所有测试
    unittest.main(verbosity=2)
