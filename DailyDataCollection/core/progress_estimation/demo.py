#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GMAS 图幅估算演示脚本

展示如何程序化使用图幅完成日期估算功能
"""

import os
import sys
from datetime import datetime, timedelta

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

def demo_basic_usage():
    """演示基本使用方法"""
    print("=== GMAS 图幅估算演示 ===\n")
    
    try:
        from core.progress_estimation import MapsheetEstimationRunner
        from core.data_models.date_types import DateType
        
        # 1. 创建估算运行器
        print("1. 创建图幅估算运行器...")
        output_dir = os.path.join(current_dir, 'demo_results')
        runner = MapsheetEstimationRunner(output_dir=output_dir)
        print(f"   输出目录: {output_dir}")
        
        # 2. 运行估算
        print("\n2. 开始运行估算...")
        results = runner.run_mapsheet_estimations(
            days_back=30,        # 使用最近30天数据
            confidence_level=0.8  # 80%置信度
        )
        
        # 3. 处理结果
        if results and 'error' not in results.get('summary_report', {}):
            print("✓ 估算完成!")
            
            # 显示汇总信息
            summary = results['summary_report']
            overall = summary.get('overall_statistics', {})
            
            print(f"\n=== 汇总结果 ===")
            print(f"处理图幅数量: {summary.get('total_mapsheets', 0)}")
            print(f"整体完成率: {overall.get('overall_completion_rate', 0):.1f}%")
            
            # 显示分类统计
            categories = summary.get('completion_categories', {})
            print(f"\n完成状态分布:")
            print(f"  已完成: {len(categories.get('completed', []))} 个")
            print(f"  接近完成: {len(categories.get('near_completion', []))} 个")
            print(f"  进行中: {len(categories.get('in_progress', []))} 个")
            print(f"  刚开始: {len(categories.get('starting', []))} 个")
            print(f"  未开始: {len(categories.get('not_started', []))} 个")
            
            # 显示方法可靠性
            print(f"\n估算方法可靠性:")
            method_reliability = summary.get('method_reliability', {})
            for method, stats in method_reliability.items():
                success_rate = stats.get('success_rate', 0) * 100
                avg_confidence = stats.get('avg_confidence', 0) * 100
                print(f"  {method}: 成功率 {success_rate:.0f}%, 平均置信度 {avg_confidence:.0f}%")
            
            return results
            
        else:
            print("✗ 估算失败")
            error_msg = results.get('summary_report', {}).get('error', '未知错误')
            print(f"错误信息: {error_msg}")
            return None
            
    except ImportError as e:
        print(f"导入模块失败: {e}")
        print("请确保在正确的项目目录中运行")
        return None
    except Exception as e:
        print(f"运行出错: {e}")
        return None

def demo_detailed_analysis(results):
    """演示详细分析结果"""
    if not results:
        return
    
    print(f"\n=== 详细分析演示 ===")
    
    mapsheet_results = results.get('mapsheet_results', {})
    if not mapsheet_results:
        print("无详细结果可分析")
        return
    
    # 选择几个代表性图幅进行详细分析
    sample_count = min(3, len(mapsheet_results))
    sample_mapsheets = list(mapsheet_results.items())[:sample_count]
    
    for sheet_no, result in sample_mapsheets:
        print(f"\n--- 图幅 {sheet_no} 详细分析 ---")
        
        # 基本信息
        sheet_info = result['sheet_info']
        print(f"完成进度: {sheet_info['current_points']:,} / {sheet_info['target_points']:,} 点")
        print(f"完成率: {sheet_info['completion_rate']:.1f}%")
        print(f"日均速度: {sheet_info['avg_daily_points']:.1f} 点/天")
        
        # 数据质量
        data_quality = result['data_quality']
        print(f"数据质量: {data_quality['quality']} - {data_quality['reason']}")
        
        # 估算结果对比
        print(f"各方法估算结果:")
        estimations = result['estimations']
        for method, estimation in estimations.items():
            if estimation.get('status') != 'fallback':
                method_name = estimation.get('method_name', method)
                est_date = estimation.get('estimated_date')
                if hasattr(est_date, 'strftime'):
                    date_str = est_date.strftime('%Y-%m-%d')
                else:
                    date_str = str(est_date)
                
                confidence = estimation.get('confidence', 0) * 100
                days_remaining = estimation.get('days_remaining', 0)
                
                print(f"  {method_name}: {date_str} (剩余{days_remaining:.0f}天, 置信度{confidence:.0f}%)")
        
        # 建议
        recommendations = result.get('recommendations', [])
        if recommendations:
            print(f"系统建议:")
            for rec in recommendations:
                print(f"  • {rec}")

def demo_custom_parameters():
    """演示自定义参数的使用"""
    print(f"\n=== 自定义参数演示 ===")
    
    try:
        from core.progress_estimation import MapsheetEstimationRunner
        from core.data_models.date_types import DateType
        
        # 创建自定义配置的运行器
        custom_output = os.path.join(current_dir, 'custom_demo_results')
        runner = MapsheetEstimationRunner(output_dir=custom_output)
        
        # 使用自定义参数
        print("使用自定义参数运行估算...")
        print("- 数据回溯期: 21天")
        print("- 置信度: 90%")
        
        results = runner.run_mapsheet_estimations(
            days_back=21,         # 较短的回溯期
            confidence_level=0.9  # 更高的置信度要求
        )
        
        if results and 'error' not in results.get('summary_report', {}):
            print("✓ 自定义参数估算完成!")
            summary = results['summary_report']
            print(f"处理图幅: {summary.get('total_mapsheets', 0)} 个")
            return results
        else:
            print("✗ 自定义参数估算失败")
            return None
            
    except Exception as e:
        print(f"自定义参数演示出错: {e}")
        return None

def main():
    """主演示函数"""
    print("GMAS 图幅完成日期估算 - 功能演示")
    print("=" * 50)
    
    # 基本使用演示
    results = demo_basic_usage()
    
    # 详细分析演示
    if results:
        demo_detailed_analysis(results)
    
    # 自定义参数演示
    custom_results = demo_custom_parameters()
    
    print(f"\n=== 演示完成 ===")
    print("生成的文件:")
    print("1. demo_results/ - 基本演示结果")
    print("2. custom_demo_results/ - 自定义参数演示结果")
    print("\n查看生成的报告文件以获取详细信息。")

if __name__ == "__main__":
    main()
