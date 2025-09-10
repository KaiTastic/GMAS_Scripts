"""
核心估算器 - 整合所有估算功能的统一入口
"""

import os
import logging
import time
import pandas as pd
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ._internal.data_analyzer import DataAnalyzer
from ._internal.finish_date_estimator import FinishDateEstimator
from ._internal.method_integrator import MethodIntegrator
from ._internal.progress_charts import ProgressCharts
from .estimation_config import EstimationConfigManager, DataSourceConfig, EstimationMethodConfig
from ..data_models.date_types import DateType

logger = logging.getLogger(__name__)


class EstimationMode(Enum):
    """估算模式"""
    BASIC = "basic"           # 基础模式
    ADVANCED = "advanced"     # 高级模式（包含智能集成）
    MAPSHEET = "mapsheet"     # 图幅模式
    REAL_TIME = "real_time"   # 实时模式


@dataclass
class EstimationConfig:
    """估算配置"""
    mode: EstimationMode = EstimationMode.ADVANCED
    days_back: int = 30
    confidence_level: float = 0.8
    use_real_data: bool = True
    enable_charts: bool = True
    enable_integration: bool = True
    output_formats: List[str] = None
    
    def __post_init__(self):
        if self.output_formats is None:
            self.output_formats = ['json', 'excel', 'charts']


