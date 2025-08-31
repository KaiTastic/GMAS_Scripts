#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GMAS 配置管理器模块 - YAML配置系统

提供统一的配置加载、验证和访问接口
"""

import os
import sys
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


class ConfigError(Exception):
    """配置相关错误"""
    pass


class ConfigManager:
    """
    配置管理器 - 单例模式
    
    负责加载和管理YAML配置文件
    """
    
    _instance = None
    _config = None
    
    def __new__(cls, config_file: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, config_file: Optional[str] = None):
        if self._config is None:
            self._load_config(config_file)
            self._validate_config()
            self._setup_paths()
    
    def _load_config(self, config_file: Optional[str] = None):
        """加载YAML配置文件"""
        if config_file is None:
            # 默认配置文件路径
            project_root = Path(__file__).parent.parent
            config_file = project_root / "config" / "settings.yaml"
        
        config_path = Path(config_file)
        if not config_path.exists():
            raise ConfigError(f"配置文件不存在: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"YAML配置文件解析失败: {e}")
        except Exception as e:
            raise ConfigError(f"配置文件加载失败: {e}")
    
    def _validate_config(self):
        """验证配置完整性"""
        required_sections = [
            'system', 'platform', 'monitoring', 'data_collection',
            'mapsheet', 'fuzzy_matching', 'resources', 'file_paths', 'logging'
        ]
        
        for section in required_sections:
            if section not in self._config:
                raise ConfigError(f"配置文件缺少必需的节: {section}")
    
    def _setup_paths(self):
        """设置和验证文件路径"""
        # 设置项目根目录
        if self._config['system']['current_path'] is None:
            self._config['system']['current_path'] = str(Path(__file__).parent.parent)
        
        # 创建统一的paths配置节
        platform_config = self.get_platform_config()
        
        self._config['paths'] = {
            'workspace': self._config['system']['workspace'],
            'wechat_folder': platform_config.get('wechat_folder', ''),
            'current_path': self._config['system']['current_path']
        }
        
        # 解析文件路径模板（如果存在）
        if 'file_paths' in self._config and 'resources' in self._config:
            current_path = Path(self._config['system']['current_path'])
            resources = self._config['resources']
            
            # 构建完整文件路径
            file_paths = {}
            for key, template in self._config['file_paths'].items():
                if '{' in template:
                    # 替换模板变量
                    path_str = template.format(**resources)
                else:
                    path_str = template
                
                file_paths[key] = str(current_path / path_str)
            
            self._config['resolved_paths'] = file_paths
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        支持点号分隔的嵌套键，如 'system.workspace'
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置字典"""
        return self._config
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取配置节"""
        return self._config.get(section, {})
    
    def get_resolved_path(self, path_key: str) -> str:
        """获取解析后的文件路径"""
        return self._config['resolved_paths'].get(path_key, '')
    
    def validate_files(self) -> bool:
        """验证必需文件是否存在"""
        required_files = [
            'sheet_names_file',
            'icon_file', 
            'kml_schema_22',
            'kml_schema_23'
        ]
        
        missing_files = []
        for file_key in required_files:
            file_path = self.get_resolved_path(file_key)
            if not os.path.exists(file_path):
                missing_files.append(f"{file_key}: {file_path}")
        
        if missing_files:
            raise ConfigError(f"以下必需文件不存在:\n" + "\n".join(missing_files))
        
        return True
    
    def get_platform_config(self) -> Dict[str, Any]:
        """获取当前平台的配置"""
        platform_config = self.get_section('platform')
        
        # 确定微信文件夹路径
        if sys.platform.startswith('win'):
            wechat_folder = platform_config['wechat_folders']['windows']
        elif sys.platform.startswith('darwin'):
            wechat_folder = platform_config['wechat_folders']['macos']
            if not wechat_folder:
                wechat_folder = os.path.expanduser("~/Documents/WeChat Files")
        else:
            raise ConfigError(f"不支持的平台: {sys.platform}")
        
        return {
            'wechat_folder': wechat_folder,
            'platform': sys.platform
        }
    
    def get_monitor_endtime(self) -> datetime:
        """获取监控结束时间"""
        end_time_config = self.get('monitoring.end_time')
        now = datetime.now()
        return now.replace(
            hour=end_time_config['hour'],
            minute=end_time_config['minute'], 
            second=end_time_config['second'],
            microsecond=0
        )


@dataclass
class DateType:
    """日期类型处理"""
    
    date_datetime: datetime = None
    yyyymmdd_str: str = ''
    yymmdd_str: str = ''
    yyyy_str: str = ''
    yyyy_mm_str: str = ''
    yy_str: str = ''
    mm_str: str = ''
    dd_str: str = ''
    yymm_str: str = ''
    
    def __post_init__(self):
        if self.yyyymmdd_str:
            self.date_datetime = datetime.strptime(self.yyyymmdd_str, "%Y%m%d")
        elif self.date_datetime:
            self.yyyymmdd_str = self.date_datetime.strftime("%Y%m%d")
        self._set_date_strings()
    
    def _set_date_strings(self):
        if self.date_datetime:
            self.yymmdd_str = self.date_datetime.strftime("%y%m%d")
            self.yyyymm_str = self.date_datetime.strftime("%Y%m")
            self.yyyy_str = self.date_datetime.strftime("%Y")
            self.yy_str = self.date_datetime.strftime("%y")
            self.mm_str = self.date_datetime.strftime("%m")
            self.dd_str = self.date_datetime.strftime("%d")
            self.yyyy_mm_str = self.date_datetime.strftime("%Y-%m")
            self.yymm_str = self.date_datetime.strftime("%y%m")
    
    def __str__(self):
        return self.yyyymmdd_str


# 全局配置实例
config = ConfigManager()


def get_config() -> ConfigManager:
    """获取全局配置实例"""
    return config


if __name__ == "__main__":
    # 测试配置管理器
    try:
        cfg = ConfigManager()
        print("配置加载成功")
        print(f"工作空间: {cfg.get('system.workspace')}")
        print(f"图幅序号范围: {cfg.get('mapsheet.sequence_min')}-{cfg.get('mapsheet.sequence_max')}")
        print(f"模糊匹配阈值: {cfg.get('fuzzy_matching.threshold')}")
        
        # 验证文件
        cfg.validate_files()
        print("所有必需文件验证通过")
        
        # 测试平台配置
        platform_info = cfg.get_platform_config()
        print(f"当前平台: {platform_info['platform']}")
        
    except ConfigError as e:
        print(f"配置错误: {e}")
    except Exception as e:
        print(f"未预期的错误: {e}")
