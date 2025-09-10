#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GMAS 图幅完成日期估算 - 简单运行脚本

快速运行图幅完成日期估算，支持多种估算方法
"""

import os
import sys
from datetime import datetime, timedelta

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

try:
    from core.progress_estimation.mapsheet_estimation_runner import MapsheetEstimationRunner
    from core.data_models.date_types import DateType
    from config.logger_manager import get_logger
    
    def run_quick_estimation():
        """快速运行图幅估算"""
        print("GMAS 图幅完成日期估算工具")
        print("=" * 50)
        
        # 设置日志
        logger = get_logger('quick_estimation')
        
        # 用户选择
        print("\n请选择运行模式:")
        print("1. 快速估算 (使用默认参数)")
        print("2. 自定义参数")
        print("3. 仅分析当前状态")
        
        choice = input("\n请输入选择 (1-3): ").strip()
        
        if choice == "1":
            # 快速模式
            days_back = 30
            confidence_level = 0.8
            print(f"\n使用默认参数: 数据回溯{days_back}天, 置信度{confidence_level:.0%}")
            
        elif choice == "2":
            # 自定义模式
            try:
                days_back = int(input("请输入数据回溯天数 (建议30): ") or "30")
                confidence_str = input("请输入置信度 (0.8): ") or "0.8"
                confidence_level = float(confidence_str)
                
                if not (7 <= days_back <= 365):
                    print("警告: 建议回溯天数在7-365之间")
                if not (0.1 <= confidence_level <= 1.0):
                    print("警告: 置信度应在0.1-1.0之间")
                    confidence_level = 0.8
                    
            except ValueError:
                print("输入无效，使用默认参数")
                days_back = 30
                confidence_level = 0.8
                
        elif choice == "3":
            # 仅分析当前状态
            days_back = 7  # 最少数据
            confidence_level = 0.5
            print("\n分析当前状态模式")
            
        else:
            print("无效选择，使用默认参数")
            days_back = 30
            confidence_level = 0.8
        
        # 设置输出目录
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = os.path.join(current_dir, f'estimation_results_{timestamp}')
        
        print(f"\n开始运行估算...")
        print(f"输出目录: {output_dir}")
        print(f"数据回溯: {days_back} 天")
        print(f"置信度: {confidence_level:.0%}")
        print("-" * 50)
        
        try:
            # 创建运行器
            runner = MapsheetEstimationRunner(output_dir=output_dir)
            
            # 运行估算
            results = runner.run_mapsheet_estimations(
                days_back=days_back,
                confidence_level=confidence_level
            )
            
            if results and 'error' not in results.get('summary_report', {}):
                print_results_summary(results)
                
                # 询问是否打开结果目录
                if input("\n是否打开结果目录? (y/n): ").lower().startswith('y'):
                    try:
                        import subprocess
                        subprocess.Popen(f'explorer "{output_dir}"', shell=True)
                    except:
                        print(f"请手动打开目录: {output_dir}")
                        
            else:
                print("\n估算失败，请检查数据文件和配置")
                
        except Exception as e:
            print(f"\n运行出错: {e}")
            print("请检查:")
            print("1. Excel数据文件是否存在")
            print("2. 文件路径配置是否正确")
            print("3. 数据格式是否符合要求")
        
        input("\n按回车键退出...")
    
    def print_results_summary(results):
        """打印结果摘要"""
        summary = results.get('summary_report', {})
        mapsheet_results = results.get('mapsheet_results', {})
        
        print("\n" + "="*60)
        print("估算完成! 结果摘要:")
        print("="*60)
        
        # 整体统计
        overall = summary.get('overall_statistics', {})
        print(f"处理图幅数量: {summary.get('total_mapsheets', 0)}")
        print(f"总目标点数: {overall.get('total_target_points', 0):,}")
        print(f"总完成点数: {overall.get('total_current_points', 0):,}")
        print(f"整体完成率: {overall.get('overall_completion_rate', 0):.1f}%")
        
        # 状态分布
        categories = summary.get('completion_categories', {})
        print(f"\n完成状态分布:")
        print(f"  已完成 (≥90%): {len(categories.get('completed', []))} 个")
        print(f"  接近完成 (70-89%): {len(categories.get('near_completion', []))} 个")
        print(f"  进行中 (30-69%): {len(categories.get('in_progress', []))} 个")
        print(f"  刚开始 (10-29%): {len(categories.get('starting', []))} 个")
        print(f"  未开始 (<10%): {len(categories.get('not_started', []))} 个")
        
        # 数据质量分布
        quality_stats = summary.get('data_quality_distribution', {})
        print(f"\n数据质量分布:")
        print(f"  优秀: {len(quality_stats.get('excellent', []))} 个")
        print(f"  良好: {len(quality_stats.get('good', []))} 个")
        print(f"  中等: {len(quality_stats.get('medium', []))} 个")
        print(f"  较差: {len(quality_stats.get('poor', []))} 个")
        
        # 显示几个典型图幅的估算结果
        print(f"\n典型图幅估算示例:")
        count = 0
        for sheet_no, result in mapsheet_results.items():
            if count >= 3:  # 最多显示3个
                break
                
            sheet_info = result['sheet_info']
            print(f"\n  图幅 {sheet_no}:")
            print(f"    完成率: {sheet_info['completion_rate']:.1f}%")
            print(f"    当前/目标: {sheet_info['current_points']:,} / {sheet_info['target_points']:,} 点")
            
            # 显示最佳估算结果
            best_estimation = None
            best_confidence = 0
            for estimation in result['estimations'].values():
                if (estimation.get('status') != 'fallback' and 
                    estimation.get('confidence', 0) > best_confidence):
                    best_estimation = estimation
                    best_confidence = estimation.get('confidence', 0)
            
            if best_estimation:
                est_date = best_estimation.get('estimated_date')
                
                # 检查是否已完成
                if sheet_info['completion_rate'] >= 100:
                    print(f"    状态: 已完成")
                    print(f"    预计完成: -")
                else:
                    if hasattr(est_date, 'strftime'):
                        est_date_str = est_date.strftime('%Y-%m-%d')
                    elif est_date == "-":
                        est_date_str = "-"
                    else:
                        est_date_str = str(est_date)
                        
                    print(f"    预计完成: {est_date_str}")
                
                print(f"    估算方法: {best_estimation.get('method_name', '未知')}")
                print(f"    置信度: {best_confidence:.0%}")
            
            count += 1
        
        print(f"\n详细结果和图表请查看输出目录中的文件")
    
    if __name__ == "__main__":
        run_quick_estimation()
        
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保在正确的项目目录中运行此脚本")
    input("按回车键退出...")
except Exception as e:
    print(f"运行出错: {e}")
    input("按回车键退出...")
