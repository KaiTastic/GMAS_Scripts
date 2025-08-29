"""
数据模型模块

包含系统中使用的各种数据模型类：
- ObservationData: 观测数据模型
- FileAttributes: 文件属性模型
- DateType: 日期类型
- DateIterator: 日期迭代器
"""

try:
    from .observation_data import ObservationData
    from .file_attributes import FileAttributes
    from .date_types import DateIterator, DateType

    __all__ = [
        'ObservationData',
        'FileAttributes', 
        'DateType',
        'DateIterator'
    ]
except ImportError as e:
    print(f"导入数据模型模块时出错: {e}")
    __all__ = []
