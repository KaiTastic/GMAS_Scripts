#!/usr/bin/env python3
"""
KMZ完成点文件匹配器
根据Excel图幅名称匹配KMZ文件中的完成点文件
支持D列和F列的匹配模式
"""

import pandas as pd
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from core.utils.matcher.string_matching.factory import create_string_matcher

class KMZSheetNameMatcher:
    def __init__(self, excel_file_path: str, kmz_csv_path: str):
        """
        初始化KMZ图幅名称匹配器
        
        Args:
            excel_file_path: Excel文件路径，包含图幅名称
            kmz_csv_path: KMZ文件CSV数据集路径
        """
        self.excel_file_path = excel_file_path
        self.kmz_csv_path = kmz_csv_path
        self.matcher = create_string_matcher("hybrid", fuzzy_threshold=0.6)
        
        # 存储数据
        self.sheet_names_d = []  # D列图幅名称
        self.sheet_names_f = []  # F列图幅名称
        self.kmz_files = []      # KMZ文件数据
        self.finished_points_files = []  # 完成点文件
        
    def load_excel_data(self) -> bool:
        """
        从Excel文件加载D列和F列的图幅名称
        
        Returns:
            bool: 加载是否成功
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(self.excel_file_path)
            
            print(f"Excel文件列数: {df.shape[1]}, 行数: {df.shape[0]}")
            print(f"列名: {list(df.columns)}")
            
            # 获取D列数据（第4列，索引为3）
            if df.shape[1] >= 4:
                d_column = df.iloc[:, 3].dropna()  # D列
                self.sheet_names_d = [str(name).strip() for name in d_column if pd.notna(name)]
                print(f"从D列加载了 {len(self.sheet_names_d)} 个图幅名称")
            
            # 获取F列数据（第6列，索引为5）
            if df.shape[1] >= 6:
                f_column = df.iloc[:, 5].dropna()  # F列
                self.sheet_names_f = [str(name).strip() for name in f_column if pd.notna(name)]
                print(f"从F列加载了 {len(self.sheet_names_f)} 个图幅名称")
            
            # 显示前几个示例
            if self.sheet_names_d:
                print(f"D列示例: {self.sheet_names_d[:5]}")
            if self.sheet_names_f:
                print(f"F列示例: {self.sheet_names_f[:5]}")
                
            return True
                
        except Exception as e:
            print(f"读取Excel文件时出错: {e}")
            return False
    
    def load_kmz_data(self) -> bool:
        """
        从CSV文件加载KMZ文件数据
        
        Returns:
            bool: 加载是否成功
        """
        try:
            df = pd.read_csv(self.kmz_csv_path, encoding='utf-8')
            self.kmz_files = df.to_dict('records')
            
            # 筛选完成点文件
            self.finished_points_files = []
            for file_record in self.kmz_files:
                filename = file_record['FileName']
                if self.is_finished_points_file(filename):
                    self.finished_points_files.append(file_record)
            
            print(f"加载了 {len(self.kmz_files)} 个KMZ文件")
            print(f"其中完成点文件: {len(self.finished_points_files)} 个")
            
            return True
            
        except Exception as e:
            print(f"读取KMZ CSV文件时出错: {e}")
            return False
    
    def is_finished_points_file(self, filename: str) -> bool:
        """
        判断是否为完成点文件
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 是否为完成点文件
        """
        # 转换为小写进行匹配
        filename_lower = filename.lower()
        
        # 检查是否包含完成点标识
        finished_points_patterns = [
            'finished_points_and_tracks',
            'finished_points_and_track',
            'finished_point_and_tracks',
            'finished_point_and_track'
        ]
        
        for pattern in finished_points_patterns:
            if pattern in filename_lower:
                return True
        
        return False
    
    def extract_date_from_filename(self, filename: str) -> Optional[str]:
        """
        从文件名中提取8位日期
        
        Args:
            filename: 文件名
            
        Returns:
            str: 提取的日期字符串 (YYYYMMDD格式) 或 None
        """
        # 匹配8位数字的日期格式 (YYYYMMDD)
        date_pattern = r'(\d{8})'
        match = re.search(date_pattern, filename)
        
        if match:
            return match.group(1)
        
        return None
    
    def extract_location_from_filename(self, filename: str) -> Optional[str]:
        """
        从完成点文件名中提取位置名称
        
        Args:
            filename: 文件名
            
        Returns:
            str: 位置名称或None
        """
        # 移除扩展名
        name_without_ext = filename.replace('.kmz', '').replace('.KMZ', '')
        
        # 查找finished_points标识符的位置
        finished_patterns = [
            '_finished_points_and_tracks_',
            '_finished_points_and_track_',
            '_finished_point_and_tracks_',
            '_finished_point_and_track_'
        ]
        
        for pattern in finished_patterns:
            if pattern in name_without_ext.lower():
                # 提取模式前的部分作为位置名称
                parts = name_without_ext.lower().split(pattern.lower())
                if parts and parts[0]:
                    return parts[0]
        
        return None
    
    def generate_expected_patterns(self) -> List[str]:
        """
        根据图幅名称生成预期的文件名模式
        
        Returns:
            List[str]: 预期文件名模式列表
        """
        patterns = []
        
        # D列模式: D列名称_finished_points_and_tracks_日期
        for sheet_name in self.sheet_names_d:
            base_pattern = f"{sheet_name}_finished_points_and_tracks"
            patterns.append({
                'pattern': base_pattern,
                'source': 'D列',
                'sheet_name': sheet_name
            })
        
        # F列模式: F列名称_finished_points_and_tracks_日期
        for sheet_name in self.sheet_names_f:
            base_pattern = f"{sheet_name}_finished_points_and_tracks"
            patterns.append({
                'pattern': base_pattern,
                'source': 'F列',
                'sheet_name': sheet_name
            })
        
        return patterns
    
    def match_files_with_patterns(self) -> Dict:
        """
        执行文件名与图幅名称的匹配
        
        Returns:
            Dict: 匹配结果
        """
        print("\n开始KMZ完成点文件匹配...")
        
        # 生成预期模式
        expected_patterns = self.generate_expected_patterns()
        print(f"生成了 {len(expected_patterns)} 个预期模式")
        
        results = {
            'total_finished_files': len(self.finished_points_files),
            'total_patterns': len(expected_patterns),
            'matched_files': [],
            'unmatched_files': [],
            'pattern_matches': defaultdict(list),
            'match_statistics': {
                'D列匹配': 0,
                'F列匹配': 0,
                '总匹配数': 0
            }
        }
        
        # 对每个完成点文件进行匹配
        for file_record in self.finished_points_files:
            filename = file_record['FileName']
            best_matches = []
            
            # 提取文件信息
            location = self.extract_location_from_filename(filename)
            date = self.extract_date_from_filename(filename)
            
            # 对每个预期模式进行匹配
            for pattern_info in expected_patterns:
                pattern = pattern_info['pattern']
                
                # 使用字符串匹配器进行匹配
                match_result, score = self.matcher.match_string_with_score(pattern, [filename])
                
                if match_result and score > 0.3:  # 设置较低的阈值
                    match_info = {
                        'pattern': pattern,
                        'source': pattern_info['source'],
                        'sheet_name': pattern_info['sheet_name'],
                        'score': score,
                        'match_details': {
                            'target': match_result,
                            'method': 'hybrid'
                        }
                    }
                    best_matches.append(match_info)
            
            # 记录结果
            file_info = {
                'filename': filename,
                'location': location,
                'date': date,
                'directory': file_record['Directory'],
                'size': file_record['Size'],
                'matches': best_matches
            }
            
            if best_matches:
                results['matched_files'].append(file_info)
                results['match_statistics']['总匹配数'] += 1
                
                # 统计D列和F列匹配
                for match in best_matches:
                    if match['source'] == 'D列':
                        results['match_statistics']['D列匹配'] += 1
                    elif match['source'] == 'F列':
                        results['match_statistics']['F列匹配'] += 1
                    
                    # 按模式分组
                    results['pattern_matches'][match['sheet_name']].append(file_info)
            else:
                results['unmatched_files'].append(file_info)
        
        return results
    
    def print_match_results(self, results: Dict):
        """
        打印匹配结果
        
        Args:
            results: 匹配结果字典
        """
        print("\n" + "="*80)
        print("KMZ完成点文件匹配结果")
        print("="*80)
        
        print(f"\n📊 总体统计:")
        print(f"   完成点文件总数: {results['total_finished_files']}")
        print(f"   预期模式总数: {results['total_patterns']}")
        print(f"   匹配成功文件数: {len(results['matched_files'])}")
        print(f"   未匹配文件数: {len(results['unmatched_files'])}")
        print(f"   匹配成功率: {len(results['matched_files'])/results['total_finished_files']*100:.1f}%")
        
        print(f"\n📈 匹配统计:")
        for source, count in results['match_statistics'].items():
            print(f"   {source}: {count}")
        
        print(f"\n🎯 匹配成功的文件 (前20个):")
        for i, file_info in enumerate(results['matched_files'][:20], 1):
            print(f"  {i}. {file_info['filename']}")
            if file_info['location']:
                print(f"     位置: {file_info['location']}")
            if file_info['date']:
                print(f"     日期: {file_info['date']}")
            
            # 显示最佳匹配
            if file_info['matches']:
                best_match = max(file_info['matches'], key=lambda x: x['score'])
                print(f"     最佳匹配: {best_match['sheet_name']} ({best_match['source']}) - 分数: {best_match['score']:.3f}")
            print()
        
        if len(results['matched_files']) > 20:
            print(f"  ... 还有 {len(results['matched_files']) - 20} 个匹配文件")
        
        print(f"\n📋 按图幅名称分组的匹配 (前10个):")
        sorted_patterns = sorted(results['pattern_matches'].items(), 
                               key=lambda x: len(x[1]), reverse=True)
        
        for pattern_name, files in sorted_patterns[:10]:
            print(f"  {pattern_name}: {len(files)} 个文件")
            for file_info in files[:3]:  # 显示前3个文件
                print(f"    - {file_info['filename']}")
            if len(files) > 3:
                print(f"    ... 还有 {len(files) - 3} 个文件")
            print()
        
        print(f"\n❌ 未匹配的文件 (前10个):")
        for i, file_info in enumerate(results['unmatched_files'][:10], 1):
            print(f"  {i}. {file_info['filename']}")
            if file_info['location']:
                print(f"     提取的位置: {file_info['location']}")
    
    def save_results(self, results: Dict, output_file: str):
        """
        保存匹配结果到文件
        
        Args:
            results: 匹配结果
            output_file: 输出文件路径
        """
        import json
        
        try:
            # 转换结果为可序列化格式
            serializable_results = {
                'total_finished_files': results['total_finished_files'],
                'total_patterns': results['total_patterns'],
                'match_statistics': results['match_statistics'],
                'matched_files': results['matched_files'],
                'unmatched_files': results['unmatched_files'],
                'pattern_matches': dict(results['pattern_matches'])
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"\n✅ 匹配结果已保存到: {output_file}")
            
        except Exception as e:
            print(f"❌ 保存结果失败: {e}")
    
    def run_matching(self) -> Dict:
        """
        运行完整的匹配流程
        
        Returns:
            Dict: 匹配结果
        """
        print("🚀 启动KMZ完成点文件匹配...")
        
        # 1. 加载Excel数据
        if not self.load_excel_data():
            return {'error': '无法加载Excel数据'}
        
        # 2. 加载KMZ数据
        if not self.load_kmz_data():
            return {'error': '无法加载KMZ数据'}
        
        # 3. 执行匹配
        results = self.match_files_with_patterns()
        
        # 4. 打印结果
        self.print_match_results(results)
        
        # 5. 保存结果
        output_file = "kmz_matching_results.json"
        self.save_results(results, output_file)
        
        return results

def main():
    """主函数"""
    # 配置文件路径
    excel_file = r"D:\MacBook\MacBookDocument\SourceCode\GitHub_Public_Repos\GMAS_Script\DailyDataCollection\resource\private\100K_sheet_names_271_name_V3_after_GEOSA_edit.xlsx"
    kmz_csv = r"D:\MacBook\MacBookDocument\SourceCode\GitHub_Public_Repos\GMAS_Script\DailyDataCollection\core\utils\matcher\string_matching\tests\test_data\kmz_files_dataset.csv"
    
    # 创建匹配器并运行
    matcher = KMZSheetNameMatcher(excel_file, kmz_csv)
    results = matcher.run_matching()
    
    if 'error' in results:
        print(f"错误: {results['error']}")
    else:
        print("\n🎉 匹配完成!")

if __name__ == "__main__":
    main()
