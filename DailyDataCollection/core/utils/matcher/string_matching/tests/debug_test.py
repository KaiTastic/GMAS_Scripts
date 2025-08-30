# -*- coding: utf-8 -*-
"""
快速诊断测试 - 查看具体的错误信息
"""

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

def test_basic_imports():
    """测试基础导入并显示详细错误"""
    try:
        print("测试基础导入...")
        
        print("  - 导入 string_types.enums...")
        from string_types.enums import TargetType, MatchType, MatchStrategy
        print("    成功")
        
        print("  - 导入 string_types.configs...")
        from string_types.configs import TargetConfig
        print("    成功")
        
        print("  - 导入 string_types.results...")
        from string_types.results import MatchResult
        print("    成功")
        
        print("  - 导入 base_matcher...")
        from base_matcher import StringMatcher
        print("    成功")
        
        print("  - 导入 exact_matcher...")
        from exact_matcher import ExactStringMatcher
        print("    成功")
        
        print("所有基础导入成功!")
        return True
        
    except Exception as e:
        print(f"基础导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_exact_matching():
    """测试精确匹配"""
    try:
        print("\n测试精确匹配...")
        from exact_matcher import ExactStringMatcher
        
        matcher = ExactStringMatcher()
        result = matcher.match_string("test", ["test", "example"])
        print(f"匹配结果: {result}")
        
        if result == "test":
            print("精确匹配测试成功!")
            return True
        else:
            print("精确匹配测试失败: 结果不正确")
            return False
            
    except Exception as e:
        print(f"精确匹配测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("快速诊断测试")
    print("=" * 40)
    
    # 测试基础导入
    import_ok = test_basic_imports()
    
    if import_ok:
        # 测试基础功能
        test_exact_matching()
    else:
        print("基础导入失败，跳过功能测试")
