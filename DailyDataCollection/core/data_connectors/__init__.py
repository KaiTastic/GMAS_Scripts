"""
数据连接器模块

提供统一的数据访问层，支持各种数据源的读取和处理
"""

from .excel_data_connector import ExcelDataConnector

__all__ = ['ExcelDataConnector']
