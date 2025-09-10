#!/usr/bin/env python3
"""
测试进度估算功能与CurrentDateFiles的集成
"""

import sys
import logging
from datetime import datetime

# 添加项目路径到sys.path
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_mapsheet_manager():
    """测试图幅管理器的目标点数功能"""
    try:
        from core.mapsheet.mapsheet_manager import mapsheet_manager
        
        print("=== 测试图幅管理器 ===")
        
        # 测试获取图幅信息
        summary = mapsheet_manager.get_summary()
        print(f"图幅总数: {summary['total_mapsheets']}")
        print(f"序号范围: {summary['sequence_range']}")
        print(f"团队范围: {summary['team_range']}")
        
        # 测试获取目标点数（使用一个示例图幅）
        if mapsheet_manager.maps_info:
            first_mapsheet_info = list(mapsheet_manager.maps_info.values())[0]
            roman_name = first_mapsheet_info.get('Roman Name')
            if roman_name:
                target = mapsheet_manager.get_mapsheet_target(roman_name)
                print(f"图幅 {roman_name} 的目标点数: {target}")
            
        return True
        
    except Exception as e:
        print(f"图幅管理器测试失败: {e}")
        return False

def test_progress_estimation_module():
    """测试进度估算模块"""
    try:
        from core.progress_estimation import quick_estimate, advanced_estimate
        
        print("\n=== 测试进度估算模块 ===")
        
        # 测试快速估算
        quick_result = quick_estimate(target_points=5000, current_points=1500)
        print("快速估算结果:")
        print(f"  完成度: {quick_result.get('completion_percentage', 0):.1f}%")
        print(f"  预计完成日期: {quick_result.get('estimated_finish_date')}")
        
        # 测试高级估算
        advanced_result = advanced_estimate(target_points=5000, current_points=1500, confidence_level=0.8)
        print("高级估算结果:")
        print(f"  完成度: {advanced_result.get('basic_estimation', {}).get('completion_percentage', 0):.1f}%")
        
        return True
        
    except Exception as e:
        print(f"进度估算模块测试失败: {e}")
        return False

def test_current_date_files_integration():
    """测试CurrentDateFiles的进度估算集成"""
    try:
        from core.mapsheet.current_date_files import CurrentDateFiles
        from core.data_models.date_types import DateType
        from datetime import datetime
        
        print("\n=== 测试CurrentDateFiles进度估算集成 ===")
        
        # 创建当前日期的DateType实例
        current_date = DateType(date_datetime=datetime.now())
        current_files = CurrentDateFiles(current_date)
        
        print(f"当前日期: {current_date}")
        print(f"图幅文件数量: {len(current_files.currentDateFiles)}")
        
        # 测试图幅目标点数属性
        targets = current_files.mapsheet_targets
        print(f"图幅目标点数配置数量: {len(targets)}")
        
        # 显示前几个图幅的目标点数
        for i, (roman_name, target) in enumerate(targets.items()):
            if i < 3:  # 只显示前3个
                print(f"  {roman_name}: {target} 点")
        
        # 测试进度估算功能
        print("\n开始进度估算...")
        estimation_results = current_files.estimate_progress(confidence_level=0.8)
        
        if "error" in estimation_results:
            print(f"进度估算失败: {estimation_results['error']}")
            return False
        
        # 显示整体结果
        overall = estimation_results.get("overall", {}).get("basic_estimation", {})
        print(f"整体进度: {overall.get('completion_percentage', 0):.1f}%")
        
        # 显示图幅统计
        summary = estimation_results.get("summary", {})
        print(f"估算的图幅数量: {summary.get('estimated_mapsheets', 0)}")
        print(f"平均完成度: {summary.get('avg_completion', 0):.1f}%")
        
        return True
        
    except Exception as e:
        print(f"CurrentDateFiles集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始进度估算功能集成测试...")
    
    tests = [
        ("图幅管理器", test_mapsheet_manager),
        ("进度估算模块", test_progress_estimation_module),
        ("CurrentDateFiles集成", test_current_date_files_integration)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"执行测试: {name}")
        result = test_func()
        results.append((name, result))
        status = "✅ 成功" if result else "❌ 失败"
        print(f"测试结果: {status}")
    
    # 汇总结果
    print(f"\n{'='*50}")
    print("测试汇总:")
    success_count = 0
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")
        if result:
            success_count += 1
    
    print(f"\n成功: {success_count}/{len(results)} 个测试")
    
    if success_count == len(results):
        print("🎉 所有测试通过！进度估算功能集成成功！")
    else:
        print("⚠️ 部分测试失败，需要进一步调试。")

if __name__ == "__main__":
    main()
