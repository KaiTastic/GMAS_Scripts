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
        
        # 可选配置节
        optional_sections = ['reports']
        
        for section in required_sections:
            if section not in self._config:
                raise ConfigError(f"配置文件缺少必需的节: {section}")
        
        # 记录可选配置节的存在情况
        for section in optional_sections:
            if section not in self._config:
                logger = self._get_logger()
                logger.debug(f"可选配置节 '{section}' 未找到，将使用默认设置")
    
    def _get_logger(self):
        """获取logger实例"""
        import logging
        return logging.getLogger(__name__)
    
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
    
    def resolve_path_template(self, path_template: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        解析路径模板中的变量
        
        支持的模板变量：
        - {workspace} / {{workspace}} - 工作空间路径
        - {date}, {year}, {month}, {day} - 日期相关变量
        - 任何在context中提供的自定义变量
        
        :param path_template: 包含模板变量的路径字符串
        :param context: 额外的模板变量上下文（如日期对象、自定义配置等）
        :return: 解析后的完整路径
        """
        try:
            if not path_template:
                return path_template
            
            resolved_path = path_template
            
            # 1. 基础路径变量替换
            workspace = (
                self._config.get('paths', {}).get('workspace') or 
                self._config.get('system', {}).get('workspace', 'D:\\RouteDesign')
            )
            
            # 替换工作空间变量（支持单双花括号）
            resolved_path = resolved_path.replace('{{workspace}}', workspace)
            resolved_path = resolved_path.replace('{workspace}', workspace)
            
            # 2. 处理上下文变量
            if context:
                # 处理日期相关变量
                if 'date_obj' in context:
                    date_obj = context['date_obj']
                    if hasattr(date_obj, 'date_datetime') and date_obj.date_datetime:
                        date_vars = {
                            'date': date_obj.date_datetime.strftime('%Y%m%d'),
                            'year': date_obj.date_datetime.strftime('%Y'),
                            'month': date_obj.date_datetime.strftime('%m'),
                            'day': date_obj.date_datetime.strftime('%d'),
                            'yyyymm': date_obj.date_datetime.strftime('%Y%m'),
                        }
                        
                        for var, value in date_vars.items():
                            resolved_path = resolved_path.replace(f'{{{{{var}}}}}', value)
                            resolved_path = resolved_path.replace(f'{{{var}}}', value)
                
                # 处理统计配置变量
                if 'stats_config' in context:
                    stats_config = context['stats_config']
                    if isinstance(stats_config, dict):
                        for key, value in stats_config.items():
                            if isinstance(value, str):
                                resolved_path = resolved_path.replace(f'{{{{{key}}}}}', value)
                                resolved_path = resolved_path.replace(f'{{{key}}}', value)
                
                # 处理其他自定义变量
                for key, value in context.items():
                    if key not in ['date_obj', 'stats_config'] and isinstance(value, str):
                        resolved_path = resolved_path.replace(f'{{{{{key}}}}}', value)
                        resolved_path = resolved_path.replace(f'{{{key}}}', value)
            
            # 3. 日志记录（调试级别）
            if resolved_path != path_template:
                logging.getLogger(__name__).debug(
                    f"路径模板解析: '{path_template}' -> '{resolved_path}'"
                )
            
            return resolved_path
            
        except Exception as e:
            logging.getLogger(__name__).error(f"路径模板解析失败: {e}")
            return path_template  # 返回原始模板作为后备
    
    def get_statistics_file_path(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        获取统计报告文件路径，支持模板解析和回退机制
        
        :param context: 上下文信息，包含日期对象、自定义路径等
        :return: 解析后的统计文件完整路径
        """
        try:
            # 1. 优先使用自定义路径（命令行参数）
            if context and 'custom_path' in context and context['custom_path']:
                custom_path = context['custom_path']
                # 自定义路径也支持模板解析
                resolved_custom_path = self.resolve_path_template(custom_path, context)
                logging.getLogger(__name__).info(f"使用自定义统计报告路径: {resolved_custom_path}")
                return resolved_custom_path
            
            # 2. 使用配置文件中的路径
            if 'reports' in self._config and 'statistics' in self._config['reports']:
                stats_config = self._config['reports']['statistics']
                
                if 'daily_details_file' in stats_config:
                    file_path_template = stats_config['daily_details_file']
                    
                    # 构建解析上下文
                    resolve_context = context.copy() if context else {}
                    resolve_context['stats_config'] = stats_config
                    
                    # 解析路径模板
                    resolved_path = self.resolve_path_template(file_path_template, resolve_context)
                    
                    # 验证路径是否可用
                    import os
                    directory = os.path.dirname(resolved_path)
                    if os.path.exists(directory) or self._ensure_directory_exists(directory):
                        return resolved_path
                    
                    # 如果主路径不可用，尝试备用目录
                    if 'backup_directory' in stats_config:
                        backup_dir_template = stats_config['backup_directory']
                        backup_dir = self.resolve_path_template(backup_dir_template, resolve_context)
                        
                        if self._ensure_directory_exists(backup_dir):
                            filename = os.path.basename(resolved_path)
                            backup_path = os.path.join(backup_dir, filename)
                            logging.getLogger(__name__).warning(
                                f"主路径不可用，使用备用路径: {backup_path}"
                            )
                            return backup_path
            
            # 3. 回退到硬编码路径（向后兼容）
            fallback_path = 'D:\\RouteDesign\\Daily_statistics_details_for_Group_3.2.xlsx'
            logging.getLogger(__name__).warning(
                f"配置文件中未找到统计报告路径配置，使用默认路径: {fallback_path}"
            )
            return fallback_path
            
        except Exception as e:
            # 异常情况下的回退路径
            fallback_path = 'D:\\RouteDesign\\Daily_statistics_details_for_Group_3.2.xlsx'
            logging.getLogger(__name__).error(
                f"获取统计报告路径时发生错误: {e}，使用默认路径: {fallback_path}"
            )
            return fallback_path
    
    def _ensure_directory_exists(self, directory_path: str) -> bool:
        """
        确保目录存在，如果不存在则尝试创建
        
        :param directory_path: 目录路径
        :return: 目录是否存在或创建成功
        """
        try:
            import os
            if not os.path.exists(directory_path):
                os.makedirs(directory_path, exist_ok=True)
                logging.getLogger(__name__).info(f"创建目录: {directory_path}")
            return True
        except Exception as e:
            logging.getLogger(__name__).error(f"无法创建目录 {directory_path}: {e}")
            return False
    
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
