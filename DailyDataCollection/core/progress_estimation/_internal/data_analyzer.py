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

from ...data_models.date_types import DateType
from ...data_models.observation_data import ObservationData
from .excel_data_connector import ExcelDataConnector

logger = logging.getLogger(__name__)


class DataAnalyzer:
    """数据分析器类，用于分析历史观测数据"""

    def __init__(self, workspace_path: str = None, use_real_data: bool = True):
        """
        初始化数据分析器
        
        Args:
            workspace_path: 工作空间路径，用于查找历史数据
            use_real_data: 是否使用真实数据（默认True），False时使用模拟数据
        """
        self.workspace_path = workspace_path or os.getcwd()
        self.use_real_data = use_real_data
        self.historical_data: pd.DataFrame = pd.DataFrame()
        self.daily_statistics: Dict[str, Any] = {}
        
        # 初始化数据连接器
        if self.use_real_data:
            self.data_connector = ExcelDataConnector(self.workspace_path)
            logger.info("数据分析器初始化完成，使用真实数据源")
        else:
            self.data_connector = None
            logger.info("数据分析器初始化完成，使用模拟数据源")
        
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
            
            if self.use_real_data and self.data_connector:
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
            else:
                # 使用模拟数据
                date_range = self._generate_date_range(start_date, end_date)
                historical_records = []
                
                for date_obj in date_range:
                    daily_data = self._extract_daily_data(date_obj)
                    if daily_data:
                        historical_records.append(daily_data)
                
                if historical_records:
                    self.historical_data = pd.DataFrame(historical_records)
                    self.historical_data['date'] = pd.to_datetime(self.historical_data['date'])
                    self.historical_data = self.historical_data.sort_values('date')
                    logger.info(f"成功生成 {len(historical_records)} 天的模拟历史数据")
                    return True
                else:
                    logger.warning("未找到历史数据")
                    return False
                
        except Exception as e:
            logger.error(f"加载历史数据失败: {e}")
            return False
    
    def _generate_date_range(self, start_date: DateType, end_date: DateType) -> List[DateType]:
        """生成日期范围"""
        date_range = []
        current = start_date.date_datetime
        end = end_date.date_datetime
        
        while current <= end:
            date_range.append(DateType(current))
            current += timedelta(days=1)
            
        return date_range
    
    def _extract_daily_data(self, date_obj: DateType) -> Optional[Dict[str, Any]]:
        """
        从指定日期提取数据
        
        优先使用真实数据，如果启用且数据连接器可用的话
        """
        try:
            if self.use_real_data and self.data_connector:
                # 使用真实数据源
                return self.data_connector.get_daily_progress_data(date_obj)
            else:
                # 使用模拟数据（保持原有逻辑用于测试）
                daily_points = self._simulate_daily_points(date_obj)
                
                if daily_points > 0:
                    return {
                        'date': date_obj.yyyymmdd_str,
                        'completed_points': daily_points,
                        'cumulative_points': daily_points,  # 这个需要累计计算
                        'teams_active': self._simulate_team_count(date_obj),
                        'workday': date_obj.date_datetime.weekday() < 5  # 工作日
                    }
            
        except Exception as e:
            logger.debug(f"提取 {date_obj.yyyymmdd_str} 数据失败: {e}")
            
        return None
    
    def _simulate_daily_points(self, date_obj: DateType) -> int:
        """模拟每日点数数据"""
        # 这里应该替换为实际的数据读取逻辑
        # 模拟数据：工作日完成更多点，周末较少
        base_points = 50
        weekday = date_obj.date_datetime.weekday()
        
        if weekday < 5:  # 工作日
            return base_points + np.random.randint(-10, 20)
        else:  # 周末
            return max(0, base_points // 3 + np.random.randint(-10, 10))
    
    def _simulate_team_count(self, date_obj: DateType) -> int:
        """模拟活跃团队数量"""
        # 模拟数据：工作日有更多团队活跃
        weekday = date_obj.date_datetime.weekday()
        if weekday < 5:
            return np.random.randint(3, 6)
        else:
            return np.random.randint(1, 3)
    
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
            'data_source': 'real_data' if self.use_real_data else 'simulated_data'
        }
        
        if not self.historical_data.empty:
            summary['data_range'] = {
                'start_date': self.historical_data['date'].min().strftime('%Y-%m-%d'),
                'end_date': self.historical_data['date'].max().strftime('%Y-%m-%d'),
                'total_days': len(self.historical_data)
            }
        
        # 如果使用真实数据，添加数据质量报告
        if self.use_real_data and self.data_connector:
            try:
                start_date = DateType(self.historical_data['date'].min())
                end_date = DateType(self.historical_data['date'].max())
                data_validation = self.data_connector.validate_data_availability(start_date, end_date)
                summary['data_quality'] = data_validation
            except Exception as e:
                logger.warning(f"获取数据质量报告失败: {e}")
        
        return summary
    
    def get_current_cumulative_progress(self) -> int:
        """获取当前累计进度"""
        if self.use_real_data and self.data_connector:
            try:
                current_date = DateType(datetime.now())
                return self.data_connector.get_cumulative_progress(current_date)
            except Exception as e:
                logger.error(f"获取当前累计进度失败: {e}")
                return 0
        else:
            # 使用历史数据的累计值
            if not self.historical_data.empty:
                return int(self.historical_data['cumulative_points'].iloc[-1])
            return 0
    
    def get_project_target_estimate(self) -> Optional[int]:
        """获取项目目标估算"""
        if self.use_real_data and self.data_connector:
            return self.data_connector.get_project_target()
        return None
    
    def switch_to_real_data(self) -> bool:
        """切换到真实数据源"""
        try:
            if not self.use_real_data:
                self.use_real_data = True
                self.data_connector = ExcelDataConnector(self.workspace_path)
                # 清空现有数据，强制重新加载
                self.historical_data = pd.DataFrame()
                self.daily_statistics = {}
                logger.info("已切换到真实数据源")
                return True
            else:
                logger.info("已经在使用真实数据源")
                return True
        except Exception as e:
            logger.error(f"切换到真实数据源失败: {e}")
            return False
    
    def switch_to_simulated_data(self) -> bool:
        """切换到模拟数据源"""
        try:
            if self.use_real_data:
                self.use_real_data = False
                self.data_connector = None
                # 清空现有数据，强制重新加载
                self.historical_data = pd.DataFrame()
                self.daily_statistics = {}
                logger.info("已切换到模拟数据源")
                return True
            else:
                logger.info("已经在使用模拟数据源")
                return True
        except Exception as e:
            logger.error(f"切换到模拟数据源失败: {e}")
            return False