# -*- coding: utf-8 -*-
"""
核心匹配器简单测试
"""

import sys
import os

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_core_matcher():
    """测试核心匹配器"""
    try:
        print("测试核心匹配器导入...")
        
        # 导入核心匹配器
        from core_matcher import MultiTargetMatcher
        print("  - 核心匹配器导入成功")
        
        # 创建实例
        matcher = MultiTargetMatcher()
        print("  - 核心匹配器实例创建成功")
        
        print("核心匹配器测试通过!")
        return True
        
    except Exception as e:
        print(f"核心匹配器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_core_matcher()
