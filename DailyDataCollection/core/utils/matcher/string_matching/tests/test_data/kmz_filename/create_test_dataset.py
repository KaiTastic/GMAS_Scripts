#!/usr/bin/env python3
"""
创建KMZ文件名测试数据集
用于字符串匹配模块的测试和验证
"""

import json
import csv
from pathlib import Path

def create_test_dataset():
    """创建测试数据集"""
    
    # 读取完整的KMZ文件分析结果
    with open('kmz_analysis_results.json', 'r', encoding='utf-8') as f:
        analysis_results = json.load(f)
    
    # 提取测试数据集
    test_dataset = {
        'metadata': {
            'total_files': analysis_results['total_files'],
            'finished_points_files': len([f for f in analysis_results['detailed_files'] 
                                         if f['pattern_info']['has_finished_points']]),
            'date_range': analysis_results['date_analysis']['date_range'],
            'unique_locations': analysis_results['location_analysis']['unique_locations'],
            'creation_date': '2025-08-31'
        },
        'finished_points_files': [],
        'sample_files': [],
        'location_patterns': {},
        'date_patterns': {}
    }
    
    # 收集finished_points文件
    finished_files = []
    location_patterns = {}
    date_patterns = {}
    
    for file_detail in analysis_results['detailed_files']:
        if file_detail['pattern_info']['has_finished_points']:
            file_info = {
                'filename': file_detail['filename'],
                'location': file_detail['pattern_info']['location_name'],
                'date': file_detail['date_info']['date_8digit'],
                'directory': file_detail['directory'],
                'size': file_detail['size'],
                'full_location_name': file_detail['filename'].split('_finished_points')[0]
            }
            finished_files.append(file_info)
            
            # 按位置分组
            location = file_info['location']
            if location not in location_patterns:
                location_patterns[location] = []
            location_patterns[location].append(file_info['filename'])
            
            # 按日期分组
            date = file_info['date']
            if date and date not in date_patterns:
                date_patterns[date] = []
            if date:
                date_patterns[date].append(file_info['filename'])
    
    test_dataset['finished_points_files'] = finished_files
    test_dataset['location_patterns'] = location_patterns
    test_dataset['date_patterns'] = date_patterns
    
    # 创建样本数据集（每个位置取前5个文件）
    sample_files = []
    for location, files in location_patterns.items():
        sample_files.extend([f for f in finished_files if f['location'] == location][:5])
    
    test_dataset['sample_files'] = sample_files
    
    # 保存测试数据集
    with open('kmz_test_dataset.json', 'w', encoding='utf-8') as f:
        json.dump(test_dataset, f, ensure_ascii=False, indent=2)
    
    # 创建CSV格式的测试数据集
    csv_data = []
    for file_info in finished_files:
        csv_data.append({
            'filename': file_info['filename'],
            'location': file_info['location'],
            'full_location_name': file_info['full_location_name'],
            'date': file_info['date'],
            'directory': file_info['directory'],
            'size': file_info['size']
        })
    
    with open('kmz_test_dataset.csv', 'w', newline='', encoding='utf-8') as f:
        if csv_data:
            writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
            writer.writeheader()
            writer.writerows(csv_data)
    
    # 打印统计信息
    print(f"✅ 测试数据集创建完成!")
    print(f"   - 总文件数: {len(finished_files)}")
    print(f"   - 位置数量: {len(location_patterns)}")
    print(f"   - 日期数量: {len(date_patterns)}")
    print(f"   - 样本文件数: {len(sample_files)}")
    print(f"   - JSON文件: kmz_test_dataset.json")
    print(f"   - CSV文件: kmz_test_dataset.csv")
    
    # 显示位置分布
    print(f"\n📍 位置分布 (top 10):")
    sorted_locations = sorted(location_patterns.items(), key=lambda x: len(x[1]), reverse=True)
    for location, files in sorted_locations[:10]:
        print(f"   {location}: {len(files)} 个文件")
    
    # 显示文件名模式示例
    print(f"\n📋 文件名模式示例:")
    for location, files in sorted_locations[:5]:
        print(f"   {location}:")
        for filename in files[:3]:
            print(f"     - {filename}")
        if len(files) > 3:
            print(f"     ... 还有 {len(files) - 3} 个文件")
        print()
    
    return test_dataset

if __name__ == "__main__":
    dataset = create_test_dataset()
