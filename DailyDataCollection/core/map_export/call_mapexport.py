#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArcGIS Pro地图导出调用脚本
该脚本用于调用mapExport.py中的功能来导出ArcGIS Pro布局为PDF文件
"""

import os
import sys
from datetime import datetime


def call_map_export():
    """
    调用mapExport.py的主要功能
    """
    try:
        # 导入mapExport模块
        from mapExport import export_layout_to_pdf
        
        print("=== ArcGIS Pro地图导出工具 ===")
        print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 配置参数
        aprx_path = r"D:\RouteDesign\Finished observation points of Group3\Mahrous.aprx"
        layout_name = "Layout"
        output_pdf_path = r"D:\RouteDesign\Finished observation points of Group3\Mahrous_export_call.pdf"
        
        print("配置参数:")
        print(f"  工程文件: {aprx_path}")
        print(f"  布局名称: {layout_name}")
        print(f"  输出文件: {output_pdf_path}")
        print()
        
        # 检查工程文件是否存在
        if not os.path.exists(aprx_path):
            print(f"❌ 错误: 工程文件不存在 - {aprx_path}")
            return False
        
        print("✅ 工程文件存在，开始导出...")
        
        # 调用导出函数
        export_layout_to_pdf(aprx_path, layout_name, output_pdf_path)
        
        # 验证输出文件
        if os.path.exists(output_pdf_path):
            file_size = os.path.getsize(output_pdf_path) / (1024 * 1024)  # MB
            print(f"✅ 导出成功完成!")
            print(f"   输出文件: {output_pdf_path}")
            print(f"   文件大小: {file_size:.2f} MB")
            return True
        else:
            print("❌ 导出失败: 未找到输出文件")
            return False
            
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("   请确保mapExport.py文件在同一目录下")
        return False
    except Exception as e:
        print(f"❌ 执行错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def batch_export_maps():
    """
    批量导出多个地图
    """
    print("=== 批量地图导出 ===")
    
    # 定义多个导出任务
    export_tasks = [
        {
            "name": "Mahrous地图",
            "aprx_path": r"D:\RouteDesign\Finished observation points of Group3\Mahrous.aprx",
            "layout_name": "Layout",
            "output_pdf_path": r"D:\RouteDesign\Finished observation points of Group3\Mahrous_batch_export.pdf"
        },
        {
            "name": "Group1观测点",
            "aprx_path": r"D:\RouteDesign\Finished observation points of Group3\Observation_Points_Group1.aprx",
            "layout_name": "Layout",
            "output_pdf_path": r"D:\RouteDesign\Finished observation points of Group3\Group1_batch_export.pdf"
        }
    ]
    
    success_count = 0
    total_count = len(export_tasks)
    
    for i, task in enumerate(export_tasks, 1):
        print(f"\n--- 任务 {i}/{total_count}: {task['name']} ---")
        
        # 检查工程文件
        if not os.path.exists(task['aprx_path']):
            print(f"❌ 跳过: 工程文件不存在 - {task['aprx_path']}")
            continue
        
        try:
            from mapExport import export_layout_to_pdf
            
            print(f"   正在导出: {task['name']}")
            export_layout_to_pdf(
                task['aprx_path'],
                task['layout_name'],
                task['output_pdf_path']
            )
            
            if os.path.exists(task['output_pdf_path']):
                file_size = os.path.getsize(task['output_pdf_path']) / (1024 * 1024)
                print(f"   ✅ 成功 ({file_size:.2f} MB)")
                success_count += 1
            else:
                print(f"   ❌ 失败: 文件未生成")
                
        except Exception as e:
            print(f"   ❌ 错误: {e}")
    
    print(f"\n批量导出完成: {success_count}/{total_count} 成功")
    return success_count


def interactive_export():
    """
    交互式地图导出
    """
    print("=== 交互式地图导出 ===")
    
    try:
        # 获取用户输入
        aprx_path = input("请输入ArcGIS Pro工程文件路径 (.aprx): ").strip()
        if not aprx_path:
            aprx_path = r"D:\RouteDesign\Finished observation points of Group3\Mahrous.aprx"
            print(f"使用默认路径: {aprx_path}")
        
        layout_name = input("请输入布局名称 (默认: Layout): ").strip()
        if not layout_name:
            layout_name = "Layout"
        
        output_pdf_path = input("请输入输出PDF路径: ").strip()
        if not output_pdf_path:
            base_dir = os.path.dirname(aprx_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_pdf_path = os.path.join(base_dir, f"export_{timestamp}.pdf")
            print(f"使用自动生成路径: {output_pdf_path}")
        
        # 执行导出
        from mapExport import export_layout_to_pdf
        export_layout_to_pdf(aprx_path, layout_name, output_pdf_path)
        
        if os.path.exists(output_pdf_path):
            print(f"✅ 交互式导出成功: {output_pdf_path}")
            return True
        else:
            print("❌ 交互式导出失败")
            return False
            
    except KeyboardInterrupt:
        print("\n用户取消操作")
        return False
    except Exception as e:
        print(f"❌ 交互式导出错误: {e}")
        return False


def main():
    """
    主函数 - 提供多种调用方式
    """
    print("ArcGIS Pro地图导出调用脚本")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        print("使用方式:")
        print("  python call_mapexport.py [mode]")
        print("  mode选项:")
        print("    single   - 单个地图导出 (默认)")
        print("    batch    - 批量地图导出")
        print("    interactive - 交互式导出")
        print()
        mode = "single"
    
    if mode == "batch":
        success_count = batch_export_maps()
        print(f"\n批量导出结果: {success_count} 个文件成功导出")
    elif mode == "interactive":
        success = interactive_export()
        print(f"\n交互式导出结果: {'成功' if success else '失败'}")
    else:  # single or default
        success = call_map_export()
        print(f"\n单个导出结果: {'成功' if success else '失败'}")


if __name__ == "__main__":
    main()
