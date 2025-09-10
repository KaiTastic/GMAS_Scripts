#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel格式验证脚本
验证已完成图幅在Excel文件中是否正确显示为"-"
"""

import pandas as pd
import os
from pathlib import Path

def verify_excel_formatting():
    """验证Excel文件中已完成图幅的格式"""
    
    # 找到最新的Excel文件
    estimation_dir = Path(__file__).parent
    excel_files = list(estimation_dir.glob("estimation_results_*/estimation_report_*.xlsx"))
    
    if not excel_files:
        print("未找到Excel文件")
        return
        
    latest_excel = max(excel_files, key=os.path.getctime)
    print(f"检查Excel文件: {latest_excel}")
    
    try:
        # 读取汇总表
        summary_df = pd.read_excel(latest_excel, sheet_name='汇总')
        print("\n汇总表:")
        print("=" * 50)
        
        # 显示相关列
        display_columns = ['图幅编号', '完成率(%)', '预计完成日期', '剩余天数']
        for col in display_columns:
            if col in summary_df.columns:
                print(f"{col:>12} ", end="")
        print()
        print("-" * 50)
        
        for _, row in summary_df.iterrows():
            for col in display_columns:
                if col in summary_df.columns:
                    value = row[col]
                    if pd.isna(value):
                        value = "NaN"
                    print(f"{str(value):>12} ", end="")
            print()
            
        # 检查已完成图幅的格式
        completed_mapsheets = summary_df[summary_df['完成率(%)'] >= 100]
        if not completed_mapsheets.empty:
            print(f"\n已完成图幅验证:")
            print("=" * 30)
            for _, row in completed_mapsheets.iterrows():
                mapsheet = row['图幅编号']
                est_date = row['预计完成日期']
                remaining = row['剩余天数']
                completion = row['完成率(%)']
                
                print(f"图幅 {mapsheet}:")
                print(f"  完成率: {completion:.1f}%")
                print(f"  预计完成日期: {est_date}")
                print(f"  剩余天数: {remaining}")
                
                # 验证格式
                if est_date == "-" and remaining == "-":
                    print(f"  ✅ 格式正确")
                else:
                    print(f"  ❌ 格式错误，应该显示为'-'")
                print()
        else:
            print("\n未找到已完成的图幅")
            
        # 读取详细表
        try:
            detail_df = pd.read_excel(latest_excel, sheet_name='详细估算')
            print("\n详细表中已完成图幅的估算结果:")
            print("=" * 40)
            
            # 检查每个图幅的结果
            for mapsheet in detail_df['图幅编号'].unique():
                mapsheet_data = detail_df[detail_df['图幅编号'] == mapsheet]
                
                # 检查这个图幅是否在汇总表中标记为已完成
                mapsheet_summary = summary_df[summary_df['图幅编号'] == mapsheet]
                if not mapsheet_summary.empty and mapsheet_summary.iloc[0]['完成率(%)'] >= 100:
                    print(f"图幅 {mapsheet} (已完成):")
                    for _, row in mapsheet_data.iterrows():
                        method = row['估算方法']
                        date_value = row['预计完成日期']
                        remaining = row['剩余天数']
                        print(f"  {method}: 预计完成日期={date_value}, 剩余天数={remaining}")
                    print()
        except Exception as e:
            print(f"详细表读取失败: {e}")
            
    except Exception as e:
        print(f"读取Excel文件失败: {e}")

if __name__ == "__main__":
    verify_excel_formatting()
