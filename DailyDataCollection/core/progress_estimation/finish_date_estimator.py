"""
完成日期估算器模块

基于历史数据和当前进度估算项目完成日期
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

from .data_analyzer import DataAnalyzer
from .completed_project_handler import CompletedProjectHandler
from ..data_models.date_types import DateType

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
        self.completed_handler = CompletedProjectHandler(skip_estimation=skip_completed_estimation)
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
            Dict: 包含估算结果的字典
        """
        if target_points <= current_points:
            # 使用专门的已完成项目处理器
            return self.completed_handler.create_completed_estimation_result(
                current_points=current_points,
                target_points=target_points,
                method=method,
                historical_data=self.data_analyzer.historical_data
            )
        
        remaining_points = target_points - current_points
        
        try:
            estimator_func = self.estimation_methods.get(method, self._estimate_by_weighted_average)
            result = estimator_func(remaining_points, confidence_level)
            
            result.update({
                'target_points': target_points,
                'current_points': current_points,
                'remaining_points': remaining_points,
                'method': method,
                'confidence_level': confidence_level
            })
            
            return result
            
        except Exception as e:
            logger.error(f"估算完成日期失败: {e}")
            return self._get_fallback_estimate(remaining_points)
    
    def _estimate_by_simple_average(self, remaining_points: int, confidence_level: float) -> Dict[str, Any]:
        """使用简单平均速度估算"""
        stats = self.data_analyzer.daily_statistics
        if not stats or 'average_daily' not in stats:
            raise ValueError("缺少历史统计数据")
        
        avg_daily = stats['average_daily']
        active_days = stats.get('active_days', 0)
        
        # 改进的平均日速度检查
        if avg_daily <= 0 or active_days == 0:
            # 如果没有活跃数据，使用基于目标的估算
            total_days = stats.get('total_days', 1)
            if total_days > 0:
                # 基于总天数和目标，估算一个合理的日速度
                estimated_daily = max(1, remaining_points / (total_days * 2))  # 假设需要2倍当前时间完成
            else:
                estimated_daily = max(1, remaining_points / 60)  # 假设60天完成
            
            days_needed = remaining_points / estimated_daily
            estimated_date = datetime.now() + timedelta(days=days_needed)
            
            return {
                'estimated_date': estimated_date,
                'days_remaining': days_needed,
                'confidence': 0.3,  # 低置信度
                'uncertainty_days': days_needed * 0.8,
                'daily_velocity': estimated_daily,
                'status': 'estimated_no_activity',
                'warning': '基于无活跃数据的估算'
            }
        
        days_needed = remaining_points / avg_daily
        estimated_date = datetime.now() + timedelta(days=days_needed)
        
        # 简单置信度计算
        std_daily = stats.get('std_daily', avg_daily * 0.3)
        uncertainty_days = (std_daily / avg_daily) * days_needed
        
        return {
            'estimated_date': estimated_date,
            'days_remaining': days_needed,
            'confidence': min(confidence_level, 0.9),
            'uncertainty_days': uncertainty_days,
            'daily_velocity': avg_daily,
            'status': 'estimated'
        }
    
    def _estimate_by_weighted_average(self, remaining_points: int, confidence_level: float) -> Dict[str, Any]:
        """使用加权平均速度估算（近期数据权重更高）"""
        if self.data_analyzer.historical_data.empty:
            raise ValueError("缺少历史数据")
        
        recent_data = self.data_analyzer.historical_data.tail(14)  # 最近14天
        if len(recent_data) < 3:
            return self._estimate_by_simple_average(remaining_points, confidence_level)
        
        # 计算加权平均（近期权重更高）
        weights = np.exp(np.linspace(0, 1, len(recent_data)))  # 指数权重
        
        # 确定使用哪个列作为每日完成点数
        if 'daily_points' in recent_data.columns:
            points_col = 'daily_points'
        elif 'completed_points' in recent_data.columns:
            points_col = 'completed_points'
        else:
            raise ValueError("数据中缺少daily_points或completed_points列")
            
        weighted_avg = np.average(recent_data[points_col], weights=weights)
        
        # 改进的加权平均速度检查
        if weighted_avg <= 0:
            # 检查是否有任何非零数据
            non_zero_data = recent_data[recent_data[points_col] > 0]
            if len(non_zero_data) > 0:
                # 使用非零数据的平均值
                weighted_avg = non_zero_data[points_col].mean()
            else:
                # 完全没有活跃数据，使用简单平均法的逻辑
                return self._estimate_by_simple_average(remaining_points, confidence_level)
        
        days_needed = remaining_points / weighted_avg
        estimated_date = datetime.now() + timedelta(days=days_needed)
        
        # 计算不确定性
        recent_std = recent_data[points_col].std()
        uncertainty_days = (recent_std / weighted_avg) * days_needed
        
        return {
            'estimated_date': estimated_date,
            'days_remaining': days_needed,
            'confidence': confidence_level,
            'uncertainty_days': uncertainty_days,
            'daily_velocity': weighted_avg,
            'status': 'estimated'
        }
    
    def _estimate_by_linear_regression(self, remaining_points: int, confidence_level: float) -> Dict[str, Any]:
        """使用线性回归估算趋势"""
        if self.data_analyzer.historical_data.empty:
            raise ValueError("缺少历史数据")
        
        data = self.data_analyzer.historical_data.copy()
        if len(data) < 5:
            return self._estimate_by_weighted_average(remaining_points, confidence_level)
        
        # 计算累计点数的线性趋势
        data['days_from_start'] = (data['date'] - data['date'].min()).dt.days
        
        # 简单线性回归
        x = data['days_from_start'].values
        y = data['cumulative_points'].values
        
        # 计算斜率（每日平均增长）
        n = len(x)
        
        # 避免除零错误
        denominator = n * np.sum(x**2) - np.sum(x)**2
        if denominator == 0:
            return self._estimate_by_weighted_average(remaining_points, confidence_level)
            
        slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / denominator
        intercept = (np.sum(y) - slope * np.sum(x)) / n
        
        # 改进的斜率检查
        if slope <= 0:
            # 如果趋势为负或零，检查是否有实际进度
            total_progress = y[-1] - y[0] if len(y) > 0 else 0
            if total_progress > 0:
                # 使用平均进度作为斜率
                slope = total_progress / len(data)
            else:
                # 没有进度，使用回退方法
                return self._estimate_by_weighted_average(remaining_points, confidence_level)
        
        # 当前进度和预测
        current_day = data['days_from_start'].max()
        current_predicted = slope * current_day + intercept
        target_cumulative = current_predicted + remaining_points
        
        # 计算需要的天数
        target_day = (target_cumulative - intercept) / slope
        days_remaining = max(0, target_day - current_day)
        
        estimated_date = datetime.now() + timedelta(days=days_remaining)
        
        # 计算R²作为置信度指标
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return {
            'estimated_date': estimated_date,
            'days_remaining': days_remaining,
            'confidence': min(r_squared, confidence_level),
            'uncertainty_days': days_remaining * (1 - r_squared) * 0.5,
            'daily_velocity': slope,
            'r_squared': r_squared,
            'status': 'estimated'
        }
    
    def _estimate_by_monte_carlo(self, remaining_points: int, confidence_level: float) -> Dict[str, Any]:
        """使用蒙特卡洛模拟估算"""
        if self.data_analyzer.historical_data.empty:
            raise ValueError("缺少历史数据")
        
        recent_data = self.data_analyzer.historical_data.tail(21)  # 最近3周
        if len(recent_data) < 7:
            return self._estimate_by_weighted_average(remaining_points, confidence_level)
        
        # 确定使用哪个列作为每日完成点数
        if 'daily_points' in recent_data.columns:
            points_col = 'daily_points'
        elif 'completed_points' in recent_data.columns:
            points_col = 'completed_points'
        else:
            raise ValueError("数据中缺少daily_points或completed_points列")
        
        # 分析工作日和周末的不同模式
        workday_points = recent_data[recent_data['workday'] == True][points_col]
        weekend_points = recent_data[recent_data['workday'] == False][points_col]
        
        if workday_points.empty:
            return self._estimate_by_weighted_average(remaining_points, confidence_level)
        
        # 蒙特卡洛模拟
        n_simulations = 1000
        completion_days = []
        
        for _ in range(n_simulations):
            points_left = remaining_points
            days = 0
            
            while points_left > 0 and days < 365:  # 防止无限循环
                days += 1
                current_date = datetime.now() + timedelta(days=days)
                is_workday = current_date.weekday() < 5
                
                if is_workday and not workday_points.empty:
                    # 从工作日数据中随机采样
                    daily_points = max(0, np.random.choice(workday_points))
                elif not weekend_points.empty:
                    # 从周末数据中随机采样
                    daily_points = max(0, np.random.choice(weekend_points))
                else:
                    daily_points = max(0, np.random.choice(workday_points))
                
                points_left -= daily_points
            
            completion_days.append(days)
        
        # 计算统计信息
        completion_days = np.array(completion_days)
        mean_days = np.mean(completion_days)
        std_days = np.std(completion_days)
        
        # 计算置信区间
        confidence_percentile = confidence_level + (1 - confidence_level) / 2
        percentile_days = np.percentile(completion_days, confidence_percentile * 100)
        
        estimated_date = datetime.now() + timedelta(days=mean_days)
        confidence_date = datetime.now() + timedelta(days=percentile_days)
        
        return {
            'estimated_date': estimated_date,
            'confidence_date': confidence_date,
            'days_remaining': mean_days,
            'days_remaining_confident': percentile_days,
            'confidence': confidence_level,
            'uncertainty_days': std_days,
            'daily_velocity': remaining_points / mean_days if mean_days > 0 else 0,
            'simulation_results': {
                'mean': mean_days,
                'std': std_days,
                'min': np.min(completion_days),
                'max': np.max(completion_days),
                'p25': np.percentile(completion_days, 25),
                'p50': np.percentile(completion_days, 50),
                'p75': np.percentile(completion_days, 75)
            },
            'status': 'estimated'
        }
    
    def _get_fallback_estimate(self, remaining_points: int) -> Dict[str, Any]:
        """回退估算方法"""
        # 使用保守的默认速度
        default_daily_rate = 30  # 保守估计每天30个点
        days_needed = remaining_points / default_daily_rate
        estimated_date = datetime.now() + timedelta(days=days_needed)
        
        return {
            'estimated_date': estimated_date,
            'days_remaining': days_needed,
            'confidence': 0.5,
            'uncertainty_days': days_needed * 0.5,
            'daily_velocity': default_daily_rate,
            'status': 'fallback_estimate',
            'warning': '使用默认参数进行保守估算'
        }
    
    def get_multiple_estimates(self, 
                             target_points: int,
                             current_points: int = 0) -> Dict[str, Dict[str, Any]]:
        """
        使用多种方法获取估算结果
        
        Args:
            target_points: 目标总点数
            current_points: 当前已完成点数
            
        Returns:
            Dict: 包含所有方法估算结果的字典
        """
        estimates = {}
        
        for method_name in self.estimation_methods.keys():
            try:
                estimates[method_name] = self.estimate_finish_date(
                    target_points, current_points, method_name
                )
            except Exception as e:
                logger.warning(f"方法 {method_name} 估算失败: {e}")
                estimates[method_name] = {
                    'status': 'failed',
                    'error': str(e)
                }
        
        return estimates
    
    def get_recommended_estimate(self, 
                               target_points: int,
                               current_points: int = 0) -> Dict[str, Any]:
        """
        获取推荐的估算结果
        
        优先级：蒙特卡洛 > 线性回归 > 加权平均 > 简单平均
        """
        methods_priority = ['monte_carlo', 'linear_regression', 'weighted_average', 'simple_average']
        
        for method in methods_priority:
            try:
                result = self.estimate_finish_date(target_points, current_points, method)
                if result.get('status') == 'estimated':
                    result['recommendation_reason'] = f'使用 {method} 方法'
                    return result
            except Exception as e:
                logger.debug(f"方法 {method} 失败: {e}")
                continue
        
        # 如果所有方法都失败，使用回退估算
        return self._get_fallback_estimate(target_points - current_points)