"""
估算门面 - 提供简化的统一接口
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from .core_estimator import CoreEstimator, EstimationConfig, EstimationMode
from .estimation_config import EstimationConfigManager
from ._internal.excel_data_connector import ExcelDataConnector
from ..data_models.date_types import DateType

logger = logging.getLogger(__name__)


class EstimationFacade:
    """估算门面类 - 提供简化的API接口"""
    
    def __init__(self, workspace_path: str = None):
        """
        初始化估算门面
        
        Args:
            workspace_path: 工作空间路径
        """
        self.workspace_path = workspace_path
        self._estimator_cache = {}
        
        # 初始化配置管理器
        print("=== 初始化进度估算系统 ===")
        self.config_manager = EstimationConfigManager()
        
        # 显示配置信息
        self._display_config_info()
        
        # 初始化数据连接器
        try:
            self.data_connector = ExcelDataConnector(workspace_path)
            print("数据连接器初始化成功")
            self._display_connection_status()
        except Exception as e:
            print(f"数据连接器初始化失败: {e}")
            logger.error(f"数据连接器初始化失败: {e}")
            self.data_connector = None
        
        print("=== 初始化完成 ===\n")
        logger.info(f"估算门面已初始化，工作空间: {workspace_path or '当前目录'}")
    
    def _display_config_info(self):
        """显示配置信息"""
        try:
            workspace = self.config_manager.get_workspace()
            mapsheet_range = self.config_manager.get_mapsheet_range()
            excel_path = self.config_manager.get_daily_details_file()
            
            print("配置信息:")
            print(f"  工作空间: {workspace}")
            print(f"  图幅范围: {mapsheet_range['min']}-{mapsheet_range['max']}")
            print(f"  Excel文件: {excel_path}")
            
        except Exception as e:
            print(f"  配置信息获取失败: {e}")
    
    def _display_connection_status(self):
        """显示连接状态"""
        if self.data_connector:
            status = self.data_connector.get_connection_status()
            file_info = status['excel_file']
            
            print("连接状态:")
            print(f"  Excel文件存在: {'是' if file_info['exists'] else '否'}")
            if file_info['exists']:
                print(f"  文件大小: {file_info.get('size_mb', 0):.2f} MB")
                print(f"  最后修改: {file_info.get('modified', 'N/A')}")
            
            print(f"  数据已加载: {'是' if status['data_loaded'] else '否'}")
            
            validation = status['data_validation']
            print(f"  数据结构有效: {'是' if validation['valid'] else '否'}")
            if not validation['valid']:
                print("  数据问题:")
                for issue in validation['issues']:
                    print(f"    - {issue}")
    
    def quick_estimate(self, 
                      target_points: int,
                      current_points: int = None,
                      days_back: int = 30) -> Dict[str, Any]:
        """
        快速估算 - 使用默认配置进行简单估算
        
        Args:
            target_points: 目标点数
            current_points: 当前点数
            days_back: 回溯天数
            
        Returns:
            Dict[str, Any]: 估算结果摘要
        """
        try:
            logger.info(f"开始快速估算 - 目标: {target_points}, 当前: {current_points}, 回溯: {days_back}天")
            
            config = EstimationConfig(
                mode=EstimationMode.BASIC,
                days_back=days_back,
                enable_charts=False,
                enable_integration=False
            )
            
            estimator = self._get_estimator(config)
            results = estimator.estimate_project(target_points, current_points)
            
            # 提取摘要信息
            summary = self._extract_summary(results)
            
            logger.info("快速估算完成")
            return summary
            
        except Exception as e:
            logger.error(f"快速估算失败: {e}")
            return {
                'error': str(e),
                'completion_percentage': 0,
                'estimated_finish_date': None,
                'days_remaining': 0,
                'confidence': 0,
                'daily_target': 0,
                'recommendations': []
            }
    
    def advanced_estimate(self, 
                         target_points: int,
                         current_points: int = None,
                         confidence_level: float = 0.8,
                         include_charts: bool = True,
                         days_back: int = 30) -> Dict[str, Any]:
        """
        高级估算 - 包含智能集成和图表生成
        
        Args:
            target_points: 目标点数
            current_points: 当前点数
            confidence_level: 置信水平
            include_charts: 是否包含图表
            days_back: 回溯天数
            
        Returns:
            Dict[str, Any]: 完整的估算结果
        """
        try:
            logger.info(f"开始高级估算 - 目标: {target_points}, 当前: {current_points}, 置信度: {confidence_level}")
            
            config = EstimationConfig(
                mode=EstimationMode.ADVANCED,
                confidence_level=confidence_level,
                enable_charts=include_charts,
                enable_integration=True,
                days_back=days_back
            )
            
            estimator = self._get_estimator(config)
            results = estimator.estimate_project(target_points, current_points)
            
            logger.info("高级估算完成")
            return results
            
        except Exception as e:
            logger.error(f"高级估算失败: {e}")
            return {
                'error': str(e),
                'estimation_mode': 'advanced',
                'timestamp': datetime.now().isoformat()
            }
    
    def mapsheet_estimation_single(self, 
                                  mapsheet_no: str,
                                  confidence_level: float = 0.8) -> Dict[str, Any]:
        """
        单个图幅估算
        
        Args:
            mapsheet_no: 图幅编号
            confidence_level: 置信水平
            
        Returns:
            Dict[str, Any]: 图幅估算结果
        """
        try:
            logger.info(f"开始单个图幅估算: {mapsheet_no}")
            
            config = EstimationConfig(
                mode=EstimationMode.MAPSHEET,
                confidence_level=confidence_level,
                enable_integration=True,
                enable_charts=False
            )
            
            estimator = self._get_estimator(config)
            results = estimator.estimate_mapsheet(mapsheet_no)
            
            logger.info(f"单个图幅估算完成: {mapsheet_no}")
            return results
            
        except Exception as e:
            logger.error(f"单个图幅估算失败 {mapsheet_no}: {e}")
            return {
                'error': str(e),
                'mapsheet_no': mapsheet_no,
                'timestamp': datetime.now().isoformat()
            }
    
    def mapsheet_estimation_batch(self, 
                                 mapsheet_list: List[str] = None,
                                 confidence_level: float = 0.8,
                                 include_summary: bool = True) -> Dict[str, Any]:
        """
        批量图幅估算
        
        Args:
            mapsheet_list: 图幅列表，None表示所有图幅
            confidence_level: 置信水平
            include_summary: 是否包含汇总信息
            
        Returns:
            Dict[str, Any]: 批量估算结果
        """
        try:
            logger.info(f"开始批量图幅估算, 图幅数量: {len(mapsheet_list) if mapsheet_list else '全部'}")
            
            config = EstimationConfig(
                mode=EstimationMode.MAPSHEET,
                confidence_level=confidence_level,
                enable_integration=True,
                enable_charts=False
            )
            
            estimator = self._get_estimator(config)
            results = estimator.batch_estimate_mapsheets(mapsheet_list)
            
            # 如果不需要详细结果，只返回汇总
            if not include_summary and 'mapsheet_results' in results:
                # 简化返回结果
                simplified_results = {
                    'total_mapsheets': results['total_mapsheets'],
                    'successful_estimates': results['successful_estimates'],
                    'failed_estimates': results['failed_estimates'],
                    'summary': results.get('summary', {}),
                    'timestamp': results['timestamp']
                }
                return simplified_results
            
            logger.info("批量图幅估算完成")
            return results
            
        except Exception as e:
            logger.error(f"批量图幅估算失败: {e}")
            return {
                'error': str(e),
                'total_mapsheets': 0,
                'successful_estimates': 0,
                'failed_estimates': 0,
                'timestamp': datetime.now().isoformat()
            }
    
    def real_time_estimate(self,
                          target_points: int,
                          current_points: int = None,
                          update_interval_hours: int = 1) -> Dict[str, Any]:
        """
        实时估算 - 基于最新数据的实时更新估算
        
        Args:
            target_points: 目标点数
            current_points: 当前点数
            update_interval_hours: 更新间隔（小时）
            
        Returns:
            Dict[str, Any]: 实时估算结果
        """
        try:
            logger.info(f"开始实时估算 - 目标: {target_points}, 更新间隔: {update_interval_hours}小时")
            
            config = EstimationConfig(
                mode=EstimationMode.REAL_TIME,
                days_back=7,  # 实时模式使用较短的历史数据
                enable_charts=True,
                enable_integration=True
            )
            
            estimator = self._get_estimator(config)
            
            # 清理缓存以确保使用最新数据
            estimator.clear_cache()
            
            results = estimator.estimate_project(target_points, current_points)
            
            # 添加实时特定信息
            if 'error' not in results:
                results['real_time_info'] = {
                    'update_interval_hours': update_interval_hours,
                    'next_update_time': (datetime.now() + timedelta(hours=update_interval_hours)).isoformat(),
                    'data_freshness': 'latest'
                }
            
            logger.info("实时估算完成")
            return results
            
        except Exception as e:
            logger.error(f"实时估算失败: {e}")
            return {
                'error': str(e),
                'estimation_mode': 'real_time',
                'timestamp': datetime.now().isoformat()
            }
    
    def get_estimation_status(self) -> Dict[str, Any]:
        """
        获取估算系统状态
        
        Returns:
            Dict[str, Any]: 系统状态信息
        """
        try:
            status = {
                'active_estimators': len(self._estimator_cache),
                'available_modes': [mode.value for mode in EstimationMode],
                'workspace_path': self.workspace_path,
                'timestamp': datetime.now().isoformat()
            }
            
            # 检查数据可用性
            try:
                config = EstimationConfig(mode=EstimationMode.BASIC, enable_charts=False, enable_integration=False)
                test_estimator = self._get_estimator(config)
                data_available = test_estimator._prepare_data()
                status['data_available'] = data_available
            except Exception as e:
                status['data_available'] = False
                status['data_error'] = str(e)
            
            return status
            
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_estimator(self, config: EstimationConfig) -> CoreEstimator:
        """获取或创建估算器实例"""
        cache_key = f"{config.mode.value}_{config.use_real_data}_{config.enable_integration}_{config.days_back}"
        
        if cache_key not in self._estimator_cache:
            self._estimator_cache[cache_key] = CoreEstimator(self.workspace_path, config)
            logger.debug(f"创建新的估算器实例: {cache_key}")
        
        return self._estimator_cache[cache_key]
    
    def _extract_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """提取结果摘要"""
        if 'error' in results:
            return {
                'error': results['error'],
                'completion_percentage': 0,
                'estimated_finish_date': None,
                'days_remaining': 0,
                'confidence': 0,
                'daily_target': 0,
                'recommendations': []
            }
        
        # 从基础估算结果中提取关键信息
        basic_results = results.get('basic_estimation', {})
        
        summary = {
            'completion_percentage': basic_results.get('completion_percentage', 0),
            'estimated_finish_date': basic_results.get('estimated_finish_date'),
            'days_remaining': basic_results.get('days_remaining', 0),
            'confidence': basic_results.get('confidence', 0),
            'daily_target': basic_results.get('daily_target', 0),
            'current_velocity': basic_results.get('current_velocity', 0),
            'recommendations': basic_results.get('recommendations', [])[:3]  # 前3个建议
        }
        
        # 如果有集成结果，优先使用集成结果
        integrated_results = results.get('integrated_estimation')
        if integrated_results and isinstance(integrated_results, dict):
            for key in summary.keys():
                if key in integrated_results:
                    summary[key] = integrated_results[key]
        
        return summary
    
    def clear_cache(self):
        """清理所有缓存"""
        for estimator in self._estimator_cache.values():
            estimator.clear_cache()
        self._estimator_cache.clear()
        logger.info("所有缓存已清理")
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取完整的系统信息"""
        info = {
            'estimation_system': self.get_estimation_status(),
            'timestamp': datetime.now().isoformat()
        }
        
        if self.data_connector:
            info['data_connection'] = self.data_connector.get_connection_status()
        else:
            info['data_connection'] = {'status': 'disconnected'}
        
        if hasattr(self, 'config_manager'):
            info['configuration'] = {
                'workspace': self.config_manager.get_workspace(),
                'mapsheet_range': self.config_manager.get_mapsheet_range(),
                'main_config_path': str(self.config_manager.main_config_path)
            }
        
        return info
    
    def test_excel_connection(self) -> Dict[str, Any]:
        """测试Excel文件连接"""
        if not self.data_connector:
            return {
                'success': False,
                'error': '数据连接器未初始化'
            }
        
        try:
            # 测试文件信息
            file_info = self.data_connector.get_file_info()
            
            # 测试数据加载
            load_success = self.data_connector.load_excel_data()
            
            # 测试数据验证
            validation = self.data_connector.validate_data_structure()
            
            # 获取工作表名称
            sheet_names = self.data_connector.get_sheet_names()
            
            return {
                'success': load_success and validation['valid'],
                'file_info': file_info,
                'data_loaded': load_success,
                'validation': validation,
                'sheet_names': sheet_names,
                'test_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'test_time': datetime.now().isoformat()
            }
    
    def print_system_summary(self):
        """打印系统状态摘要"""
        print("\n=== 进度估算系统状态摘要 ===")
        
        # 配置信息
        if hasattr(self, 'config_manager'):
            workspace = self.config_manager.get_workspace()
            mapsheet_range = self.config_manager.get_mapsheet_range()
            print(f"工作空间: {workspace}")
            print(f"图幅范围: {mapsheet_range['min']}-{mapsheet_range['max']}")
        
        # 数据连接状态
        if self.data_connector:
            status = self.data_connector.get_connection_status()
            file_info = status['excel_file']
            print(f"Excel文件: {'存在' if file_info['exists'] else '不存在'}")
            if file_info['exists']:
                print(f"  文件路径: {file_info['path']}")
                print(f"  文件大小: {file_info.get('size_mb', 0):.2f} MB")
            
            validation = status['data_validation']
            print(f"数据有效性: {'有效' if validation['valid'] else '无效'}")
            if not validation['valid']:
                print("  问题:")
                for issue in validation['issues']:
                    print(f"    - {issue}")
        else:
            print("数据连接: 未建立")
        
        # 估算器状态
        estimation_status = self.get_estimation_status()
        print(f"活跃估算器: {estimation_status['active_estimators']}")
        print(f"数据可用性: {'可用' if estimation_status.get('data_available', False) else '不可用'}")
        
        print("==============================\n")
    
    def run_full_estimation_with_config(self) -> Dict[str, Any]:
        """使用主配置文件运行完整估算"""
        try:
            print("开始基于主配置的完整估算...")
            
            # 验证连接
            test_result = self.test_excel_connection()
            if not test_result['success']:
                return {
                    'error': f"Excel连接测试失败: {test_result.get('error', '未知错误')}",
                    'timestamp': datetime.now().isoformat()
                }
            
            print("Excel连接测试通过")
            
            # 获取图幅范围
            mapsheet_range = self.config_manager.get_mapsheet_range()
            
            # 运行全面估算
            result = self.full_estimate(
                target_points=5000,  # 可以从配置中读取
                current_points=None,  # 自动从数据中获取
                days_back=60
            )
            
            # 添加配置信息到结果中
            result['config_info'] = {
                'workspace': self.config_manager.get_workspace(),
                'mapsheet_range': f"{mapsheet_range['min']}-{mapsheet_range['max']}",
                'excel_file': self.config_manager.get_daily_details_file()
            }
            
            print("基于主配置的完整估算完成")
            return result
            
        except Exception as e:
            logger.error(f"完整估算失败: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
