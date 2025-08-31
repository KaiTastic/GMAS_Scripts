#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿拉伯语罗马音匹配综合测试
测试所有阿拉伯语增强功能的性能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.utils.matcher.string_matching.use_cases.romanization_matcher import EnhancedRomanizationMatcher

def test_arabic_comprehensive():
    """综合测试阿拉伯语罗马音匹配"""
    print("=== 阿拉伯语罗马音匹配综合测试 ===\n")
    
    # 初始化匹配器
    matcher = EnhancedRomanizationMatcher(
        fuzzy_threshold=0.6,
        debug=True,
        enable_phonetic_matching=True,
        enable_cross_language=True,
        enable_adaptive_learning=True
    )
    
    # 测试数据集
    test_cases = [
        # 1. 基础阿拉伯名字测试
        {
            "category": "基础男性名字",
            "tests": [
                ("محمد", ["Muhammad", "Mohammed", "Mohamed", "Ahmad", "Ali"]),
                ("أحمد", ["Ahmad", "Ahmed", "Muhammad", "Hassan", "Omar"]),
                ("علي", ["Ali", "Aly", "Omar", "Hassan", "Khalid"]),
                ("عبدالله", ["Abdullah", "Abd Allah", "Abdallah", "Ibrahim", "Omar"]),
                ("خالد", ["Khalid", "Khaled", "Halid", "Ahmad", "Hassan"]),
            ]
        },
        
        # 2. 女性名字测试
        {
            "category": "女性名字",
            "tests": [
                ("فاطمة", ["Fatima", "Fatma", "Fatimah", "Aisha", "Maryam"]),
                ("عائشة", ["Aisha", "Aysha", "Aishah", "Fatima", "Zainab"]),
                ("خديجة", ["Khadija", "Khadijah", "Hadija", "Fatima", "Maryam"]),
                ("زينب", ["Zainab", "Zaynab", "Zeinab", "Aisha", "Fatima"]),
                ("مريم", ["Maryam", "Mariam", "Mary", "Fatima", "Aisha"]),
            ]
        },
        
        # 3. 城市和地名测试
        {
            "category": "城市地名",
            "tests": [
                ("الرياض", ["Riyadh", "Ar-Riyadh", "Er Riyadh", "Cairo", "Dubai"]),
                ("القاهرة", ["Cairo", "Al-Qahirah", "El Qahira", "Riyadh", "Baghdad"]),
                ("دبي", ["Dubai", "Dubayy", "Dubay", "Abu Dhabi", "Doha"]),
                ("بغداد", ["Baghdad", "Baghdād", "Bagdad", "Damascus", "Cairo"]),
                ("الدوحة", ["Doha", "Ad-Dawḥah", "Ad-Doha", "Kuwait", "Muscat"]),
            ]
        },
        
        # 4. 复杂变体测试
        {
            "category": "复杂变体",
            "tests": [
                ("عبدالرحمن", ["Abdurrahman", "Abd al-Rahman", "Abdelrahman", "Abdullah", "Ibrahim"]),
                ("إبراهيم", ["Ibrahim", "Ibraheem", "Abraham", "Ismail", "Ahmad"]),
                ("يوسف", ["Yusuf", "Youssef", "Joseph", "Yousef", "Omar"]),
                ("حسين", ["Hussein", "Hussain", "Hosein", "Hassan", "Ali"]),
                ("طارق", ["Tariq", "Tarik", "Tareq", "Omar", "Khalid"]),
            ]
        },
        
        # 5. 方言变体测试
        {
            "category": "方言变体",
            "tests": [
                ("جمال", ["Jamal", "Gamal", "Djamal", "Ahmad", "Omar"]),  # ج的方言差异
                ("قاسم", ["Qasim", "Kasim", "Gasim", "Ahmad", "Hassan"]),  # ق的方言差异
                ("ثابت", ["Thabit", "Sabit", "Tabit", "Ahmad", "Omar"]),  # ث的方言差异
            ]
        },
        
        # 6. 现代变体和聊天语言测试
        {
            "category": "现代变体",
            "tests": [
                ("Mo7amed", ["Muhammad", "Mohamed", "Mohammed", "Ahmad", "Ali"]),  # 数字替代
                ("A7med", ["Ahmad", "Ahmed", "Muhammad", "Ali", "Omar"]),  # 数字替代
                ("3ali", ["Ali", "Aly", "Omar", "Ahmad", "Hassan"]),  # 数字替代
                ("5alid", ["Khalid", "Khaled", "Omar", "Ahmad", "Hassan"]),  # 数字替代
            ]
        },
        
        # 7. 国家名称测试
        {
            "category": "国家名称",
            "tests": [
                ("السعودية", ["Saudi Arabia", "As-Sa'ūdiyyah", "KSA", "Egypt", "UAE"]),
                ("مصر", ["Egypt", "Miṣr", "Masr", "Saudi Arabia", "Iraq"]),
                ("الإمارات", ["UAE", "Al-Imārāt", "Emirates", "Saudi Arabia", "Qatar"]),
                ("العراق", ["Iraq", "Al-'Irāq", "Egypt", "Syria", "Jordan"]),
            ]
        },
        
        # 8. 挑战性测试（相似但不同的名字）
        {
            "category": "挑战性测试",
            "tests": [
                ("حسن", ["Hassan", "Hussein", "Hasan", "Omar", "Ali"]),  # Hassan vs Hussein
                ("حسين", ["Hussein", "Hassan", "Hussain", "Omar", "Ali"]),  # Hussein vs Hassan
                ("سعد", ["Saad", "Sa'd", "Saed", "Said", "Omar"]),  # Saad vs Said
                ("سعيد", ["Said", "Saeed", "Sa'id", "Saad", "Omar"]),  # Said vs Saad
            ]
        }
    ]
    
    # 执行测试
    total_tests = 0
    passed_tests = 0
    category_results = {}
    
    for category_data in test_cases:
        category = category_data["category"]
        category_total = 0
        category_passed = 0
        
        print(f"\n--- {category} ---")
        
        for arabic_name, candidates in category_data["tests"]:
            total_tests += 1
            category_total += 1
            
            # 执行匹配
            match_result, score = matcher.match_string_with_score(arabic_name, candidates)
            expected = candidates[0]  # 第一个候选项是期望的匹配
            
            # 判断是否成功
            success = match_result == expected
            if success:
                passed_tests += 1
                category_passed += 1
                status = "✓"
            else:
                status = "✗"
            
            print(f"  {status} {arabic_name} -> {match_result} (分数: {score:.3f}, 期望: {expected})")
        
        # 计算分类成功率
        category_rate = (category_passed / category_total) * 100 if category_total > 0 else 0
        category_results[category] = category_rate
        print(f"  分类成功率: {category_passed}/{category_total} ({category_rate:.1f}%)")
    
    # 打印总结
    print(f"\n=== 测试总结 ===")
    overall_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    print(f"总体成功率: {passed_tests}/{total_tests} ({overall_rate:.1f}%)")
    
    print(f"\n各分类成功率:")
    for category, rate in category_results.items():
        print(f"  {category}: {rate:.1f}%")
    
    # 性能评估
    print(f"\n=== 性能评估 ===")
    if overall_rate >= 90:
        print("🌟 优秀: 阿拉伯语罗马音匹配性能极佳")
    elif overall_rate >= 80:
        print("👍 良好: 阿拉伯语罗马音匹配性能良好")
    elif overall_rate >= 70:
        print("⚠️  一般: 阿拉伯语罗马音匹配性能中等，需要优化")
    else:
        print("❌ 差劲: 阿拉伯语罗马音匹配性能较差，需要大幅改进")
    
    # 详细性能分析
    print(f"\n=== 详细分析 ===")
    best_categories = [cat for cat, rate in category_results.items() if rate >= 90]
    worst_categories = [cat for cat, rate in category_results.items() if rate < 70]
    
    if best_categories:
        print(f"表现最佳的类别: {', '.join(best_categories)}")
    
    if worst_categories:
        print(f"需要改进的类别: {', '.join(worst_categories)}")
    
    print(f"\n测试完成!")
    return overall_rate

if __name__ == "__main__":
    test_arabic_comprehensive()
