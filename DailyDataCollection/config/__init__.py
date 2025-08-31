#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GMAS 配置模块 - 统一配置管理

提供基于YAML的模块化配置系统
"""

from .config_manager import (
    ConfigManager,
    ConfigError,
    DateType,
    get_config
)

from .logger_manager import (
    LoggerManager,
    get_logger,
    timer
)

# 导出主要接口
__all__ = [
    # 配置管理
    'ConfigManager',
    'ConfigError', 
    'DateType',
    'get_config',
    
    # 日志管理
    'LoggerManager',
    'get_logger',
    'timer',
    
    # 便捷访问
    'config',
    'logger'
]

# 全局实例
config = get_config()
logger = get_logger()

# 兼容性常量（供现有代码使用）
try:
    # 基础配置
    WORKSPACE = config.get('system.workspace')
    WECHAT_FOLDER = config.get_platform_config()['wechat_folder']
    
    # 监控配置
    MONITOR_TIME_INTERVAL_SECOND = config.get('monitoring.time_interval_seconds')
    MONITOR_STATUS_INTERVAL_MINUTE = config.get('monitoring.status_interval_minutes')
    MONITOR_ENDTIME = config.get_monitor_endtime()
    
    # 数据收集配置
    TRACEBACK_DATE = config.get('data_collection.traceback_date')
    TRACEBACK_DAYS = config.get('data_collection.traceback_days')
    TRACEFORWARD_DAYS = config.get('data_collection.traceforward_days')
    COLLECTION_WEEKDAYS = config.get('data_collection.collection_weekdays')
    
    # 图幅配置
    SEQUENCE_MIN = config.get('mapsheet.sequence_min')
    SEQUENCE_MAX = config.get('mapsheet.sequence_max')
    
    # 模糊匹配配置
    ENABLE_FUZZY_MATCHING = config.get('fuzzy_matching.enabled')
    FUZZY_MATCHING_THRESHOLD = config.get('fuzzy_matching.threshold')
    FUZZY_MATCHING_DEBUG = config.get('fuzzy_matching.debug')
    
    # 资源文件配置
    SHEET_NAMES_LUT_100K = config.get('resources.sheet_names_lut')
    ICON_FILE_1 = config.get('resources.icon_file')
    MAP_PROJECT_FOLDER = config.get('resources.map_project_folder')
    
    # 文件路径
    SHEET_NAMES_FILE = config.get_resolved_path('sheet_names_file')
    ICON_1 = config.get_resolved_path('icon_file')
    KML_SCHEMA_22 = config.get_resolved_path('kml_schema_22')
    KML_SCHEMA_23 = config.get_resolved_path('kml_schema_23')
    
    # 验证必需文件
    config.validate_files()
    
    # 空字典常量
    EMPTY_DICT = {}
    
except Exception as e:
    logger.error(f"配置初始化失败: {e}")
    raise