class CoreEstimator:
    """核心估算器 - 统一的估算功能入口"""
    
    def __init__(self, workspace_path: str = None, config: EstimationConfig = None):
        """
        初始化核心估算器
        
        Args:
            workspace_path: 工作空间路径
            config: 估算配置
        """
        self.workspace_path = workspace_path or os.getcwd()
        self.config = config or EstimationConfig()
        
        # 初始化配置管理器
        self.config_manager = EstimationConfigManager()
        
        # 初始化核心组件
        self._init_components()
        
        # 缓存管理
        self._result_cache = {}
        self._cache_timestamps = {}
        
        logger.info(f"核心估算器初始化完成 - 模式: {self.config.mode.value}")
        
    def _init_components(self):
        """初始化各个组件"""
        try:
            # 获取配置
            data_config = self.config_manager.get_data_source_config()
            
            # 初始化数据分析器
            self.data_analyzer = DataAnalyzer(
                self.workspace_path, 
                use_real_data=self.config.use_real_data
            )
            
            # 延迟初始化其他组件
            self.finish_estimator = None
            self.method_integrator = None
            self.charts_generator = None
            
            logger.info("核心组件初始化完成")
            
        except Exception as e:
            logger.error(f"初始化组件失败: {e}")
            raise
        
    def estimate_project(self, 
                        target_points: int,
                        current_points: int = None,
                        start_date: DateType = None,
                        target_date: DateType = None) -> Dict[str, Any]:
        """
        执行项目估算
        
        Args:
            target_points: 目标点数
            current_points: 当前点数
            start_date: 开始日期
            target_date: 目标日期
            
        Returns:
            Dict[str, Any]: 完整的估算结果
        """
        try:
            logger.info(f"开始项目估算 - 目标点数: {target_points}, 当前点数: {current_points}")
            
            # 检查缓存
            cache_key = self._generate_cache_key(target_points, current_points, start_date, target_date)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                logger.info("使用缓存结果")
                return cached_result
            
            # 1. 数据准备
            data_prepared = self._prepare_data(start_date)
            if not data_prepared:
                return self._create_error_result("数据准备失败")
            
            # 2. 初始化估算器
            if not self.finish_estimator:
                self.finish_estimator = FinishDateEstimator(self.data_analyzer)
            
            # 3. 执行基础估算
            basic_results = self._execute_basic_estimation(
                target_points, current_points, target_date
            )
            
            if not basic_results or 'error' in basic_results:
                return basic_results or self._create_error_result("基础估算失败")
            
            # 4. 智能集成（如果启用）
            integrated_results = None
            if self.config.enable_integration:
                integrated_results = self._execute_integration(basic_results)
            
            # 5. 生成图表（如果启用）
            chart_results = None
            if self.config.enable_charts:
                chart_results = self._generate_charts(target_points, current_points)
            
            # 6. 整合结果
            final_results = self._compile_results(basic_results, integrated_results, chart_results)
            
            # 7. 缓存结果
            self._cache_result(cache_key, final_results)
            
            logger.info("项目估算完成")
            return final_results
            
        except Exception as e:
            logger.error(f"项目估算失败: {e}")
            return self._create_error_result(str(e))
    
    def estimate_mapsheet(self, mapsheet_no: str) -> Dict[str, Any]:
        """
        执行单个图幅估算
        
        Args:
            mapsheet_no: 图幅编号
            
        Returns:
            Dict[str, Any]: 图幅估算结果
        """
        try:
            logger.info(f"开始图幅估算: {mapsheet_no}")
            
            # 检查数据
            if not self._prepare_data():
                return self._create_error_result("数据准备失败")
            
            # 获取图幅特定数据
            mapsheet_data = self._get_mapsheet_data(mapsheet_no)
            if not mapsheet_data:
                return self._create_error_result(f"未找到图幅 {mapsheet_no} 的数据")
            
            # 执行图幅级别估算
            mapsheet_results = self._execute_mapsheet_estimation(mapsheet_no, mapsheet_data)
            
            logger.info(f"图幅估算完成: {mapsheet_no}")
            return mapsheet_results
            
        except Exception as e:
            logger.error(f"图幅估算失败 {mapsheet_no}: {e}")
            return self._create_error_result(str(e))
    
    def batch_estimate_mapsheets(self, mapsheet_list: List[str] = None) -> Dict[str, Any]:
        """
        批量图幅估算
        
        Args:
            mapsheet_list: 图幅列表，None表示所有图幅
            
        Returns:
            Dict[str, Any]: 批量估算结果
        """
        try:
            logger.info(f"开始批量图幅估算, 图幅数量: {len(mapsheet_list) if mapsheet_list else '全部'}")
            
            # 准备数据
            if not self._prepare_data():
                return self._create_error_result("数据准备失败")
            
            # 获取图幅列表
            if not mapsheet_list:
                mapsheet_list = self._get_all_mapsheets()
            
            batch_results = {
                'total_mapsheets': len(mapsheet_list),
                'successful_estimates': 0,
                'failed_estimates': 0,
                'mapsheet_results': {},
                'summary': {},
                'timestamp': datetime.now().isoformat()
            }
            
            # 批量处理图幅
            for mapsheet_no in mapsheet_list:
                try:
                    result = self.estimate_mapsheet(mapsheet_no)
                    if 'error' not in result:
                        batch_results['successful_estimates'] += 1
                        batch_results['mapsheet_results'][mapsheet_no] = result
                    else:
                        batch_results['failed_estimates'] += 1
                        batch_results['mapsheet_results'][mapsheet_no] = result
                        
                except Exception as e:
                    logger.error(f"批量估算中图幅 {mapsheet_no} 失败: {e}")
                    batch_results['failed_estimates'] += 1
                    batch_results['mapsheet_results'][mapsheet_no] = self._create_error_result(str(e))
            
            # 生成汇总
            batch_results['summary'] = self._generate_batch_summary(batch_results['mapsheet_results'])
            
            logger.info(f"批量图幅估算完成 - 成功: {batch_results['successful_estimates']}, 失败: {batch_results['failed_estimates']}")
            return batch_results
            
        except Exception as e:
            logger.error(f"批量图幅估算失败: {e}")
            return self._create_error_result(str(e))
    
    def _prepare_data(self, start_date: DateType = None) -> bool:
        """准备数据"""
        try:
            if start_date is None:
                start_date = DateType(datetime.now() - timedelta(days=self.config.days_back))
            
            return self.data_analyzer.load_historical_data(start_date)
            
        except Exception as e:
            logger.error(f"数据准备失败: {e}")
            return False
    
    def _execute_basic_estimation(self, target_points: int, current_points: int = None, target_date: DateType = None) -> Dict[str, Any]:
        """执行基础估算"""
        try:
            # 设置项目配置
            self.finish_estimator.set_project_config(
                target_points=target_points,
                current_points=current_points or 0,
                target_date=target_date
            )
            
            # 执行估算
            estimation_results = self.finish_estimator.estimate_finish_date()
            
            return estimation_results
            
        except Exception as e:
            logger.error(f"基础估算失败: {e}")
            return self._create_error_result(str(e))
    
    def _execute_integration(self, basic_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """执行智能集成"""
        try:
            if not self.method_integrator:
                self.method_integrator = MethodIntegrator()
            
            # 智能集成处理
            integrated_results = self.method_integrator.integrate_methods(basic_results)
            
            return integrated_results
            
        except Exception as e:
            logger.error(f"智能集成失败: {e}")
            return None
    
    def _generate_charts(self, target_points: int, current_points: int = None) -> Optional[Dict[str, Any]]:
        """生成图表"""
        try:
            if not self.charts_generator:
                output_dir = os.path.join(self.workspace_path, 'estimation_output')
                self.charts_generator = ProgressCharts(self.data_analyzer, output_dir)
            
            # 生成图表
            chart_results = self.charts_generator.generate_all_charts(
                target_points=target_points,
                current_points=current_points or 0
            )
            
            return chart_results
            
        except Exception as e:
            logger.error(f"图表生成失败: {e}")
            return None
    
    def _compile_results(self, basic_results: Dict[str, Any], integrated_results: Optional[Dict[str, Any]], chart_results: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """整合结果"""
        compiled = {
            'estimation_mode': self.config.mode.value,
            'timestamp': datetime.now().isoformat(),
            'basic_estimation': basic_results,
            'integrated_estimation': integrated_results,
            'charts': chart_results,
            'configuration': {
                'confidence_level': self.config.confidence_level,
                'days_back': self.config.days_back,
                'use_real_data': self.config.use_real_data
            }
        }
        
        return compiled
    
    def _get_mapsheet_data(self, mapsheet_no: str) -> Optional[Dict[str, Any]]:
        """获取图幅数据"""
        try:
            # 从历史数据中筛选特定图幅的数据
            if hasattr(self.data_analyzer, 'historical_data') and not self.data_analyzer.historical_data.empty:
                mapsheet_data = self.data_analyzer.historical_data[
                    self.data_analyzer.historical_data.get('mapsheet', '') == mapsheet_no
                ]
                
                if not mapsheet_data.empty:
                    return mapsheet_data.to_dict('records')
            
            return None
            
        except Exception as e:
            logger.error(f"获取图幅数据失败 {mapsheet_no}: {e}")
            return None
    
    def _execute_mapsheet_estimation(self, mapsheet_no: str, mapsheet_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行图幅级别估算"""
        try:
            # 简化的图幅估算逻辑
            total_points = sum(record.get('points', 0) for record in mapsheet_data)
            total_days = len(mapsheet_data)
            
            if total_days > 0:
                avg_daily_points = total_points / total_days
                completion_percentage = min(100, (total_points / 1000) * 100)  # 假设每个图幅1000点
                
                return {
                    'mapsheet_no': mapsheet_no,
                    'total_points': total_points,
                    'total_days': total_days,
                    'avg_daily_points': avg_daily_points,
                    'completion_percentage': completion_percentage,
                    'status': 'completed' if completion_percentage >= 100 else 'in_progress'
                }
            else:
                return self._create_error_result("无有效数据")
                
        except Exception as e:
            logger.error(f"图幅估算执行失败 {mapsheet_no}: {e}")
            return self._create_error_result(str(e))
    
    def _get_all_mapsheets(self) -> List[str]:
        """获取所有图幅"""
        try:
            if hasattr(self.data_analyzer, 'historical_data') and not self.data_analyzer.historical_data.empty:
                mapsheets = self.data_analyzer.historical_data.get('mapsheet', pd.Series()).unique()
                return [ms for ms in mapsheets if ms and str(ms) != 'nan']
            return []
        except Exception as e:
            logger.error(f"获取图幅列表失败: {e}")
            return []
    
    def _generate_batch_summary(self, mapsheet_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """生成批量处理汇总"""
        try:
            successful_results = {k: v for k, v in mapsheet_results.items() if 'error' not in v}
            
            if not successful_results:
                return {'total_points': 0, 'average_completion': 0, 'completed_mapsheets': 0}
            
            total_points = sum(result.get('total_points', 0) for result in successful_results.values())
            avg_completion = sum(result.get('completion_percentage', 0) for result in successful_results.values()) / len(successful_results)
            completed_mapsheets = sum(1 for result in successful_results.values() if result.get('status') == 'completed')
            
            return {
                'total_points': total_points,
                'average_completion': avg_completion,
                'completed_mapsheets': completed_mapsheets,
                'in_progress_mapsheets': len(successful_results) - completed_mapsheets
            }
            
        except Exception as e:
            logger.error(f"生成批量汇总失败: {e}")
            return {}
    
    def _generate_cache_key(self, target_points: int, current_points: int, start_date: DateType, target_date: DateType) -> str:
        """生成缓存键"""
        key_parts = [
            str(target_points),
            str(current_points or 0),
            str(start_date) if start_date else 'None',
            str(target_date) if target_date else 'None',
            self.config.mode.value,
            str(self.config.confidence_level)
        ]
        return '_'.join(key_parts)
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """获取缓存结果"""
        if not self.config_manager.get_performance_config().cache_enabled:
            return None
        
        if cache_key in self._result_cache:
            cache_time = self._cache_timestamps.get(cache_key)
            if cache_time:
                cache_age_hours = (time.time() - cache_time) / 3600
                ttl_hours = self.config_manager.get_performance_config().cache_ttl_hours
                
                if cache_age_hours < ttl_hours:
                    return self._result_cache[cache_key]
                else:
                    # 清理过期缓存
                    del self._result_cache[cache_key]
                    del self._cache_timestamps[cache_key]
        
        return None
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """缓存结果"""
        if self.config_manager.get_performance_config().cache_enabled:
            self._result_cache[cache_key] = result
            self._cache_timestamps[cache_key] = time.time()
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            'error': error_message,
            'timestamp': datetime.now().isoformat(),
            'estimation_mode': self.config.mode.value if hasattr(self, 'config') else 'unknown'
        }
    
    def clear_cache(self):
        """清理缓存"""
        self._result_cache.clear()
        self._cache_timestamps.clear()
        logger.info("缓存已清理")
