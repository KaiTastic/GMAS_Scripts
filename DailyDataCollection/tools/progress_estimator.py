"""
进度估算工具模块

提供项目进度估算和预测功能，作为独立的分析工具
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ProgressEstimator:
    """进度估算器 - 独立的工具类"""
    
    def __init__(self):
        self.mapsheet_manager = None
        self.data_connector = None
        self._initialize_dependencies()
    
    def _initialize_dependencies(self):
        """延迟初始化依赖模块"""
        try:
            from core.mapsheet.mapsheet_manager import get_mapsheet_manager
            from core.data_connectors.excel_data_connector import ExcelDataConnector
            
            self.mapsheet_manager = get_mapsheet_manager()
            self.data_connector = ExcelDataConnector()
            
        except ImportError as e:
            logger.warning(f"初始化依赖模块失败: {e}")
    
    def estimate_completion_date(self, mapsheet_id: str = None) -> Dict[str, Any]:
        """
        估算完成日期
        
        Args:
            mapsheet_id: 特定图幅ID，如果为None则估算整体项目
            
        Returns:
            包含估算结果的字典
        """
        if not self.mapsheet_manager or not self.data_connector:
            return {'error': '依赖模块未正确初始化'}
        
        try:
            if mapsheet_id:
                return self._estimate_single_mapsheet(mapsheet_id)
            else:
                return self._estimate_overall_project()
                
        except Exception as e:
            logger.error(f"估算完成日期失败: {e}")
            return {'error': str(e)}
    
    def _estimate_single_mapsheet(self, mapsheet_id: str) -> Dict[str, Any]:
        """估算单个图幅的完成时间"""
        # 查找图幅序号
        sequence = None
        for seq, info in self.mapsheet_manager.maps_info.items():
            if info['Roman Name'] == mapsheet_id or info.get('File Name') == mapsheet_id:
                sequence = seq
                break
        
        if not sequence:
            return {'error': f'未找到图幅: {mapsheet_id}'}
        
        # 获取历史数据
        hist_data = self.mapsheet_manager._historical_data.get(sequence)
        if not hist_data or not hist_data.daily_completions:
            return {'error': f'图幅 {mapsheet_id} 缺少历史数据'}
        
        # 计算平均每日完成速度
        daily_points = list(hist_data.daily_completions.values())
        recent_days = daily_points[-14:]  # 最近14天的数据
        avg_daily_speed = sum(recent_days) / len(recent_days) if recent_days else 0
        
        if avg_daily_speed <= 0:
            return {'error': f'图幅 {mapsheet_id} 无有效进度数据'}
        
        # 计算剩余点数和预估天数
        remaining_points = max(0, hist_data.target_total - hist_data.total_completed)
        estimated_days = remaining_points / avg_daily_speed if avg_daily_speed > 0 else float('inf')
        
        # 计算预估完成日期
        last_date = max(hist_data.daily_completions.keys())
        last_datetime = datetime.strptime(last_date, '%Y-%m-%d')
        estimated_completion = last_datetime + timedelta(days=int(estimated_days))
        
        return {
            'mapsheet_id': mapsheet_id,
            'current_points': hist_data.total_completed,
            'target_points': hist_data.target_total,
            'remaining_points': remaining_points,
            'avg_daily_speed': round(avg_daily_speed, 2),
            'estimated_days_remaining': int(estimated_days),
            'estimated_completion_date': estimated_completion.strftime('%Y-%m-%d'),
            'completion_percentage': hist_data.completion_percentage
        }
    
    def _estimate_overall_project(self) -> Dict[str, Any]:
        """估算整体项目完成时间"""
        total_current = 0
        total_target = 0
        total_daily_speed = 0
        active_mapsheets = 0
        
        for seq, hist_data in self.mapsheet_manager._historical_data.items():
            if hist_data.daily_completions:
                total_current += hist_data.total_completed
                total_target += hist_data.target_total
                
                # 计算该图幅的日均速度
                daily_points = list(hist_data.daily_completions.values())
                recent_days = daily_points[-7:]  # 最近7天
                if recent_days:
                    mapsheet_speed = sum(recent_days) / len(recent_days)
                    if mapsheet_speed > 0:
                        total_daily_speed += mapsheet_speed
                        active_mapsheets += 1
        
        if total_daily_speed <= 0:
            return {'error': '项目无有效进度数据'}
        
        # 计算整体估算
        remaining_points = max(0, total_target - total_current)
        estimated_days = remaining_points / total_daily_speed if total_daily_speed > 0 else float('inf')
        
        # 预估完成日期
        estimated_completion = datetime.now() + timedelta(days=int(estimated_days))
        
        return {
            'project_summary': {
                'total_current_points': total_current,
                'total_target_points': total_target,
                'remaining_points': remaining_points,
                'overall_completion_percentage': (total_current / total_target * 100) if total_target > 0 else 0
            },
            'performance_metrics': {
                'total_daily_speed': round(total_daily_speed, 2),
                'active_mapsheets': active_mapsheets,
                'avg_speed_per_mapsheet': round(total_daily_speed / active_mapsheets, 2) if active_mapsheets > 0 else 0
            },
            'estimation': {
                'estimated_days_remaining': int(estimated_days),
                'estimated_completion_date': estimated_completion.strftime('%Y-%m-%d'),
                'confidence_level': self._calculate_confidence_level(active_mapsheets)
            }
        }
    
    def _calculate_confidence_level(self, active_mapsheets: int) -> str:
        """计算估算的置信度"""
        if active_mapsheets >= 20:
            return "高"
        elif active_mapsheets >= 10:
            return "中"
        elif active_mapsheets >= 5:
            return "低"
        else:
            return "很低"
    
    def analyze_progress_trend(self, days: int = 30) -> Dict[str, Any]:
        """
        分析进度趋势
        
        Args:
            days: 分析最近多少天的数据
            
        Returns:
            趋势分析结果
        """
        if not self.mapsheet_manager:
            return {'error': '图幅管理器未初始化'}
        
        try:
            # 收集最近N天的数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            daily_totals = {}  # 日期 -> 总点数
            
            for seq, hist_data in self.mapsheet_manager._historical_data.items():
                if not hist_data.daily_completions:
                    continue
                
                for date_str, points in hist_data.daily_completions.items():
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    
                    if start_date <= date_obj <= end_date:
                        if date_str not in daily_totals:
                            daily_totals[date_str] = 0
                        daily_totals[date_str] += points
            
            if not daily_totals:
                return {'error': '指定时间范围内无数据'}
            
            # 分析趋势
            sorted_dates = sorted(daily_totals.keys())
            daily_points = [daily_totals[date] for date in sorted_dates]
            
            # 计算趋势指标
            avg_daily = sum(daily_points) / len(daily_points)
            recent_avg = sum(daily_points[-7:]) / min(7, len(daily_points))  # 最近7天平均
            early_avg = sum(daily_points[:7]) / min(7, len(daily_points))   # 前7天平均
            
            # 趋势判断
            if recent_avg > early_avg * 1.1:
                trend = "上升"
            elif recent_avg < early_avg * 0.9:
                trend = "下降"
            else:
                trend = "稳定"
            
            return {
                'analysis_period': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'total_days': len(daily_points)
                },
                'performance_metrics': {
                    'avg_daily_points': round(avg_daily, 2),
                    'recent_avg_points': round(recent_avg, 2),
                    'early_avg_points': round(early_avg, 2),
                    'trend_direction': trend,
                    'trend_strength': abs(recent_avg - early_avg) / early_avg if early_avg > 0 else 0
                },
                'daily_data': {
                    'dates': sorted_dates,
                    'points': daily_points
                }
            }
            
        except Exception as e:
            logger.error(f"分析进度趋势失败: {e}")
            return {'error': str(e)}
    
    def generate_forecast_report(self) -> str:
        """生成预测报告"""
        try:
            # 获取项目估算
            project_estimation = self.estimate_completion_date()
            if 'error' in project_estimation:
                return f"生成报告失败: {project_estimation['error']}"
            
            # 获取趋势分析
            trend_analysis = self.analyze_progress_trend()
            
            # 生成报告
            report = []
            report.append("=" * 60)
            report.append("项目进度预测报告")
            report.append("=" * 60)
            report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append("")
            
            # 项目概况
            summary = project_estimation['project_summary']
            report.append("项目概况:")
            report.append(f"  当前完成点数: {summary['total_current_points']:,}")
            report.append(f"  目标总点数: {summary['total_target_points']:,}")
            report.append(f"  剩余点数: {summary['remaining_points']:,}")
            report.append(f"  整体完成率: {summary['overall_completion_percentage']:.1f}%")
            report.append("")
            
            # 性能指标
            performance = project_estimation['performance_metrics']
            report.append("性能指标:")
            report.append(f"  日均完成速度: {performance['total_daily_speed']:.1f} 点/天")
            report.append(f"  活跃图幅数量: {performance['active_mapsheets']}")
            report.append(f"  平均每图幅速度: {performance['avg_speed_per_mapsheet']:.1f} 点/天")
            report.append("")
            
            # 完成预测
            estimation = project_estimation['estimation']
            report.append("完成预测:")
            report.append(f"  预计剩余天数: {estimation['estimated_days_remaining']} 天")
            report.append(f"  预计完成日期: {estimation['estimated_completion_date']}")
            report.append(f"  预测置信度: {estimation['confidence_level']}")
            report.append("")
            
            # 趋势分析
            if 'error' not in trend_analysis:
                metrics = trend_analysis['performance_metrics']
                report.append("趋势分析 (最近30天):")
                report.append(f"  平均日完成点数: {metrics['avg_daily_points']:.1f}")
                report.append(f"  最近7天平均: {metrics['recent_avg_points']:.1f}")
                report.append(f"  趋势方向: {metrics['trend_direction']}")
            
            report.append("")
            report.append("=" * 60)
            
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"生成预测报告失败: {e}")
            return f"生成报告失败: {str(e)}"


# 工具函数
def estimate_project_completion() -> Dict[str, Any]:
    """便捷函数：估算项目完成时间"""
    estimator = ProgressEstimator()
    return estimator.estimate_completion_date()


def analyze_recent_progress(days: int = 7) -> Dict[str, Any]:
    """便捷函数：分析最近进度"""
    estimator = ProgressEstimator()
    return estimator.analyze_progress_trend(days)


def generate_quick_report() -> str:
    """便捷函数：生成快速报告"""
    estimator = ProgressEstimator()
    return estimator.generate_forecast_report()
