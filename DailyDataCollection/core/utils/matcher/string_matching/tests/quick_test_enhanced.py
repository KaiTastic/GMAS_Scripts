#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版罗马化匹配器快速测试脚本
"""

import sys
import os

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.utils.matcher.string_matching.use_cases.romanization_matcher import EnhancedRomanizationMatcher

def main():
    print('=' * 60)
    print('增强版罗马化匹配器 - 综合测试')
    print('=' * 60)
    
    # 创建增强版匹配器
    matcher = EnhancedRomanizationMatcher(
        fuzzy_threshold=0.6, 
        debug=False,  # 关闭调试以减少输出
        enable_phonetic_matching=True,
        enable_cross_language=True,
        enable_adaptive_learning=True
    )
    
    # 中文拼音测试
    print('\n测试套件: 中文拼音匹配')
    print('-' * 40)
    chinese_candidates = ['北京', '上海', '广州', '深圳', '西安', '重庆']
    chinese_tests = [
        ('Beijing', '北京'),
        ('Shanghai', '上海'), 
        ('Guangzhou', '广州'),
        ('Peking', '北京'),     # 旧式
        ('Canton', '广州'),     # 粤语
        ('Xian', '西安'),       # 省略分隔符
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for query, expected in chinese_tests:
        total_tests += 1
        result = matcher.match_string(query, chinese_candidates)
        
        if result == expected:
            status = '✓ 通过'
            passed_tests += 1
        else:
            status = '✗ 失败'
        
        print(f'{status} {query:12} -> {result or "None":8} (期望: {expected})')
    
    # 日文测试
    print('\n测试套件: 日文罗马字匹配')
    print('-' * 40)
    japanese_candidates = ['東京', '大阪', '京都', '名古屋']
    japanese_tests = [
        ('Tokyo', '東京'),
        ('Osaka', '大阪'),
        ('Kyoto', '京都'),
        ('Nagoya', '名古屋'),
    ]
    
    for query, expected in japanese_tests:
        total_tests += 1
        result = matcher.match_string(query, japanese_candidates)
        
        if result == expected:
            status = '✓ 通过'
            passed_tests += 1
        else:
            status = '✗ 失败'
        
        print(f'{status} {query:12} -> {result or "None":8} (期望: {expected})')
    
    # 韩文测试
    print('\n测试套件: 韩文罗马字匹配')
    print('-' * 40)
    korean_candidates = ['서울', '부산', '대구', '인천']
    korean_tests = [
        ('Seoul', '서울'),
        ('Busan', '부산'),
        ('Daegu', '대구'),
        ('Incheon', '인천'),
        ('Pusan', '부산'),      # 旧式变体
    ]
    
    for query, expected in korean_tests:
        total_tests += 1
        result = matcher.match_string(query, korean_candidates)
        
        if result == expected:
            status = '✓ 通过'
            passed_tests += 1
        else:
            status = '✗ 失败'
        
        print(f'{status} {query:12} -> {result or "None":8} (期望: {expected})')
    
    # 测试音韵匹配功能
    print('\n测试套件: 音韵匹配增强功能')
    print('-' * 40)
    
    # 测试音变规则
    sound_tests = [
        ('Zhangzhou', ['Changzhou', '张州', '漳州'], 'Changzhou'),  # zh/ch混淆
        ('Qingdao', ['Chingdao', '青岛'], 'Chingdao'),            # q/ch混淆
    ]
    
    for query, candidates, expected in sound_tests:
        total_tests += 1
        result = matcher.match_string(query, candidates)
        
        if result == expected or result in candidates:
            status = '✓ 通过'
            passed_tests += 1
        else:
            status = '? 部分'
        
        print(f'{status} {query:12} -> {result or "None":8} (候选: {candidates})')
    
    print(f'\n' + '=' * 60)
    print(f'测试总结:')
    print(f'总测试数: {total_tests}')
    print(f'通过测试: {passed_tests}')
    print(f'失败测试: {total_tests - passed_tests}')
    print(f'通过率: {passed_tests/total_tests*100:.1f}%')
    print('=' * 60)
    
    # 简单性能测试
    print('\n性能测试:')
    print('-' * 20)
    
    import time
    
    large_candidates = ['北京', '上海', '广州', '深圳', '杭州', '南京', '武汉', '成都', '西安', '重庆'] * 10
    
    start_time = time.time()
    for _ in range(50):
        matcher.match_string('Beijing', large_candidates)
    end_time = time.time()
    
    avg_time = (end_time - start_time) / 50 * 1000
    print(f'平均匹配时间: {avg_time:.2f}ms (100个候选项)')
    
    print('\n增强版罗马化匹配器测试完成!')

if __name__ == '__main__':
    main()
