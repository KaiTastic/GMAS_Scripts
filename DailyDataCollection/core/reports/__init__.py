"""
报告生成模块

包含各种报告生成器：
- Excel报告生成
- 数据提交报告
"""

try:
    from .data_submission import DataSubmition

    __all__ = [
        'DataSubmition'
    ]
except ImportError as e:
    print(f"导入报告生成模块时出错: {e}")
    __all__ = []
