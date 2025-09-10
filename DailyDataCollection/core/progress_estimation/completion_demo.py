"""
已完成项目智能处理演示
展示不同处理策略的效果和性能差异
"""

import sys
import os
from datetime import datetime, timedelta
import time

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

from core.progress_estimation.mapsheet_estimation_runner import MapsheetEstimationRunner
from core.progress_estimation.completed_project_handler import CompletedProjectHandler


def demonstrate_completion_strategies():
    """演示不同的已完成项目处理策略"""
    
    print("=" * 70)
    print("GMAS 已完成项目智能处理演示")
    print("=" * 70)
    
    # 策略A：跳过复杂估算
    print("\n🚀 策略A：跳过复杂估算（节省资源）")
    print("-" * 50)
    
    start_time = time.time()
    runner_skip = MapsheetEstimationRunner(
        output_dir="completion_demo_skip",
        skip_completed_estimation=True
    )
    
    results_skip = runner_skip.run_mapsheet_estimations(days_back=15)
    skip_time = time.time() - start_time
    
    print(f"⏱️  处理时间: {skip_time:.2f}秒")
    show_completion_results(results_skip, "策略A")
    
    # 策略B：完整分析
    print(f"\n📊 策略B：完整分析（深度洞察）")
    print("-" * 50)
    
    start_time = time.time()
    runner_full = MapsheetEstimationRunner(
        output_dir="completion_demo_full",
        skip_completed_estimation=False
    )
    
    results_full = runner_full.run_mapsheet_estimations(days_back=15)
    full_time = time.time() - start_time
    
    print(f"⏱️  处理时间: {full_time:.2f}秒")
    show_completion_results(results_full, "策略B")
    
    # 性能比较
    print(f"\n⚡ 性能比较:")
    print(f"策略A (跳过): {skip_time:.2f}秒")
    print(f"策略B (完整): {full_time:.2f}秒")
    print(f"时间节省: {((full_time - skip_time) / full_time * 100):.1f}%")


def show_completion_results(results, strategy_name):
    """显示完成状态结果"""
    mapsheet_results = results.get('mapsheet_results', {})
    
    completed_count = 0
    completion_details = []
    
    for sheet_no, result in mapsheet_results.items():
        sheet_info = result['sheet_info']
        completion_rate = sheet_info['completion_rate']
        
        if completion_rate >= 100:
            completed_count += 1
            
            # 检查估算结果的详细信息
            estimations = result['estimations']
            sample_estimation = next(iter(estimations.values()))
            
            completion_detail = {
                'sheet_no': sheet_no,
                'completion_rate': completion_rate,
                'status': sample_estimation.get('status', 'unknown'),
                'has_completion_details': 'completion_details' in sample_estimation,
                'message': sample_estimation.get('message', 'N/A')
            }
            completion_details.append(completion_detail)
    
    print(f"📈 {strategy_name} 结果:")
    print(f"   已完成图幅: {completed_count} 个")
    
    # 显示前3个已完成项目的详情
    for detail in completion_details[:3]:
        print(f"\n   📊 图幅 {detail['sheet_no']}:")
        print(f"      完成率: {detail['completion_rate']:.1f}%")
        print(f"      处理状态: {detail['status']}")
        
        if detail['has_completion_details']:
            print(f"      🔍 包含详细分析")
        else:
            print(f"      ⚡ 快速处理")
        
        if detail['message'] != 'N/A':
            print(f"      💬 {detail['message']}")


def demonstrate_completion_handler():
    """演示CompletedProjectHandler的直接使用"""
    
    print(f"\n" + "=" * 70)
    print("已完成项目处理器直接使用演示")
    print("=" * 70)
    
    # 创建处理器实例
    handler_skip = CompletedProjectHandler(skip_estimation=True)
    handler_full = CompletedProjectHandler(skip_estimation=False)
    
    # 模拟不同完成情况的项目
    test_cases = [
        {'current': 1000, 'target': 1000, 'name': '正好完成'},
        {'current': 1050, 'target': 1000, 'name': '轻微超额'},
        {'current': 1200, 'target': 1000, 'name': '中度超额'},
        {'current': 1350, 'target': 1000, 'name': '显著超额'},
    ]
    
    print("\n🔍 不同完成情况的分析对比:")
    print("-" * 50)
    
    for case in test_cases:
        print(f"\n📋 {case['name']} ({case['current']}/{case['target']}):")
        
        # 快速处理
        result_skip = handler_skip.create_completed_estimation_result(
            case['current'], case['target'], 'simple_average'
        )
        
        # 完整分析
        result_full = handler_full.create_completed_estimation_result(
            case['current'], case['target'], 'simple_average'
        )
        
        print(f"   ⚡ 快速: {result_skip.get('status', 'unknown')} - {result_skip.get('message', 'N/A')}")
        print(f"   📊 完整: {result_full.get('status', 'unknown')} - {result_full.get('message', 'N/A')}")
        
        # 显示完整分析的额外信息
        if 'completion_details' in result_full:
            details = result_full['completion_details']
            category = details.get('completion_category', 'unknown')
            excess_rate = details.get('excess_rate', 0)
            efficiency = details.get('efficiency_assessment', {})
            
            print(f"      分类: {category}")
            print(f"      超额率: {excess_rate:.1f}%")
            print(f"      效率评级: {efficiency.get('level', 'unknown')}")


def demonstrate_completion_summary():
    """演示已完成项目汇总分析"""
    
    print(f"\n" + "=" * 70)
    print("已完成项目汇总分析演示")
    print("=" * 70)
    
    handler = CompletedProjectHandler(skip_estimation=False)
    
    # 模拟多个已完成项目
    mock_projects = []
    test_data = [
        (1000, 1000), (1020, 1000), (1050, 1000), (1150, 1000),
        (980, 1000), (1300, 1000), (1080, 1000), (1200, 1000)
    ]
    
    for current, target in test_data:
        completion_status = handler.analyze_completion_status(current, target)
        mock_projects.append(completion_status)
    
    # 生成汇总分析
    summary = handler.get_completion_summary(mock_projects)
    
    print(f"\n📊 汇总分析结果:")
    print(f"   总计已完成项目: {summary.get('total_completed_projects', 0)} 个")
    print(f"   平均完成率: {summary.get('average_completion_rate', 0):.1f}%")
    print(f"   平均效率评分: {summary.get('average_efficiency_score', 0):.1%}")
    print(f"   超目标项目: {summary.get('over_target_projects', 0)} 个")
    print(f"   显著超额项目: {summary.get('significantly_over_projects', 0)} 个")
    
    # 分类分布
    category_dist = summary.get('completion_category_distribution', {})
    if category_dist:
        print(f"\n📈 完成类型分布:")
        for category, count in category_dist.items():
            category_names = {
                'exactly_completed': '正好完成',
                'slightly_over': '轻微超额',
                'moderately_over': '中度超额',
                'significantly_over': '显著超额'
            }
            print(f"   {category_names.get(category, category)}: {count} 个")


if __name__ == "__main__":
    try:
        # 运行不同策略演示
        demonstrate_completion_strategies()
        
        # 运行处理器直接使用演示
        demonstrate_completion_handler()
        
        # 运行汇总分析演示
        demonstrate_completion_summary()
        
        print(f"\n" + "=" * 70)
        print("已完成项目智能处理演示完成")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
