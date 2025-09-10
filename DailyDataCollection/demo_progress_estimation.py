#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GMAS 进度估算模块演示脚本

演示如何使用新的进度估算功能
"""

import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.progress_estimation import ProgressTracker
from core.data_models.date_types import DateType


def demo_progress_estimation():
    """演示进度估算功能"""
    print("GMAS 进度估算模块演示")
    print("=" * 50)
    
    try:
        # 1. 创建进度跟踪器
        print("\n1. 初始化进度跟踪器...")
        workspace_path = os.path.join(os.getcwd(), 'demo_workspace')
        tracker = ProgressTracker(workspace_path)
        print("✓ 进度跟踪器创建成功")
        
        # 2. 设置项目参数
        print("\n2. 设置项目参数...")
        target_points = 2000  # 目标总点数
        current_points = 650  # 当前已完成点数
        start_date = DateType(datetime.now() - timedelta(days=45))
        target_date = DateType(datetime.now() + timedelta(days=30))
        
        success = tracker.initialize_project(
            target_points=target_points,
            current_points=current_points,
            start_date=start_date,
            target_date=target_date
        )
        
        if success:
            print(f"✓ 项目初始化成功: {current_points}/{target_points} 点")
        
        # 3. 加载历史数据（使用模拟数据）
        print("\n3. 加载历史数据...")
        data_start = DateType(datetime.now() - timedelta(days=21))
        success = tracker.load_historical_data(start_date=data_start)
        
        if success:
            print("✓ 历史数据加载成功")
        else:
            print("⚠ 历史数据加载失败，将使用模拟数据")
        
        # 4. 获取进度摘要
        print("\n4. 获取进度摘要...")
        summary = tracker.get_current_progress_summary()
        
        if 'error' not in summary:
            print("✓ 进度摘要获取成功")
            
            # 显示关键信息
            project_info = summary.get('project_info', {})
            print(f"   - 目标点数: {project_info.get('target_points')}")
            print(f"   - 当前点数: {project_info.get('current_points')}")
            
            if 'completion_percentage' in summary:
                print(f"   - 完成率: {summary['completion_percentage']:.1f}%")
            
            # 显示完成日期预估
            if 'finish_estimate' in summary:
                estimate = summary['finish_estimate']
                if estimate.get('estimated_date'):
                    est_date = estimate['estimated_date']
                    if hasattr(est_date, 'strftime'):
                        print(f"   - 预估完成日期: {est_date.strftime('%Y-%m-%d')}")
                    print(f"   - 剩余天数: {estimate.get('days_remaining', 0):.1f}")
                    print(f"   - 置信度: {estimate.get('confidence', 0)*100:.1f}%")
        
        # 5. 计算每日目标
        print("\n5. 计算每日目标...")
        daily_target = tracker.get_daily_target()
        
        if 'error' not in daily_target:
            print("✓ 每日目标计算成功")
            print(f"   - 每日需完成: {daily_target.get('daily_target', 0):.1f} 点")
            print(f"   - 剩余天数: {daily_target.get('remaining_days', 0)} 天")
            print(f"   - 可行性评估: {daily_target.get('feasibility', 'unknown')}")
        
        # 6. 生成进度报告
        print("\n6. 生成进度报告...")
        
        # 生成不包含图表的报告（避免GUI环境问题）
        report = tracker.generate_progress_report(
            include_charts=False,
            chart_types=[]
        )
        
        if 'error' not in report:
            print("✓ 进度报告生成成功")
            
            # 显示建议
            recommendations = report.get('recommendations', [])
            if recommendations:
                print("\n   项目建议:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"   {i}. {rec}")
            
            # 显示报告文件路径
            if 'summary_file' in report:
                print(f"\n   报告文件: {report['summary_file']}")
        
        # 7. 尝试生成图表（如果环境支持）
        print("\n7. 尝试生成图表...")
        try:
            chart_report = tracker.generate_progress_report(
                include_charts=True,
                chart_types=['dashboard']  # 只生成仪表板
            )
            
            charts = chart_report.get('charts', {})
            if charts:
                print("✓ 图表生成成功")
                for chart_type, path in charts.items():
                    print(f"   - {chart_type}: {path}")
            else:
                print("⚠ 图表生成失败或跳过")
                
        except Exception as e:
            print(f"⚠ 图表生成失败: {e}")
        
        print("\n演示完成！")
        print("=" * 50)
        
    except Exception as e:
        print(f"✗ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demo_progress_estimation()