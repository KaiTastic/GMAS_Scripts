# -*- coding: utf-8 -*-
"""
简单的导入测试脚本
"""

import sys
import os

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_types_import():
    """测试types模块导入"""
    try:
        print("测试types模块导入...")
        
        # 测试子模块导入
        from string_types import enums, base, results, configs, validators
        print("  - 子模块导入成功")
        
        # 测试枚举导入
        from string_types.enums import TargetType, MatchType, MatchStrategy
        print("  - 枚举类型导入成功")
        
        # 测试基础类型导入
        from string_types.base import BaseConfig, BaseResult
        print("  - 基础类型导入成功")
        
        # 测试结果类型导入  
        from string_types.results import MatchResult
        print("  - 结果类型导入成功")
        
        # 测试配置类型导入
        from string_types.configs import TargetConfig
        print("  - 配置类型导入成功")
        
        # 创建一个简单的实例测试
        target_config = TargetConfig(
            target_type=TargetType.NAME,
            patterns=["test"],
            matcher_strategy=MatchStrategy.EXACT
        )
        print(f"  - 实例创建成功: {target_config.target_type}")
        
        match_result = MatchResult(
            matched_string="test",
            similarity_score=1.0,
            match_type=MatchType.EXACT
        )
        print(f"  - 结果实例创建成功: {match_result.matched_string}")
        
        print("types模块导入测试 - 全部通过!")
        return True
        
    except Exception as e:
        print(f"types模块导入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_core_modules_import():
    """测试核心模块导入"""
    try:
        print("\n测试核心模块导入...")
        
        # 测试基础匹配器
        from base_matcher import StringMatcher
        print("  - 基础匹配器导入成功")
        
        # 测试具体匹配器
        from exact_matcher import ExactStringMatcher
        print("  - 精确匹配器导入成功")
        
        from fuzzy_matcher import FuzzyStringMatcher
        print("  - 模糊匹配器导入成功")
        
        from hybrid_matcher import HybridStringMatcher
        print("  - 混合匹配器导入成功")
        
        # 测试相似度计算器
        from similarity_calculator import SimilarityCalculator
        print("  - 相似度计算器导入成功")
        
        # 测试工厂
        from factory import create_string_matcher
        print("  - 工厂函数导入成功")
        
        # 创建实例测试
        exact_matcher = ExactStringMatcher()
        fuzzy_matcher = FuzzyStringMatcher()
        hybrid_matcher = HybridStringMatcher()
        
        print("  - 匹配器实例创建成功")
        
        print("核心模块导入测试 - 全部通过!")
        return True
        
    except Exception as e:
        print(f"核心模块导入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始模块导入测试...")
    print("=" * 50)
    
    # 测试types模块
    types_ok = test_types_import()
    
    # 测试核心模块  
    core_ok = test_core_modules_import()
    
    print("\n" + "=" * 50)
    print("测试总结:")
    print(f"Types模块: {'通过' if types_ok else '失败'}")
    print(f"核心模块: {'通过' if core_ok else '失败'}")
    
    if types_ok and core_ok:
        print("所有导入测试通过!")
        return True
    else:
        print("存在导入问题，需要进一步修复")
        return False

if __name__ == "__main__":
    main()
