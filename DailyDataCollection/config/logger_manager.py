#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GMAS 日志管理模块 - 基于YAML配置的日志系统

提供统一的日志记录和管理功能
"""

import sys
import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
from typing import Optional, Dict, Any
from functools import wraps
import time

from .config_manager import get_config


class LoggerManager:
    """
    日志管理器 - 单例模式
    
    基于YAML配置提供统一的日志记录功能
    """
    
    _instance = None
    _loggers = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.config = get_config()
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """
        获取日志记录器
        
        Args:
            name: 日志记录器名称，默认使用配置中的名称
            
        Returns:
            配置好的日志记录器
        """
        if name is None:
            name = self.config.get('logging.default.name', 'gmas_logger')
        
        if name not in self._loggers:
            self._loggers[name] = self._create_logger(name)
        
        return self._loggers[name]
    
    def _create_logger(self, name: str) -> logging.Logger:
        """创建配置好的日志记录器"""
        logger = logging.getLogger(name)
        
        # 清除现有处理器
        logger.handlers.clear()
        
        # 设置日志级别
        log_level = self.config.get('logging.default.level', 'INFO')
        logger.setLevel(getattr(logging, log_level.upper()))
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self._get_formatter())
        logger.addHandler(console_handler)
        
        # 添加文件处理器
        log_file = self.config.get('logging.default.log_file', 'gmas_collection.log')
        max_bytes = self.config.get('logging.default.max_bytes', 5242880)
        backup_count = self.config.get('logging.default.backup_count', 2)
        
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(self._get_formatter())
        logger.addHandler(file_handler)
        
        # 添加邮件处理器（如果启用）
        if self.config.get('logging.email.enabled', False):
            self._add_email_handler(logger)
        
        return logger
    
    def _get_formatter(self, format_type: str = 'default') -> logging.Formatter:
        """获取日志格式化器"""
        if format_type == 'simple':
            format_string = '%(asctime)s - %(levelname)s - %(message)s'
        else:
            format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        return logging.Formatter(format_string)
    
    def _add_email_handler(self, logger: logging.Logger):
        """添加邮件通知处理器"""
        email_config = self.config.get_section('logging')['email']
        
        try:
            mail_handler = SMTPHandler(
                mailhost=(email_config['mailhost'], email_config['port']),
                fromaddr=email_config['fromaddr'],
                toaddrs=email_config['toaddrs'],
                subject=email_config['subject'],
                credentials=(email_config['username'], email_config['password']),
                secure=()
            )
            mail_handler.setLevel(logging.ERROR)
            mail_handler.setFormatter(self._get_formatter())
            logger.addHandler(mail_handler)
        except Exception as e:
            logger.warning(f"邮件处理器配置失败: {e}")
    
    def close_all_loggers(self, message: Optional[str] = None):
        """关闭所有日志记录器"""
        for name, logger in self._loggers.items():
            if message:
                logger.info(message)
            
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
        
        self._loggers.clear()


def timer(func):
    """
    性能计时装饰器
    
    记录函数执行时间
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        logger = LoggerManager().get_logger()
        logger.debug(f"函数 '{func.__name__}' 执行耗时 {elapsed_time:.4f} 秒")
        return result
    return wrapper


# 便捷函数
def get_logger(name: Optional[str] = None) -> logging.Logger:
    """获取日志记录器的便捷函数"""
    return LoggerManager().get_logger(name)


if __name__ == "__main__":
    # 测试日志管理器
    try:
        logger = get_logger('test_logger')
        
        logger.debug('这是一个调试消息')
        logger.info('这是一个信息消息')
        logger.warning('这是一个警告消息')
        logger.error('这是一个错误消息')
        logger.critical('这是一个严重错误消息')
        
        # 测试计时装饰器
        @timer
        def test_function():
            time.sleep(0.1)
            return "测试完成"
        
        result = test_function()
        logger.info(f"测试结果: {result}")
        
        # 关闭日志记录器
        LoggerManager().close_all_loggers("测试完成，关闭日志记录器")
        
    except Exception as e:
        print(f"日志管理器测试失败: {e}")
