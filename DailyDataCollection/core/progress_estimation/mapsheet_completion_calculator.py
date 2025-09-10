#!/usr/bin/env python3
"""
图幅完成日期计算器

基于实际Excel数据计算每个图幅的预计完成日期
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import re

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def load_and_analyze_excel_data():
    """加载并分析Excel数据"""
    print("=== 加载并分析Excel数据 ===")
    
    from core.progress_estimation._internal.excel_data_connector import ExcelDataConnector
    
    connector = ExcelDataConnector()
    success = connector.load_excel_data()
    
    if not success or connector.excel_data is None:
        print("❌ Excel数据加载失败")
        return None, None
    
    data = connector.excel_data
    print(f"✅ 数据加载成功: {data.shape[0]}行 x {data.shape[1]}列")
    
    # 分析列结构
    print(f"\n列结构分析:")
    date_columns = []
    team_info_columns = []
    
    for i, col in enumerate(data.columns):
        col_str = str(col)
        print(f"  {i:2d}: {col_str[:50]}")
        
        # 识别日期列（包含日期格式的列）
        if '2025-' in col_str or '2024-' in col_str:
            try:
                # 尝试解析为日期
                date_obj = pd.to_datetime(col_str)
                date_columns.append((i, col_str, date_obj))
            except:
                pass
        
        # 识别团队信息列
        if any(keyword in col_str.lower() for keyword in ['team', 'sheet', 'person', 'total']):
            team_info_columns.append((i, col_str))
    
    print(f"\n发现 {len(date_columns)} 个日期列:")
    for i, (col_idx, col_name, date_obj) in enumerate(date_columns[:10]):
        print(f"  {i+1:2d}: {date_obj.strftime('%Y-%m-%d')} (列{col_idx})")
    
    print(f"\n发现 {len(team_info_columns)} 个信息列:")
    for i, (col_idx, col_name) in enumerate(team_info_columns):
        print(f"  {i+1:2d}: {col_name} (列{col_idx})")
    
    return data, {'date_columns': date_columns, 'team_info_columns': team_info_columns}


def extract_mapsheet_data(data, analysis_info):
    """提取图幅数据"""
    print("\n=== 提取图幅数据 ===")
    
    date_columns = analysis_info['date_columns']
    team_info_columns = analysis_info['team_info_columns']
    
    if not date_columns:
        print("❌ 未找到日期列")
        return None
    
    # 构建图幅数据结构
    mapsheet_data = {}
    
    # 获取图幅信息（从团队列或图幅名称列）
    sheet_name_col = None
    team_col = None
    
    for col_idx, col_name in team_info_columns:
        if 'sheet' in col_name.lower() and 'name' in col_name.lower():
            sheet_name_col = col_idx
        elif 'team' in col_name.lower():
            team_col = col_idx
    
    # 处理每一行数据（每行代表一个图幅/团队）
    for row_idx in range(len(data)):
        # 获取图幅标识
        mapsheet_id = None
        
        if sheet_name_col is not None:
            sheet_name = data.iloc[row_idx, sheet_name_col]
            if pd.notna(sheet_name):
                mapsheet_id = str(sheet_name).strip()
        
        if not mapsheet_id and team_col is not None:
            team_name = data.iloc[row_idx, team_col]
            if pd.notna(team_name):
                mapsheet_id = str(team_name).strip()
        
        if not mapsheet_id:
            mapsheet_id = f"Row_{row_idx}"
        
        # 提取该图幅的日期-观测点数据
        daily_data = []
        for col_idx, col_name, date_obj in date_columns:
            points_value = data.iloc[row_idx, col_idx]
            
            if pd.notna(points_value):
                try:
                    points = float(points_value)
                    if points > 0:  # 只记录有效观测点
                        daily_data.append({
                            'date': date_obj.date(),
                            'points': int(points)
                        })
                except (ValueError, TypeError):
                    continue
        
        if daily_data:
            # 按日期排序
            daily_data.sort(key=lambda x: x['date'])
            mapsheet_data[mapsheet_id] = daily_data
    
    print(f"✅ 提取了 {len(mapsheet_data)} 个图幅的数据:")
    for mapsheet_id, daily_data in mapsheet_data.items():
        if daily_data:
            total_points = sum(d['points'] for d in daily_data)
            date_range = f"{daily_data[0]['date']} - {daily_data[-1]['date']}"
            print(f"  {mapsheet_id[:20]:20s}: {total_points:4d} 点, {len(daily_data):2d} 天, {date_range}")
    
    return mapsheet_data


def calculate_completion_predictions(mapsheet_data, target_points_per_mapsheet=1000):
    """计算完成预测"""
    print(f"\n=== 计算完成预测 (目标: {target_points_per_mapsheet} 点/图幅) ===")
    
    predictions = {}
    
    for mapsheet_id, daily_data in mapsheet_data.items():
        if not daily_data:
            continue
        
        # 计算当前统计
        total_points = sum(d['points'] for d in daily_data)
        total_days = len(daily_data)
        avg_daily = total_points / total_days if total_days > 0 else 0
        
        # 计算最近趋势（最近7天或一半数据）
        recent_days = min(7, len(daily_data) // 2, len(daily_data))
        if recent_days > 0:
            recent_data = daily_data[-recent_days:]
            recent_avg = sum(d['points'] for d in recent_data) / len(recent_data)
        else:
            recent_avg = avg_daily
        
        # 计算趋势变化
        if total_days >= 4:
            first_half = daily_data[:len(daily_data)//2]
            second_half = daily_data[len(daily_data)//2:]
            
            first_avg = sum(d['points'] for d in first_half) / len(first_half) if first_half else 0
            second_avg = sum(d['points'] for d in second_half) / len(second_half) if second_half else 0
            
            trend = (second_avg - first_avg) / first_avg if first_avg > 0 else 0
        else:
            trend = 0
        
        # 完成度和剩余工作
        completion_rate = total_points / target_points_per_mapsheet
        remaining_points = max(0, target_points_per_mapsheet - total_points)
        
        # 预测完成日期（使用多种方法）
        last_date = daily_data[-1]['date']
        predictions_methods = {}
        
        # 方法1: 基于总体平均速度
        if avg_daily > 0 and remaining_points > 0:
            days_needed = remaining_points / avg_daily
            finish_date = last_date + timedelta(days=days_needed)
            predictions_methods['avg_method'] = {
                'days_needed': days_needed,
                'finish_date': finish_date,
                'daily_rate': avg_daily
            }
        
        # 方法2: 基于最近趋势
        if recent_avg > 0 and remaining_points > 0:
            days_needed = remaining_points / recent_avg
            finish_date = last_date + timedelta(days=days_needed)
            predictions_methods['recent_method'] = {
                'days_needed': days_needed,
                'finish_date': finish_date,
                'daily_rate': recent_avg
            }
        
        # 方法3: 考虑趋势的预测
        if recent_avg > 0 and remaining_points > 0:
            # 假设趋势会继续，但有上限
            trend_adjusted_rate = recent_avg * (1 + min(trend, 0.5))  # 限制趋势影响
            trend_adjusted_rate = max(trend_adjusted_rate, recent_avg * 0.5)  # 设置下限
            
            days_needed = remaining_points / trend_adjusted_rate
            finish_date = last_date + timedelta(days=days_needed)
            predictions_methods['trend_method'] = {
                'days_needed': days_needed,
                'finish_date': finish_date,
                'daily_rate': trend_adjusted_rate,
                'trend': trend
            }
        
        # 选择最佳预测（通常使用最近趋势，但要合理性检查）
        best_prediction = None
        if 'recent_method' in predictions_methods:
            best_prediction = predictions_methods['recent_method']
        elif 'avg_method' in predictions_methods:
            best_prediction = predictions_methods['avg_method']
        elif 'trend_method' in predictions_methods:
            best_prediction = predictions_methods['trend_method']
        
        predictions[mapsheet_id] = {
            'current_points': total_points,
            'target_points': target_points_per_mapsheet,
            'completion_rate': completion_rate,
            'remaining_points': remaining_points,
            'total_days': total_days,
            'avg_daily': avg_daily,
            'recent_avg': recent_avg,
            'trend': trend,
            'last_date': last_date,
            'predictions': predictions_methods,
            'best_prediction': best_prediction,
            'status': 'completed' if completion_rate >= 1.0 else 'in_progress'
        }
    
    return predictions


def display_predictions(predictions):
    """显示预测结果"""
    print("\n=== 图幅完成日期预测结果 ===")
    
    # 按完成度排序
    sorted_predictions = sorted(predictions.items(), 
                               key=lambda x: x[1]['completion_rate'], 
                               reverse=True)
    
    print("图幅标识              | 当前点数 | 完成度 | 平均速度 | 最近速度 | 预计完成日期 | 还需天数")
    print("-" * 95)
    
    for mapsheet_id, pred in sorted_predictions:
        current = pred['current_points']
        target = pred['target_points']
        completion = pred['completion_rate'] * 100
        avg_speed = pred['avg_daily']
        recent_speed = pred['recent_avg']
        
        if pred['status'] == 'completed':
            finish_info = "已完成"
            days_info = "   -"
        elif pred['best_prediction']:
            finish_date = pred['best_prediction']['finish_date']
            days_needed = pred['best_prediction']['days_needed']
            finish_info = finish_date.strftime('%Y-%m-%d')
            days_info = f"{days_needed:5.1f}"
        else:
            finish_info = "无法预测"
            days_info = "   -"
        
        print(f"{mapsheet_id[:20]:20s} | {current:8d} | {completion:5.1f}% | "
              f"{avg_speed:6.1f}   | {recent_speed:6.1f}   | {finish_info:12s} | {days_info}")


def generate_detailed_report(predictions):
    """生成详细报告"""
    print("\n=== 详细分析报告 ===")
    
    # 总体统计
    total_mapsheets = len(predictions)
    completed_mapsheets = sum(1 for p in predictions.values() if p['status'] == 'completed')
    in_progress_mapsheets = total_mapsheets - completed_mapsheets
    
    total_points = sum(p['current_points'] for p in predictions.values())
    total_target = sum(p['target_points'] for p in predictions.values())
    overall_completion = total_points / total_target if total_target > 0 else 0
    
    print(f"1. 总体概况:")
    print(f"   图幅总数: {total_mapsheets}")
    print(f"   已完成: {completed_mapsheets} ({completed_mapsheets/total_mapsheets*100:.1f}%)")
    print(f"   进行中: {in_progress_mapsheets}")
    print(f"   总观测点: {total_points:,}")
    print(f"   目标点数: {total_target:,}")
    print(f"   总体完成度: {overall_completion:.1%}")
    
    # 完成时间分析
    if in_progress_mapsheets > 0:
        valid_predictions = [p for p in predictions.values() 
                           if p['status'] == 'in_progress' and p['best_prediction']]
        
        if valid_predictions:
            finish_dates = [p['best_prediction']['finish_date'] for p in valid_predictions]
            earliest_finish = min(finish_dates)
            latest_finish = max(finish_dates)
            
            print(f"\n2. 完成时间预测:")
            print(f"   最早完成: {earliest_finish.strftime('%Y年%m月%d日')}")
            print(f"   最晚完成: {latest_finish.strftime('%Y年%m月%d日')}")
            print(f"   预测跨度: {(latest_finish - earliest_finish).days} 天")
            
            # 按月份统计预期完成的图幅数量
            monthly_completions = {}
            for date in finish_dates:
                month_key = date.strftime('%Y-%m')
                monthly_completions[month_key] = monthly_completions.get(month_key, 0) + 1
            
            print(f"\n3. 月度完成预测:")
            for month, count in sorted(monthly_completions.items()):
                print(f"   {month}: {count} 个图幅")
    
    # 效率分析
    speeds = [p['recent_avg'] for p in predictions.values() if p['status'] == 'in_progress']
    if speeds:
        avg_speed = np.mean(speeds)
        std_speed = np.std(speeds)
        
        print(f"\n4. 效率分析:")
        print(f"   平均观测速度: {avg_speed:.1f} 点/天")
        print(f"   速度标准差: {std_speed:.1f}")
        
        # 识别高效和低效图幅
        high_performers = [mapsheet_id for mapsheet_id, p in predictions.items() 
                          if p['status'] == 'in_progress' and p['recent_avg'] > avg_speed + std_speed]
        low_performers = [mapsheet_id for mapsheet_id, p in predictions.items() 
                         if p['status'] == 'in_progress' and p['recent_avg'] < avg_speed - std_speed]
        
        if high_performers:
            print(f"   高效图幅 ({len(high_performers)}个): {', '.join(high_performers)}")
        if low_performers:
            print(f"   需关注图幅 ({len(low_performers)}个): {', '.join(low_performers)}")


def save_results_to_excel(predictions, output_file="mapsheet_completion_predictions.xlsx"):
    """保存结果到Excel文件"""
    print(f"\n=== 保存结果到 {output_file} ===")
    
    try:
        # 准备数据
        results_data = []
        
        for mapsheet_id, pred in predictions.items():
            row = {
                '图幅标识': mapsheet_id,
                '当前观测点数': pred['current_points'],
                '目标点数': pred['target_points'],
                '完成度(%)': pred['completion_rate'] * 100,
                '剩余点数': pred['remaining_points'],
                '观测天数': pred['total_days'],
                '平均日观测点': pred['avg_daily'],
                '最近日观测点': pred['recent_avg'],
                '趋势(%)': pred['trend'] * 100,
                '最后观测日期': pred['last_date'].strftime('%Y-%m-%d'),
                '状态': '已完成' if pred['status'] == 'completed' else '进行中'
            }
            
            if pred['best_prediction']:
                row['预计完成日期'] = pred['best_prediction']['finish_date'].strftime('%Y-%m-%d')
                row['预计还需天数'] = pred['best_prediction']['days_needed']
                row['预测日观测率'] = pred['best_prediction']['daily_rate']
            else:
                row['预计完成日期'] = '已完成' if pred['status'] == 'completed' else '无法预测'
                row['预计还需天数'] = 0 if pred['status'] == 'completed' else None
                row['预测日观测率'] = None
            
            results_data.append(row)
        
        # 创建DataFrame并保存
        df = pd.DataFrame(results_data)
        
        # 按完成度排序
        df = df.sort_values('完成度(%)', ascending=False)
        
        # 保存到Excel
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='图幅完成预测', index=False)
        
        print(f"✅ 结果已保存到 {output_file}")
        print(f"   包含 {len(results_data)} 个图幅的详细预测信息")
        
    except Exception as e:
        print(f"❌ 保存失败: {e}")


def main():
    """主函数"""
    print("=" * 70)
    print("           GMAS 图幅完成日期计算器")
    print("=" * 70)
    
    try:
        # 1. 加载和分析Excel数据
        data, analysis_info = load_and_analyze_excel_data()
        
        if data is None:
            print("❌ 无法加载数据，程序终止")
            return False
        
        # 2. 提取图幅数据
        mapsheet_data = extract_mapsheet_data(data, analysis_info)
        
        if not mapsheet_data:
            print("❌ 无法提取图幅数据，程序终止")
            return False
        
        # 3. 计算完成预测
        print("\n请输入目标参数:")
        try:
            target_input = input("每个图幅目标观测点数 (默认1000): ").strip()
            target_points = int(target_input) if target_input else 1000
        except ValueError:
            target_points = 1000
            print(f"使用默认值: {target_points}")
        
        predictions = calculate_completion_predictions(mapsheet_data, target_points)
        
        # 4. 显示结果
        display_predictions(predictions)
        
        # 5. 生成详细报告
        generate_detailed_report(predictions)
        
        # 6. 询问是否保存结果
        while True:
            save_choice = input("\n是否保存结果到Excel文件? (y/n): ").lower().strip()
            if save_choice in ['y', 'yes', '是']:
                save_results_to_excel(predictions)
                break
            elif save_choice in ['n', 'no', '否']:
                print("跳过保存")
                break
            else:
                print("请输入 y 或 n")
        
        print("\n" + "=" * 70)
        print("           计算完成")
        print("=" * 70)
        print("\n🎯 关键发现:")
        
        completed = sum(1 for p in predictions.values() if p['status'] == 'completed')
        in_progress = len(predictions) - completed
        
        print(f"📊 {len(predictions)} 个图幅中，{completed} 个已完成，{in_progress} 个进行中")
        
        if in_progress > 0:
            valid_preds = [p for p in predictions.values() 
                          if p['status'] == 'in_progress' and p['best_prediction']]
            if valid_preds:
                finish_dates = [p['best_prediction']['finish_date'] for p in valid_preds]
                latest_finish = max(finish_dates)
                print(f"⏰ 预计全部完成时间: {latest_finish.strftime('%Y年%m月%d日')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()
        return False



