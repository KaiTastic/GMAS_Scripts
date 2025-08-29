"""
文件处理模块

包含各种文件处理器：
- FileIO: 抽象文件IO基类
- GeneralIO: 通用文件IO
- KMZFile: KMZ文件处理器
"""

try:
    from .base_io import FileIO, GeneralIO
    from .kmz_handler import KMZFile

    __all__ = [
        'FileIO',
        'GeneralIO',
        'KMZFile'
    ]
except ImportError as e:
    print(f"导入文件处理模块时出错: {e}")
    __all__ = []
