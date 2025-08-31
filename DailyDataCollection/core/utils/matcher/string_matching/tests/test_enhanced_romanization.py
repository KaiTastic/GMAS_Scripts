#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版罗马化字母匹配器测试
测试多语言、音韵级匹配、自适应学习等高级功能
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
from core.utils.matcher.string_matching.use_cases.romanization_matcher import (
    EnhancedRomanizationMatcher, RomanizationMatcher, 
    RomanizationMapping, RomanizationDatabase,
    PhoneticMapping, SyllableInfo
)


class TestEnhancedRomanizationMatcher(unittest.TestCase):
    """增强版罗马化匹配器测试"""
    
    def setUp(self):
        self.enhanced_matcher = EnhancedRomanizationMatcher(
            fuzzy_threshold=0.6, 
            debug=True,
            enable_phonetic_matching=True,
            enable_cross_language=True,
            enable_adaptive_learning=True
        )
        
        # 传统匹配器用于对比
        self.traditional_matcher = RomanizationMatcher(fuzzy_threshold=0.6, debug=True)
    
    def test_enhanced_chinese_pinyin_variants(self):
        """测试增强版中文拼音变体匹配"""
        chinese_cities = ["北京", "上海", "广州", "深圳", "西安", "重庆"]
        
        # 测试各种拼音变体
        test_cases = [
            # 标准拼音
            ("Beijing", "北京"),
            ("Shanghai", "上海"),
            ("Guangzhou", "广州"),
            
            # 旧式拼音变体
            ("Peking", "北京"),        # Wade-Giles
            ("Canton", "广州"),        # 粤语音译
            ("Sian", "西安"),          # 省略分隔符
            ("Chung-king", "重庆"),    # 旧式拼写
            
            # 不同分隔符
            ("Xi an", "西安"),         # 空格
            ("Xi_an", "西安"),         # 下划线
            ("Chong qing", "重庆"),    # 空格
        ]
        
        for pinyin, expected_chinese in test_cases:
            with self.subTest(query=pinyin, expected=expected_chinese):
                # 增强版匹配器
                enhanced_result = self.enhanced_matcher.match_string(pinyin, chinese_cities)
                # 传统匹配器对比
                traditional_result = self.traditional_matcher.match_string(pinyin, chinese_cities)
                
                self.assertEqual(enhanced_result, expected_chinese,
                               f"增强版匹配器未能匹配 {pinyin} -> {expected_chinese}")
                
                # 增强版应该至少不比传统版差
                if traditional_result == expected_chinese:
                    self.assertEqual(enhanced_result, expected_chinese)
    
    def test_multi_language_detection(self):
        """测试多语言检测功能"""
        test_cases = [
            # 中文+拼音
            ("北京", ["Beijing", "Shanghai", "Tokyo"], "Beijing"),
            ("Beijing", ["北京", "上海", "東京"], "北京"),
            
            # 日文+罗马字
            ("東京", ["Tokyo", "Osaka", "Seoul"], "Tokyo"),
            ("Tokyo", ["東京", "大阪", "서울"], "東京"),
            
            # 韩文+罗马字
            ("서울", ["Seoul", "Busan", "Tokyo"], "Seoul"),
            ("Seoul", ["서울", "부산", "東京"], "서울"),
            
            # 阿拉伯文+拉丁化
            ("محمد", ["Muhammad", "Ahmad", "Ali"], "Muhammad"),
            ("Muhammad", ["محمد", "أحمد", "علي"], "محمد"),
        ]
        
        for query, candidates, expected in test_cases:
            with self.subTest(query=query, candidates=candidates):
                result = self.enhanced_matcher.match_string(query, candidates)
                self.assertEqual(result, expected,
                               f"多语言检测失败: {query} 在 {candidates} 中应匹配 {expected}")
    
    def test_phonetic_similarity_matching(self):
        """测试音韵相似性匹配"""
        # 启用音韵匹配的匹配器
        phonetic_matcher = EnhancedRomanizationMatcher(
            fuzzy_threshold=0.5,
            enable_phonetic_matching=True,
            debug=True
        )
        
        test_cases = [
            # 中文音韵相似
            ("Zhangzhou", ["Changzhou", "Zhengzhou", "Guangzhou"], "Changzhou"),  # zh/ch混淆
            ("Qingdao", ["Chingdao", "Jingdao", "Pingdao"], "Chingdao"),        # q/ch混淆
            
            # 日文音韵相似
            ("Toukyou", ["Tokyo", "Toukyo", "Tokio"], "Tokyo"),                  # 长音简化
            ("Oosaka", ["Osaka", "Osako", "Ohsaka"], "Osaka"),                   # 长音简化
            
            # 阿拉伯文音韵相似
            ("Khaled", ["Khalid", "Halid", "Kalid"], "Khalid"),                  # kh/h变化
            ("Mohammed", ["Muhammad", "Mohamed", "Muhammed"], "Muhammad"),        # 元音变化
        ]
        
        for query, candidates, expected in test_cases:
            with self.subTest(query=query):
                result = phonetic_matcher.match_string(query, candidates)
                # 音韵匹配应该能找到相似的结果
                self.assertIsNotNone(result, f"音韵匹配失败: {query} 在 {candidates} 中")
                # 如果有期望结果，检查是否匹配
                if expected:
                    self.assertEqual(result, expected)
    
    def test_syllable_structure_matching(self):
        """测试音节结构匹配"""
        test_cases = [
            # 中文音节结构
            ("Bei-jing", ["Beijing", "Nanjing", "Tianjing"], "Beijing"),
            ("Shang-hai", ["Shanghai", "Shanghi", "Shangai"], "Shanghai"),
            
            # 日文音节结构
            ("To-kyo", ["Tokyo", "Tokio", "Toukyo"], "Tokyo"),
            ("O-sa-ka", ["Osaka", "Osako", "Ohsaka"], "Osaka"),
            
            # 韩文音节结构
            ("Seo-ul", ["Seoul", "Seul", "Soul"], "Seoul"),
            ("Bu-san", ["Busan", "Pusan", "Bosan"], "Busan"),
        ]
        
        for query, candidates, expected in test_cases:
            with self.subTest(query=query):
                result = self.enhanced_matcher.match_string(query, candidates)
                self.assertEqual(result, expected,
                               f"音节结构匹配失败: {query} -> {expected}")
    
    def test_cross_language_similarity(self):
        """测试跨语言相似性"""
        # 启用跨语言匹配
        cross_lang_matcher = EnhancedRomanizationMatcher(
            fuzzy_threshold=0.4,
            enable_cross_language=True,
            debug=True
        )
        
        test_cases = [
            # 中日韩地名的相似性
            ("Seoul", ["서울", "東京", "北京"], "서울"),          # 韩文原名
            ("Tokyo", ["東京", "서울", "北京"], "東京"),          # 日文原名
            ("Beijing", ["北京", "東京", "서울"], "北京"),        # 中文原名
            
            # 阿拉伯名字的变体
            ("Ali", ["علي", "Ahmad", "Omar"], "علي"),            # 阿拉伯文原名
            ("Ahmad", ["أحمد", "علي", "عمر"], "أحمد"),          # 阿拉伯文原名
        ]
        
        for query, candidates, expected in test_cases:
            with self.subTest(query=query):
                result = cross_lang_matcher.match_string(query, candidates)
                self.assertEqual(result, expected,
                               f"跨语言相似性匹配失败: {query} -> {expected}")
    
    def test_adaptive_learning(self):
        """测试自适应学习功能"""
        # 启用自适应学习
        learning_matcher = EnhancedRomanizationMatcher(
            fuzzy_threshold=0.6,
            enable_adaptive_learning=True,
            debug=True
        )
        
        # 模拟多次匹配同一对映射
        target = "NewCity"
        candidates = ["新城市", "老城市", "中城市"]
        expected = "新城市"
        
        # 第一次匹配可能失败或分数较低
        first_result = learning_matcher.match_string(target, candidates)
        
        # 手动添加学习映射来模拟学习过程
        learning_matcher.add_custom_mapping("新城市", "NewCity", "chinese", 0.9)
        
        # 再次匹配应该成功
        second_result = learning_matcher.match_string(target, candidates)
        self.assertEqual(second_result, expected,
                        f"自适应学习后匹配失败: {target} -> {expected}")
    
    def test_enhanced_sound_change_rules(self):
        """测试增强版音变规则"""
        test_cases = [
            # 中文音变规则
            ("Zhengzhou", ["Chengzhou", "Zhengchou", "Zengzhou"], "Chengzhou"),  # zh/ch
            ("Xiamen", ["Siamen", "Shammen", "Hiamen"], "Siamen"),               # x/s
            
            # 日文音变规则
            ("Fukuoka", ["Hukuoka", "Fukuouka", "Fukoka"], "Hukuoka"),          # f/h
            ("Hiroshima", ["Hirosima", "Hiroshma", "Hirroshima"], "Hirosima"),   # sh/s
            
            # 韩文音变规则
            ("Gwangju", ["Kwangju", "Guangju", "Gwangchu"], "Kwangju"),          # gw/kw
            ("Daejeon", ["Taejon", "Daechon", "Taejeon"], "Taejon"),             # d/t, eo/o
            
            # 阿拉伯文音变规则
            ("Khaled", ["Haled", "Kalid", "Khaled"], "Haled"),                   # kh/h
            ("Muhammad", ["Mohamed", "Muhammed", "Mohammad"], "Mohamed"),         # 元音变化
        ]
        
        for query, candidates, expected in test_cases:
            with self.subTest(query=query):
                result = self.enhanced_matcher.match_string(query, candidates)
                self.assertIsNotNone(result, f"增强音变规则匹配失败: {query} 在 {candidates} 中")
                if expected in candidates:
                    # 如果期望结果在候选中，应该能匹配到
                    self.assertEqual(result, expected)
    
    def test_character_level_similarity(self):
        """测试字符级相似性"""
        test_cases = [
            # 轻微拼写错误
            ("Bejing", ["Beijing", "Nanjing", "Tianjin"], "Beijing"),            # 缺失字母
            ("Shanghaii", ["Shanghai", "Shenzhen", "Hangzhou"], "Shanghai"),     # 多余字母
            ("Guangzou", ["Guangzhou", "Ganzhou", "Guizhou"], "Guangzhou"),      # 字母替换
            
            # 日文罗马字变体
            ("Tokyio", ["Tokyo", "Kyoto", "Osaka"], "Tokyo"),                    # 多余字母
            ("Osaca", ["Osaka", "Asaka", "Iwaka"], "Osaka"),                     # 字母替换
            
            # 韩文罗马字变体
            ("Seul", ["Seoul", "Jeju", "Busan"], "Seoul"),                       # 缺失字母
            ("Bussan", ["Busan", "Ulsan", "Cheonan"], "Busan"),                  # 多余字母
        ]
        
        for query, candidates, expected in test_cases:
            with self.subTest(query=query):
                result = self.enhanced_matcher.match_string(query, candidates)
                self.assertEqual(result, expected,
                               f"字符级相似性匹配失败: {query} -> {expected}")
    
    def test_performance_comparison(self):
        """测试性能对比"""
        import time
        
        # 准备测试数据
        test_data = [
            ("Beijing", ["北京", "上海", "广州", "深圳", "杭州"] * 10),
            ("Tokyo", ["東京", "大阪", "京都", "名古屋", "横浜"] * 10),
            ("Seoul", ["서울", "부산", "대구", "인천", "광주"] * 10),
            ("Muhammad", ["محمد", "أحمد", "علي", "فاطمة", "عبدالله"] * 10),
        ]
        
        # 测试增强版匹配器
        start_time = time.time()
        enhanced_results = []
        for query, candidates in test_data:
            result = self.enhanced_matcher.match_string(query, candidates)
            enhanced_results.append(result)
        enhanced_time = time.time() - start_time
        
        # 测试传统匹配器
        start_time = time.time()
        traditional_results = []
        for query, candidates in test_data:
            result = self.traditional_matcher.match_string(query, candidates)
            traditional_results.append(result)
        traditional_time = time.time() - start_time
        
        print(f"\n性能对比:")
        print(f"增强版匹配器时间: {enhanced_time:.4f}秒")
        print(f"传统匹配器时间: {traditional_time:.4f}秒")
        print(f"性能比率: {enhanced_time/traditional_time:.2f}x")
        
        # 增强版应该能找到更多匹配
        enhanced_matches = sum(1 for r in enhanced_results if r is not None)
        traditional_matches = sum(1 for r in traditional_results if r is not None)
        
        print(f"增强版匹配成功数: {enhanced_matches}/{len(test_data)}")
        print(f"传统版匹配成功数: {traditional_matches}/{len(test_data)}")
        
        # 增强版匹配成功率应该不低于传统版
        self.assertGreaterEqual(enhanced_matches, traditional_matches)
    
    def test_romanization_mapping_extensions(self):
        """测试罗马化映射扩展功能"""
        # 测试变体映射
        mapping = RomanizationMapping(
            original="北京",
            romanized="Beijing",
            language="chinese",
            confidence=1.0,
            variants=["Peking", "Bei-jing"],
            region="standard",
            source="pinyin"
        )
        
        # 添加自定义映射
        self.enhanced_matcher.add_custom_mapping("测试市", "TestCity", "chinese", 0.95)
        
        # 测试自定义映射是否生效
        result = self.enhanced_matcher.match_string("TestCity", ["测试市", "其他市", "样本市"])
        self.assertEqual(result, "测试市", "自定义映射未生效")
        
        # 测试反向匹配
        reverse_result = self.enhanced_matcher.match_string("测试市", ["TestCity", "OtherCity", "SampleCity"])
        self.assertEqual(reverse_result, "TestCity", "自定义映射反向匹配失败")
    
    def test_syllable_info_parsing(self):
        """测试音节信息解析"""
        # 创建音节信息
        syllable = SyllableInfo(
            onset="zh",
            nucleus="ang",
            coda="",
            tone="1",
            full="zhang"
        )
        
        self.assertEqual(syllable.onset, "zh")
        self.assertEqual(syllable.nucleus, "ang")
        self.assertEqual(syllable.full, "zhang")
    
    def test_phonetic_mapping_usage(self):
        """测试音韵映射使用"""
        # 创建音韵映射
        phonetic_mapping = PhoneticMapping(
            sound="zh",
            romanizations=["zh", "z", "j"],
            language="chinese",
            weight=1.0
        )
        
        self.assertEqual(phonetic_mapping.sound, "zh")
        self.assertIn("zh", phonetic_mapping.romanizations)
        self.assertIn("z", phonetic_mapping.romanizations)
    
    def test_language_weight_adjustment(self):
        """测试语言权重调整"""
        # 调整语言权重
        self.enhanced_matcher.language_weights['chinese'] = 1.5
        self.enhanced_matcher.language_weights['japanese'] = 0.8
        
        # 测试权重影响匹配结果
        mixed_candidates = ["北京", "東京", "Beijing", "Tokyo"]
        
        # 中文权重较高，应该优先匹配中文
        result1 = self.enhanced_matcher.match_string("Beijing", mixed_candidates)
        
        # 调整权重后再测试
        self.enhanced_matcher.language_weights['chinese'] = 0.5
        self.enhanced_matcher.language_weights['japanese'] = 1.5
        
        # 验证权重系统工作
        self.assertIsNotNone(result1)


class TestRomanizationDatabase(unittest.TestCase):
    """罗马化数据库测试"""
    
    def setUp(self):
        self.db = RomanizationDatabase()
    
    def test_database_operations(self):
        """测试数据库基本操作"""
        # 添加映射
        mapping = RomanizationMapping("北京", "Beijing", "chinese", 1.0)
        self.db.add_mapping(mapping)
        
        # 搜索映射
        results = self.db.search("北京")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].romanized, "Beijing")
        
        # 搜索反向映射
        reverse_results = self.db.search("Beijing")
        self.assertEqual(len(reverse_results), 1)
        self.assertEqual(reverse_results[0].original, "北京")
    
    def test_get_romanizations(self):
        """测试获取罗马化形式"""
        # 添加多个映射
        mappings = [
            RomanizationMapping("北京", "Beijing", "chinese", 1.0),
            RomanizationMapping("北京", "Peking", "chinese", 0.9),
        ]
        
        for mapping in mappings:
            self.db.add_mapping(mapping)
        
        # 获取所有罗马化形式
        romanizations = self.db.get_all_romanizations("北京")
        self.assertIn("Beijing", romanizations)
        self.assertIn("Peking", romanizations)
        self.assertEqual(len(romanizations), 2)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
