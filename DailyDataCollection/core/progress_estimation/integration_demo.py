"""
智能估算方法集成示例
展示如何使用新的MethodIntegrator进行多方法智能集成
"""

import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

from core.progress_estimation.mapsheet_estimation_runner import MapsheetEstimationRunner
from core.progress_estimation.method_integrator import MethodIntegrator


def demonstrate_method_integration():
    """演示智能方法集成功能"""
    
    print("=" * 60)
    print("GMAS 智能估算方法集成演示")
    print("=" * 60)
    
    # 创建估算运行器
    output_dir = "integration_demo_results"
    runner = MapsheetEstimationRunner(output_dir)
    
    print(f"输出目录: {output_dir}")
    print("开始运行智能集成估算...")
    print("-" * 40)
    
    try:
        # 运行估算（使用较短的回溯期便于演示）
        results = runner.run_mapsheet_estimations(
            days_back=20,
            confidence_level=0.8
        )
        
        mapsheet_results = results.get('mapsheet_results', {})
        summary = results.get('summary_report', {})
        
        if not mapsheet_results:
            print("❌ 未获得估算结果")
            return
        
        print(f"✅ 成功处理 {len(mapsheet_results)} 个图幅")
        print()
        
        # 展示集成分析结果
        print("🧠 智能集成分析结果:")
        print("-" * 40)
        
        for sheet_no, result in list(mapsheet_results.items())[:3]:  # 显示前3个图幅
            print(f"\n📊 图幅 {sheet_no}:")
            
            # 基本信息
            sheet_info = result['sheet_info']
            print(f"   完成率: {sheet_info['completion_rate']:.1f}%")
            print(f"   当前/目标: {sheet_info['current_points']} / {sheet_info['target_points']}")
            
            # 各方法估算结果
            estimations = result['estimations']
            print(f"   📈 各方法估算:")
            for method, est in estimations.items():
                if est.get('status') != 'fallback':
                    days = est.get('days_remaining', 0)
                    confidence = est.get('confidence', 0)
                    print(f"     • {method}: {days:.1f}天 (置信度: {confidence:.1%})")
            
            # 智能集成结果
            integration = result.get('integration', {})
            if integration:
                print(f"   🎯 智能集成结果:")
                
                # 最佳方法
                best_method = integration.get('best_method')
                if best_method:
                    method_name = best_method.get('method', 'unknown')
                    reliability = best_method.get('reliability_score', 0)
                    print(f"     推荐方法: {method_name} (可靠性: {reliability:.1%})")
                
                # 组合估算
                ensemble = integration.get('ensemble_estimation')
                if ensemble:
                    ensemble_days = ensemble.get('days_remaining', 0)
                    ensemble_conf = ensemble.get('confidence', 0)
                    print(f"     组合估算: {ensemble_days:.1f}天 (置信度: {ensemble_conf:.1%})")
                
                # 一致性分析
                consistency = integration.get('consistency_analysis', {})
                cons_score = consistency.get('score', 0)
                cons_level = consistency.get('consistency', 'unknown')
                print(f"     结果一致性: {cons_level} ({cons_score:.1%})")
                
                # 智能建议
                recommendations = integration.get('recommendations', [])
                if recommendations:
                    print(f"     💡 智能建议:")
                    for rec in recommendations[:2]:  # 显示前2个建议
                        print(f"       - {rec}")
        
        # 展示汇总统计
        print(f"\n📈 整体集成分析:")
        print("-" * 40)
        
        integration_analysis = summary.get('integration_analysis', {})
        if integration_analysis:
            # 最佳方法分布
            best_methods = integration_analysis.get('best_methods_distribution', {})
            if best_methods:
                print("最佳方法分布:")
                for method, count in best_methods.items():
                    print(f"  • {method}: {count} 次")
            
            # 组合估算平均置信度
            avg_ensemble_conf = integration_analysis.get('ensemble_confidence_avg', 0)
            if avg_ensemble_conf > 0:
                print(f"组合估算平均置信度: {avg_ensemble_conf:.1%}")
            
            # 一致性分布
            consistency_dist = integration_analysis.get('consistency_distribution', {})
            if consistency_dist:
                print("结果一致性分布:")
                for level, count in consistency_dist.items():
                    print(f"  • {level}: {count} 个图幅")
        
        print(f"\n📁 详细结果已保存到: {output_dir}")
        print("   包含智能集成分析的Excel报告、JSON详情等")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


def demonstrate_manual_integration():
    """演示手动使用MethodIntegrator的功能"""
    
    print("\n" + "=" * 60)
    print("手动方法集成器演示")
    print("=" * 60)
    
    # 创建集成器
    integrator = MethodIntegrator()
    
    # 模拟估算结果
    mock_estimations = {
        'simple_average': {
            'estimated_date': datetime.now() + timedelta(days=25),
            'days_remaining': 25,
            'confidence': 0.7,
            'status': 'estimated'
        },
        'weighted_average': {
            'estimated_date': datetime.now() + timedelta(days=23),
            'days_remaining': 23,
            'confidence': 0.8,
            'status': 'estimated'
        },
        'linear_regression': {
            'estimated_date': datetime.now() + timedelta(days=27),
            'days_remaining': 27,
            'confidence': 0.9,
            'status': 'estimated'
        },
        'monte_carlo': {
            'estimated_date': datetime.now() + timedelta(days=24),
            'days_remaining': 24,
            'confidence': 0.85,
            'status': 'estimated'
        }
    }
    
    # 模拟数据质量
    mock_data_quality = {
        'quality': 'good',
        'total_days': 15,
        'active_days': 12,
        'activity_rate': 0.8
    }
    
    try:
        # 执行集成
        integration_result = integrator.integrate_estimation_results(
            mock_estimations, mock_data_quality
        )
        
        print("🔧 手动集成结果:")
        print("-" * 30)
        
        # 最佳方法
        best_method = integration_result.get('best_method')
        if best_method:
            print(f"推荐方法: {best_method['method']}")
            print(f"可靠性评分: {best_method['reliability_score']:.1%}")
            print(f"推荐理由: {best_method['reason']}")
        
        # 组合估算
        ensemble = integration_result.get('ensemble_estimation')
        if ensemble:
            print(f"\n组合估算结果:")
            print(f"  预计天数: {ensemble['days_remaining']:.1f}")
            print(f"  置信度: {ensemble['confidence']:.1%}")
            print(f"  使用方法: {', '.join(ensemble['methods_used'])}")
        
        # 一致性分析
        consistency = integration_result.get('consistency_analysis')
        if consistency:
            print(f"\n一致性分析:")
            print(f"  一致性水平: {consistency['consistency']}")
            print(f"  一致性评分: {consistency['score']:.1%}")
            print(f"  方法差异天数: {consistency.get('date_range_days', 0)}")
        
        # 建议
        recommendations = integration_result.get('recommendations', [])
        if recommendations:
            print(f"\n💡 集成建议:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
    except Exception as e:
        print(f"❌ 手动集成演示失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行演示
    demonstrate_method_integration()
    
    # 运行手动集成演示
    demonstrate_manual_integration()
    
    print("\n" + "=" * 60)
    print("智能估算方法集成演示完成")
    print("=" * 60)
