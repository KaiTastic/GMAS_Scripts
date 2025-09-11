#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GMAS 配置模块 - 统一配置管理

提供企业级的配置管理解决方案，整合了：
- 统一配置管理
- 配置热重载
- 配置验证
- 多环境支持
- 智能缓存
- 线程安全

使用示例:
    from config import get_config
    
    config = get_config()
    app_name = config.get('system.app_name', 'GMAS')
    config.set('features.new_feature', True)
    
    # 支持点号语法的配置访问
    db_host = config.get('database.connection.host')
    
    # 配置节访问
    logging_config = config.get_section('logging')
"""

# 导入统一配置管理器
from .config_manager import (
    ConfigManager,
    ConfigError,
    DateType,
    ConfigValidationRule,
    get_config
)

# 导出接口
__all__ = [
    'ConfigManager',
    'ConfigError', 
    'DateType',
    'ConfigValidationRule',
    'get_config',
]

# 全局配置实例，便于直接使用
config = get_config()

# 版本信息
__version__ = '2.0.0'
__author__ = 'GMAS Team'
__description__ = 'Enterprise-grade configuration management for GMAS project'
