#!/usr/bin/env python3
"""
进度预测功能演示
展示如何使用CurrentDateFiles类的进度估算功能
"""

import sys
from datetime import datetime

# 添加项目路径
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_progress_estimation():
    """演示进度估算功能"""
    print("=" * 60)
    print("🚀 GMAS项目进度估算功能演示")
    print("=" * 60)
    
    try:
        # 导入必要的模块
        from core.mapsheet.current_date_files import CurrentDateFiles
        from core.data_models.date_types import DateType
        
        # 创建当前日期的数据集合
        current_date = DateType(date_datetime=datetime.now())
        current_files = CurrentDateFiles(current_date)
        
        print(f"📅 分析日期: {current_date}")
        print(f"📊 图幅数量: {len(current_files.currentDateFiles)}")
        print(f"📈 累计完成点数: {current_files.totalPointNum:,}")
        print(f"📋 今日新增点数: {current_files.totalDaiyIncreasePointNum:,}")
        
        # 显示图幅目标配置
        print(f"\n📋 图幅目标配置:")
        targets = current_files.mapsheet_targets
        total_target = sum(targets.values())
        print(f"  总目标点数: {total_target:,}")
        print(f"  平均每图幅: {total_target // len(targets):,} 点")
        
        # 执行进度估算
        print(f"\n🔍 执行进度估算...")
        results = current_files.estimate_progress(confidence_level=0.8)
        
        if "error" in results:
            print(f"❌ 估算失败: {results['error']}")
            return
        
        # 显示整体进度
        overall = results.get("overall", {}).get("basic_estimation", {})
        completion = overall.get('completion_percentage', 0)
        print(f"\n📊 整体项目进度:")
        print(f"  完成度: {completion:.1f}%")
        
        finish_date = overall.get('estimated_finish_date')
        if finish_date:
            print(f"  预计完成: {finish_date.strftime('%Y年%m月%d日')}")
        
        days_remaining = overall.get('days_remaining', 0)
        print(f"  剩余天数: {days_remaining} 天")
        
        daily_target = overall.get('daily_target', 0)
        print(f"  建议日产: {daily_target:.0f} 点/天")
        
        # 显示状态分布
        statuses = results.get("summary", {}).get("completion_statuses", {})
        print(f"\n📈 图幅状态分布:")
        print(f"  ⚪ 未开始: {statuses.get('not_started', 0)} 个")
        print(f"  🔵 初期 (0-25%): {statuses.get('early_stage', 0)} 个")
        print(f"  🟡 进行中 (25-75%): {statuses.get('in_progress', 0)} 个")
        print(f"  🟠 后期 (75-95%): {statuses.get('advanced', 0)} 个")
        print(f"  🟢 接近完成 (95-99%): {statuses.get('near_complete', 0)} 个")
        print(f"  ✅ 已完成: {statuses.get('completed', 0)} 个")
        
        # 使用屏幕显示功能
        print(f"\n💡 您也可以通过以下方式查看详细进度:")
        print(f"  1. current_files.display_progress_estimation()")
        print(f"  2. current_files.onScreenDisplay() # 包含进度估算选项")
        print(f"  3. current_files.dailyExcelReport() # 自动添加到Excel报告")
        
        print(f"\n✅ 进度估算演示完成！")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demo_progress_estimation()
