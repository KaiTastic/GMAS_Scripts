"""
进度图表生成器模块

生成燃尽图、燃起图和其他进度相关的可视化图表
"""

import os
import logging
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from .data_analyzer import DataAnalyzer
from .finish_date_estimator import FinishDateEstimator

logger = logging.getLogger(__name__)

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class ProgressCharts:
    """进度图表生成器类"""

    def __init__(self, data_analyzer: DataAnalyzer, output_dir: str = None):
        """
        初始化进度图表生成器
        
        Args:
            data_analyzer: 数据分析器实例
            output_dir: 图表输出目录
        """
        self.data_analyzer = data_analyzer
        self.output_dir = output_dir or os.path.join(os.getcwd(), 'charts')
        self.colors = {
            'primary': '#2E86C1',
            'secondary': '#F39C12', 
            'success': '#28B463',
            'warning': '#F1C40F',
            'danger': '#E74C3C',
            'info': '#85C1E9',
            'grid': '#E5E7E9'
        }
        
        # 确保输出目录存在
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    
    def generate_burndown_chart(self, 
                              target_points: int,
                              current_points: int = 0,
                              finish_estimator: FinishDateEstimator = None,
                              save_path: str = None) -> str:
        """
        生成燃尽图
        
        Args:
            target_points: 目标总点数
            current_points: 当前已完成点数
            finish_estimator: 完成日期估算器
            save_path: 保存路径
            
        Returns:
            str: 保存的文件路径
        """
        if self.data_analyzer.historical_data.empty:
            logger.warning("没有历史数据，无法生成燃尽图")
            return ""
        
        try:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            data = self.data_analyzer.historical_data.copy()
            
            # 计算剩余工作量
            data['remaining_work'] = target_points - data['cumulative_points']
            
            # 绘制实际燃尽线
            ax.plot(data['date'], data['remaining_work'], 
                   color=self.colors['primary'], linewidth=2, 
                   label='实际进度', marker='o', markersize=4)
            
            # 绘制理想燃尽线
            start_date = data['date'].min()
            today = datetime.now()
            
            if finish_estimator:
                estimate = finish_estimator.get_recommended_estimate(target_points, current_points)
                if estimate.get('estimated_date'):
                    end_date = estimate['estimated_date']
                else:
                    end_date = today + timedelta(days=30)  # 默认30天后
            else:
                end_date = today + timedelta(days=30)
            
            ideal_dates = pd.date_range(start=start_date, end=end_date, freq='D')
            ideal_remaining = np.linspace(target_points, 0, len(ideal_dates))
            
            ax.plot(ideal_dates, ideal_remaining, 
                   color=self.colors['secondary'], linewidth=2, 
                   linestyle='--', label='理想进度')
            
            # 添加今日线
            ax.axvline(x=today, color=self.colors['warning'], 
                      linestyle='-', alpha=0.7, label='今日')
            
            # 如果有预估完成日期，添加预估线
            if finish_estimator:
                estimate = finish_estimator.get_recommended_estimate(target_points, current_points)
                if estimate.get('estimated_date'):
                    estimated_date = estimate['estimated_date']
                    ax.axvline(x=estimated_date, color=self.colors['success'], 
                              linestyle=':', alpha=0.7, label=f'预估完成日期')
            
            # 设置图表样式
            ax.set_xlabel('日期', fontsize=12)
            ax.set_ylabel('剩余工作量 (点数)', fontsize=12)
            ax.set_title('项目燃尽图 (Burndown Chart)', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, color=self.colors['grid'])
            ax.legend(fontsize=10)
            
            # 格式化日期轴
            ax.xaxis.set_major_locator(mdates.WeekdayLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            plt.xticks(rotation=45)
            
            # 设置Y轴从0开始
            ax.set_ylim(bottom=0)
            
            plt.tight_layout()
            
            # 保存图表
            if not save_path:
                save_path = os.path.join(self.output_dir, f'burndown_chart_{datetime.now().strftime("%Y%m%d")}.png')
            
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"燃尽图已保存至: {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"生成燃尽图失败: {e}")
            plt.close()
            return ""
    
    def generate_burnup_chart(self, 
                            target_points: int,
                            current_points: int = 0,
                            finish_estimator: FinishDateEstimator = None,
                            save_path: str = None) -> str:
        """
        生成燃起图
        
        Args:
            target_points: 目标总点数
            current_points: 当前已完成点数
            finish_estimator: 完成日期估算器
            save_path: 保存路径
            
        Returns:
            str: 保存的文件路径
        """
        if self.data_analyzer.historical_data.empty:
            logger.warning("没有历史数据，无法生成燃起图")
            return ""
        
        try:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            data = self.data_analyzer.historical_data.copy()
            
            # 绘制实际完成线
            ax.plot(data['date'], data['cumulative_points'], 
                   color=self.colors['success'], linewidth=2, 
                   label='实际完成', marker='o', markersize=4)
            
            # 绘制目标线
            target_line_dates = pd.date_range(start=data['date'].min(), 
                                            end=data['date'].max() + timedelta(days=30), 
                                            freq='D')
            target_line_values = [target_points] * len(target_line_dates)
            
            ax.plot(target_line_dates, target_line_values, 
                   color=self.colors['danger'], linewidth=2, 
                   linestyle='-', label=f'目标 ({target_points} 点)')
            
            # 绘制理想进度线
            if finish_estimator:
                estimate = finish_estimator.get_recommended_estimate(target_points, current_points)
                if estimate.get('estimated_date'):
                    end_date = estimate['estimated_date']
                    ideal_dates = pd.date_range(start=data['date'].min(), end=end_date, freq='D')
                    ideal_values = np.linspace(0, target_points, len(ideal_dates))
                    
                    ax.plot(ideal_dates, ideal_values, 
                           color=self.colors['secondary'], linewidth=2, 
                           linestyle='--', label='理想进度')
            
            # 添加今日线
            today = datetime.now()
            ax.axvline(x=today, color=self.colors['warning'], 
                      linestyle='-', alpha=0.7, label='今日')
            
            # 设置图表样式
            ax.set_xlabel('日期', fontsize=12)
            ax.set_ylabel('累计完成量 (点数)', fontsize=12)
            ax.set_title('项目燃起图 (Burnup Chart)', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, color=self.colors['grid'])
            ax.legend(fontsize=10)
            
            # 格式化日期轴
            ax.xaxis.set_major_locator(mdates.WeekdayLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            plt.xticks(rotation=45)
            
            # 设置Y轴从0开始
            ax.set_ylim(bottom=0)
            
            plt.tight_layout()
            
            # 保存图表
            if not save_path:
                save_path = os.path.join(self.output_dir, f'burnup_chart_{datetime.now().strftime("%Y%m%d")}.png')
            
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"燃起图已保存至: {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"生成燃起图失败: {e}")
            plt.close()
            return ""
    
    def generate_velocity_chart(self, save_path: str = None) -> str:
        """
        生成速度趋势图
        
        Args:
            save_path: 保存路径
            
        Returns:
            str: 保存的文件路径
        """
        if self.data_analyzer.historical_data.empty:
            logger.warning("没有历史数据，无法生成速度图")
            return ""
        
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            
            data = self.data_analyzer.historical_data.copy()
            
            # 上图：每日完成量
            bars = ax1.bar(data['date'], data['completed_points'], 
                          color=self.colors['primary'], alpha=0.7, label='每日完成量')
            
            # 添加移动平均线
            if 'velocity_7day' in data.columns:
                ax1.plot(data['date'], data['velocity_7day'], 
                        color=self.colors['danger'], linewidth=2, 
                        label='7天移动平均')
            
            ax1.set_xlabel('日期', fontsize=12)
            ax1.set_ylabel('每日完成点数', fontsize=12)
            ax1.set_title('每日完成量和速度趋势', fontsize=14, fontweight='bold')
            ax1.grid(True, alpha=0.3, color=self.colors['grid'])
            ax1.legend(fontsize=10)
            
            # 下图：团队活跃度
            ax2.bar(data['date'], data['teams_active'], 
                   color=self.colors['info'], alpha=0.7, label='活跃团队数')
            
            ax2.set_xlabel('日期', fontsize=12)
            ax2.set_ylabel('活跃团队数', fontsize=12)
            ax2.set_title('团队活跃度', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3, color=self.colors['grid'])
            ax2.legend(fontsize=10)
            
            # 格式化日期轴
            for ax in [ax1, ax2]:
                ax.xaxis.set_major_locator(mdates.WeekdayLocator())
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            
            # 保存图表
            if not save_path:
                save_path = os.path.join(self.output_dir, f'velocity_chart_{datetime.now().strftime("%Y%m%d")}.png')
            
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"速度图已保存至: {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"生成速度图失败: {e}")
            plt.close()
            return ""
    
    def generate_progress_dashboard(self, 
                                  target_points: int,
                                  current_points: int = 0,
                                  finish_estimator: FinishDateEstimator = None,
                                  save_path: str = None) -> str:
        """
        生成综合进度仪表板
        
        Args:
            target_points: 目标总点数
            current_points: 当前已完成点数
            finish_estimator: 完成日期估算器
            save_path: 保存路径
            
        Returns:
            str: 保存的文件路径
        """
        if self.data_analyzer.historical_data.empty:
            logger.warning("没有历史数据，无法生成仪表板")
            return ""
        
        try:
            fig = plt.figure(figsize=(16, 12))
            
            # 创建子图布局
            gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
            
            data = self.data_analyzer.historical_data.copy()
            
            # 1. 进度概览（饼图）
            ax1 = fig.add_subplot(gs[0, 0])
            completed_ratio = current_points / target_points if target_points > 0 else 0
            remaining_ratio = 1 - completed_ratio
            
            labels = ['已完成', '剩余']
            sizes = [completed_ratio, remaining_ratio]
            colors = [self.colors['success'], self.colors['grid']]
            
            ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax1.set_title(f'项目进度概览\n({current_points}/{target_points} 点)')
            
            # 2. 燃尽图（简化版）
            ax2 = fig.add_subplot(gs[0, 1:])
            remaining_work = target_points - data['cumulative_points']
            ax2.plot(data['date'], remaining_work, color=self.colors['primary'], linewidth=2)
            ax2.set_title('燃尽趋势')
            ax2.set_ylabel('剩余工作量')
            ax2.grid(True, alpha=0.3)
            
            # 3. 每日完成量
            ax3 = fig.add_subplot(gs[1, :])
            bars = ax3.bar(data['date'], data['completed_points'], 
                          color=self.colors['primary'], alpha=0.7)
            
            if 'velocity_7day' in data.columns:
                ax3.plot(data['date'], data['velocity_7day'], 
                        color=self.colors['danger'], linewidth=2, label='7天平均')
                ax3.legend()
            
            ax3.set_title('每日完成量趋势')
            ax3.set_ylabel('完成点数')
            ax3.grid(True, alpha=0.3)
            
            # 4. 统计信息表格
            ax4 = fig.add_subplot(gs[2, 0])
            ax4.axis('off')
            
            stats = self.data_analyzer.daily_statistics
            if stats:
                stats_text = f"""项目统计信息:
                
总天数: {stats.get('total_days', 'N/A')}
总完成点数: {stats.get('total_points', 'N/A')}
平均每日: {stats.get('average_daily', 0):.1f} 点
最高每日: {stats.get('max_daily', 'N/A')} 点
当前进度: {completed_ratio*100:.1f}%"""
                
                ax4.text(0.1, 0.9, stats_text, transform=ax4.transAxes, 
                        fontsize=10, verticalalignment='top',
                        bbox=dict(boxstyle="round,pad=0.3", facecolor=self.colors['info'], alpha=0.3))
            
            # 5. 预估信息
            ax5 = fig.add_subplot(gs[2, 1])
            ax5.axis('off')
            
            if finish_estimator:
                estimate = finish_estimator.get_recommended_estimate(target_points, current_points)
                if estimate.get('estimated_date'):
                    est_date = estimate['estimated_date'].strftime('%Y-%m-%d')
                    days_remaining = estimate.get('days_remaining', 0)
                    confidence = estimate.get('confidence', 0)
                    
                    estimate_text = f"""完成预估:
                    
预估完成日期: {est_date}
剩余天数: {days_remaining:.1f} 天
置信度: {confidence*100:.1f}%
使用方法: {estimate.get('method', 'N/A')}"""
                    
                    ax5.text(0.1, 0.9, estimate_text, transform=ax5.transAxes, 
                            fontsize=10, verticalalignment='top',
                            bbox=dict(boxstyle="round,pad=0.3", facecolor=self.colors['warning'], alpha=0.3))
            
            # 6. 团队表现
            ax6 = fig.add_subplot(gs[2, 2])
            team_data = data.groupby('teams_active')['completed_points'].sum()
            if not team_data.empty:
                ax6.bar(team_data.index, team_data.values, color=self.colors['info'])
                ax6.set_title('团队数量 vs 完成量')
                ax6.set_xlabel('活跃团队数')
                ax6.set_ylabel('总完成点数')
            
            plt.suptitle('GMAS 项目进度仪表板', fontsize=16, fontweight='bold')
            
            # 保存图表
            if not save_path:
                save_path = os.path.join(self.output_dir, f'progress_dashboard_{datetime.now().strftime("%Y%m%d")}.png')
            
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"进度仪表板已保存至: {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"生成进度仪表板失败: {e}")
            plt.close()
            return ""
    
    def generate_all_charts(self, 
                          target_points: int,
                          current_points: int = 0,
                          finish_estimator: FinishDateEstimator = None) -> Dict[str, str]:
        """
        生成所有类型的图表
        
        Args:
            target_points: 目标总点数
            current_points: 当前已完成点数
            finish_estimator: 完成日期估算器
            
        Returns:
            Dict[str, str]: 包含所有图表文件路径的字典
        """
        chart_paths = {}
        
        try:
            # 生成燃尽图
            burndown_path = self.generate_burndown_chart(target_points, current_points, finish_estimator)
            if burndown_path:
                chart_paths['burndown'] = burndown_path
            
            # 生成燃起图
            burnup_path = self.generate_burnup_chart(target_points, current_points, finish_estimator)
            if burnup_path:
                chart_paths['burnup'] = burnup_path
            
            # 生成速度图
            velocity_path = self.generate_velocity_chart()
            if velocity_path:
                chart_paths['velocity'] = velocity_path
            
            # 生成仪表板
            dashboard_path = self.generate_progress_dashboard(target_points, current_points, finish_estimator)
            if dashboard_path:
                chart_paths['dashboard'] = dashboard_path
            
            logger.info(f"成功生成 {len(chart_paths)} 个图表")
            
        except Exception as e:
            logger.error(f"批量生成图表失败: {e}")
        
        return chart_paths