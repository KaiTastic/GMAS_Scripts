"""
数据分析器模块

分析历史观测数据，计算完成速度、趋势和统计信息
"""

import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from core.data_models.date_types import DateType
from core.data_models.observation_data import ObservationData
from core.data_connectors.excel_data_connector import ExcelDataConnector

logger = logging.getLogger(__name__)


class DataAnalyzer:
    """数据分析器类，用于分析历史观测数据"""

    def __init__(self, workspace_path: str = None):
        """
        初始化数据分析器
        
        Args:
            workspace_path: 工作空间路径，用于查找历史数据
        """
        self.workspace_path = workspace_path or os.getcwd()
        self.historical_data: pd.DataFrame = pd.DataFrame()
        self.daily_statistics: Dict[str, Any] = {}
        
        # 初始化数据连接器
        self.data_connector = ExcelDataConnector(self.workspace_path)
        logger.info("数据分析器初始化完成")
        
    def load_historical_data(self, start_date: DateType, end_date: DateType = None) -> bool:
        """
        加载指定日期范围的历史数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期，默认为今天
            
        Returns:
            bool: 是否成功加载数据
        """
        try:
            if end_date is None:
                end_date = DateType(datetime.now())
            
            # 使用真实数据源（Excel）
            historical_records = self.data_connector.extract_historical_data(start_date, end_date)
            
            if historical_records:
                self.historical_data = pd.DataFrame(historical_records)
                self.historical_data['date'] = pd.to_datetime(self.historical_data['date'])
                self.historical_data = self.historical_data.sort_values('date')
                logger.info(f"成功从Excel加载 {len(historical_records)} 天的历史数据")
                return True
            else:
                logger.warning("从Excel未找到历史数据")
                return False
                
        except Exception as e:
            logger.error(f"加载历史数据失败: {e}")
            return False
    
    
    def _extract_daily_data(self, date_obj: DateType) -> Optional[Dict[str, Any]]:
        """
        从指定日期提取数据
        """
        try:
            return self.data_connector.get_daily_progress_data(date_obj)
        except Exception as e:
            logger.debug(f"提取 {date_obj.yyyymmdd_str} 数据失败: {e}")
            
        return None
    
    def calculate_daily_velocity(self) -> pd.DataFrame:
        """计算每日速度统计"""
        if self.historical_data.empty:
            logger.warning("没有历史数据可用于计算速度")
            return pd.DataFrame()
        
        try:
            # 计算累计点数
            self.historical_data['cumulative_points'] = self.historical_data['completed_points'].cumsum()
            
            # 计算移动平均
            self.historical_data['velocity_7day'] = (
                self.historical_data['completed_points'].rolling(window=7, min_periods=1).mean()
            )
            self.historical_data['velocity_14day'] = (
                self.historical_data['completed_points'].rolling(window=14, min_periods=1).mean()
            )
            
            # 计算工作日平均速度
            workday_data = self.historical_data[self.historical_data['workday'] == True]
            if not workday_data.empty:
                workday_avg = workday_data['completed_points'].mean()
                self.daily_statistics['workday_average'] = workday_avg
            
            # 计算总体统计
            self.daily_statistics.update({
                'total_days': len(self.historical_data),
                'total_points': self.historical_data['completed_points'].sum(),
                'average_daily': self.historical_data['completed_points'].mean(),
                'std_daily': self.historical_data['completed_points'].std(),
                'max_daily': self.historical_data['completed_points'].max(),
                'min_daily': self.historical_data['completed_points'].min()
            })
            
            return self.historical_data.copy()
            
        except Exception as e:
            logger.error(f"计算每日速度失败: {e}")
            return pd.DataFrame()
    
    def _calculate_daily_statistics(self):
        """计算日统计信息（内部方法）"""
        try:
            if self.historical_data.empty:
                logger.warning("没有历史数据可用于计算统计")
                return
            
            # 确定使用哪个列作为每日完成点数
            if 'daily_points' in self.historical_data.columns:
                daily_points_col = 'daily_points'
            elif 'completed_points' in self.historical_data.columns:
                daily_points_col = 'completed_points'
            else:
                logger.error("历史数据中未找到daily_points或completed_points列")
                return
            
            daily_points = self.historical_data[daily_points_col]
            
            # 计算累计点数（如果没有的话）
            if 'cumulative_points' not in self.historical_data.columns:
                self.historical_data['cumulative_points'] = daily_points.cumsum()
            
            # 计算移动平均
            self.historical_data['velocity_7day'] = daily_points.rolling(window=7, min_periods=1).mean()
            self.historical_data['velocity_14day'] = daily_points.rolling(window=14, min_periods=1).mean()
            
            # 计算工作日统计
            if 'workday' in self.historical_data.columns:
                workday_data = self.historical_data[self.historical_data['workday'] == True]
                if not workday_data.empty:
                    workday_avg = workday_data[daily_points_col].mean()
                    self.daily_statistics['workday_average'] = workday_avg
            
            # 更新总体统计
            self.daily_statistics.update({
                'total_days': len(self.historical_data),
                'total_points': daily_points.sum(),
                'average_daily': daily_points.mean(),
                'std_daily': daily_points.std(),
                'max_daily': daily_points.max(),
                'min_daily': daily_points.min(),
                'active_days': len(self.historical_data[daily_points > 0])
            })
            
            logger.debug(f"日统计计算完成，活跃天数: {self.daily_statistics.get('active_days', 0)}")
            
        except Exception as e:
            logger.error(f"计算日统计失败: {e}")
            # 设置默认值
            self.daily_statistics = {
                'total_days': 0,
                'total_points': 0,
                'average_daily': 0,
                'std_daily': 0,
                'max_daily': 0,
                'min_daily': 0,
                'active_days': 0
            }
    
    def get_velocity_trend(self, window_size: int = 7) -> Dict[str, float]:
        """
        获取速度趋势分析
        
        Args:
            window_size: 移动窗口大小（天）
            
        Returns:
            Dict: 包含趋势信息的字典
        """
        if self.historical_data.empty:
            return {}
        
        try:
            recent_data = self.historical_data.tail(window_size * 2)
            if len(recent_data) < window_size:
                return {}
            
            # 计算早期和近期的平均速度
            early_avg = recent_data.head(window_size)['completed_points'].mean()
            recent_avg = recent_data.tail(window_size)['completed_points'].mean()
            
            # 计算趋势
            trend_change = recent_avg - early_avg
            trend_percentage = (trend_change / early_avg * 100) if early_avg > 0 else 0
            
            return {
                'early_average': early_avg,
                'recent_average': recent_avg,
                'trend_change': trend_change,
                'trend_percentage': trend_percentage,
                'trend_direction': 'increasing' if trend_change > 0 else 'decreasing' if trend_change < 0 else 'stable'
            }
            
        except Exception as e:
            logger.error(f"获取速度趋势失败: {e}")
            return {}
    
    def get_team_performance(self) -> Dict[str, Any]:
        """获取团队表现分析"""
        if self.historical_data.empty:
            return {}
        
        try:
            team_stats = {
                'average_teams_active': self.historical_data['teams_active'].mean(),
                'max_teams_active': self.historical_data['teams_active'].max(),
                'team_efficiency': self.historical_data['completed_points'].sum() / self.historical_data['teams_active'].sum() if self.historical_data['teams_active'].sum() > 0 else 0
            }
            
            return team_stats
            
        except Exception as e:
            logger.error(f"获取团队表现分析失败: {e}")
            return {}
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """获取汇总统计信息"""
        summary = {
            'daily_statistics': self.daily_statistics,
            'velocity_trend': self.get_velocity_trend(),
            'team_performance': self.get_team_performance(),
            'data_source': 'real_data'
        }
        
        if not self.historical_data.empty:
            summary['data_range'] = {
                'start_date': self.historical_data['date'].min().strftime('%Y-%m-%d'),
                'end_date': self.historical_data['date'].max().strftime('%Y-%m-%d'),
                'total_days': len(self.historical_data)
            }
        
        # 添加数据质量报告
        try:
            if not self.historical_data.empty:
                start_date = DateType(self.historical_data['date'].min())
                end_date = DateType(self.historical_data['date'].max())
                data_validation = self.data_connector.validate_data_availability(start_date, end_date)
                summary['data_quality'] = data_validation
        except Exception as e:
            logger.warning(f"获取数据质量报告失败: {e}")
        
        return summary
    
    def get_current_cumulative_progress(self) -> int:
        """获取当前累计进度"""
        try:
            current_date = DateType(datetime.now())
            return self.data_connector.get_cumulative_progress(current_date)
        except Exception as e:
            logger.error(f"获取当前累计进度失败: {e}")
            # 使用历史数据的累计值作为备选
            if not self.historical_data.empty:
                return int(self.historical_data['cumulative_points'].iloc[-1])
            return 0
    
    def get_project_target_estimate(self) -> Optional[int]:
        """获取项目目标估算"""
        return self.data_connector.get_project_target()
    
    def get_weighted_daily_average(self, recent_weight: float = 0.7) -> float:
        """
        获取加权日均完成量
        
        Args:
            recent_weight: 近期数据的权重，默认0.7（近期数据权重更高）
            
        Returns:
            float: 加权日均完成量
        """
        if self.historical_data.empty:
            return 0.0
        
        try:
            # 获取每日完成量
            daily_completed = self.historical_data['completed_points']
            
            if len(daily_completed) == 0:
                return 0.0
            
            # 如果只有一天数据，直接返回
            if len(daily_completed) == 1:
                return float(daily_completed.iloc[0])
            
            # 计算加权平均
            # 近期数据权重更高
            n = len(daily_completed)
            weights = np.linspace(1 - recent_weight, recent_weight, n)
            weights = weights / weights.sum()  # 归一化权重
            
            weighted_avg = np.average(daily_completed, weights=weights)
            
            logger.debug(f"计算加权日均完成量: {weighted_avg:.2f} (基于 {n} 天数据)")
            return float(weighted_avg)
            
        except Exception as e:
            logger.error(f"计算加权日均完成量失败: {e}")
            # 降级为简单平均
            return float(self.historical_data['completed_points'].mean()) if not self.historical_data.empty else 0.0

    def get_daily_average_completion(self) -> float:
        """
        获取简单日均完成量
        
        Returns:
            float: 简单日均完成量
        """
        if self.historical_data.empty:
            return 0.0
        
        try:
            # 确保历史数据中有completed_points列
            if 'completed_points' not in self.historical_data.columns:
                logger.warning("历史数据中没有completed_points列")
                return 0.0
            
            daily_avg = self.historical_data['completed_points'].mean()
            logger.debug(f"计算简单日均完成量: {daily_avg:.2f}")
            return float(daily_avg)
            
        except Exception as e:
            logger.error(f"计算简单日均完成量失败: {e}")
            return 0.0

    def get_linear_regression_prediction(self) -> Dict[str, Any]:
        """
        获取线性回归预测结果
        
        Returns:
            Dict[str, Any]: 包含回归预测信息的字典
        """
        if self.historical_data.empty:
            return {"error": "没有历史数据进行回归分析"}
        
        try:
            import numpy as np
            from sklearn.linear_model import LinearRegression
            
            # 准备数据
            dates = pd.to_datetime(self.historical_data['date'])
            # 将日期转换为数值（从第一天开始的天数）
            days_from_start = (dates - dates.min()).dt.days.values.reshape(-1, 1)
            completion_points = self.historical_data['completed_points'].values
            
            if len(days_from_start) < 2:
                return {"error": "数据点太少，无法进行回归分析"}
            
            # 执行线性回归
            model = LinearRegression()
            model.fit(days_from_start, completion_points)
            
            # 预测下一天的完成点数
            next_day = days_from_start[-1][0] + 1
            predicted_points = model.predict([[next_day]])[0]
            
            # 计算R²分数
            r2_score = model.score(days_from_start, completion_points)
            
            return {
                "predicted_daily_points": max(0, predicted_points),  # 确保非负
                "slope": model.coef_[0],
                "intercept": model.intercept_,
                "r2_score": r2_score,
                "confidence": "high" if r2_score > 0.7 else "medium" if r2_score > 0.3 else "low"
            }
            
        except ImportError:
            logger.warning("sklearn未安装，使用简单趋势预测")
            # 降级为简单趋势分析
            if len(self.historical_data) >= 7:
                recent_avg = self.historical_data['completed_points'].tail(7).mean()
                return {
                    "predicted_daily_points": recent_avg,
                    "method": "simple_trend",
                    "confidence": "medium"
                }
            else:
                return {
                    "predicted_daily_points": self.get_daily_average_completion(),
                    "method": "overall_average", 
                    "confidence": "low"
                }
        except Exception as e:
            logger.error(f"线性回归预测失败: {e}")
            return {"error": str(e)}

    def get_daily_completion_statistics(self) -> Dict[str, Any]:
        """
        获取每日完成统计信息
        
        Returns:
            Dict[str, Any]: 统计信息字典
        """
        if self.historical_data.empty:
            return {"error": "没有历史数据"}
        
        try:
            completed_points = self.historical_data['completed_points']
            
            stats = {
                "mean": completed_points.mean(),
                "median": completed_points.median(),
                "std": completed_points.std(),
                "min": completed_points.min(),
                "max": completed_points.max(),
                "total_days": len(completed_points),
                "active_days": len(completed_points[completed_points > 0]),
                "zero_days": len(completed_points[completed_points == 0]),
                "percentiles": {
                    "25th": completed_points.quantile(0.25),
                    "75th": completed_points.quantile(0.75),
                    "90th": completed_points.quantile(0.90)
                }
            }
            
            # 计算趋势
            if len(completed_points) >= 7:
                recent_avg = completed_points.tail(7).mean()
                overall_avg = completed_points.mean()
                stats["trend"] = "increasing" if recent_avg > overall_avg * 1.1 else \
                                "decreasing" if recent_avg < overall_avg * 0.9 else "stable"
            else:
                stats["trend"] = "unknown"
            
            return stats
            
        except Exception as e:
            logger.error(f"计算每日完成统计失败: {e}")
            return {"error": str(e)}