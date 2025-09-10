"""
进度跟踪器模块

整合数据分析、完成日期估算和图表生成功能的主控制器
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

from .data_analyzer import DataAnalyzer
from .finish_date_estimator import FinishDateEstimator
from .progress_charts import ProgressCharts
from ..data_models.date_types import DateType

logger = logging.getLogger(__name__)


class ProgressTracker:
    """进度跟踪器主类，整合所有进度估算功能"""

    def __init__(self, workspace_path: str = None, output_dir: str = None):
        """
        初始化进度跟踪器
        
        Args:
            workspace_path: 工作空间路径
            output_dir: 输出目录路径
        """
        self.workspace_path = workspace_path or os.getcwd()
        self.output_dir = output_dir or os.path.join(self.workspace_path, 'progress_reports')
        
        # 初始化各个组件
        self.data_analyzer = DataAnalyzer(self.workspace_path)
        self.finish_estimator = None  # 将在数据加载后初始化
        self.charts_generator = ProgressCharts(self.data_analyzer, self.output_dir)
        
        # 项目配置
        self.project_config = {
            'target_points': 0,
            'current_points': 0,
            'start_date': None,
            'target_date': None
        }
        
        logger.info(f"进度跟踪器已初始化，输出目录: {self.output_dir}")
    
    def initialize_project(self, 
                          target_points: int,
                          current_points: int = 0,
                          start_date: DateType = None,
                          target_date: DateType = None) -> bool:
        """
        初始化项目配置
        
        Args:
            target_points: 目标总点数
            current_points: 当前已完成点数
            start_date: 项目开始日期
            target_date: 目标完成日期
            
        Returns:
            bool: 是否成功初始化
        """
        try:
            self.project_config.update({
                'target_points': target_points,
                'current_points': current_points,
                'start_date': start_date,
                'target_date': target_date
            })
            
            logger.info(f"项目已初始化: 目标 {target_points} 点, 当前 {current_points} 点")
            return True
            
        except Exception as e:
            logger.error(f"项目初始化失败: {e}")
            return False
    
    def load_historical_data(self, 
                           start_date: DateType = None,
                           end_date: DateType = None,
                           days_back: int = 30) -> bool:
        """
        加载历史数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            days_back: 如果没有指定开始日期，从今天往前多少天
            
        Returns:
            bool: 是否成功加载数据
        """
        try:
            if start_date is None:
                start_date = DateType(datetime.now() - timedelta(days=days_back))
            
            success = self.data_analyzer.load_historical_data(start_date, end_date)
            
            if success:
                # 计算速度统计
                self.data_analyzer.calculate_daily_velocity()
                
                # 初始化完成日期估算器
                self.finish_estimator = FinishDateEstimator(self.data_analyzer)
                
                logger.info("历史数据加载完成，进度跟踪器就绪")
                return True
            else:
                logger.warning("历史数据加载失败或无数据")
                return False
                
        except Exception as e:
            logger.error(f"加载历史数据失败: {e}")
            return False
    
    def get_current_progress_summary(self) -> Dict[str, Any]:
        """
        获取当前进度摘要
        
        Returns:
            Dict: 包含进度摘要的字典
        """
        try:
            summary = {
                'project_info': self.project_config.copy(),
                'timestamp': datetime.now().isoformat(),
                'data_available': not self.data_analyzer.historical_data.empty
            }
            
            if self.project_config['target_points'] > 0:
                completion_rate = self.project_config['current_points'] / self.project_config['target_points']
                summary['completion_rate'] = completion_rate
                summary['completion_percentage'] = completion_rate * 100
            
            # 添加数据分析摘要
            if not self.data_analyzer.historical_data.empty:
                summary['data_analysis'] = self.data_analyzer.get_summary_statistics()
            
            # 添加完成日期估算
            if self.finish_estimator and self.project_config['target_points'] > 0:
                estimate = self.finish_estimator.get_recommended_estimate(
                    self.project_config['target_points'],
                    self.project_config['current_points']
                )
                summary['finish_estimate'] = estimate
            
            return summary
            
        except Exception as e:
            logger.error(f"获取进度摘要失败: {e}")
            return {'error': str(e)}
    
    def generate_progress_report(self, 
                               include_charts: bool = True,
                               chart_types: List[str] = None) -> Dict[str, Any]:
        """
        生成完整的进度报告
        
        Args:
            include_charts: 是否包含图表
            chart_types: 要生成的图表类型列表
            
        Returns:
            Dict: 包含报告内容和文件路径的字典
        """
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'summary': self.get_current_progress_summary(),
                'charts': {},
                'recommendations': []
            }
            
            # 生成图表
            if include_charts and not self.data_analyzer.historical_data.empty:
                if chart_types is None:
                    chart_types = ['burndown', 'burnup', 'velocity', 'dashboard']
                
                chart_paths = {}
                
                for chart_type in chart_types:
                    try:
                        if chart_type == 'burndown':
                            path = self.charts_generator.generate_burndown_chart(
                                self.project_config['target_points'],
                                self.project_config['current_points'],
                                self.finish_estimator
                            )
                        elif chart_type == 'burnup':
                            path = self.charts_generator.generate_burnup_chart(
                                self.project_config['target_points'],
                                self.project_config['current_points'],
                                self.finish_estimator
                            )
                        elif chart_type == 'velocity':
                            path = self.charts_generator.generate_velocity_chart()
                        elif chart_type == 'dashboard':
                            path = self.charts_generator.generate_progress_dashboard(
                                self.project_config['target_points'],
                                self.project_config['current_points'],
                                self.finish_estimator
                            )
                        else:
                            continue
                        
                        if path:
                            chart_paths[chart_type] = path
                            
                    except Exception as e:
                        logger.warning(f"生成 {chart_type} 图表失败: {e}")
                
                report['charts'] = chart_paths
                logger.info(f"成功生成 {len(chart_paths)} 个图表")
            
            # 生成建议
            recommendations = self._generate_recommendations()
            report['recommendations'] = recommendations
            
            # 保存报告摘要
            report_summary_path = os.path.join(self.output_dir, f'progress_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
            self._save_text_report(report, report_summary_path)
            report['summary_file'] = report_summary_path
            
            return report
            
        except Exception as e:
            logger.error(f"生成进度报告失败: {e}")
            return {'error': str(e)}
    
    def _generate_recommendations(self) -> List[str]:
        """基于当前数据生成建议"""
        recommendations = []
        
        try:
            # 检查完成率
            if self.project_config['target_points'] > 0:
                completion_rate = self.project_config['current_points'] / self.project_config['target_points']
                
                if completion_rate < 0.3:
                    recommendations.append("项目进度较慢，建议检查是否有资源或流程问题")
                elif completion_rate > 0.8:
                    recommendations.append("项目进度良好，接近完成")
            
            # 检查速度趋势
            if not self.data_analyzer.historical_data.empty:
                trend = self.data_analyzer.get_velocity_trend()
                
                if trend.get('trend_direction') == 'decreasing':
                    recommendations.append("完成速度呈下降趋势，建议分析原因并采取改进措施")
                elif trend.get('trend_direction') == 'increasing':
                    recommendations.append("完成速度呈上升趋势，保持当前工作模式")
            
            # 检查团队表现
            team_performance = self.data_analyzer.get_team_performance()
            if team_performance:
                avg_teams = team_performance.get('average_teams_active', 0)
                if avg_teams < 2:
                    recommendations.append("活跃团队数量较少，考虑增加人力投入")
            
            # 检查预估完成日期
            if self.finish_estimator:
                estimate = self.finish_estimator.get_recommended_estimate(
                    self.project_config['target_points'],
                    self.project_config['current_points']
                )
                
                if estimate.get('confidence', 0) < 0.6:
                    recommendations.append("完成日期预估置信度较低，建议收集更多历史数据")
                
                if self.project_config.get('target_date'):
                    target_date = self.project_config['target_date'].date_datetime
                    estimated_date = estimate.get('estimated_date')
                    
                    if estimated_date and estimated_date > target_date:
                        recommendations.append("预估完成日期晚于目标日期，建议调整计划或增加资源")
            
            if not recommendations:
                recommendations.append("项目进展正常，继续保持当前节奏")
                
        except Exception as e:
            logger.error(f"生成建议失败: {e}")
            recommendations.append("无法生成建议，请检查数据完整性")
        
        return recommendations
    
    def _save_text_report(self, report: Dict[str, Any], file_path: str) -> None:
        """保存文本格式的报告摘要"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("GMAS 项目进度报告\n")
                f.write("=" * 50 + "\n\n")
                
                # 基本信息
                f.write("项目基本信息:\n")
                f.write("-" * 20 + "\n")
                config = report['summary']['project_info']
                f.write(f"目标点数: {config.get('target_points', 'N/A')}\n")
                f.write(f"当前点数: {config.get('current_points', 'N/A')}\n")
                
                if 'completion_percentage' in report['summary']:
                    f.write(f"完成率: {report['summary']['completion_percentage']:.1f}%\n")
                
                f.write(f"报告生成时间: {report['timestamp']}\n\n")
                
                # 完成日期预估
                if 'finish_estimate' in report['summary']:
                    f.write("完成日期预估:\n")
                    f.write("-" * 20 + "\n")
                    estimate = report['summary']['finish_estimate']
                    
                    if estimate.get('estimated_date'):
                        est_date = estimate['estimated_date']
                        if hasattr(est_date, 'strftime'):
                            f.write(f"预估完成日期: {est_date.strftime('%Y-%m-%d')}\n")
                        else:
                            f.write(f"预估完成日期: {est_date}\n")
                    
                    f.write(f"剩余天数: {estimate.get('days_remaining', 'N/A'):.1f}\n")
                    f.write(f"置信度: {estimate.get('confidence', 0)*100:.1f}%\n")
                    f.write(f"估算方法: {estimate.get('method', 'N/A')}\n\n")
                
                # 数据统计
                if 'data_analysis' in report['summary']:
                    analysis = report['summary']['data_analysis']
                    f.write("数据统计:\n")
                    f.write("-" * 20 + "\n")
                    
                    daily_stats = analysis.get('daily_statistics', {})
                    f.write(f"总天数: {daily_stats.get('total_days', 'N/A')}\n")
                    f.write(f"总完成点数: {daily_stats.get('total_points', 'N/A')}\n")
                    f.write(f"平均每日: {daily_stats.get('average_daily', 0):.1f} 点\n")
                    f.write(f"最高每日: {daily_stats.get('max_daily', 'N/A')} 点\n\n")
                
                # 建议
                f.write("项目建议:\n")
                f.write("-" * 20 + "\n")
                for i, rec in enumerate(report.get('recommendations', []), 1):
                    f.write(f"{i}. {rec}\n")
                
                # 生成的图表
                if report.get('charts'):
                    f.write("\n生成的图表:\n")
                    f.write("-" * 20 + "\n")
                    for chart_type, path in report['charts'].items():
                        f.write(f"{chart_type}: {path}\n")
            
            logger.info(f"报告摘要已保存至: {file_path}")
            
        except Exception as e:
            logger.error(f"保存文本报告失败: {e}")
    
    def update_current_progress(self, current_points: int) -> bool:
        """
        更新当前进度
        
        Args:
            current_points: 当前已完成点数
            
        Returns:
            bool: 是否成功更新
        """
        try:
            self.project_config['current_points'] = current_points
            logger.info(f"进度已更新至 {current_points} 点")
            return True
        except Exception as e:
            logger.error(f"更新进度失败: {e}")
            return False
    
    def get_daily_target(self, target_date: DateType = None) -> Dict[str, Any]:
        """
        计算每日目标完成量
        
        Args:
            target_date: 目标完成日期
            
        Returns:
            Dict: 包含每日目标信息的字典
        """
        try:
            if target_date is None:
                target_date = self.project_config.get('target_date')
            
            if not target_date:
                return {'error': '未设置目标日期'}
            
            remaining_points = self.project_config['target_points'] - self.project_config['current_points']
            remaining_days = (target_date.date_datetime - datetime.now()).days
            
            if remaining_days <= 0:
                return {
                    'status': 'overdue',
                    'message': '目标日期已过期'
                }
            
            daily_target = remaining_points / remaining_days
            
            # 计算基于历史数据的可行性
            feasibility = 'unknown'
            if not self.data_analyzer.historical_data.empty:
                avg_daily = self.data_analyzer.daily_statistics.get('average_daily', 0)
                if avg_daily > 0:
                    if daily_target <= avg_daily * 0.8:
                        feasibility = 'easy'
                    elif daily_target <= avg_daily * 1.2:
                        feasibility = 'achievable'
                    elif daily_target <= avg_daily * 1.5:
                        feasibility = 'challenging'
                    else:
                        feasibility = 'difficult'
            
            return {
                'daily_target': daily_target,
                'remaining_points': remaining_points,
                'remaining_days': remaining_days,
                'feasibility': feasibility,
                'target_date': target_date.yyyymmdd_str,
                'current_average': self.data_analyzer.daily_statistics.get('average_daily', 0)
            }
            
        except Exception as e:
            logger.error(f"计算每日目标失败: {e}")
            return {'error': str(e)}