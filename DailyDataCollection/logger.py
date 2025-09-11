#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GMAS 项目统一日志管理模块

提供项目级的日志记录和管理功能，支持：
- 多级别日志记录
- 文件轮转
- 控制台输出
- 模块级日志管理
- 配置驱动
"""

import logging
import logging.handlers
import sys
import os
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
from functools import wraps
import time


class LoggerManager:
    """
    统一日志管理器 - 单例模式
    
    提供项目级的日志记录和管理功能
    """
    
    _instance = None
    _loggers: Dict[str, logging.Logger] = {}
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._setup_default_config()
            self._initialized = True
    
    def _setup_default_config(self):
        """设置默认配置"""
        self.default_config = {
            'level': 'INFO',
            'console_level': 'INFO',
            'file_level': 'DEBUG',
            'log_dir': './logs',
            'log_file': 'gmas_collection.log',
            'max_bytes': 5 * 1024 * 1024,  # 5MB
            'backup_count': 3,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'date_format': '%Y-%m-%d %H:%M:%S'
        }
    
    def update_config(self, config: Dict[str, Any]):
        """更新日志配置"""
        self.default_config.update(config)
        # 重新配置所有已创建的日志器
        for logger_name in list(self._loggers.keys()):
            del self._loggers[logger_name]
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """
        获取日志记录器
        
        Args:
            name: 日志记录器名称，默认为 'GMAS'
            
        Returns:
            配置好的日志记录器
        """
        if name is None:
            name = 'GMAS'
        
        if name not in self._loggers:
            self._loggers[name] = self._create_logger(name)
        
        return self._loggers[name]
    
    def _create_logger(self, name: str) -> logging.Logger:
        """创建并配置日志记录器"""
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, self.default_config['level']))
        
        # 清除现有处理器
        logger.handlers.clear()
        
        # 创建格式化器
        formatter = logging.Formatter(
            self.default_config['format'],
            self.default_config['date_format']
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.default_config['console_level']))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 文件处理器
        log_dir = Path(self.default_config['log_dir'])
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / self.default_config['log_file']
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.default_config['max_bytes'],
            backupCount=self.default_config['backup_count'],
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, self.default_config['file_level']))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger


# 全局日志管理器实例
_logger_manager = LoggerManager()

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取日志记录器的便捷函数
    
    Args:
        name: 日志记录器名称
        
    Returns:
        配置好的日志记录器
    """
    return _logger_manager.get_logger(name)

def configure_logging(config: Dict[str, Any]):
    """
    配置日志系统
    
    Args:
        config: 日志配置字典
    """
    _logger_manager.update_config(config)

def timer(func):
    """
    性能计时装饰器
    
    用于测量函数执行时间
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger('timer')
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            logger.info(f"{func.__name__} 执行时间: {end_time - start_time:.4f}秒")
            return result
        except Exception as e:
            end_time = time.time()
            logger.error(f"{func.__name__} 执行失败 (耗时: {end_time - start_time:.4f}秒): {e}")
            raise
    return wrapper

# 默认日志记录器
logger = get_logger()

# 导出接口
__all__ = [
    'LoggerManager',
    'get_logger', 
    'configure_logging',
    'timer',
    'logger'
]

if __name__ == "__main__":
    # 测试日志功能
    test_logger = get_logger('test')
    test_logger.info("这是一条测试信息")
    test_logger.debug("这是一条调试信息")
    test_logger.warning("这是一条警告信息")
    test_logger.error("这是一条错误信息")



