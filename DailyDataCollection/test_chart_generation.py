#!/usr/bin/env python3
"""
测试新图表生成功能
"""

from core.progress_estimation import EstimationFacade
import os

def test_chart_generation():
    print("=== 测试独立折线图生成 ===")
    
    facade = EstimationFacade()
    
    # 生成图表
    result = facade.advanced_estimate(
        target_points=5000, 
        current_points=1500, 
        confidence_level=0.8
    )
    
    print("Advanced estimation completed!")
    print("Generated charts:")
    
    # 列出生成的文件
    output_dir = 'estimation_output'
    if os.path.exists(output_dir):
        files = [f for f in os.listdir(output_dir) if f.endswith('.png')]
        for f in sorted(files):
            filepath = os.path.join(output_dir, f)
            size = os.path.getsize(filepath) / 1024  # KB
            print(f'  - {f} ({size:.1f} KB)')
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_chart_generation()
