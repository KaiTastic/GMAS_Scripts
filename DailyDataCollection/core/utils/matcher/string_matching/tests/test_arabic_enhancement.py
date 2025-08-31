#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿拉伯语罗马音增强测试
"""

import sys
import os

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.utils.matcher.string_matching.use_cases.romanization_matcher import EnhancedRomanizationMatcher

def test_arabic_romanization():
    print('测试当前阿拉伯语罗马音匹配:')
    print('=' * 50)
    
    matcher = EnhancedRomanizationMatcher(debug=False)
    
    # 阿拉伯语测试数据
    arabic_names = ['محمد', 'أحمد', 'علي', 'فاطمة', 'عبدالله', 'خالد', 'عائشة', 'عمر']
    arabic_cities = ['الرياض', 'القاهرة', 'دبي', 'بغداد']
    
    # 测试人名
    print('阿拉伯人名匹配:')
    name_tests = [
        ('Muhammad', 'محمد'),
        ('Mohammed', 'محمد'),
        ('Mohamed', 'محمد'),
        ('Ahmad', 'أحمد'),
        ('Ahmed', 'أحمد'),
        ('Ali', 'علي'),
        ('Fatima', 'فاطمة'),
        ('Fatma', 'فاطمة'),
        ('Abdullah', 'عبدالله'),
        ('Abd Allah', 'عبدالله'),
        ('Khalid', 'خالد'),
        ('Khaled', 'خالد'),
        ('Aisha', 'عائشة'),
        ('Aysha', 'عائشة'),
        ('Omar', 'عمر'),
        ('Umar', 'عمر'),
    ]
    
    passed = 0
    total = len(name_tests)
    
    for latin, expected in name_tests:
        result = matcher.match_string(latin, arabic_names)
        status = '✓' if result == expected else '✗'
        if result == expected:
            passed += 1
        print(f'{status} {latin:12} -> {result or "None":8} (期望: {expected})')
    
    print(f'\n人名匹配结果: {passed}/{total} ({passed/total*100:.1f}%)')
    
    # 测试城市名
    print('\n阿拉伯城市名匹配:')
    city_tests = [
        ('Riyadh', 'الرياض'),
        ('Ar-Riyadh', 'الرياض'),
        ('Cairo', 'القاهرة'),
        ('Al-Qahirah', 'القاهرة'),
        ('Dubai', 'دبي'),
        ('Dubayy', 'دبي'),
        ('Baghdad', 'بغداد'),
        ('Baghdād', 'بغداد'),
    ]
    
    city_passed = 0
    city_total = len(city_tests)
    
    for latin, expected in city_tests:
        result = matcher.match_string(latin, arabic_cities)
        status = '✓' if result == expected else '✗'
        if result == expected:
            city_passed += 1
        print(f'{status} {latin:12} -> {result or "None":8} (期望: {expected})')
    
    print(f'\n城市名匹配结果: {city_passed}/{city_total} ({city_passed/city_total*100:.1f}%)')
    
    return passed + city_passed, total + city_total

if __name__ == '__main__':
    test_arabic_romanization()
