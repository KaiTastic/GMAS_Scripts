#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分图幅完成时间预估器

为每个图幅单独分析进度并预估完成时间
"""

import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from statistics import mean, stdev

# 导入项目模块
from core.data_models.date_types import DateType
from .real_excel_data_connector import RealExcelDataConnector

logger = logging.getLogger(__name__)


class MapsheetCompletionEstimator:
    """分图幅完成时间预估器"""
    
    def __init__(self, excel_connector: RealExcelDataConnector = None):
        """
        初始化分图幅完成时间预估器
        
        Args:
            excel_connector: 真实Excel数据连接器，如果为None则创建新实例
        """
        self.excel_connector = excel_connector or RealExcelDataConnector()
        self.mapsheet_data = {}
        self.mapsheet_status = {}
        
    def analyze_all_mapsheets(self, days_back: int = 30) -> Dict[str, Dict]:
        """
        分析所有图幅的完成时间预估
        
        Args:
            days_back: 回溯分析的天数
            
        Returns:
            Dict[str, Dict]: 每个图幅的完成时间预估结果
        """
        logger.info(f"开始分析所有图幅的完成时间预估（回溯{days_back}天）")
        
        # 1. 获取当前状态
        self.mapsheet_status = self.excel_connector.get_mapsheet_current_status()
        if not self.mapsheet_status:
            logger.error("无法获取图幅状态数据")
            return {}
        
        # 2. 获取历史数据
        end_date = DateType(datetime.now())
        start_date = DateType(datetime.now() - timedelta(days=days_back))
        self.mapsheet_data = self.excel_connector.extract_mapsheet_historical_data(start_date, end_date)
        
        if not self.mapsheet_data:
            logger.error("无法获取图幅历史数据")
            return {}
        
        # 3. 为每个图幅计算完成时间预估
        estimation_results = {}
        
        for mapsheet_name in self.mapsheet_status.keys():
            try:
                estimation = self._estimate_mapsheet_completion(mapsheet_name)
                estimation_results[mapsheet_name] = estimation
                
            except Exception as e:
                logger.error(f"预估图幅 {mapsheet_name} 完成时间失败: {e}")
                estimation_results[mapsheet_name] = {
                    'status': 'error',
                    'error_message': str(e)
                }
        
        logger.info(f"完成 {len(estimation_results)} 个图幅的完成时间预估")
        return estimation_results
    
    def _estimate_mapsheet_completion(self, mapsheet_name: str) -> Dict[str, Any]:
        """
        预估单个图幅的完成时间
        
        Args:
            mapsheet_name: 图幅名称
            
        Returns:
            Dict: 完成时间预估结果
        """
        status = self.mapsheet_status.get(mapsheet_name, {})
        historical_data = self.mapsheet_data.get(mapsheet_name, [])
        
        if not status or not historical_data:
            return {
                'status': 'insufficient_data',
                'message': '数据不足，无法进行预估'
            }
        
        current_points = status['current_points']
        target_points = status['estimated_target']
        remaining_points = target_points - current_points
        
        # 如果已完成
        if remaining_points <= 0:
            return {
                'status': 'completed',
                'completion_rate': 100.0,
                'estimated_completion_date': '已完成',
                'remaining_days': 0,
                'confidence': 100.0
            }
        
        # 分析历史趋势
        trend_analysis = self._analyze_completion_trend(historical_data)
        
        # 使用多种方法预估完成时间
        estimates = self._calculate_completion_estimates(
            remaining_points, 
            historical_data, 
            trend_analysis
        )
        
        # 选择最可靠的预估
        best_estimate = self._select_best_estimate(estimates, trend_analysis)
        
        return {
            'status': 'estimated',
            'mapsheet_name': mapsheet_name,
            'current_points': current_points,
            'target_points': target_points,
            'remaining_points': remaining_points,
            'completion_rate': (current_points / target_points * 100) if target_points > 0 else 0,
            'estimated_completion_date': best_estimate['completion_date'],
            'remaining_days': best_estimate['remaining_days'],
            'confidence': best_estimate['confidence'],
            'daily_rate': best_estimate['daily_rate'],
            'trend_analysis': trend_analysis,
            'all_estimates': estimates
        }
    
    def _analyze_completion_trend(self, historical_data: List[Dict]) -> Dict[str, Any]:
        """
        分析完成趋势
        
        Args:
            historical_data: 历史数据
            
        Returns:
            Dict: 趋势分析结果
        """
        if len(historical_data) < 3:
            return {
                'trend': 'insufficient_data',
                'stability': 'unknown',
                'recent_performance': 'unknown'
            }
        
        # 提取有效数据（有点数的日期）
        active_records = [r for r in historical_data if r['daily_points'] > 0]
        
        if len(active_records) < 2:
            return {
                'trend': 'inactive',
                'stability': 'low',
                'recent_performance': 'poor',
                'avg_daily': 0,
                'active_days': 0
            }
        
        daily_points = [r['daily_points'] for r in active_records]
        dates = [r['date_obj'] for r in active_records]
        
        # 计算基本统计
        avg_daily = mean(daily_points)
        std_daily = stdev(daily_points) if len(daily_points) > 1 else 0
        
        # 分析趋势（最近1周 vs 早期数据）
        recent_days = 7
        if len(active_records) > recent_days:
            recent_avg = mean([r['daily_points'] for r in active_records[-recent_days:]])
            early_avg = mean([r['daily_points'] for r in active_records[:-recent_days]])
            
            if recent_avg > early_avg * 1.2:
                trend = 'improving'
            elif recent_avg < early_avg * 0.8:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        # 评估稳定性（基于标准差）
        if std_daily <= avg_daily * 0.3:
            stability = 'high'
        elif std_daily <= avg_daily * 0.6:
            stability = 'medium'
        else:
            stability = 'low'
        
        # 最近表现
        recent_performance = 'good' if len(active_records) >= 3 else 'poor'
        
        return {
            'trend': trend,
            'stability': stability,
            'recent_performance': recent_performance,
            'avg_daily': avg_daily,
            'std_daily': std_daily,
            'active_days': len(active_records),
            'total_days': len(historical_data),
            'activity_rate': len(active_records) / len(historical_data) * 100
        }
    
    def _calculate_completion_estimates(self, remaining_points: int, 
                                      historical_data: List[Dict], 
                                      trend_analysis: Dict) -> Dict[str, Dict]:
        """
        使用多种方法计算完成时间预估
        
        Args:
            remaining_points: 剩余点数
            historical_data: 历史数据
            trend_analysis: 趋势分析结果
            
        Returns:
            Dict: 各种预估方法的结果
        """
        estimates = {}
        
        if trend_analysis['avg_daily'] <= 0:
            # 如果没有有效的日均数据，返回保守估计
            return {
                'conservative': {
                    'daily_rate': 1,
                    'remaining_days': remaining_points,
                    'completion_date': (datetime.now() + timedelta(days=remaining_points)).strftime('%Y-%m-%d'),
                    'confidence': 10.0
                }
            }
        
        # 1. 简单平均法
        simple_daily_rate = trend_analysis['avg_daily']
        simple_days = remaining_points / simple_daily_rate
        estimates['simple_average'] = {
            'daily_rate': simple_daily_rate,
            'remaining_days': simple_days,
            'completion_date': (datetime.now() + timedelta(days=simple_days)).strftime('%Y-%m-%d'),
            'confidence': 60.0 if trend_analysis['stability'] == 'high' else 40.0
        }
        
        # 2. 加权平均法（最近的数据权重更高）
        active_records = [r for r in historical_data if r['daily_points'] > 0]
        if len(active_records) >= 3:
            weights = np.linspace(0.5, 1.5, len(active_records))  # 线性增加的权重
            weighted_avg = np.average([r['daily_points'] for r in active_records], weights=weights)
            weighted_days = remaining_points / weighted_avg
            
            estimates['weighted_average'] = {
                'daily_rate': weighted_avg,
                'remaining_days': weighted_days,
                'completion_date': (datetime.now() + timedelta(days=weighted_days)).strftime('%Y-%m-%d'),
                'confidence': 70.0 if trend_analysis['trend'] == 'improving' else 50.0
            }
        
        # 3. 趋势调整法
        trend_multiplier = 1.0
        if trend_analysis['trend'] == 'improving':
            trend_multiplier = 1.2  # 假设趋势会继续
        elif trend_analysis['trend'] == 'declining':
            trend_multiplier = 0.8  # 假设趋势会继续
        
        trend_daily_rate = simple_daily_rate * trend_multiplier
        trend_days = remaining_points / trend_daily_rate
        
        estimates['trend_adjusted'] = {
            'daily_rate': trend_daily_rate,
            'remaining_days': trend_days,
            'completion_date': (datetime.now() + timedelta(days=trend_days)).strftime('%Y-%m-%d'),
            'confidence': 65.0 if trend_analysis['stability'] == 'high' else 45.0
        }
        
        # 4. 保守估计（考虑工作日）
        # 假设只在工作日工作，每周5天
        workday_rate = simple_daily_rate * 5 / 7  # 调整为工作日速率
        conservative_days = remaining_points / workday_rate if workday_rate > 0 else remaining_points
        
        estimates['conservative'] = {
            'daily_rate': workday_rate,
            'remaining_days': conservative_days,
            'completion_date': (datetime.now() + timedelta(days=conservative_days)).strftime('%Y-%m-%d'),
            'confidence': 80.0  # 保守估计通常置信度较高
        }
        
        return estimates
    
    def _select_best_estimate(self, estimates: Dict[str, Dict], 
                            trend_analysis: Dict) -> Dict[str, Any]:
        """
        选择最可靠的完成时间预估
        
        Args:
            estimates: 各种预估方法的结果
            trend_analysis: 趋势分析结果
            
        Returns:
            Dict: 最佳预估结果
        """
        if not estimates:
            return {
                'daily_rate': 1,
                'remaining_days': 999,
                'completion_date': '无法预估',
                'confidence': 0.0
            }
        
        # 根据数据质量和趋势选择最佳方法
        if trend_analysis['stability'] == 'high' and trend_analysis['trend'] == 'improving':
            # 数据稳定且趋势向好，优先使用加权平均
            preferred_method = 'weighted_average'
        elif trend_analysis['activity_rate'] > 50:
            # 活跃度高，使用趋势调整
            preferred_method = 'trend_adjusted'
        else:
            # 其他情况使用保守估计
            preferred_method = 'conservative'
        
        # 如果首选方法不存在，按优先级选择
        method_priority = ['weighted_average', 'trend_adjusted', 'simple_average', 'conservative']
        
        selected_method = preferred_method if preferred_method in estimates else None
        if not selected_method:
            for method in method_priority:
                if method in estimates:
                    selected_method = method
                    break
        
        if selected_method:
            result = estimates[selected_method].copy()
            result['selected_method'] = selected_method
            return result
        else:
            # 回退选项
            return list(estimates.values())[0]
    
    def generate_mapsheet_completion_report(self, estimation_results: Dict[str, Dict]) -> str:
        """
        生成分图幅完成时间报告
        
        Args:
            estimation_results: 预估结果
            
        Returns:
            str: 格式化的报告文本
        """
        report_lines = []
        report_lines.append("GMAS 分图幅完成时间预估报告")
        report_lines.append("=" * 60)
        report_lines.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"分析图幅数量: {len(estimation_results)}")
        report_lines.append("")
        
        # 按完成率排序
        sorted_results = sorted(
            [(name, result) for name, result in estimation_results.items() 
             if result.get('status') == 'estimated'],
            key=lambda x: x[1].get('completion_rate', 0),
            reverse=True
        )
        
        # 统计信息
        completed_count = sum(1 for result in estimation_results.values() 
                            if result.get('status') == 'completed')
        estimated_count = len(sorted_results)
        error_count = sum(1 for result in estimation_results.values() 
                         if result.get('status') == 'error')
        
        report_lines.append("图幅状态统计:")
        report_lines.append("-" * 30)
        report_lines.append(f"已完成图幅: {completed_count}")
        report_lines.append(f"进行中图幅: {estimated_count}")
        report_lines.append(f"数据错误图幅: {error_count}")
        report_lines.append("")
        
        # 详细的完成时间预估
        report_lines.append("分图幅完成时间预估:")
        report_lines.append("-" * 30)
        
        for mapsheet_name, result in sorted_results:
            completion_rate = result.get('completion_rate', 0)
            est_date = result.get('estimated_completion_date', '未知')
            remaining_days = result.get('remaining_days', 0)
            confidence = result.get('confidence', 0)
            current_points = result.get('current_points', 0)
            target_points = result.get('target_points', 0)
            
            report_lines.append(f"{mapsheet_name}:")
            report_lines.append(f"  完成率: {completion_rate:.1f}% ({current_points}/{target_points})")
            report_lines.append(f"  预估完成: {est_date}")
            report_lines.append(f"  剩余天数: {remaining_days:.1f} 天")
            report_lines.append(f"  置信度: {confidence:.1f}%")
            report_lines.append("")
        
        # 已完成的图幅
        completed_mapsheets = [name for name, result in estimation_results.items() 
                              if result.get('status') == 'completed']
        
        if completed_mapsheets:
            report_lines.append("已完成图幅:")
            report_lines.append("-" * 30)
            for mapsheet in completed_mapsheets:
                report_lines.append(f"✓ {mapsheet}")
            report_lines.append("")
        
        # 数据质量问题
        error_mapsheets = [(name, result) for name, result in estimation_results.items() 
                          if result.get('status') == 'error']
        
        if error_mapsheets:
            report_lines.append("数据质量问题:")
            report_lines.append("-" * 30)
            for mapsheet, result in error_mapsheets:
                error_msg = result.get('error_message', '未知错误')
                report_lines.append(f"⚠ {mapsheet}: {error_msg}")
            report_lines.append("")
        
        # 完成时间排序（最早完成的在前）
        completion_dates = []
        for mapsheet_name, result in sorted_results:
            if result.get('estimated_completion_date') and result.get('estimated_completion_date') != '未知':
                try:
                    date_obj = datetime.strptime(result['estimated_completion_date'], '%Y-%m-%d')
                    completion_dates.append((mapsheet_name, date_obj, result))
                except:
                    continue
        
        completion_dates.sort(key=lambda x: x[1])
        
        if completion_dates:
            report_lines.append("预估完成时间排序:")
            report_lines.append("-" * 30)
            for i, (mapsheet, date_obj, result) in enumerate(completion_dates[:10], 1):
                completion_rate = result.get('completion_rate', 0)
                report_lines.append(f"{i:2d}. {mapsheet}: {date_obj.strftime('%Y-%m-%d')} "
                                  f"(完成率: {completion_rate:.1f}%)")
            
            if len(completion_dates) > 10:
                report_lines.append(f"    ... 还有 {len(completion_dates) - 10} 个图幅")
        
        report_lines.append("")
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
