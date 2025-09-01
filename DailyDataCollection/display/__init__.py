"""
Display 模块 - 专门处理所有类型的显示功能

这个模块提供了不同类型的显示管理器：
- MonitorDisplay: 监控相关显示
- CollectionDisplay: 数据收集统计显示  
- ReportDisplay: 报告相关显示
- MessageDisplay: 通用消息显示
"""

from .monitor_display import MonitorDisplay
from .collection_display import CollectionDisplay
from .report_display import ReportDisplay
from .message_display import MessageDisplay

__all__ = [
    'MonitorDisplay',
    'CollectionDisplay', 
    'ReportDisplay',
    'MessageDisplay'
]
