#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门的测试数据集和数据驱动测试
包含各种真实场景的测试数据和对应的测试用例
"""

import unittest
import sys
import os
import json
from typing import List, Dict, Any, Tuple
import random

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# 导入要测试的模块
from exact_matcher import ExactStringMatcher
from fuzzy_matcher import FuzzyStringMatcher
from hybrid_matcher import HybridStringMatcher
from similarity_calculator import SimilarityCalculator


class TestDatasets:
    """测试数据集合类"""
    
    # 多语言人名数据集
    MULTILINGUAL_NAMES = {
        'english': [
            "John Smith", "Mary Johnson", "David Wilson", "Sarah Brown", "Michael Davis",
            "Jennifer Garcia", "Christopher Martinez", "Jessica Rodriguez", "Matthew Anderson", 
            "Amanda Taylor", "Daniel Moore", "Michelle Martin", "Anthony Jackson", "Lisa White"
        ],
        'chinese': [
            "张伟", "王芳", "李娜", "刘强", "陈敏", "杨静", "赵磊", "黄丽", "周勇", "吴艳",
            "徐明", "孙洁", "朱军", "马红", "胡涛", "郭莉", "林峰", "何美", "高鹏", "梁霞"
        ],
        'japanese': [
            "田中太郎", "佐藤花子", "高橋一郎", "山田美咲", "渡辺健太", "伊藤あい",
            "中村大輔", "小林真理", "加藤翔太", "吉田みゆき", "山口隆", "松本舞",
            "井上拓也", "木村恵子", "斎藤雄介", "清水由美子"
        ],
        'korean': [
            "김민수", "이지영", "박준호", "최수진", "정우석", "한소영", "임대한", "송민경",
            "윤재현", "강은지", "조성민", "신혜진", "장동욱", "오수정", "홍진우", "문지은"
        ],
        'arabic': [
            "محمد أحمد", "فاطمة علي", "عبدالله حسن", "عائشة محمود", "عمر سالم",
            "خديجة يوسف", "حسام الدين", "نورا إبراهيم", "طارق عبدالرحمن", "مريم خالد"
        ]
    }
    
    # 科技产品数据集
    TECH_PRODUCTS = {
        'smartphones': [
            "iPhone 15 Pro Max 1TB Natural Titanium",
            "Samsung Galaxy S24 Ultra 1TB Titanium Gray",
            "Google Pixel 8 Pro 512GB Obsidian",
            "OnePlus 12 512GB Flowy Emerald", 
            "Xiaomi 14 Ultra 1TB Photography Kit",
            "Sony Xperia 1 V 512GB Platinum Silver",
            "ASUS ROG Phone 8 Pro 1TB Phantom Black",
            "Nothing Phone (2a) 256GB Milk White"
        ],
        'laptops': [
            "MacBook Pro 16-inch M3 Max 128GB 8TB SSD",
            "Dell XPS 17 Intel i9 64GB 2TB OLED",
            "HP Spectre x360 16 Intel Evo i7 32GB",
            "Lenovo ThinkPad X1 Carbon Gen 11 32GB",
            "ASUS ZenBook Pro 16X OLED i9 64GB",
            "Microsoft Surface Laptop Studio 2 i7",
            "Razer Blade 18 RTX 4090 64GB 4TB",
            "Alienware x17 R2 RTX 4080 32GB"
        ],
        'accessories': [
            "Apple AirPods Pro 2nd Gen USB-C",
            "Sony WH-1000XM5 Wireless Headphones",
            "Bose QuietComfort 45 Bluetooth Headphones",
            "Logitech MX Master 3S Wireless Mouse",
            "Keychron K8 Pro QMK/VIA Wireless",
            "Apple Magic Keyboard with Touch ID",
            "Samsung T7 Portable SSD 4TB",
            "Anker PowerCore 26800 PD 45W"
        ]
    }
    
    # 地理位置数据集
    GEOGRAPHIC_LOCATIONS = {
        'cities_worldwide': [
            "New York, United States", "London, United Kingdom", "Tokyo, Japan",
            "Paris, France", "Sydney, Australia", "Toronto, Canada",
            "Berlin, Germany", "Amsterdam, Netherlands", "Stockholm, Sweden",
            "Copenhagen, Denmark", "Zurich, Switzerland", "Singapore, Singapore"
        ],
        'chinese_cities': [
            "北京市东城区王府井大街", "上海市黄浦区南京东路步行街",
            "广州市天河区珠江新城CBD", "深圳市南山区科技园南区",
            "杭州市西湖区西湖风景名胜区", "南京市玄武区紫金山风景区",
            "武汉市武昌区东湖高新技术开发区", "成都市锦江区春熙路商圈",
            "西安市雁塔区高新技术产业开发区", "重庆市渝中区解放碑商圈"
        ],
        'landmarks': [
            "Eiffel Tower, Paris, France", "Great Wall of China, Beijing",
            "Statue of Liberty, New York, USA", "Big Ben, London, UK",
            "Sydney Opera House, Sydney, Australia", "Taj Mahal, Agra, India",
            "Machu Picchu, Cusco Region, Peru", "Christ the Redeemer, Rio de Janeiro, Brazil",
            "Colosseum, Rome, Italy", "Petra, Ma'an Governorate, Jordan"
        ]
    }
    
    # 文件系统路径数据集
    FILE_SYSTEM_PATHS = {
        'unix_paths': [
            "/home/user/documents/projects/2025/string_matcher/src/main.py",
            "/var/log/applications/web_server_access_20250130.log",
            "/usr/local/bin/python3.11",
            "/opt/software/database/config/production_settings.json",
            "/tmp/backup_files/database_dump_20250130_143025.sql",
            "/etc/nginx/sites-available/default_ssl.conf"
        ],
        'windows_paths': [
            "C:\\Users\\Administrator\\Desktop\\project_files\\StringMatcher.sln",
            "D:\\BackupData\\DatabaseBackups\\FullBackup_20250130_150000.bak",
            "E:\\Development\\Projects\\StringMatching\\Tests\\TestData.json",
            "F:\\Media\\Documents\\Reports\\Annual_Report_2024_Final.pdf",
            "G:\\Software\\IDEs\\VisualStudio2022\\Common7\\IDE\\devenv.exe",
            "H:\\Shared\\TeamDocuments\\Specifications\\API_Documentation_v2.3.docx"
        ],
        'network_paths': [
            "\\\\fileserver\\shared\\documents\\team_projects\\current\\",
            "\\\\backup-server\\daily-backups\\2025\\01\\30\\",
            "\\\\media-server\\video-library\\documentaries\\technology\\",
            "ftp://files.company.com/public/software/releases/v2.1.0/",
            "https://cdn.website.com/assets/images/products/high-res/",
            "sftp://secure-server.domain.com/encrypted/confidential/"
        ]
    }
    
    # 专业术语数据集
    PROFESSIONAL_TERMS = {
        'software_engineering': [
            "Object-Oriented Programming (OOP)", "Test-Driven Development (TDD)",
            "Continuous Integration/Continuous Deployment (CI/CD)", 
            "Model-View-Controller (MVC) Architecture",
            "Application Programming Interface (API)",
            "Software Development Life Cycle (SDLC)",
            "Agile Software Development Methodology",
            "Version Control System (VCS)",
            "Database Management System (DBMS)",
            "Integrated Development Environment (IDE)"
        ],
        'data_science': [
            "Machine Learning Algorithm", "Deep Neural Network",
            "Natural Language Processing (NLP)", "Computer Vision",
            "Big Data Analytics", "Data Mining Techniques",
            "Statistical Analysis Methods", "Predictive Modeling",
            "Feature Engineering Process", "Model Performance Evaluation"
        ],
        'cybersecurity': [
            "Multi-Factor Authentication (MFA)", "Zero Trust Security Model",
            "Intrusion Detection System (IDS)", "Security Information and Event Management (SIEM)",
            "Penetration Testing Methodology", "Vulnerability Assessment",
            "Encryption Key Management", "Digital Certificate Authority",
            "Firewall Configuration Rules", "Incident Response Protocol"
        ]
    }
    
    # 时间和日期格式数据集
    DATETIME_FORMATS = {
        'date_formats': [
            "2025-01-30", "30/01/2025", "01-30-2025", "Jan 30, 2025",
            "January 30th, 2025", "30.01.2025", "2025年1月30日", 
            "30-Jan-2025", "20250130", "30 January 2025"
        ],
        'time_formats': [
            "14:30:45", "2:30:45 PM", "14:30:45.123", "2:30 PM",
            "14:30", "02:30:45", "14h30m45s", "2:30:45.123 PM",
            "143045", "230PM"
        ],
        'datetime_combinations': [
            "2025-01-30T14:30:45Z", "2025-01-30 14:30:45 UTC",
            "Jan 30, 2025 at 2:30 PM EST", "30/01/2025 14:30:45",
            "2025年1月30日 14时30分45秒", "January 30, 2025, 2:30:45 PM",
            "Wed, 30 Jan 2025 14:30:45 GMT", "2025-01-30T14:30:45.123+08:00"
        ]
    }


class TestDataDrivenMatching(unittest.TestCase):
    """数据驱动的匹配测试"""
    
    def setUp(self):
        self.exact_matcher = ExactStringMatcher()
        self.fuzzy_matcher = FuzzyStringMatcher(threshold=0.6)
        self.hybrid_matcher = HybridStringMatcher(fuzzy_threshold=0.6)
    
    def test_multilingual_name_matching(self):
        """测试多语言人名匹配"""
        test_scenarios = [
            # 英文名测试
            {
                'language': 'english',
                'candidates': TestDatasets.MULTILINGUAL_NAMES['english'],
                'test_cases': [
                    ("John Smith", "John Smith"),           # 精确匹配
                    ("john smith", "John Smith"),           # 大小写不同
                    ("Jon Smith", "John Smith"),            # 拼写错误
                    ("J. Smith", "John Smith"),             # 缩写形式
                    ("Smith, John", "John Smith"),          # 格式不同
                ]
            },
            # 中文名测试
            {
                'language': 'chinese', 
                'candidates': TestDatasets.MULTILINGUAL_NAMES['chinese'],
                'test_cases': [
                    ("张伟", "张伟"),                      # 精确匹配
                    ("张 伟", "张伟"),                     # 包含空格
                    ("Zhang Wei", None),                   # 拼音形式（期望不匹配）
                    ("王芳", "王芳"),                      # 精确匹配
                ]
            }
        ]
        
        for scenario in test_scenarios:
            language = scenario['language']
            candidates = scenario['candidates']
            
            for query, expected in scenario['test_cases']:
                with self.subTest(language=language, query=query):
                    # 测试不区分大小写的精确匹配
                    case_insensitive_matcher = ExactStringMatcher(case_sensitive=False)
                    exact_result = case_insensitive_matcher.match_string(query, candidates)
                    
                    # 测试模糊匹配
                    fuzzy_result = self.fuzzy_matcher.match_string(query, candidates)
                    
                    # 测试混合匹配
                    hybrid_result = self.hybrid_matcher.match_string(query, candidates)
                    
                    if expected is not None:
                        # 至少有一个匹配器应该找到正确结果
                        results = [exact_result, fuzzy_result, hybrid_result]
                        self.assertIn(expected, results,
                                    f"None of the matchers found expected result '{expected}' for query '{query}'")
    
    def test_tech_product_matching(self):
        """测试科技产品匹配"""
        all_products = []
        for category, products in TestDatasets.TECH_PRODUCTS.items():
            all_products.extend(products)
        
        test_cases = [
            # 品牌匹配
            ("iPhone", "iPhone 15 Pro Max 1TB Natural Titanium"),
            ("Samsung Galaxy", "Samsung Galaxy S24 Ultra 1TB Titanium Gray"),
            ("Google Pixel", "Google Pixel 8 Pro 512GB Obsidian"),
            ("MacBook", "MacBook Pro 16-inch M3 Max 128GB 8TB SSD"),
            
            # 型号匹配
            ("15 Pro Max", "iPhone 15 Pro Max 1TB Natural Titanium"),
            ("S24 Ultra", "Samsung Galaxy S24 Ultra 1TB Titanium Gray"),
            ("XPS 17", "Dell XPS 17 Intel i9 64GB 2TB OLED"),
            
            # 规格匹配
            ("1TB", None),  # 可能匹配多个产品
            ("512GB", None),  # 可能匹配多个产品
            ("M3 Max", "MacBook Pro 16-inch M3 Max 128GB 8TB SSD"),
            
            # 颜色匹配
            ("Natural Titanium", "iPhone 15 Pro Max 1TB Natural Titanium"),
            ("Titanium Gray", "Samsung Galaxy S24 Ultra 1TB Titanium Gray"),
            ("Obsidian", "Google Pixel 8 Pro 512GB Obsidian"),
        ]
        
        for query, expected in test_cases:
            with self.subTest(query=query):
                fuzzy_result = self.fuzzy_matcher.match_string(query, all_products)
                hybrid_result = self.hybrid_matcher.match_string(query, all_products)
                
                if expected is not None:
                    # 至少有一个匹配器应该找到期望结果
                    self.assertIn(expected, [fuzzy_result, hybrid_result],
                                f"No matcher found expected result '{expected}' for query '{query}'")
                
                # 结果应该是合理的（非None或在候选列表中）
                if fuzzy_result is not None:
                    self.assertIn(fuzzy_result, all_products)
                if hybrid_result is not None:
                    self.assertIn(hybrid_result, all_products)
    
    def test_geographic_location_matching(self):
        """测试地理位置匹配"""
        all_locations = []
        for category, locations in TestDatasets.GEOGRAPHIC_LOCATIONS.items():
            all_locations.extend(locations)
        
        test_cases = [
            # 城市名匹配
            ("New York", "New York, United States"),
            ("London", "London, United Kingdom"),
            ("Tokyo", "Tokyo, Japan"),
            ("北京", "北京市东城区王府井大街"),
            ("上海", "上海市黄浦区南京东路步行街"),
            
            # 地标匹配
            ("Eiffel Tower", "Eiffel Tower, Paris, France"),
            ("Great Wall", "Great Wall of China, Beijing"),
            ("Opera House", "Sydney Opera House, Sydney, Australia"),
            
            # 区域匹配
            ("天河区", "广州市天河区珠江新城CBD"),
            ("南山区", "深圳市南山区科技园南区"),
            ("高新区", None),  # 可能匹配多个地点
        ]
        
        for query, expected in test_cases:
            with self.subTest(query=query):
                fuzzy_result = self.fuzzy_matcher.match_string(query, all_locations)
                hybrid_result = self.hybrid_matcher.match_string(query, all_locations)
                
                if expected is not None:
                    # 检查是否找到期望结果
                    self.assertIn(expected, [fuzzy_result, hybrid_result],
                                f"No matcher found expected result '{expected}' for query '{query}'")
    
    def test_file_path_matching(self):
        """测试文件路径匹配"""
        all_paths = []
        for category, paths in TestDatasets.FILE_SYSTEM_PATHS.items():
            all_paths.extend(paths)
        
        test_cases = [
            # 文件名匹配
            ("main.py", "/home/user/documents/projects/2025/string_matcher/src/main.py"),
            ("StringMatcher.sln", "C:\\Users\\Administrator\\Desktop\\project_files\\StringMatcher.sln"),
            ("TestData.json", "E:\\Development\\Projects\\StringMatching\\Tests\\TestData.json"),
            
            # 目录匹配
            ("documents", None),  # 可能匹配多个路径
            ("Desktop", "C:\\Users\\Administrator\\Desktop\\project_files\\StringMatcher.sln"),
            ("projects", None),   # 可能匹配多个路径
            
            # 扩展名匹配
            (".py", "/home/user/documents/projects/2025/string_matcher/src/main.py"),
            (".log", "/var/log/applications/web_server_access_20250130.log"),
            (".sql", "/tmp/backup_files/database_dump_20250130_143025.sql"),
            
            # 特殊路径匹配
            ("fileserver", "\\\\fileserver\\shared\\documents\\team_projects\\current\\"),
            ("https://", "https://cdn.website.com/assets/images/products/high-res/"),
        ]
        
        for query, expected in test_cases:
            with self.subTest(query=query):
                fuzzy_result = self.fuzzy_matcher.match_string(query, all_paths)
                hybrid_result = self.hybrid_matcher.match_string(query, all_paths)
                
                if expected is not None:
                    self.assertIn(expected, [fuzzy_result, hybrid_result],
                                f"No matcher found expected result '{expected}' for query '{query}'")
    
    def test_professional_terms_matching(self):
        """测试专业术语匹配"""
        all_terms = []
        for category, terms in TestDatasets.PROFESSIONAL_TERMS.items():
            all_terms.extend(terms)
        
        test_cases = [
            # 缩写匹配
            ("OOP", "Object-Oriented Programming (OOP)"),
            ("TDD", "Test-Driven Development (TDD)"),
            ("CI/CD", "Continuous Integration/Continuous Deployment (CI/CD)"),
            ("MVC", "Model-View-Controller (MVC) Architecture"),
            ("API", "Application Programming Interface (API)"),
            
            # 部分术语匹配
            ("Machine Learning", "Machine Learning Algorithm"),
            ("Neural Network", "Deep Neural Network"),
            ("Natural Language", "Natural Language Processing (NLP)"),
            ("Multi-Factor", "Multi-Factor Authentication (MFA)"),
            
            # 相似术语匹配
            ("Deep Learning", "Deep Neural Network"),
            ("Computer Vision", "Computer Vision"),
            ("Penetration Test", "Penetration Testing Methodology"),
        ]
        
        for query, expected in test_cases:
            with self.subTest(query=query):
                fuzzy_result = self.fuzzy_matcher.match_string(query, all_terms)
                hybrid_result = self.hybrid_matcher.match_string(query, all_terms)
                
                if expected is not None:
                    self.assertIn(expected, [fuzzy_result, hybrid_result],
                                f"No matcher found expected result '{expected}' for query '{query}'")
    
    def test_datetime_format_matching(self):
        """测试日期时间格式匹配"""
        all_formats = []
        for category, formats in TestDatasets.DATETIME_FORMATS.items():
            all_formats.extend(formats)
        
        test_cases = [
            # 标准格式匹配
            ("2025-01-30", "2025-01-30"),
            ("30/01/2025", "30/01/2025"),
            ("14:30:45", "14:30:45"),
            
            # 格式变体匹配
            ("2025/01/30", "30/01/2025"),    # 相似格式
            ("Jan 30", "Jan 30, 2025"),      # 部分匹配
            ("14:30", "14:30:45"),           # 部分匹配
            
            # 本地化格式匹配
            ("2025年1月30日", "2025年1月30日"),
            ("January 30", "January 30th, 2025"),
        ]
        
        for query, expected in test_cases:
            with self.subTest(query=query):
                fuzzy_result = self.fuzzy_matcher.match_string(query, all_formats)
                hybrid_result = self.hybrid_matcher.match_string(query, all_formats)
                
                if expected is not None:
                    self.assertIn(expected, [fuzzy_result, hybrid_result],
                                f"No matcher found expected result '{expected}' for query '{query}'")


class TestSimilarityValidation(unittest.TestCase):
    """相似度计算验证测试"""
    
    def test_similarity_consistency_across_datasets(self):
        """测试不同数据集中相似度计算的一致性"""
        test_datasets = [
            TestDatasets.MULTILINGUAL_NAMES['english'],
            TestDatasets.TECH_PRODUCTS['smartphones'], 
            TestDatasets.GEOGRAPHIC_LOCATIONS['cities_worldwide'],
            TestDatasets.PROFESSIONAL_TERMS['software_engineering']
        ]
        
        for dataset in test_datasets:
            dataset_name = str(dataset[:2])  # 使用前两个元素作为标识
            
            with self.subTest(dataset=dataset_name):
                # 测试自相似性
                for item in dataset[:3]:  # 测试前3个项目
                    similarity = SimilarityCalculator.calculate_similarity(item, item)
                    self.assertEqual(similarity, 1.0, f"Self-similarity should be 1.0 for '{item}'")
                
                # 测试对称性
                if len(dataset) >= 2:
                    item1, item2 = dataset[0], dataset[1]
                    sim1 = SimilarityCalculator.calculate_similarity(item1, item2)
                    sim2 = SimilarityCalculator.calculate_similarity(item2, item1)
                    self.assertEqual(sim1, sim2, f"Similarity should be symmetric for '{item1}' and '{item2}'")
                
                # 测试三角不等式（如果可能）
                if len(dataset) >= 3:
                    item1, item2, item3 = dataset[0], dataset[1], dataset[2]
                    sim12 = SimilarityCalculator.calculate_similarity(item1, item2)
                    sim23 = SimilarityCalculator.calculate_similarity(item2, item3)
                    sim13 = SimilarityCalculator.calculate_similarity(item1, item3)
                    
                    # 相似度的"距离"应该满足三角不等式：d(a,c) <= d(a,b) + d(b,c)
                    # 其中 d(x,y) = 1 - similarity(x,y)
                    dist12 = 1 - sim12
                    dist23 = 1 - sim23 
                    dist13 = 1 - sim13
                    
                    self.assertLessEqual(dist13, dist12 + dist23 + 0.1,  # 允许小的数值误差
                                       f"Triangle inequality violated for '{item1}', '{item2}', '{item3}'")


class TestMatcherRobustness(unittest.TestCase):
    """匹配器健壮性测试"""
    
    def test_special_characters_handling(self):
        """测试特殊字符处理"""
        special_char_data = [
            "file@2025-01-30.txt",
            "user_name_with_underscores",
            "path/with/forward/slashes",
            "path\\with\\backward\\slashes",
            "string with spaces",
            "string-with-hyphens",
            "string.with.dots",
            "string,with,commas",
            "string;with;semicolons",
            "string:with:colons",
            "string(with)parentheses",
            "string[with]brackets",
            "string{with}braces",
            "string<with>angle_brackets",
            "string'with'quotes",
            "string\"with\"double_quotes",
            "string+with+plus",
            "string=with=equals",
            "string&with&ampersand",
            "string%with%percent",
            "string#with#hash",
            "string!with!exclamation",
            "string?with?question",
        ]
        
        matchers = [
            self.exact_matcher,
            self.fuzzy_matcher, 
            self.hybrid_matcher
        ]
        
        for matcher in matchers:
            matcher_name = matcher.__class__.__name__
            
            for special_string in special_char_data:
                with self.subTest(matcher=matcher_name, string=special_string):
                    # 测试自匹配
                    result = matcher.match_string(special_string, special_char_data)
                    
                    if isinstance(matcher, ExactStringMatcher):
                        self.assertEqual(result, special_string)
                    else:
                        # 模糊匹配和混合匹配至少应该找到自己
                        self.assertIsNotNone(result)
    
    def test_unicode_handling(self):
        """测试Unicode字符处理"""
        unicode_data = [
            "Hello 世界",                    # 英文+中文
            "Café ☕ Coffee",                # 特殊字符+Emoji
            "Привет мир",                   # 俄文
            "مرحبا بالعالم",                # 阿拉伯文
            "こんにちは世界",                # 日文
            "안녕하세요 세계",               # 韩文
            "🌟 Star ⭐ Light",            # Emoji
            "Math: π ≈ 3.14159",           # 数学符号
            "Currency: € $ ¥ £",           # 货币符号
            "Arrows: ← → ↑ ↓",             # 箭头符号
        ]
        
        matchers = [
            ExactStringMatcher(case_sensitive=False),
            FuzzyStringMatcher(threshold=0.5),
            HybridStringMatcher(fuzzy_threshold=0.5)
        ]
        
        for matcher in matchers:
            matcher_name = matcher.__class__.__name__
            
            for unicode_string in unicode_data:
                with self.subTest(matcher=matcher_name, string=unicode_string):
                    try:
                        # 测试Unicode字符串的自匹配
                        result = matcher.match_string(unicode_string, unicode_data)
                        
                        # 应该至少找到自己或相似的字符串
                        self.assertIsNotNone(result, f"Failed to match Unicode string: {unicode_string}")
                        
                    except Exception as e:
                        self.fail(f"{matcher_name} failed with Unicode string '{unicode_string}': {e}")
    
    def test_extreme_length_strings(self):
        """测试极端长度字符串"""
        # 很短的字符串
        short_strings = ["a", "ab", "abc", "中", "🌟"]
        
        # 很长的字符串
        long_strings = [
            "a" * 1000,
            "This is a very long string that contains many words and should test the performance and correctness of string matching algorithms when dealing with lengthy text inputs that might occur in real-world applications." * 10,
            "中文很长的字符串测试" * 100,
        ]
        
        test_cases = [
            ("Short strings", short_strings),
            ("Long strings", long_strings)
        ]
        
        matchers = [
            ExactStringMatcher(),
            FuzzyStringMatcher(threshold=0.8),  # 使用较高阈值提高性能
        ]
        
        for test_name, test_strings in test_cases:
            for matcher in matchers:
                matcher_name = matcher.__class__.__name__
                
                with self.subTest(test=test_name, matcher=matcher_name):
                    for test_string in test_strings:
                        try:
                            # 测试自匹配
                            result = matcher.match_string(test_string, test_strings)
                            
                            if isinstance(matcher, ExactStringMatcher):
                                self.assertEqual(result, test_string)
                            else:
                                # 模糊匹配应该至少找到自己或相似字符串
                                self.assertIsNotNone(result)
                                
                        except Exception as e:
                            self.fail(f"{matcher_name} failed with {test_name.lower()} string: {e}")


if __name__ == '__main__':
    print("Running Data-Driven String Matcher Tests...")
    print("=" * 60)
    
    unittest.main(verbosity=2)
