"""
估算配置中心 - 统一管理所有估算相关配置
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DataSourceConfig:
    """数据源配置"""
    use_real_data: bool = True
    excel_file_path: str = ""
    sheet_name: str = "观测数据"
    date_column: str = "观测日期"
    points_column: str = "每日点数"
    mapsheet_column: str = "图幅号"
    fallback_to_mock: bool = True


@dataclass
class EstimationMethodConfig:
    """估算方法配置"""
    enable_simple_average: bool = True
    enable_weighted_average: bool = True
    enable_exponential_smoothing: bool = True
    enable_linear_regression: bool = True
    enable_monte_carlo: bool = True
    monte_carlo_iterations: int = 10000
    confidence_levels: List[float] = None
    
    def __post_init__(self):
        if self.confidence_levels is None:
            self.confidence_levels = [0.5, 0.8, 0.9, 0.95]


@dataclass
class ChartConfig:
    """图表配置"""
    enable_charts: bool = True
    chart_types: List[str] = None
    chart_style: str = "default"
    dpi: int = 300
    figsize: tuple = (12, 8)
    color_scheme: str = "professional"
    
    def __post_init__(self):
        if self.chart_types is None:
            self.chart_types = ['burndown', 'burnup', 'velocity', 'cumulative']


@dataclass
class OutputConfig:
    """输出配置"""
    output_dir: str = "estimation_output"
    formats: List[str] = None
    include_raw_data: bool = False
    include_charts: bool = True
    compress_output: bool = False
    
    def __post_init__(self):
        if self.formats is None:
            self.formats = ['json', 'excel']


@dataclass
class PerformanceConfig:
    """性能配置"""
    max_workers: int = 4
    cache_enabled: bool = True
    cache_ttl_hours: int = 24
    batch_size: int = 50
    timeout_seconds: int = 300


class EstimationConfigManager:
    """估算配置管理器"""
    
    def __init__(self, config_file: str = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file or "estimation_settings.yaml"
        self._config_cache = {}
        
        # 获取主配置文件路径
        self.main_config_path = Path(__file__).parent.parent.parent / 'config' / 'settings.yaml'
        self.main_config = self._load_main_config()
        
        self._load_default_config()
        self._load_user_config()
    
    def _load_main_config(self):
        """加载主配置文件"""
        try:
            with open(self.main_config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"无法加载主配置文件 {self.main_config_path}: {e}")
            return {}
    
    def get_daily_details_file(self):
        """获取每日统计详情文件路径"""
        # 从主配置文件获取工作空间和文件名
        workspace = self.main_config.get('system', {}).get('workspace', '')
        daily_details_file_name = self.main_config.get('reports', {}).get('statistics', {}).get('daily_details_file_name', '')
        
        if workspace and daily_details_file_name:
            return os.path.join(workspace, daily_details_file_name)
        
        # 备用方案：使用daily_details_file模板
        daily_details_template = self.main_config.get('reports', {}).get('statistics', {}).get('daily_details_file', '')
        if daily_details_template:
            return daily_details_template.format(
                workspace=workspace,
                daily_details_file_name=daily_details_file_name
            )
        
        # 最后备用方案：使用备用目录
        backup_dir = self.main_config.get('reports', {}).get('statistics', {}).get('backup_directory', '')
        if backup_dir and daily_details_file_name:
            backup_path = backup_dir.format(workspace=workspace)
            return os.path.join(backup_path, daily_details_file_name)
        
        raise ValueError("无法从配置文件中确定Excel文件路径")
    
    def get_workspace(self):
        """获取工作空间路径"""
        return self.main_config.get('system', {}).get('workspace', '')
    
    def get_mapsheet_range(self):
        """获取图幅范围"""
        mapsheet_config = self.main_config.get('mapsheet', {})
        return {
            'min': mapsheet_config.get('sequence_min', 41),
            'max': mapsheet_config.get('sequence_max', 51)
        }
    
    def get_main_setting(self, key, default=None):
        """获取主配置项"""
        keys = key.split('.')
        value = self.main_config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value
    
    def _load_default_config(self):
        """加载默认配置"""
        self._config_cache = {
            'data_source': DataSourceConfig(),
            'estimation_methods': EstimationMethodConfig(),
            'charts': ChartConfig(),
            'output': OutputConfig(),
            'performance': PerformanceConfig()
        }
    
    def _load_user_config(self):
        """加载用户配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                
                # 合并用户配置
                if user_config:
                    self._merge_config(user_config)
                
            except Exception as e:
                logger.warning(f"加载用户配置失败，使用默认配置: {e}")
    
    def _merge_config(self, user_config: Dict[str, Any]):
        """合并用户配置到默认配置"""
        for section, values in user_config.items():
            if section in self._config_cache and isinstance(values, dict):
                config_obj = self._config_cache[section]
                for key, value in values.items():
                    if hasattr(config_obj, key):
                        setattr(config_obj, key, value)
    
    def get_data_source_config(self) -> DataSourceConfig:
        """获取数据源配置"""
        return self._config_cache['data_source']
    
    def get_estimation_methods_config(self) -> EstimationMethodConfig:
        """获取估算方法配置"""
        return self._config_cache['estimation_methods']
    
    def get_chart_config(self) -> ChartConfig:
        """获取图表配置"""
        return self._config_cache['charts']
    
    def get_output_config(self) -> OutputConfig:
        """获取输出配置"""
        return self._config_cache['output']
    
    def get_performance_config(self) -> PerformanceConfig:
        """获取性能配置"""
        return self._config_cache['performance']
    
    def update_data_source_config(self, **kwargs):
        """更新数据源配置"""
        config = self._config_cache['data_source']
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    def update_estimation_methods_config(self, **kwargs):
        """更新估算方法配置"""
        config = self._config_cache['estimation_methods']
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    def save_config(self):
        """保存当前配置到文件"""
        try:
            config_dict = {}
            for section, config_obj in self._config_cache.items():
                config_dict[section] = asdict(config_obj)
            
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
                         
            logger.info(f"配置已保存到: {self.config_file}")
                         
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            raise
    
    def reset_to_defaults(self):
        """重置为默认配置"""
        self._load_default_config()
        logger.info("配置已重置为默认值")
