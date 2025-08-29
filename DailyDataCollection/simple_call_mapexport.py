#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的mapExport调用脚本
"""

def simple_call():
    """简单调用mapExport功能"""
    print("开始调用mapExport...")
    
    try:
        # 直接导入并执行
        import sys
        import os
        
        # 确保能导入mapExport
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        from mapExport import export_layout_to_pdf
        
        # 配置参数
        aprx_path = r"D:\RouteDesign\Finished observation points of Group3\Mahrous.aprx"
        layout_name = "Layout"
        output_pdf_path = r"D:\RouteDesign\Finished observation points of Group3\Mahrous_simple_call.pdf"
        
        print(f"工程文件: {aprx_path}")
        print(f"输出文件: {output_pdf_path}")
        
        # 执行导出
        export_layout_to_pdf(aprx_path, layout_name, output_pdf_path)
        
        # 检查结果
        if os.path.exists(output_pdf_path):
            size_mb = os.path.getsize(output_pdf_path) / (1024 * 1024)
            print(f"✅ 成功! 文件大小: {size_mb:.2f} MB")
        else:
            print("❌ 失败: 文件未生成")
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_call()
