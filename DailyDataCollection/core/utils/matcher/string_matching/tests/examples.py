# -*- coding: utf-8 -*-
"""
String Matching 模块使用示例

演示如何使用各种匹配器和功能
"""

import sys
import os

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def demo_basic_matchers():
    """演示基础匹配器使用"""
    print("=== 基础匹配器演示 ===")
    
    from exact_matcher import ExactStringMatcher
    from fuzzy_matcher import FuzzyStringMatcher
    from hybrid_matcher import HybridStringMatcher
    
    test_patterns = ["图幅A01", "图幅B02", "示例图幅", "测试文件"]
    test_files = [
        "图幅A01_20250830.pdf",
        "图幅B02数据.xlsx", 
        "示例图副_错字.doc",
        "不存在的文件.txt"
    ]
    
    # 精确匹配器
    print("\n1. 精确匹配器:")
    exact_matcher = ExactStringMatcher()
    for filename in test_files:
        result = exact_matcher.match_string(filename, test_patterns)
        print(f"   文件: {filename} -> 匹配: {result}")
    
    # 模糊匹配器
    print("\n2. 模糊匹配器:")
    fuzzy_matcher = FuzzyStringMatcher(threshold=0.6)
    for filename in test_files:
        result, score = fuzzy_matcher.match_string_with_score(filename, test_patterns)
        print(f"   文件: {filename} -> 匹配: {result} (相似度: {score:.2f})")
    
    # 混合匹配器
    print("\n3. 混合匹配器:")
    hybrid_matcher = HybridStringMatcher(fuzzy_threshold=0.6)
    for filename in test_files:
        result, score = hybrid_matcher.match_string_with_score(filename, test_patterns)
        print(f"   文件: {filename} -> 匹配: {result} (相似度: {score:.2f})")


def demo_name_matchers():
    """演示名称匹配器使用"""
    print("\n=== 名称匹配器演示 ===")
    
    from name_matcher import ExactNameMatcher, FuzzyNameMatcher, HybridNameMatcher
    
    mapsheet_names = ["H49E001001", "H49E001002", "H49E002001", "城市规划图", "地形图A"]
    test_filenames = [
        "H49E001001_地形图.pdf",
        "H49E001002数据收集.xlsx",
        "H49E002001_修订版.doc",
        "城市规化图_2025.pdf",  # 有错字
        "未知图幅.txt"
    ]
    
    matchers = [
        ("精确名称匹配", ExactNameMatcher()),
        ("模糊名称匹配", FuzzyNameMatcher(fuzzy_threshold=0.7)),
        ("混合名称匹配", HybridNameMatcher(fuzzy_threshold=0.7))
    ]
    
    for matcher_name, matcher in matchers:
        print(f"\n{matcher_name}:")
        for filename in test_filenames:
            result = matcher.match_mapsheet_name(filename, mapsheet_names)
            print(f"   {filename} -> {result}")


def demo_multi_target_matcher():
    """演示多目标匹配器使用"""
    print("\n=== 多目标匹配器演示 ===")
    
    from core_matcher import MultiTargetMatcher
    from string_types.enums import TargetType, MatchStrategy
    from string_types.configs import TargetConfig
    
    # 创建多目标匹配器
    matcher = MultiTargetMatcher()
    
    # 添加图幅名称目标
    mapsheet_config = TargetConfig(
        target_type=TargetType.NAME,
        patterns=["H49E001001", "H49E001002", "城市规划图"],
        matcher_strategy=MatchStrategy.FUZZY,
        fuzzy_threshold=0.7
    )
    matcher.add_target("mapsheets", mapsheet_config)
    
    # 添加文件扩展名目标
    extension_config = TargetConfig(
        target_type=TargetType.FILE_EXTENSION,
        patterns=[".pdf", ".xlsx", ".doc", ".dwg"],
        matcher_strategy=MatchStrategy.EXACT
    )
    matcher.add_target("extensions", extension_config)
    
    # 添加日期目标 (使用便捷方法) - 暂时注释掉，因为实现有问题
    # matcher.add_date_target("dates")
    
    print("多目标匹配器配置完成:")
    print(f"   目标数量: {len(matcher.targets)}")
    for name, config in matcher.targets.items():
        print(f"   - {name}: {config.target_type.value} ({config.matcher_strategy.value})")


def demo_factory_functions():
    """演示工厂函数使用"""
    print("\n=== 工厂函数演示 ===")
    
    from factory import create_string_matcher, create_name_matcher
    
    # 使用工厂创建不同类型的匹配器
    matchers = [
        create_string_matcher("exact"),
        create_string_matcher("fuzzy", fuzzy_threshold=0.8),
        create_string_matcher("hybrid", fuzzy_threshold=0.6)
    ]
    
    test_string = "测试文档"
    candidates = ["测试文件", "示例文档", "测式文档"]  # 最后一个有错字
    
    for i, matcher in enumerate(matchers):
        matcher_type = ["精确", "模糊", "混合"][i]
        result = matcher.match_string(test_string, candidates)
        print(f"   {matcher_type}匹配器: {test_string} -> {result}")
    
    # 使用名称匹配器工厂
    name_matcher = create_name_matcher("fuzzy", fuzzy_threshold=0.7)
    print(f"\n   名称匹配器类型: {name_matcher.__class__.__name__}")


def demo_types_system():
    """演示类型系统使用"""
    print("\n=== 类型系统演示 ===")
    
    from string_types.enums import TargetType, MatchType, MatchStrategy
    from string_types.configs import TargetConfig
    from string_types.results import MatchResult
    
    # 创建配置
    config = TargetConfig(
        target_type=TargetType.NAME,
        patterns=["图幅A", "图幅B"],
        matcher_strategy=MatchStrategy.HYBRID,
        fuzzy_threshold=0.75,
        case_sensitive=False,
        required=True
    )
    
    print("目标配置:")
    print(f"   类型: {config.target_type.value}")
    print(f"   策略: {config.matcher_strategy.value}")
    print(f"   模糊阈值: {config.fuzzy_threshold}")
    print(f"   区分大小写: {config.case_sensitive}")
    
    # 创建匹配结果
    result = MatchResult(
        matched_string="图幅A",
        similarity_score=0.95,
        match_type=MatchType.HYBRID,
        confidence=0.9,
        alternatives=["图幅B"]
    )
    
    print("\n匹配结果:")
    print(f"   匹配字符串: {result.matched_string}")
    print(f"   相似度: {result.similarity_score}")
    print(f"   匹配类型: {result.match_type.value}")
    print(f"   是否匹配: {result.is_matched}")
    print(f"   备选项: {result.alternatives}")


def main():
    """主演示函数"""
    print("String Matching 模块使用演示")
    print("=" * 60)
    
    # 运行所有演示
    demo_basic_matchers()
    demo_name_matchers()
    demo_multi_target_matcher()
    demo_factory_functions()
    demo_types_system()
    
    print("\n" + "=" * 60)
    print("演示完成！")
    print("\n模块特性总结:")
    print("- 支持精确、模糊、混合三种匹配策略")
    print("- 提供专门的名称匹配器用于文件名和图幅名匹配")
    print("- 支持多目标匹配，可同时匹配多种类型的目标")
    print("- 完整的类型系统，支持配置和结果的结构化处理")
    print("- 工厂模式，便于创建和管理不同类型的匹配器")
    print("- 良好的模块化设计，易于扩展和维护")


if __name__ == "__main__":
    main()
