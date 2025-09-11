#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GMAS 统一配置管理器 - 企业级配置管理解决方案

整合了基础配置管理和高级功能：
- YAML配置加载和验证
- 配置热重载
- 配置缓存
- 多环境支持
- 配置路径访问（支持点号语法）
"""

import os
import sys
import yaml
import threading
import time
import platform
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 导入项目日志模块
from logger import get_logger


class ConfigError(Exception):
    """配置相关错误"""
    pass


class DateType(Enum):
    """日期类型枚举"""
    TODAY = "today"
    YESTERDAY = "yesterday"
    CUSTOM = "custom"


@dataclass
class ConfigValidationRule:
    """配置验证规则"""
    path: str  # 配置路径，如 "database.host"
    required: bool = True
    type_check: Optional[type] = None
    validator: Optional[Callable] = None
    default: Any = None


class ConfigurationWatcher(FileSystemEventHandler):
    """配置文件监控器"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.logger = get_logger('config.watcher')
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(('.yaml', '.yml')):
            self.logger.info(f"配置文件已修改: {event.src_path}")
            self.config_manager.reload_config()


class ConfigManager:
    """
    统一配置管理器 - 单例模式
    
    整合了基础和高级配置管理功能
    """
    
    _instance = None
    _config = None
    _lock = threading.RLock()
    
    def __new__(cls, config_file: Optional[str] = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, config_file: Optional[str] = None):
        if self._config is None:
            with self._lock:
                if self._config is None:
                    self.logger = get_logger('config')
                    self._observers = []
                    self._cache = {}
                    self._cache_ttl = {}
                    self._validation_rules: List[ConfigValidationRule] = []
                    self._config_file = None
                    self._file_observer = None
                    
                    # 平台检测
                    self._setup_platform()
                    
                    self._load_config(config_file)
                    self._validate_config()
                    self._setup_paths()
                    self._setup_file_watcher()
    
    def _load_config(self, config_file: Optional[str] = None):
        """加载YAML配置文件"""
        if config_file is None:
            # 默认配置文件路径
            project_root = Path(__file__).parent
            config_file = project_root / "settings.yaml"
        
        self._config_file = Path(config_file)
        
        if not self._config_file.exists():
            raise ConfigError(f"配置文件不存在: {self._config_file}")
        
        try:
            with open(self._config_file, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
            self.logger.info(f"配置文件加载成功: {self._config_file}")
        except yaml.YAMLError as e:
            raise ConfigError(f"YAML配置文件解析错误: {e}")
        except Exception as e:
            raise ConfigError(f"配置文件加载失败: {e}")
    
    def _setup_platform(self):
        """检测当前平台并设置平台特定配置"""
        system = platform.system().lower()
        if system == 'darwin':
            self._platform = 'macos'
        elif system == 'windows':
            self._platform = 'windows'
        elif system == 'linux':
            self._platform = 'linux'
        else:
            self._platform = 'default'
            self.logger.warning(f"未知平台: {system}，使用默认配置")
        
        self.logger.info(f"检测到平台: {self._platform}")
    
    def get_platform(self) -> str:
        """获取当前平台标识"""
        return getattr(self, '_platform', 'default')
    
    def _validate_config(self):
        """验证配置文件内容"""
        # 基础结构验证
        required_sections = ['data_collection', 'file_paths', 'logging']
        
        for section in required_sections:
            if section not in self._config:
                self.logger.warning(f"配置文件缺少必需的节: {section}")
        
        # 自定义验证规则
        for rule in self._validation_rules:
            self._validate_rule(rule)
    
    def _validate_rule(self, rule: ConfigValidationRule):
        """验证单个配置规则"""
        value = self.get(rule.path)
        
        if rule.required and value is None:
            if rule.default is not None:
                self.set(rule.path, rule.default)
            else:
                raise ConfigError(f"必需的配置项缺失: {rule.path}")
        
        if value is not None and rule.type_check:
            if not isinstance(value, rule.type_check):
                raise ConfigError(f"配置项类型错误: {rule.path}, 期望 {rule.type_check}, 实际 {type(value)}")
        
        if value is not None and rule.validator:
            if not rule.validator(value):
                raise ConfigError(f"配置项验证失败: {rule.path}")
    
    def _setup_paths(self):
        """设置路径相关配置"""
        # 确保日志目录存在
        log_dir = Path('./logs')
        log_dir.mkdir(exist_ok=True)
        
        # 确保输出目录存在
        output_dirs = [
            'estimation_output',
            'resource',
            'resource/private'
        ]
        
        for dir_path in output_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def _setup_file_watcher(self):
        """设置配置文件监控"""
        try:
            self._watcher = ConfigurationWatcher(self)
            self._file_observer = Observer()
            self._file_observer.schedule(
                self._watcher,
                str(self._config_file.parent),
                recursive=False
            )
            self._file_observer.start()
            self.logger.info("配置文件监控已启动")
        except Exception as e:
            self.logger.warning(f"配置文件监控启动失败: {e}")
    
    def get(self, key: str, default: Any = None, use_cache: bool = True, expand_vars: bool = True) -> Any:
        """
        获取配置值（支持点号路径）
        
        Args:
            key: 配置键，支持点号分隔的路径，如 'logging.default.level'
            default: 默认值
            use_cache: 是否使用缓存
            expand_vars: 是否展开变量和引用
            
        Returns:
            配置值
        """
        cache_key = f"{key}_{expand_vars}" if expand_vars else key
        
        if use_cache and cache_key in self._cache:
            if cache_key not in self._cache_ttl or time.time() < self._cache_ttl[cache_key]:
                return self._cache[cache_key]
        
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                if isinstance(value, dict):
                    value = value[k]
                else:
                    return default
            
            # 展开变量和引用
            if expand_vars and isinstance(value, str):
                value = self._expand_variables(value)
            
            # 缓存结果（默认缓存5分钟）
            if use_cache:
                self._cache[cache_key] = value
                self._cache_ttl[cache_key] = time.time() + 300  # 5分钟
            
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置值
        
        Args:
            key: 配置键，支持点号分隔的路径
            value: 配置值
        """
        keys = key.split('.')
        config = self._config
        
        # 导航到目标位置
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            elif not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        
        # 设置值
        old_value = config.get(keys[-1])
        config[keys[-1]] = value
        
        # 清除相关缓存
        self._clear_cache_for_key(key)
        
        # 通知观察者
        self._notify_observers(key, old_value, value)
        
        self.logger.debug(f"配置已更新: {key} = {value}")
    
    def _expand_variables(self, value: str, max_depth: int = 10) -> str:
        """
        展开配置中的变量和引用
        
        支持的格式：
        - {key.subkey} - 引用其他配置值
        - {platform.workspace} - 引用平台特定工作空间
        - {workspace} - 引用 system.workspace
        - {daily_details_file_name} - 引用 reports.statistics.daily_details_file_name
        
        Args:
            value: 包含变量的字符串
            max_depth: 最大递归深度，防止循环引用
            
        Returns:
            展开后的字符串
        """
        if not isinstance(value, str) or '{' not in value or max_depth <= 0:
            return value
        
        # 查找所有 {key} 模式
        pattern = r'\{([^}]+)\}'
        matches = re.findall(pattern, value)
        
        if not matches:
            return value
        
        expanded_value = value
        
        for var_name in matches:
            var_value = None
            
            # 处理平台特定变量
            if var_name.startswith('platform.'):
                var_value = self._get_platform_specific_value(var_name)
            # 特殊处理一些常用变量
            elif var_name == 'workspace':
                var_value = self.get('system.workspace', expand_vars=False)
            elif var_name == 'daily_details_file_name':
                var_value = self.get('reports.statistics.daily_details_file_name', expand_vars=False)
            else:
                # 普通的配置引用
                var_value = self.get(var_name, expand_vars=False)
            
            if var_value is not None:
                # 如果引用的值也包含变量，递归展开
                if isinstance(var_value, str) and '{' in var_value:
                    var_value = self._expand_variables(var_value, max_depth - 1)
                
                # 路径标准化
                if isinstance(var_value, str):
                    var_value = self._normalize_path(var_value)
                
                expanded_value = expanded_value.replace(f'{{{var_name}}}', str(var_value))
        
        return expanded_value
    
    def _get_platform_specific_value(self, var_name: str) -> Any:
        """获取平台特定的配置值"""
        # 移除 'platform.' 前缀
        key_parts = var_name[9:].split('.')  # 移除 'platform.' 
        
        # 构建平台特定的键路径
        platform_key = f"platform.{'.'.join(key_parts)}.{self._platform}"
        platform_value = self.get(platform_key, expand_vars=False)
        
        if platform_value is not None:
            return platform_value
        
        # 尝试获取默认值
        default_key = f"platform.{'.'.join(key_parts)}.default"
        default_value = self.get(default_key, expand_vars=False)
        
        if default_value is not None:
            self.logger.debug(f"使用默认平台配置: {default_key}")
            return default_value
        
        # 如果都没有找到，记录警告
        self.logger.warning(f"未找到平台特定配置: {var_name} (平台: {self._platform})")
        return None
    
    def _normalize_path(self, path: str) -> str:
        """统一路径格式，处理不同平台的路径分隔符"""
        if not isinstance(path, str):
            return path
            
        # 统一使用正斜杠
        normalized = path.replace('\\', '/')
        
        # 对于Windows绝对路径特殊处理 (保持驱动器字母格式)
        if self._platform == 'windows' and re.match(r'^[a-zA-Z]:/', normalized):
            return normalized
        
        # 对于其他平台的绝对路径
        if normalized.startswith('/'):
            return normalized
            
        # 相对路径保持不变
        return normalized

    def _clear_cache_for_key(self, key: str):
        """清除指定键的缓存"""
        # 清除精确匹配的缓存
        if key in self._cache:
            del self._cache[key]
            del self._cache_ttl[key]
        
        # 清除以此键开头的所有缓存
        prefix = key + '.'
        keys_to_remove = [k for k in self._cache.keys() if k.startswith(prefix)]
        for k in keys_to_remove:
            del self._cache[k]
            del self._cache_ttl[k]
    
    def reload_config(self):
        """重新加载配置文件"""
        try:
            old_config = self._config.copy()
            self._load_config()
            self._validate_config()
            
            # 清除所有缓存
            self._cache.clear()
            self._cache_ttl.clear()
            
            self.logger.info("配置文件重新加载成功")
            
            # 通知配置变更
            self._notify_observers('__config_reloaded__', old_config, self._config)
            
        except Exception as e:
            self.logger.error(f"配置文件重新加载失败: {e}")
            raise ConfigError(f"配置重新加载失败: {e}")
    
    def add_validation_rule(self, rule: ConfigValidationRule):
        """添加配置验证规则"""
        self._validation_rules.append(rule)
    
    def add_observer(self, observer: Callable[[str, Any, Any], None]):
        """添加配置变更观察者"""
        self._observers.append(observer)
    
    def _notify_observers(self, key: str, old_value: Any, new_value: Any):
        """通知配置变更观察者"""
        for observer in self._observers:
            try:
                observer(key, old_value, new_value)
            except Exception as e:
                self.logger.error(f"通知观察者失败: {e}")
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取整个配置节"""
        return self.get(section, {})
    
    def has_key(self, key: str) -> bool:
        """检查配置键是否存在"""
        return self.get(key) is not None
    
    def save_config(self, file_path: Optional[str] = None):
        """保存当前配置到文件"""
        target_file = Path(file_path) if file_path else self._config_file
        
        try:
            with open(target_file, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
            self.logger.info(f"配置已保存到: {target_file}")
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            raise ConfigError(f"保存配置失败: {e}")
    
    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()
    
    def clear_cache(self):
        """清除所有缓存"""
        self._cache.clear()
        self._cache_ttl.clear()
        self.logger.info("配置缓存已清除")
    
    def __del__(self):
        """析构函数，停止文件监控"""
        if hasattr(self, '_file_observer') and self._file_observer:
            try:
                self._file_observer.stop()
                self._file_observer.join()
            except:
                pass


# 全局配置管理器实例
_config_manager = ConfigManager()

def get_config() -> ConfigManager:
    """获取全局配置管理器实例"""
    return _config_manager

# 导出接口
__all__ = [
    'ConfigManager',
    'ConfigError',
    'DateType',
    'ConfigValidationRule',
    'get_config'
]
