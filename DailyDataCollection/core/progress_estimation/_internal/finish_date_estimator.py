"""
完成日期估算器模块

基于历史数据和当前进度，使用多种算法估算项目完成日期
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

from .data_analyzer import DataAnalyzer

logger = logging.getLogger(__name__)


class FinishDateEstimator:
    """完成日期估算器类"""

    def __init__(self, data_analyzer: DataAnalyzer, skip_completed_estimation: bool = False):
        """
        初始化完成日期估算器
        
        Args:
            data_analyzer: 数据分析器实例
            skip_completed_estimation: 是否跳过已完成项目的复杂估算（True=节省资源）
        """
        self.data_analyzer = data_analyzer
        self.skip_completed_estimation = skip_completed_estimation
        self.estimation_methods = {
            'simple_average': self._estimate_by_simple_average,
            'weighted_average': self._estimate_by_weighted_average, 
            'linear_regression': self._estimate_by_linear_regression,
            'monte_carlo': self._estimate_by_monte_carlo
        }
    
    def estimate_finish_date(self, 
                           target_points: int,
                           current_points: int = 0,
                           method: str = 'weighted_average',
                           confidence_level: float = 0.8) -> Dict[str, Any]:
        """
        估算完成日期
        
        Args:
            target_points: 目标总点数
            current_points: 当前已完成点数
            method: 估算方法
            confidence_level: 置信度
            
        Returns:
            包含估算结果的字典
        """
        logger.info(f"开始完成日期估算：目标{target_points}点，当前{current_points}点")
        
        # 检查是否已完成
        if current_points >= target_points:
            return self._create_completed_result(target_points, current_points)
        
        remaining_points = target_points - current_points
        
        # 获取估算方法
        if method not in self.estimation_methods:
            logger.warning(f"未知的估算方法: {method}，使用默认方法 'weighted_average'")
            method = 'weighted_average'
        
        estimation_func = self.estimation_methods[method]
        
        try:
            # 执行估算
            result = estimation_func(remaining_points, confidence_level)
            result.update({
                'target_points': target_points,
                'current_points': current_points,
                'remaining_points': remaining_points,
                'method': method,
                'confidence_level': confidence_level,
                'estimation_date': datetime.now()
            })
            
            logger.info(f"完成日期估算完成，方法: {method}")
            return result
            
        except Exception as e:
            logger.error(f"估算失败: {str(e)}")
            return self._create_error_result(str(e), target_points, current_points)

    def _create_completed_result(self, target_points: int, current_points: int) -> Dict[str, Any]:
        """创建已完成项目的结果"""
        return {
            'status': 'completed',
            'estimated_finish_date': datetime.now().date(),
            'estimated_days_remaining': 0,
            'target_points': target_points,
            'current_points': current_points,
            'remaining_points': 0,
            'method': 'completed',
            'confidence_level': 1.0,
            'estimation_date': datetime.now(),
            'message': '项目已完成'
        }

    def _create_error_result(self, error_msg: str, target_points: int, current_points: int) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            'status': 'error',
            'error': error_msg,
            'target_points': target_points,
            'current_points': current_points,
            'estimation_date': datetime.now()
        }

    def _estimate_by_simple_average(self, remaining_points: int, confidence_level: float) -> Dict[str, Any]:
        """基于简单平均的估算方法"""
        try:
            # 获取历史日均完成点数
            daily_avg = self.data_analyzer.get_daily_average_completion()
            
            if daily_avg <= 0:
                raise ValueError("历史日均完成点数无效")
            
            estimated_days = remaining_points / daily_avg
            estimated_finish_date = datetime.now() + timedelta(days=estimated_days)
            
            return {
                'status': 'success',
                'estimated_finish_date': estimated_finish_date.date(),
                'estimated_days_remaining': int(estimated_days),
                'daily_average': daily_avg,
                'method_details': {
                    'algorithm': 'simple_average',
                    'daily_avg_points': daily_avg
                }
            }
            
        except Exception as e:
            raise ValueError(f"简单平均估算失败: {str(e)}")

    def _estimate_by_weighted_average(self, remaining_points: int, confidence_level: float) -> Dict[str, Any]:
        """基于加权平均的估算方法"""
        try:
            # 获取加权日均完成点数（近期数据权重更高）
            weighted_avg = self.data_analyzer.get_weighted_daily_average()
            
            if weighted_avg <= 0:
                raise ValueError("加权日均完成点数无效")
            
            estimated_days = remaining_points / weighted_avg
            estimated_finish_date = datetime.now() + timedelta(days=estimated_days)
            
            return {
                'status': 'success',
                'estimated_finish_date': estimated_finish_date.date(),
                'estimated_days_remaining': int(estimated_days),
                'weighted_daily_average': weighted_avg,
                'method_details': {
                    'algorithm': 'weighted_average',
                    'weighted_avg_points': weighted_avg
                }
            }
            
        except Exception as e:
            raise ValueError(f"加权平均估算失败: {str(e)}")

    def _estimate_by_linear_regression(self, remaining_points: int, confidence_level: float) -> Dict[str, Any]:
        """基于线性回归的估算方法"""
        try:
            # 获取线性回归预测的日均完成点数
            regression_result = self.data_analyzer.get_linear_regression_prediction()
            
            if not regression_result or regression_result.get('daily_rate', 0) <= 0:
                raise ValueError("线性回归预测无效")
            
            daily_rate = regression_result['daily_rate']
            estimated_days = remaining_points / daily_rate
            estimated_finish_date = datetime.now() + timedelta(days=estimated_days)
            
            # 计算置信区间
            confidence_days = estimated_days * (1 + (1 - confidence_level))
            confidence_date = datetime.now() + timedelta(days=confidence_days)
            
            return {
                'status': 'success',
                'estimated_finish_date': estimated_finish_date.date(),
                'estimated_days_remaining': int(estimated_days),
                'confidence_finish_date': confidence_date.date(),
                'r_squared': regression_result.get('r_squared', 0),
                'method_details': {
                    'algorithm': 'linear_regression',
                    'daily_rate': daily_rate,
                    'r_squared': regression_result.get('r_squared', 0)
                }
            }
            
        except Exception as e:
            raise ValueError(f"线性回归估算失败: {str(e)}")

    def _estimate_by_monte_carlo(self, remaining_points: int, confidence_level: float) -> Dict[str, Any]:
        """基于蒙特卡洛模拟的估算方法"""
        try:
            # 获取历史完成点数的统计数据
            historical_data = self.data_analyzer.get_daily_completion_statistics()
            
            if not historical_data or len(historical_data) < 5:
                raise ValueError("历史数据不足，无法进行蒙特卡洛模拟")
            
            # 蒙特卡洛模拟参数
            num_simulations = 10000
            daily_means = np.array(historical_data)
            mean_completion = np.mean(daily_means)
            std_completion = np.std(daily_means)
            
            if std_completion <= 0:
                std_completion = mean_completion * 0.2  # 假设20%的变异系数
            
            # 运行模拟
            simulation_results = []
            for _ in range(num_simulations):
                daily_rates = np.random.normal(mean_completion, std_completion, remaining_points)
                daily_rates = np.maximum(daily_rates, 0.1)  # 确保最小值
                
                cumulative_points = 0
                days = 0
                for rate in daily_rates:
                    cumulative_points += rate
                    days += 1
                    if cumulative_points >= remaining_points:
                        break
                
                simulation_results.append(days)
            
            # 计算结果统计
            simulation_results = np.array(simulation_results)
            mean_days = np.mean(simulation_results)
            
            # 计算置信区间
            confidence_percentile = confidence_level * 100
            confidence_days = np.percentile(simulation_results, confidence_percentile)
            
            estimated_finish_date = datetime.now() + timedelta(days=mean_days)
            confidence_finish_date = datetime.now() + timedelta(days=confidence_days)
            
            return {
                'status': 'success',
                'estimated_finish_date': estimated_finish_date.date(),
                'estimated_days_remaining': int(mean_days),
                'confidence_finish_date': confidence_finish_date.date(),
                'confidence_days_remaining': int(confidence_days),
                'method_details': {
                    'algorithm': 'monte_carlo',
                    'num_simulations': num_simulations,
                    'mean_daily_completion': mean_completion,
                    'std_daily_completion': std_completion,
                    'simulation_mean_days': mean_days,
                    'simulation_std_days': np.std(simulation_results)
                }
            }
            
        except Exception as e:
            raise ValueError(f"蒙特卡洛模拟失败: {str(e)}")

    def compare_methods(self, target_points: int, current_points: int = 0, confidence_level: float = 0.8) -> Dict[str, Any]:
        """比较所有估算方法的结果"""
        results = {}
        
        for method_name in self.estimation_methods.keys():
            try:
                result = self.estimate_finish_date(
                    target_points, current_points, method_name, confidence_level
                )
                results[method_name] = result
            except Exception as e:
                logger.warning(f"方法 {method_name} 估算失败: {str(e)}")
                results[method_name] = {'status': 'error', 'error': str(e)}
        
        return {
            'comparison_results': results,
            'target_points': target_points,
            'current_points': current_points,
            'confidence_level': confidence_level,
            'comparison_date': datetime.now()
        }

    def get_estimation_summary(self, target_points: int, current_points: int = 0) -> Dict[str, Any]:
        """获取估算摘要信息"""
        remaining_points = target_points - current_points
        progress_percentage = (current_points / target_points) * 100 if target_points > 0 else 0
        
        # 获取基础统计信息
        try:
            daily_avg = self.data_analyzer.get_daily_average_completion()
            weighted_avg = self.data_analyzer.get_weighted_daily_average()
            
            return {
                'project_info': {
                    'target_points': target_points,
                    'current_points': current_points,
                    'remaining_points': remaining_points,
                    'progress_percentage': round(progress_percentage, 2)
                },
                'daily_statistics': {
                    'daily_average': daily_avg,
                    'weighted_average': weighted_avg
                },
                'available_methods': list(self.estimation_methods.keys()),
                'recommended_method': self._get_recommended_method(remaining_points),
                'summary_date': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"获取估算摘要失败: {str(e)}")
            return {
                'project_info': {
                    'target_points': target_points,
                    'current_points': current_points,
                    'remaining_points': remaining_points,
                    'progress_percentage': round(progress_percentage, 2)
                },
                'error': str(e),
                'summary_date': datetime.now()
            }

    def _get_recommended_method(self, remaining_points: int) -> str:
        """根据剩余工作量推荐最适合的估算方法"""
        try:
            historical_data = self.data_analyzer.get_daily_completion_statistics()
            data_size = len(historical_data) if historical_data else 0
            
            if remaining_points <= 50:
                return 'simple_average'  # 小项目用简单方法
            elif data_size >= 30:
                return 'monte_carlo'  # 数据充足用蒙特卡洛
            elif data_size >= 10:
                return 'linear_regression'  # 中等数据用回归
            else:
                return 'weighted_average'  # 数据不足用加权平均
                
        except Exception:
            return 'weighted_average'  # 默认方法
