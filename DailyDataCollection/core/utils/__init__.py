"""
工具函数模块

包含系统中使用的各种工具函数：
- 文件搜索工具
- 路径处理工具
- 数据转换工具
"""

try:
    from .file_utils import (
        list_fullpath_of_files_with_keywords,
        find_files_with_max_number
    )

    __all__ = [
        'list_fullpath_of_files_with_keywords',
        'find_files_with_max_number'
    ]
except ImportError as e:
    print(f"导入工具函数模块时出错: {e}")
    __all__ = []
