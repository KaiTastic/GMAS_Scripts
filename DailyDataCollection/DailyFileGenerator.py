"""
DailyFileGenerator - 重定向到兼容层

此文件是为了向后兼容而保留的重定向文件。
原始的 DailyFileGenerator.py 已被移动到 deprecated/ 文件夹。

建议使用新的模块化结构或兼容层。
"""

import warnings
import sys
import os

# 显示弃用警告
warnings.warn(
    "DailyFileGenerator.py 已被弃用并移动到 deprecated/ 文件夹。\n"
    "请使用以下方式之一：\n"
    "1. 导入 DailyFileGenerator_compat (兼容层)\n"
    "2. 使用新的模块化结构 (core 包)\n"
    "详细信息请查看 README.md 文件。",
    DeprecationWarning,
    stacklevel=2
)

# 尝试从兼容层导入所有内容
try:
    from DailyFileGenerator_compat import *
    print("注意：已自动重定向到兼容层 (DailyFileGenerator_compat)")
except ImportError as e:
    print(f"错误：无法导入兼容层: {e}")
    print("请检查 core 包的安装或使用 deprecated/DailyFileGenerator.py")
    
    # 提供访问原始文件的方式
    deprecated_path = os.path.join(os.path.dirname(__file__), 'deprecated', 'DailyFileGenerator.py')
    if os.path.exists(deprecated_path):
        print(f"原始文件位于: {deprecated_path}")
    
    sys.exit(1)

# 如果直接运行此文件，显示提示信息
if __name__ == "__main__":
    print("=" * 60)
    print("DailyFileGenerator 迁移提示")
    print("=" * 60)
    print("此文件已被重构为模块化架构。")
    print("\n推荐的使用方式：")
    print("1. 使用新的主程序：python main.py")
    print("2. 使用兼容层：from DailyFileGenerator_compat import *")
    print("3. 使用新模块：from core.mapsheet import CurrentDateFiles")
    print("\n原始文件位置：deprecated/DailyFileGenerator.py")
    print("=" * 60)
