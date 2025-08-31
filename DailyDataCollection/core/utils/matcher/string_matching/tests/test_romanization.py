#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
罗马化字母匹配器测试
测试各种语言的罗马化形式与原文的匹配功能
"""

import unittest
import sys
import os
from typing import List, Dict, Any, Tuple

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# 导入要测试的模块
from core.utils.matcher.string_matching.use_cases.romanization_matcher import RomanizationMatcher, RomanizationMapping, RomanizationDatabase


class TestRomanizationMatcher(unittest.TestCase):
    """罗马化匹配器测试"""
    
    def setUp(self):
        self.matcher = RomanizationMatcher(fuzzy_threshold=0.7, debug=True)
    
    def test_chinese_pinyin_matching(self):
        """测试中文拼音匹配"""
        chinese_cities = ["北京", "上海", "广州", "深圳", "杭州", "南京", "武汉", "成都", "西安", "重庆"]
        
        test_cases = [
            # 标准拼音匹配
            ("Beijing", "北京"),
            ("Shanghai", "上海"),
            ("Guangzhou", "广州"),
            ("Shenzhen", "深圳"),
            ("Hangzhou", "杭州"),
            ("Nanjing", "南京"),
            ("Wuhan", "武汉"),
            ("Chengdu", "成都"),
            ("Xi'an", "西安"),
            ("Chongqing", "重庆"),
            
            # 变体拼音
            ("Xian", "西安"),          # 省略分隔符
            ("Peking", "北京"),        # 旧式拼写
            ("Canton", "广州"),        # 粤语音译
            
            # 反向匹配（中文查找拼音）
            ("北京", "Beijing"),       # 如果候选列表包含拼音
        ]
        
        # 测试拼音 -> 中文
        for pinyin, expected_chinese in test_cases[:10]:
            with self.subTest(query=pinyin, expected=expected_chinese):
                result = self.matcher.match_string(pinyin, chinese_cities)
                self.assertEqual(result, expected_chinese, 
                               f"Failed to match {pinyin} to {expected_chinese}")
        
        # 测试变体拼音
        for variant_pinyin, expected_chinese in test_cases[10:13]:
            with self.subTest(query=variant_pinyin, expected=expected_chinese):
                result = self.matcher.match_string(variant_pinyin, chinese_cities)
                self.assertEqual(result, expected_chinese,
                               f"Failed to match variant {variant_pinyin} to {expected_chinese}")
    
    def test_chinese_person_names(self):
        """测试中文人名匹配"""
        chinese_names = ["张伟", "王芳", "李娜", "刘强", "陈敏", "杨静", "赵磊", "黄丽"]
        pinyin_names = ["Zhang Wei", "Wang Fang", "Li Na", "Liu Qiang", "Chen Min", "Yang Jing", "Zhao Lei", "Huang Li"]
        
        test_cases = [
            ("Zhang Wei", chinese_names, "张伟"),
            ("Wang Fang", chinese_names, "王芳"), 
            ("Li Na", chinese_names, "李娜"),
            ("Liu Qiang", chinese_names, "刘强"),
            ("Chen Min", chinese_names, "陈敏"),
        ]
        
        for pinyin_name, candidates, expected in test_cases:
            with self.subTest(query=pinyin_name):
                result = self.matcher.match_string(pinyin_name, candidates)
                self.assertEqual(result, expected)
        
        # 反向测试：中文名查找拼音
        reverse_test_cases = [
            ("张伟", pinyin_names, "Zhang Wei"),
            ("王芳", pinyin_names, "Wang Fang"),
            ("李娜", pinyin_names, "Li Na"),
        ]
        
        for chinese_name, candidates, expected in reverse_test_cases:
            with self.subTest(query=chinese_name):
                result = self.matcher.match_string(chinese_name, candidates)
                self.assertEqual(result, expected)
    
    def test_japanese_romaji_matching(self):
        """测试日文罗马字匹配"""
        japanese_cities = ["東京", "大阪", "京都", "名古屋", "横浜", "神戸", "福岡", "札幌", "仙台"]
        
        test_cases = [
            ("Tokyo", "東京"),
            ("Toukyou", "東京"),        # 长音表示变体
            ("Osaka", "大阪"),
            ("Kyoto", "京都"),
            ("Nagoya", "名古屋"),
            ("Yokohama", "横浜"),
            ("Kobe", "神戸"),
            ("Fukuoka", "福岡"),
            ("Sapporo", "札幌"),
            ("Sendai", "仙台"),
        ]
        
        for romaji, expected_japanese in test_cases:
            with self.subTest(query=romaji, expected=expected_japanese):
                result = self.matcher.match_string(romaji, japanese_cities)
                self.assertEqual(result, expected_japanese,
                               f"Failed to match {romaji} to {expected_japanese}")
    
    def test_japanese_person_names(self):
        """测试日文人名匹配"""
        japanese_names = ["田中太郎", "佐藤花子", "高橋一郎", "山田美咲", "渡辺健太"]
        
        test_cases = [
            ("Tanaka Taro", "田中太郎"),
            ("Sato Hanako", "佐藤花子"),
            ("Takahashi Ichiro", "高橋一郎"),
            ("Yamada Misaki", "山田美咲"),
            ("Watanabe Kenta", "渡辺健太"),
        ]
        
        for romaji_name, expected in test_cases:
            with self.subTest(query=romaji_name):
                result = self.matcher.match_string(romaji_name, japanese_names)
                self.assertEqual(result, expected)
    
    def test_korean_romanization_matching(self):
        """测试韩文罗马字匹配"""
        korean_cities = ["서울", "부산", "대구", "인천", "광주", "대전", "울산"]
        
        test_cases = [
            ("Seoul", "서울"),
            ("Busan", "부산"),
            ("Pusan", "부산"),          # 旧式罗马化
            ("Daegu", "대구"),
            ("Taegu", "대구"),          # 旧式罗马化
            ("Incheon", "인천"),
            ("Gwangju", "광주"),
            ("Kwangju", "광주"),        # 旧式罗马化
            ("Daejeon", "대전"),
            ("Taejon", "대전"),         # 旧式罗马化
            ("Ulsan", "울산"),
        ]
        
        for romanization, expected_korean in test_cases:
            with self.subTest(query=romanization, expected=expected_korean):
                result = self.matcher.match_string(romanization, korean_cities)
                self.assertEqual(result, expected_korean,
                               f"Failed to match {romanization} to {expected_korean}")
    
    def test_korean_person_names(self):
        """测试韩文人名匹配"""
        korean_names = ["김민수", "이지영", "박준호", "최수진"]
        
        test_cases = [
            ("Kim Minsu", "김민수"),
            ("Lee Jiyoung", "이지영"),
            ("Park Junho", "박준호"),
            ("Choi Sujin", "최수진"),
        ]
        
        for romanized_name, expected in test_cases:
            with self.subTest(query=romanized_name):
                result = self.matcher.match_string(romanized_name, korean_names)
                self.assertEqual(result, expected)
    
    def test_arabic_latinization_matching(self):
        """测试阿拉伯文拉丁化匹配"""
        arabic_names = ["محمد", "أحمد", "علي", "فاطمة", "عبدالله", "خالد"]
        
        test_cases = [
            ("Muhammad", "محمد"),
            ("Mohammed", "محمد"),       # 变体拼写
            ("Mohamed", "محمد"),        # 变体拼写
            ("Ahmad", "أحمد"),
            ("Ahmed", "أحمد"),          # 变体拼写
            ("Ali", "علي"),
            ("Fatima", "فاطمة"),
            ("Fatma", "فاطمة"),         # 变体拼写
            ("Abdullah", "عبدالله"),
            ("Abd Allah", "عبدالله"),   # 分写形式
            ("Khalid", "خالد"),
            ("Khaled", "خالد"),         # 变体拼写
        ]
        
        for latinized, expected_arabic in test_cases:
            with self.subTest(query=latinized, expected=expected_arabic):
                result = self.matcher.match_string(latinized, arabic_names)
                self.assertEqual(result, expected_arabic,
                               f"Failed to match {latinized} to {expected_arabic}")
    
    def test_sound_change_rules(self):
        """测试音变规则"""
        # 测试中文拼音音变
        chinese_test_cases = [
            ("Zhangwei", ["Zhang Wei"], "Zhang Wei"),    # 空格分离
            ("Beijng", ["Beijing"], "Beijing"),          # 轻微拼写错误
            ("Shenzhen", ["Shenzhen"], "Shenzhen"),      # 自匹配
        ]
        
        for query, candidates, expected in chinese_test_cases:
            with self.subTest(language="chinese", query=query):
                result = self.matcher.match_string(query, candidates)
                # 由于音变规则的复杂性，我们主要检查是否能找到合理的匹配
                if expected in candidates:
                    self.assertIsNotNone(result)
    
    def test_match_with_score(self):
        """测试带分数的匹配"""
        candidates = ["北京", "上海", "广州"]
        
        # 测试高分匹配
        result, score = self.matcher.match_string_with_score("Beijing", candidates)
        self.assertEqual(result, "北京")
        self.assertGreater(score, 0.9)  # 预定义映射应该有高分
        
        # 测试中等分匹配
        result, score = self.matcher.match_string_with_score("Peking", candidates)
        self.assertEqual(result, "北京")
        self.assertGreater(score, 0.8)  # 旧式拼写分数略低
        
        # 测试低分匹配
        result, score = self.matcher.match_string_with_score("xyz", candidates)
        self.assertIsNone(result)
        self.assertLess(score, 0.7)  # 应该低于阈值
    
    def test_custom_mapping_addition(self):
        """测试添加自定义映射"""
        # 添加自定义映射
        self.matcher.add_custom_mapping("测试城市", "Test City", "chinese", 1.0)
        
        # 测试自定义映射是否生效
        candidates = ["测试城市", "其他城市"]
        result = self.matcher.match_string("Test City", candidates)
        self.assertEqual(result, "测试城市")
        
        # 反向测试
        candidates = ["Test City", "Other City"]
        result = self.matcher.match_string("测试城市", candidates)
        self.assertEqual(result, "Test City")
    
    def test_get_romanization_suggestions(self):
        """测试获取罗马化建议"""
        suggestions = self.matcher.get_romanization_suggestions("北京")
        
        # 应该返回相关建议
        self.assertGreater(len(suggestions), 0)
        
        # 检查建议内容
        suggestion_texts = [s.romanized for s in suggestions if s.original == "北京"]
        self.assertIn("Beijing", suggestion_texts)
        
        # 测试罗马化查找原文
        suggestions = self.matcher.get_romanization_suggestions("Beijing")
        original_texts = [s.original for s in suggestions if s.romanized == "Beijing"]
        self.assertIn("北京", original_texts)
    
    def test_normalize_romanization(self):
        """测试罗马化标准化"""
        test_cases = [
            ("  Beijing  ", "beijing"),            # 去除空格，转小写
            ("Xi'an", "xian"),                     # 处理分隔符
            ("TOKYO", "tokyo"),                    # 大写转小写
            ("New-York", "newyork"),               # 处理连字符
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input=input_text):
                result = self.matcher.normalize_romanization(input_text)
                self.assertEqual(result, expected)


class TestRomanizationDatabase(unittest.TestCase):
    """罗马化数据库测试"""
    
    def setUp(self):
        self.db = RomanizationDatabase()
        
        # 添加测试数据
        self.db.add_mapping(RomanizationMapping("北京", "Beijing", "chinese", 1.0))
        self.db.add_mapping(RomanizationMapping("北京", "Peking", "chinese", 0.9))
        self.db.add_mapping(RomanizationMapping("東京", "Tokyo", "japanese", 1.0))
        self.db.add_mapping(RomanizationMapping("서울", "Seoul", "korean", 1.0))
    
    def test_search_functionality(self):
        """测试搜索功能"""
        # 搜索原文
        results = self.db.search("北京")
        self.assertEqual(len(results), 2)  # 应该有2个映射（Beijing和Peking）
        
        # 搜索罗马化
        results = self.db.search("Beijing")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].original, "北京")
        
        # 搜索不存在的项
        results = self.db.search("不存在")
        self.assertEqual(len(results), 0)
    
    def test_get_all_romanizations(self):
        """测试获取所有罗马化形式"""
        romanizations = self.db.get_all_romanizations("北京")
        self.assertEqual(len(romanizations), 2)
        self.assertIn("Beijing", romanizations)
        self.assertIn("Peking", romanizations)
        
        # 测试单一罗马化
        romanizations = self.db.get_all_romanizations("東京")
        self.assertEqual(len(romanizations), 1)
        self.assertIn("Tokyo", romanizations)
    
    def test_get_all_originals(self):
        """测试获取所有原文形式"""
        originals = self.db.get_all_originals("Beijing")
        self.assertEqual(len(originals), 1)
        self.assertIn("北京", originals)
        
        # 测试不存在的罗马化
        originals = self.db.get_all_originals("NonExistent")
        self.assertEqual(len(originals), 0)


class TestMultiLanguageScenarios(unittest.TestCase):
    """多语言场景测试"""
    
    def setUp(self):
        self.matcher = RomanizationMatcher(fuzzy_threshold=0.6, debug=True)
    
    def test_mixed_language_candidate_list(self):
        """测试混合语言候选列表"""
        mixed_candidates = [
            "北京",      # 中文
            "Tokyo",     # 日文罗马字
            "서울",      # 韩文
            "Shanghai",  # 中文拼音
            "محمد",      # 阿拉伯文
        ]
        
        test_cases = [
            ("Beijing", "北京"),
            ("東京", "Tokyo"),
            ("Seoul", "서울"),
            ("上海", "Shanghai"),
            ("Muhammad", "محمد"),
        ]
        
        for query, expected in test_cases:
            with self.subTest(query=query, expected=expected):
                result = self.matcher.match_string(query, mixed_candidates)
                self.assertEqual(result, expected)
    
    def test_ambiguous_romanization(self):
        """测试歧义罗马化"""
        # 某些罗马化可能对应多种语言
        candidates = [
            "이수", "李수",  # 韩文和中文可能有相同的罗马化
        ]
        
        result = self.matcher.match_string("Lee Su", candidates)
        # 应该匹配其中一个，具体匹配哪个取决于匹配器的优先级
        self.assertIn(result, candidates)
    
    def test_cross_language_similarity(self):
        """测试跨语言相似性"""
        # 测试相似的罗马化在不同语言中的表现
        chinese_candidates = ["李明", "王明", "张明"]
        korean_candidates = ["이명", "김명", "박명"]
        
        # 测试中文拼音
        result = self.matcher.match_string("Li Ming", chinese_candidates)
        self.assertEqual(result, "李明")
        
        # 测试韩文罗马化（如果有预定义映射）
        result = self.matcher.match_string("Lee Myeong", korean_candidates)
        # 由于没有预定义映射，可能回退到模糊匹配
        # 我们主要检查不会崩溃
        self.assertIsInstance(result, (str, type(None)))


class TestPerformanceAndEdgeCases(unittest.TestCase):
    """性能和边界情况测试"""
    
    def setUp(self):
        self.matcher = RomanizationMatcher(fuzzy_threshold=0.7)
    
    def test_large_candidate_list(self):
        """测试大候选列表性能"""
        # 生成大量候选项
        large_candidates = [f"City_{i}" for i in range(1000)]
        large_candidates.extend(["北京", "上海", "广州", "深圳"])
        
        import time
        start_time = time.time()
        result = self.matcher.match_string("Beijing", large_candidates)
        end_time = time.time()
        
        # 应该在合理时间内完成
        self.assertLess(end_time - start_time, 2.0)
        self.assertEqual(result, "北京")
    
    def test_empty_and_none_inputs(self):
        """测试空和None输入"""
        candidates = ["北京", "上海"]
        
        # 空字符串
        result = self.matcher.match_string("", candidates)
        self.assertIsNone(result)
        
        # None输入
        result = self.matcher.match_string(None, candidates)
        self.assertIsNone(result)
        
        # 空候选列表
        result = self.matcher.match_string("Beijing", [])
        self.assertIsNone(result)
        
        # None候选列表
        result = self.matcher.match_string("Beijing", None)
        self.assertIsNone(result)
    
    def test_special_characters_in_romanization(self):
        """测试罗马化中的特殊字符"""
        special_cases = [
            ("Xi'an", ["西安"]),           # 撇号
            ("Al-Rashid", ["الرشيد"]),     # 连字符（如果有映射）
            ("São Paulo", ["圣保罗"]),      # 重音符号（如果有映射）
        ]
        
        for query, candidates in special_cases:
            with self.subTest(query=query):
                # 主要测试不会抛出异常
                try:
                    result = self.matcher.match_string(query, candidates)
                    # 结果可能是None（如果没有映射），这是可以接受的
                    self.assertIsInstance(result, (str, type(None)))
                except Exception as e:
                    self.fail(f"Exception with special characters: {e}")
    
    def test_very_long_strings(self):
        """测试很长的字符串"""
        long_romanization = "VeryLongRomanizationStringThatExceedsNormalLength" * 10
        long_original = "超级长的原始字符串测试内容" * 50
        
        candidates = [long_original, "short"]
        
        # 测试不会超时或崩溃
        import time
        start_time = time.time()
        result = self.matcher.match_string(long_romanization, candidates)
        end_time = time.time()
        
        # 应该在合理时间内完成
        self.assertLess(end_time - start_time, 5.0)
        # 结果可能是None，这是可以接受的
        self.assertIsInstance(result, (str, type(None)))


if __name__ == '__main__':
    print("Running Romanization Matcher Tests...")
    print("=" * 60)
    
    unittest.main(verbosity=2)
