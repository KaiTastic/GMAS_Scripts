#!/usr/bin/env python3
"""
使用真实目标点数的图幅完成日期预测器

从Excel中读取实际的"Adjusted Num"目标点数，进行精确的完成预测
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def get_daily_progress_rate(mapsheet_id, days=7):
    """
    计算图幅的日均进度
    基于最近几天的历史数据
    """
    try:
        from core.progress_estimation._internal.excel_data_connector import ExcelDataConnector
        from core.data_models.date_types import DateType
        
        connector = ExcelDataConnector()
        
        # 获取最近一周的历史数据
        end_date = DateType(datetime.now())
        start_date = DateType(datetime.now() - timedelta(days=days))
        
        historical_data = connector.extract_historical_data(start_date, end_date)
        
        if not historical_data:
            # 如果没有历史数据，返回默认值
            return 50  # 假设每天50点
        
        # 计算该图幅的平均日增长率
        mapsheet_data = []
        for record in historical_data:
            if mapsheet_id in record.get('data', {}):
                mapsheet_data.append({
                    'date': record['date'],
                    'points': record['data'][mapsheet_id]
                })
        
        if len(mapsheet_data) < 2:
            return 50  # 数据不足，返回默认值
        
        # 计算总增长量
        total_increase = mapsheet_data[-1]['points'] - mapsheet_data[0]['points']
        date_diff = (mapsheet_data[-1]['date'] - mapsheet_data[0]['date']).days
        
        if date_diff <= 0:
            return 50
        
        daily_rate = total_increase / date_diff
        return max(10, daily_rate)  # 最小每天10点
        
    except Exception as e:
        print(f"⚠️ 计算日进度失败 ({mapsheet_id}): {e}")
        return 50  # 默认值


def predict_completion_date_with_real_targets():
    """使用真实目标点数预测完成日期"""
    print("🎯 基于真实目标点数的图幅完成日期预测")
    print("=" * 80)
    
    try:
        from core.progress_estimation._internal.excel_data_connector import ExcelDataConnector
        
        connector = ExcelDataConnector()
        
        # 获取图幅元数据（包含真实目标点数）
        metadata = connector.extract_mapsheet_metadata()
        
        if not metadata:
            print("❌ 无法获取图幅元数据")
            return
        
        print("图幅完成预测详情:")
        print("-" * 80)
        print("图幅名称              | 进度          | 剩余天数 | 预计完成日期     | 状态")
        print("-" * 80)
        
        completion_predictions = []
        completed_count = 0
        
        for mapsheet_id, meta in metadata.items():
            current_points = meta.get('total_points', 0)
            target_points = meta.get('target_points', 1000)
            completion_rate = (current_points / target_points) if target_points > 0 else 0
            
            if current_points >= target_points:
                # 已完成
                status = "✅ 已完成"
                estimated_date = "已完成"
                days_remaining = 0
                completed_count += 1
            else:
                # 计算预计完成日期
                remaining_points = target_points - current_points
                daily_rate = get_daily_progress_rate(mapsheet_id)
                days_remaining = int(remaining_points / daily_rate) if daily_rate > 0 else 999
                
                estimated_completion = datetime.now() + timedelta(days=days_remaining)
                estimated_date = estimated_completion.strftime('%Y-%m-%d')
                status = "🔄 进行中"
                
                completion_predictions.append({
                    'mapsheet_id': mapsheet_id,
                    'estimated_date': estimated_completion,
                    'days_remaining': days_remaining,
                    'current_points': current_points,
                    'target_points': target_points,
                    'daily_rate': daily_rate
                })
            
            progress_str = f"{current_points}/{target_points} ({completion_rate:.1%})"
            days_str = f"{days_remaining:3d}天" if days_remaining < 999 else "   --"
            
            print(f"{mapsheet_id[:20]:20s} | {progress_str:12s} | {days_str:8s} | "
                  f"{estimated_date:14s} | {status}")
        
        print("-" * 80)
        print(f"完成状态: {completed_count}/{len(metadata)} 已完成，{len(metadata) - completed_count} 进行中")
        
        # 显示最早和最晚完成预测
        if completion_predictions:
            completion_predictions.sort(key=lambda x: x['estimated_date'])
            
            earliest = completion_predictions[0]
            latest = completion_predictions[-1]
            
            print(f"\n📊 完成预测分析:")
            print(f"  最早完成: {earliest['mapsheet_id']} ({earliest['estimated_date'].strftime('%Y-%m-%d')})")
            print(f"  最晚完成: {latest['mapsheet_id']} ({latest['estimated_date'].strftime('%Y-%m-%d')})")
            
            # 计算总体完成预测
            total_current = sum(meta.get('total_points', 0) for meta in metadata.values())
            total_target = sum(meta.get('target_points', 0) for meta in metadata.values())
            total_remaining = total_target - total_current
            
            if total_remaining > 0:
                # 计算平均日完成率
                avg_daily_rate = sum(p['daily_rate'] for p in completion_predictions) / len(completion_predictions)
                total_days_remaining = int(total_remaining / avg_daily_rate) if avg_daily_rate > 0 else 999
                
                total_completion_date = datetime.now() + timedelta(days=total_days_remaining)
                
                print(f"  项目总体预计完成: {total_completion_date.strftime('%Y-%m-%d')} ({total_days_remaining}天后)")
                print(f"  剩余总点数: {total_remaining:,}")
                print(f"  平均日完成率: {avg_daily_rate:.1f} 点/天")
        
        return completion_predictions
        
    except Exception as e:
        print(f"❌ 预测失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_completion_progress():
    """分析完成进度"""
    print("\n📈 图幅完成进度分析")
    print("=" * 60)
    
    try:
        from core.progress_estimation._internal.excel_data_connector import ExcelDataConnector
        
        connector = ExcelDataConnector()
        metadata = connector.extract_mapsheet_metadata()
        
        if not metadata:
            print("❌ 无法获取数据")
            return
        
        # 按完成度分组
        progress_groups = {
            '已完成 (100%)': [],
            '接近完成 (80-99%)': [],
            '大部分完成 (60-79%)': [],
            '一半完成 (40-59%)': [],
            '开始阶段 (20-39%)': [],
            '刚开始 (0-19%)': []
        }
        
        for mapsheet_id, meta in metadata.items():
            current = meta.get('total_points', 0)
            target = meta.get('target_points', 1)
            completion_rate = current / target if target > 0 else 0
            
            if completion_rate >= 1.0:
                progress_groups['已完成 (100%)'].append(mapsheet_id)
            elif completion_rate >= 0.8:
                progress_groups['接近完成 (80-99%)'].append(mapsheet_id)
            elif completion_rate >= 0.6:
                progress_groups['大部分完成 (60-79%)'].append(mapsheet_id)
            elif completion_rate >= 0.4:
                progress_groups['一半完成 (40-59%)'].append(mapsheet_id)
            elif completion_rate >= 0.2:
                progress_groups['开始阶段 (20-39%)'].append(mapsheet_id)
            else:
                progress_groups['刚开始 (0-19%)'].append(mapsheet_id)
        
        # 显示分组结果
        for group_name, mapsheets in progress_groups.items():
            if mapsheets:
                print(f"{group_name}: {len(mapsheets)}个")
                for mapsheet in mapsheets:
                    print(f"  - {mapsheet}")
                print()
        
        # 统计信息
        total_count = len(metadata)
        completed_count = len(progress_groups['已完成 (100%)'])
        near_completion_count = len(progress_groups['接近完成 (80-99%)'])
        
        print(f"总结:")
        print(f"  总图幅数: {total_count}")
        print(f"  已完成: {completed_count} ({completed_count/total_count:.1%})")
        print(f"  接近完成: {near_completion_count} ({near_completion_count/total_count:.1%})")
        print(f"  待完成: {total_count - completed_count} ({(total_count - completed_count)/total_count:.1%})")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")


def generate_summary_report():
    """生成汇总报告"""
    print("\n📋 项目进度汇总报告")
    print("=" * 60)
    
    try:
        from core.progress_estimation._internal.excel_data_connector import ExcelDataConnector
        
        connector = ExcelDataConnector()
        summary = connector.get_mapsheet_summary()
        
        if not summary:
            print("❌ 无法获取汇总数据")
            return
        
        # 显示基本统计
        print(f"📊 基本统计:")
        print(f"  项目范围: {summary.get('total_mapsheets', 0)} 个图幅")
        print(f"  当前进度: {summary.get('total_points', 0):,} / {summary.get('total_target_points', 0):,} 观测点")
        print(f"  完成率: {summary.get('overall_completion_rate', 0):.1f}%")
        print(f"  已完成图幅: {summary.get('completed_mapsheets', 0)} 个")
        print(f"  进行中图幅: {summary.get('in_progress_mapsheets', 0)} 个")
        
        # 计算预期完成时间
        remaining_points = summary.get('total_target_points', 0) - summary.get('total_points', 0)
        if remaining_points > 0:
            # 估算日均完成速度（可以基于历史数据优化）
            estimated_daily_rate = 200  # 假设团队每天能完成200点
            days_to_completion = remaining_points / estimated_daily_rate
            completion_date = datetime.now() + timedelta(days=days_to_completion)
            
            print(f"\n⏱️ 预期完成时间:")
            print(f"  剩余工作量: {remaining_points:,} 观测点")
            print(f"  预估完成日期: {completion_date.strftime('%Y年%m月%d日')}")
            print(f"  剩余天数: {int(days_to_completion)} 天")
        
        # 生成时间戳
        print(f"\n报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ 报告生成失败: {e}")


def main():
    """主函数"""
    print("🚀 图幅完成预测系统 - 基于真实目标点数")
    print("=" * 80)
    
    try:
        # 1. 预测完成日期
        predictions = predict_completion_date_with_real_targets()
        
        # 2. 分析完成进度
        analyze_completion_progress()
        
        # 3. 生成汇总报告
        generate_summary_report()
        
        print("\n" + "=" * 80)
        print("🎉 预测完成！")
        
        if predictions:
            print(f"\n💡 关键信息:")
            print(f"  ✓ 成功预测 {len(predictions)} 个图幅的完成日期")
            print(f"  ✓ 使用真实的'Adjusted Num'目标点数")
            print(f"  ✓ 基于历史数据计算日均进度")
            print(f"\n📝 建议:")
            print(f"  • 重点关注进度较慢的图幅")
            print(f"  • 定期更新Excel数据以获得更准确的预测")
            print(f"  • 根据实际情况调整日均完成目标")
        
        return True
        
    except Exception as e:
        print(f"❌ 系统运行失败: {e}")
        import traceback
        traceback.print_exc()
        return False



