#!/usr/bin/env python3
"""
KMZ文件数据集分析器
分析收集到的KMZ文件数据集，为字符串匹配提供基础数据
"""

import pandas as pd
import re
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
import json

class KMZDatasetAnalyzer:
    def __init__(self, csv_file_path: str):
        """
        初始化KMZ数据集分析器
        
        Args:
            csv_file_path: CSV数据集文件路径
        """
        self.csv_file_path = csv_file_path
        self.df = None
        
    def load_data(self):
        """加载CSV数据"""
        try:
            self.df = pd.read_csv(self.csv_file_path, encoding='utf-8')
            print(f"成功加载 {len(self.df)} 个KMZ文件记录")
            return True
        except Exception as e:
            print(f"加载数据失败: {e}")
            return False
    
    def extract_date_patterns(self, filename: str):
        """
        从文件名中提取日期模式
        
        Args:
            filename: 文件名
            
        Returns:
            dict: 包含各种日期信息的字典
        """
        result = {
            'date_8digit': None,  # YYYYMMDD
            'date_6digit': None,  # YYMMDD
            'year': None,
            'month': None,
            'day': None
        }
        
        # 8位日期 (YYYYMMDD)
        pattern_8 = r'(\d{8})'
        match_8 = re.search(pattern_8, filename)
        if match_8:
            date_str = match_8.group(1)
            try:
                date_obj = datetime.strptime(date_str, '%Y%m%d')
                result['date_8digit'] = date_str
                result['year'] = date_obj.year
                result['month'] = date_obj.month
                result['day'] = date_obj.day
            except ValueError:
                pass
        
        # 6位日期 (YYMMDD)
        if not result['date_8digit']:
            pattern_6 = r'(\d{6})'
            match_6 = re.search(pattern_6, filename)
            if match_6:
                date_str = match_6.group(1)
                try:
                    date_obj = datetime.strptime(date_str, '%y%m%d')
                    result['date_6digit'] = date_str
                    result['year'] = date_obj.year
                    result['month'] = date_obj.month
                    result['day'] = date_obj.day
                except ValueError:
                    pass
        
        return result
    
    def extract_name_patterns(self, filename: str):
        """
        从文件名中提取地名和模式
        
        Args:
            filename: 文件名
            
        Returns:
            dict: 包含地名和模式信息的字典
        """
        # 移除扩展名
        name_without_ext = filename.replace('.kmz', '').replace('.KMZ', '')
        
        result = {
            'base_name': name_without_ext,
            'has_finished_points_and_tracks': ('finished_points_and_tracks' in name_without_ext.lower() or 
                                              'finished_points' in name_without_ext.lower() or 
                                              'finished' in name_without_ext.lower()),
            'has_plan_routes': 'plan_routes' in name_without_ext.lower() or 'plan_route' in name_without_ext.lower(),
            'location_name': None,
            'pattern_type': None
        }
        
        # 提取位置名称（假设是下划线分隔的第一部分）
        parts = name_without_ext.split('_')
        if len(parts) > 0:
            result['location_name'] = parts[0]
        
        # 确定模式类型
        if result['has_finished_points_and_tracks']:
            result['pattern_type'] = 'finished_points_and_tracks'
        elif result['has_plan_routes']:
            result['pattern_type'] = 'plan_routes'
        else:
            result['pattern_type'] = 'other'
        
        return result
    
    def exact_pattern_match(self, filename: str):
        """
        精确匹配文件名模式
        严格按照预期格式进行匹配：位置名_finished_points_and_tracks_YYYYMMDD
        
        Args:
            filename: 文件名
            
        Returns:
            dict: 精确匹配结果
        """
        # 移除扩展名
        name_without_ext = filename.replace('.kmz', '').replace('.KMZ', '')
        
        result = {
            'is_exact_match': False,
            'location_part': None,
            'middle_part': None,
            'date_part': None,
            'exact_pattern_type': None
        }
        
        # 精确匹配模式1: 位置名_finished_points_and_tracks_YYYYMMDD
        pattern1 = r'^(.+?)_(finished_points_and_tracks)_(\d{8})(?:\(\d+\))?$'
        match1 = re.match(pattern1, name_without_ext, re.IGNORECASE)
        
        if match1:
            result['is_exact_match'] = True
            result['location_part'] = match1.group(1)
            result['middle_part'] = match1.group(2)
            result['date_part'] = match1.group(3)
            result['exact_pattern_type'] = 'finished_points_and_tracks'
            return result
        
        # 精确匹配模式2: 位置名_plan_routes_YYYYMMDD
        pattern2 = r'^(.+?)_(plan_routes?)_(\d{8})(?:\(\d+\))?$'
        match2 = re.match(pattern2, name_without_ext, re.IGNORECASE)
        
        if match2:
            result['is_exact_match'] = True
            result['location_part'] = match2.group(1)
            result['middle_part'] = match2.group(2)
            result['date_part'] = match2.group(3)
            result['exact_pattern_type'] = 'plan_routes'
            return result
        
        # 精确匹配模式3: GMAS_Points_and_tracks_until_YYYYMMDD
        pattern3 = r'^(GMAS)_(Points_and_tracks_until)_(\d{8})(?:\(\d+\))?$'
        match3 = re.match(pattern3, name_without_ext, re.IGNORECASE)
        
        if match3:
            result['is_exact_match'] = True
            result['location_part'] = match3.group(1)
            result['middle_part'] = match3.group(2)
            result['date_part'] = match3.group(3)
            result['exact_pattern_type'] = 'gmas_points'
            return result
        
        return result
    
    def fuzzy_location_match(self, location_candidate: str, known_locations: list):
        """
        对位置名称进行模糊匹配
        
        Args:
            location_candidate: 候选位置名称
            known_locations: 已知位置名称列表
            
        Returns:
            dict: 位置匹配结果
        """
        if not location_candidate:
            return {'match': None, 'confidence': 0.0, 'method': 'none'}
        
        location_candidate = location_candidate.strip()
        best_match = None
        best_confidence = 0.0
        best_method = 'none'
        
        for known_loc in known_locations:
            if not known_loc:
                continue
                
            # 1. 完全匹配
            if location_candidate.lower() == known_loc.lower():
                return {'match': known_loc, 'confidence': 1.0, 'method': 'exact'}
            
            # 2. 包含匹配
            if location_candidate.lower() in known_loc.lower():
                confidence = len(location_candidate) / len(known_loc)
                if confidence > best_confidence:
                    best_match = known_loc
                    best_confidence = confidence
                    best_method = 'contains'
            
            if known_loc.lower() in location_candidate.lower():
                confidence = len(known_loc) / len(location_candidate)
                if confidence > best_confidence:
                    best_match = known_loc
                    best_confidence = confidence
                    best_method = 'contained'
            
            # 3. 前缀匹配
            if location_candidate.lower().startswith(known_loc.lower()[:3]) and len(known_loc) >= 3:
                confidence = 0.7
                if confidence > best_confidence:
                    best_match = known_loc
                    best_confidence = confidence
                    best_method = 'prefix'
            
            # 4. 去除特殊字符后匹配
            clean_candidate = re.sub(r'[^a-zA-Z]', '', location_candidate).lower()
            clean_known = re.sub(r'[^a-zA-Z]', '', known_loc).lower()
            
            if clean_candidate == clean_known and len(clean_candidate) > 2:
                confidence = 0.9
                if confidence > best_confidence:
                    best_match = known_loc
                    best_confidence = confidence
                    best_method = 'clean_match'
        
        return {'match': best_match, 'confidence': best_confidence, 'method': best_method}
    
    def fuzzy_middle_part_match(self, middle_candidate: str):
        """
        对中间部分（关键词）进行模糊匹配
        
        Args:
            middle_candidate: 候选中间部分
            
        Returns:
            dict: 中间部分匹配结果
        """
        if not middle_candidate:
            return {'pattern_type': None, 'confidence': 0.0, 'keywords_found': [], 'issues': []}
        
        middle_lower = middle_candidate.lower()
        
        # 定义模式关键词和变体
        pattern_keywords = {
            'finished_points_and_tracks': {
                'required': ['finished', 'points'],
                'optional': ['tracks', 'and'],
                'variants': {
                    'finished': ['finish', 'complete', 'done'],
                    'points': ['point', 'pts', 'pt'],
                    'tracks': ['track', 'trk', 'route', 'path'],
                    'and': ['&', 'n']
                }
            },
            'plan_routes': {
                'required': ['plan', 'route'],
                'optional': [],
                'variants': {
                    'plan': ['planning', 'planned', 'planed'],
                    'route': ['routes', 'routing', 'path', 'track']
                }
            },
            'gmas_points': {
                'required': ['gmas'],
                'optional': ['points'],
                'variants': {
                    'gmas': ['gms'],
                    'points': ['point', 'pts', 'pt']
                }
            }
        }
        
        results = {}
        
        for pattern_type, config in pattern_keywords.items():
            score = 0
            found_keywords = []
            confidence = 0.0
            issues = []
            
            # 检查必需关键词
            required_found = 0
            for req_keyword in config['required']:
                if req_keyword in middle_lower:
                    score += 2
                    required_found += 1
                    found_keywords.append(req_keyword)
                else:
                    # 检查变体
                    variants = config['variants'].get(req_keyword, [])
                    for variant in variants:
                        if variant in middle_lower:
                            score += 1.5
                            required_found += 1
                            found_keywords.append(f"{req_keyword}({variant})")
                            break
            
            # 检查可选关键词
            for opt_keyword in config['optional']:
                if opt_keyword in middle_lower:
                    score += 1
                    found_keywords.append(opt_keyword)
                else:
                    # 检查变体
                    variants = config['variants'].get(opt_keyword, [])
                    for variant in variants:
                        if variant in middle_lower:
                            score += 0.8
                            found_keywords.append(f"{opt_keyword}({variant})")
                            break
            
            # 计算置信度
            total_required = len(config['required'])
            if total_required > 0:
                confidence = (required_found / total_required) * 0.8 + (score / (total_required * 2 + len(config['optional']))) * 0.2
            
            # 检查问题
            if required_found < total_required:
                issues.append(f"缺少必需关键词: {[kw for kw in config['required'] if kw not in middle_lower]}")
            
            if confidence > 0:
                results[pattern_type] = {
                    'confidence': confidence,
                    'keywords_found': found_keywords,
                    'score': score,
                    'issues': issues
                }
        
        if not results:
            return {'pattern_type': None, 'confidence': 0.0, 'keywords_found': [], 'issues': ['无法识别任何已知模式']}
        
        # 选择最佳匹配
        best_pattern = max(results.items(), key=lambda x: x[1]['confidence'])
        return {
            'pattern_type': best_pattern[0],
            'confidence': best_pattern[1]['confidence'],
            'keywords_found': best_pattern[1]['keywords_found'],
            'issues': best_pattern[1]['issues']
        }
    
    def fuzzy_date_match(self, date_candidate: str):
        """
        对日期部分进行模糊匹配和修复
        
        Args:
            date_candidate: 候选日期字符串
            
        Returns:
            dict: 日期匹配结果
        """
        if not date_candidate:
            return {'date': None, 'confidence': 0.0, 'format': None, 'issues': []}
        
        issues = []
        
        # 提取所有可能的数字序列
        number_sequences = re.findall(r'\d+', date_candidate)
        
        for seq in number_sequences:
            # 1. 标准8位日期格式 YYYYMMDD
            if len(seq) == 8:
                try:
                    datetime.strptime(seq, '%Y%m%d')
                    return {'date': seq, 'confidence': 1.0, 'format': 'YYYYMMDD', 'issues': []}
                except ValueError:
                    issues.append(f"8位数字{seq}不是有效日期")
            
            # 2. 6位日期格式 YYMMDD
            elif len(seq) == 6:
                try:
                    # 尝试作为YYMMDD解析
                    parsed_date = datetime.strptime(seq, '%y%m%d')
                    full_date = parsed_date.strftime('%Y%m%d')
                    return {'date': full_date, 'confidence': 0.9, 'format': 'YYMMDD->YYYYMMDD', 'issues': []}
                except ValueError:
                    issues.append(f"6位数字{seq}不是有效YYMMDD格式")
            
            # 3. 处理可能的日期变体
            elif len(seq) > 8:
                # 可能是日期+额外数字
                for i in range(len(seq) - 7):
                    substr = seq[i:i+8]
                    try:
                        datetime.strptime(substr, '%Y%m%d')
                        return {
                            'date': substr, 
                            'confidence': 0.8, 
                            'format': f'extracted_from_{seq}',
                            'issues': [f"从{seq}中提取了{substr}"]
                        }
                    except ValueError:
                        continue
                
                # 尝试前8位
                if len(seq) >= 8:
                    front_8 = seq[:8]
                    try:
                        datetime.strptime(front_8, '%Y%m%d')
                        return {
                            'date': front_8,
                            'confidence': 0.7,
                            'format': f'front_8_from_{seq}',
                            'issues': [f"使用了{seq}的前8位: {front_8}"]
                        }
                    except ValueError:
                        issues.append(f"前8位{front_8}不是有效日期")
                
                # 尝试后8位
                if len(seq) >= 8:
                    back_8 = seq[-8:]
                    try:
                        datetime.strptime(back_8, '%Y%m%d')
                        return {
                            'date': back_8,
                            'confidence': 0.6,
                            'format': f'back_8_from_{seq}',
                            'issues': [f"使用了{seq}的后8位: {back_8}"]
                        }
                    except ValueError:
                        issues.append(f"后8位{back_8}不是有效日期")
        
        # 4. 尝试组合多个数字序列
        if len(number_sequences) >= 3:
            # 可能是年-月-日分开的格式
            try:
                if len(number_sequences[0]) == 4:  # YYYY
                    year = number_sequences[0]
                    month = number_sequences[1].zfill(2)
                    day = number_sequences[2].zfill(2)
                    combined_date = year + month + day
                    datetime.strptime(combined_date, '%Y%m%d')
                    return {
                        'date': combined_date,
                        'confidence': 0.8,
                        'format': 'combined_YYYY_MM_DD',
                        'issues': [f"从分离的数字{number_sequences[:3]}组合而成"]
                    }
            except (ValueError, IndexError):
                issues.append("无法从分离的数字组合成有效日期")
        
        return {
            'date': None,
            'confidence': 0.0,
            'format': None,
            'issues': issues + [f"无法从'{date_candidate}'中提取有效日期"]
        }
    
    def fuzzy_pattern_match(self, filename: str):
        """
        对无法精确匹配的文件进行增强的模糊匹配
        使用分组件的专门匹配逻辑
        
        Args:
            filename: 文件名
            
        Returns:
            dict: 增强的模糊匹配结果
        """
        # 移除扩展名
        name_without_ext = filename.replace('.kmz', '').replace('.KMZ', '')
        
        result = {
            'is_fuzzy_match': False,
            'location_part': None,
            'middle_part': None,
            'date_part': None,
            'fuzzy_pattern_type': None,
            'confidence': 0.0,
            'issues': [],
            'component_analysis': {}
        }
        
        # 分割文件名为可能的组件
        parts = name_without_ext.split('_')
        
        # 1. 日期组件分析
        date_analysis = self.fuzzy_date_match(name_without_ext)
        result['component_analysis']['date'] = date_analysis
        
        if date_analysis['date']:
            result['date_part'] = date_analysis['date']
            result['confidence'] += date_analysis['confidence'] * 0.4
            if date_analysis['issues']:
                result['issues'].extend([f"日期: {issue}" for issue in date_analysis['issues']])
        else:
            result['issues'].append("无法识别有效日期")
        
        # 2. 中间部分（关键词）分析
        middle_analysis = self.fuzzy_middle_part_match(name_without_ext)
        result['component_analysis']['middle'] = middle_analysis
        
        if middle_analysis['pattern_type']:
            result['fuzzy_pattern_type'] = middle_analysis['pattern_type']
            result['middle_part'] = middle_analysis['pattern_type']
            result['confidence'] += middle_analysis['confidence'] * 0.4
            if middle_analysis['issues']:
                result['issues'].extend([f"关键词: {issue}" for issue in middle_analysis['issues']])
        else:
            result['issues'].append("无法识别已知的文件类型模式")
        
        # 3. 位置组件分析
        # 获取已知位置列表（从数据集中提取）
        known_locations = self.get_known_locations()
        
        # 尝试从文件名中提取候选位置
        location_candidates = self.extract_location_candidates(name_without_ext, result['date_part'], result['middle_part'])
        
        best_location_match = None
        best_location_confidence = 0.0
        
        for candidate in location_candidates:
            location_analysis = self.fuzzy_location_match(candidate, known_locations)
            result['component_analysis'][f'location_{candidate}'] = location_analysis
            
            if location_analysis['confidence'] > best_location_confidence:
                best_location_match = location_analysis
                best_location_confidence = location_analysis['confidence']
        
        if best_location_match and best_location_match['match']:
            result['location_part'] = best_location_match['match']
            result['confidence'] += best_location_confidence * 0.2
            if best_location_match['method'] != 'exact':
                result['issues'].append(f"位置使用模糊匹配: {best_location_match['method']}")
        else:
            # 如果没有匹配的已知位置，使用最可能的候选位置
            if location_candidates:
                result['location_part'] = location_candidates[0]
                result['confidence'] += 0.1
                result['issues'].append("位置为未知地名，使用提取的候选名称")
            else:
                result['issues'].append("无法提取位置信息")
        
        # 4. 最终评估
        # 只有当我们至少有日期或模式类型时才认为是成功的模糊匹配
        if result['date_part'] or result['fuzzy_pattern_type']:
            result['is_fuzzy_match'] = True
            
            # 调整置信度：必须有核心组件
            if not result['date_part']:
                result['confidence'] *= 0.5
                result['issues'].append("缺少日期信息严重影响匹配质量")
            
            if not result['fuzzy_pattern_type']:
                result['confidence'] *= 0.5
                result['issues'].append("缺少类型模式严重影响匹配质量")
            
            # 置信度评级
            if result['confidence'] >= 0.8:
                result['quality'] = 'high'
            elif result['confidence'] >= 0.6:
                result['quality'] = 'medium'
            elif result['confidence'] >= 0.4:
                result['quality'] = 'low'
            else:
                result['quality'] = 'very_low'
                result['issues'].append("匹配质量过低，建议人工检查")
        else:
            result['issues'].append("缺少核心组件，无法进行有效的模糊匹配")
        
        return result
    
    def get_known_locations(self):
        """从数据集中提取已知位置名称"""
        if not hasattr(self, '_known_locations'):
            locations = set()
            if self.df is not None:
                for _, row in self.df.iterrows():
                    filename = row['FileName']
                    # 尝试从已匹配的文件中提取位置
                    exact_match = self.exact_pattern_match(filename)
                    if exact_match['is_exact_match'] and exact_match['location_part']:
                        locations.add(exact_match['location_part'])
            
            # 添加一些常见的地理名称变体
            common_locations = [
                'mahrous', 'mahmoud', 'mahros', 'mahroos',
                'taleh', 'tale', 'tal', 'tala',
                'jizi', 'jizy', 'gizi', 'gizy',
                'group3', 'group_3', 'grp3', 'g3'
            ]
            locations.update(common_locations)
            self._known_locations = list(locations)
        
        return self._known_locations
    
    def extract_location_candidates(self, filename: str, date_part: str, middle_part: str):
        """从文件名中提取位置候选名称"""
        candidates = []
        parts = filename.split('_')
        
        # 创建要排除的词列表
        exclude_terms = set()
        if date_part:
            exclude_terms.add(date_part)
        
        # 添加常见的非位置词汇
        common_non_location = {
            'finished', 'points', 'tracks', 'and', 'plan', 'route', 'routes', 
            'gmas', 'point', 'track', 'complete', 'done', 'planning', 'planned'
        }
        
        for part in parts:
            part_clean = part.strip()
            if not part_clean:
                continue
            
            # 跳过包含日期的部分
            if date_part and date_part in part:
                continue
            
            # 跳过纯数字
            if part_clean.isdigit():
                continue
            
            # 跳过常见的非位置词汇
            if part_clean.lower() in common_non_location:
                continue
            
            # 跳过包含常见关键词的部分
            if any(term in part_clean.lower() for term in common_non_location):
                continue
            
            # 移除括号和其他特殊字符
            cleaned_part = re.sub(r'[^\w]', '', part_clean)
            if len(cleaned_part) >= 3:  # 只考虑长度>=3的候选位置
                candidates.append(cleaned_part)
        
        # 如果没有找到候选位置，尝试使用第一个部分
        if not candidates and parts:
            first_part = re.sub(r'[^\w]', '', parts[0])
            if len(first_part) >= 3:
                candidates.append(first_part)
        
        return candidates
    
    def analyze_dataset(self):
        """分析整个数据集"""
        if self.df is None:
            print("请先加载数据")
            return None
        
        analysis_results = {
            'total_files': len(self.df),
            'date_analysis': {},
            'pattern_analysis': {},
            'location_analysis': {},
            'file_size_analysis': {},
            'temporal_analysis': {},
            'detailed_files': []
        }
        
        # 添加分析列
        date_info_list = []
        pattern_info_list = []
        exact_match_list = []
        fuzzy_match_list = []
        
        for _, row in self.df.iterrows():
            filename = row['FileName']
            
            # 提取日期信息
            date_info = self.extract_date_patterns(filename)
            date_info_list.append(date_info)
            
            # 提取模式信息
            pattern_info = self.extract_name_patterns(filename)
            pattern_info_list.append(pattern_info)
            
            # 精确匹配分析
            exact_match_info = self.exact_pattern_match(filename)
            exact_match_list.append(exact_match_info)
            
            # 模糊匹配分析（仅对无法精确匹配的文件）
            if not exact_match_info['is_exact_match']:
                fuzzy_match_info = self.fuzzy_pattern_match(filename)
                fuzzy_match_list.append(fuzzy_match_info)
            else:
                # 精确匹配的文件不需要模糊匹配
                fuzzy_match_list.append({
                    'is_fuzzy_match': False,
                    'location_part': None,
                    'middle_part': None,
                    'date_part': None,
                    'fuzzy_pattern_type': None,
                    'confidence': 0.0,
                    'issues': []
                })
            
            # 详细文件信息
            file_detail = {
                'filename': filename,
                'directory': row['Directory'],
                'size': row['Size'],
                'date_info': date_info,
                'pattern_info': pattern_info,
                'exact_match_info': exact_match_info,
                'fuzzy_match_info': fuzzy_match_list[-1]
            }
            analysis_results['detailed_files'].append(file_detail)
        
        # 日期分析
        years = [info['year'] for info in date_info_list if info['year']]
        months = [info['month'] for info in date_info_list if info['month']]
        dates_8digit = [info['date_8digit'] for info in date_info_list if info['date_8digit']]
        
        analysis_results['date_analysis'] = {
            'files_with_dates': len([d for d in date_info_list if d['date_8digit'] or d['date_6digit']]),
            'year_distribution': dict(Counter(years)),
            'month_distribution': dict(Counter(months)),
            'date_range': {
                'earliest': min(dates_8digit) if dates_8digit else None,
                'latest': max(dates_8digit) if dates_8digit else None
            }
        }
        
        # 模式分析
        pattern_types = [info['pattern_type'] for info in pattern_info_list]
        location_names = [info['location_name'] for info in pattern_info_list if info['location_name']]
        exact_match_types = [info['exact_pattern_type'] for info in exact_match_list if info['is_exact_match']]
        fuzzy_match_types = [info['fuzzy_pattern_type'] for info in fuzzy_match_list if info['is_fuzzy_match']]
        
        # 统计模糊匹配的置信度
        fuzzy_confidences = [info['confidence'] for info in fuzzy_match_list if info['is_fuzzy_match']]
        avg_fuzzy_confidence = sum(fuzzy_confidences) / len(fuzzy_confidences) if fuzzy_confidences else 0
        
        # 统计无法匹配的文件
        unmatched_files = [
            i for i, (exact, fuzzy) in enumerate(zip(exact_match_list, fuzzy_match_list))
            if not exact['is_exact_match'] and not fuzzy['is_fuzzy_match']
        ]
        
        analysis_results['pattern_analysis'] = {
            'pattern_type_distribution': dict(Counter(pattern_types)),
            'finished_points_and_tracks_files': len([p for p in pattern_info_list if p['has_finished_points_and_tracks']]),
            'plan_routes_files': len([p for p in pattern_info_list if p['has_plan_routes']]),
            'exact_match_analysis': {
                'total_exact_matches': len([e for e in exact_match_list if e['is_exact_match']]),
                'exact_match_types': dict(Counter(exact_match_types)),
                'exact_match_rate': len([e for e in exact_match_list if e['is_exact_match']]) / len(exact_match_list) * 100
            },
            'fuzzy_match_analysis': {
                'total_fuzzy_matches': len([f for f in fuzzy_match_list if f['is_fuzzy_match']]),
                'fuzzy_match_types': dict(Counter(fuzzy_match_types)),
                'average_confidence': avg_fuzzy_confidence,
                'high_confidence_matches': len([f for f in fuzzy_match_list if f['is_fuzzy_match'] and f['confidence'] >= 0.7]),
                'low_confidence_matches': len([f for f in fuzzy_match_list if f['is_fuzzy_match'] and f['confidence'] < 0.5])
            },
            'total_coverage': {
                'exact_matches': len([e for e in exact_match_list if e['is_exact_match']]),
                'fuzzy_matches': len([f for f in fuzzy_match_list if f['is_fuzzy_match']]),
                'unmatched': len(unmatched_files),
                'total_coverage_rate': (len([e for e in exact_match_list if e['is_exact_match']]) + 
                                      len([f for f in fuzzy_match_list if f['is_fuzzy_match']])) / len(exact_match_list) * 100
            }
        }
        
        analysis_results['location_analysis'] = {
            'unique_locations': len(set(location_names)),
            'location_frequency': dict(Counter(location_names).most_common(20))  # 前20个最频繁的位置
        }
        
        # 文件大小分析
        sizes = self.df['Size'].astype(int)
        analysis_results['file_size_analysis'] = {
            'total_size_mb': sizes.sum() / (1024 * 1024),
            'average_size_kb': sizes.mean() / 1024,
            'size_range': {
                'min_kb': sizes.min() / 1024,
                'max_kb': sizes.max() / 1024
            }
        }
        
        # 时间分析（基于目录）
        directories = self.df['Directory'].value_counts()
        analysis_results['temporal_analysis'] = {
            'directory_distribution': directories.to_dict(),
            'most_active_periods': directories.head(10).to_dict()
        }
        
        return analysis_results
    
    def print_analysis_summary(self, results):
        """打印分析摘要"""
        if not results:
            return
        
        print("\n" + "="*80)
        print("KMZ文件数据集分析报告")
        print("="*80)
        
        print(f"\n📊 总体统计:")
        print(f"   总文件数: {results['total_files']:,}")
        print(f"   总大小: {results['file_size_analysis']['total_size_mb']:.1f} MB")
        print(f"   平均文件大小: {results['file_size_analysis']['average_size_kb']:.1f} KB")
        
        print(f"\n📅 日期分析:")
        print(f"   包含日期的文件: {results['date_analysis']['files_with_dates']}")
        print(f"   年份分布: {results['date_analysis']['year_distribution']}")
        print(f"   日期范围: {results['date_analysis']['date_range']['earliest']} ~ {results['date_analysis']['date_range']['latest']}")
        
        print(f"\n🏷️ 文件模式分析:")
        for pattern, count in results['pattern_analysis']['pattern_type_distribution'].items():
            print(f"   {pattern}: {count} 个文件")
        
        print(f"\n🎯 精确匹配分析:")
        exact_analysis = results['pattern_analysis']['exact_match_analysis']
        print(f"   精确匹配文件数: {exact_analysis['total_exact_matches']}")
        print(f"   精确匹配率: {exact_analysis['exact_match_rate']:.1f}%")
        print(f"   精确匹配类型分布:")
        for match_type, count in exact_analysis['exact_match_types'].items():
            print(f"     {match_type}: {count} 个文件")
        
        print(f"\n🔍 模糊匹配分析:")
        fuzzy_analysis = results['pattern_analysis']['fuzzy_match_analysis']
        total_coverage = results['pattern_analysis']['total_coverage']
        print(f"   模糊匹配文件数: {fuzzy_analysis['total_fuzzy_matches']}")
        print(f"   平均置信度: {fuzzy_analysis['average_confidence']:.2f}")
        print(f"   高置信度匹配 (≥0.7): {fuzzy_analysis['high_confidence_matches']} 个文件")
        print(f"   低置信度匹配 (<0.5): {fuzzy_analysis['low_confidence_matches']} 个文件")
        print(f"   模糊匹配类型分布:")
        for match_type, count in fuzzy_analysis['fuzzy_match_types'].items():
            print(f"     {match_type}: {count} 个文件")
        
        print(f"\n📈 总体覆盖率分析:")
        print(f"   精确匹配: {total_coverage['exact_matches']} 个文件")
        print(f"   模糊匹配: {total_coverage['fuzzy_matches']} 个文件")
        print(f"   无法匹配: {total_coverage['unmatched']} 个文件")
        print(f"   总覆盖率: {total_coverage['total_coverage_rate']:.1f}%")
        
        print(f"\n📍 位置分析:")
        print(f"   唯一位置数: {results['location_analysis']['unique_locations']}")
        print(f"   最频繁的位置:")
        for location, count in list(results['location_analysis']['location_frequency'].items())[:10]:
            print(f"     {location}: {count} 个文件")
        
        print(f"\n📁 时间分布分析:")
        print(f"   最活跃的时期:")
        for period, count in list(results['temporal_analysis']['most_active_periods'].items())[:10]:
            print(f"     {period}: {count} 个文件")
    
    def save_analysis_results(self, results, output_file):
        """保存分析结果到JSON文件"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            print(f"\n✅ 分析结果已保存到: {output_file}")
        except Exception as e:
            print(f"❌ 保存分析结果失败: {e}")
    
    def show_unmatched_files(self, results):
        """显示无法匹配的文件详情"""
        unmatched_files = []
        
        for file_detail in results['detailed_files']:
            exact_match = file_detail['exact_match_info']
            fuzzy_match = file_detail['fuzzy_match_info']
            
            if not exact_match['is_exact_match'] and not fuzzy_match['is_fuzzy_match']:
                unmatched_files.append({
                    'filename': file_detail['filename'],
                    'directory': file_detail['directory'],
                    'fuzzy_issues': fuzzy_match['issues']
                })
        
        if unmatched_files:
            print(f"\n❌ 无法匹配的文件 ({len(unmatched_files)}):")
            for i, file_info in enumerate(unmatched_files[:10], 1):  # 只显示前10个
                print(f"   {i}. {file_info['filename']}")
                if file_info['fuzzy_issues']:
                    print(f"      问题: {', '.join(file_info['fuzzy_issues'])}")
            
            if len(unmatched_files) > 10:
                print(f"   ... 还有 {len(unmatched_files) - 10} 个无法匹配的文件")
        else:
            print(f"\n✅ 所有文件都能够成功匹配！")
    
    def show_fuzzy_matched_files(self, results):
        """显示模糊匹配文件的详情"""
        fuzzy_matched_files = []
        
        for file_detail in results['detailed_files']:
            exact_match = file_detail['exact_match_info']
            fuzzy_match = file_detail['fuzzy_match_info']
            
            if not exact_match['is_exact_match'] and fuzzy_match['is_fuzzy_match']:
                fuzzy_matched_files.append({
                    'filename': file_detail['filename'],
                    'directory': file_detail['directory'],
                    'size': file_detail['size'],
                    'fuzzy_info': fuzzy_match
                })
        
        if fuzzy_matched_files:
            print(f"\n🔍 模糊匹配文件详情 ({len(fuzzy_matched_files)}):")
            for i, file_info in enumerate(fuzzy_matched_files, 1):
                fuzzy = file_info['fuzzy_info']
                print(f"\n   {i}. {file_info['filename']}")
                print(f"      目录: {file_info['directory']}")
                print(f"      大小: {file_info['size']/1024:.1f} KB")
                print(f"      匹配类型: {fuzzy['fuzzy_pattern_type']}")
                print(f"      置信度: {fuzzy['confidence']:.2f}")
                print(f"      位置部分: {fuzzy['location_part']}")
                print(f"      中间部分: {fuzzy['middle_part']}")
                print(f"      日期部分: {fuzzy['date_part']}")
                if fuzzy['issues']:
                    print(f"      问题: {', '.join(fuzzy['issues'])}")
        else:
            print(f"\n✅ 没有需要模糊匹配的文件！")
    
    def extract_finished_points_files(self, results):
        """提取符合'finished_points_and_tracks'模式的文件"""
        finished_points_files = []
        
        for file_detail in results['detailed_files']:
            if file_detail['pattern_info']['has_finished_points_and_tracks']:
                finished_points_files.append({
                    'filename': file_detail['filename'],
                    'location': file_detail['pattern_info']['location_name'],
                    'date': file_detail['date_info']['date_8digit'],
                    'directory': file_detail['directory']
                })
        
        print(f"\n🎯 符合'finished_points_and_tracks'模式的文件: {len(finished_points_files)}")
        
        # 按位置分组
        by_location = defaultdict(list)
        for file in finished_points_files:
            by_location[file['location']].append(file)
        
        print(f"   涉及位置数: {len(by_location)}")
        for location, files in sorted(by_location.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
            print(f"     {location}: {len(files)} 个文件")
        
        return finished_points_files

def main():
    """主函数"""
    csv_file = "D:\\MacBook\\MacBookDocument\\SourceCode\\GitHub_Public_Repos\\GMAS_Script\\DailyDataCollection\\core\\utils\\matcher\\string_matching\\tests\\test_data\\kmz_filename\\kmz_files_dataset.csv"
    
    # 创建分析器
    analyzer = KMZDatasetAnalyzer(csv_file)
    
    # 加载数据
    if not analyzer.load_data():
        return
    
    # 执行分析
    print("正在分析KMZ文件数据集...")
    results = analyzer.analyze_dataset()
    
    if results:
        # 打印摘要
        analyzer.print_analysis_summary(results)
        
        # 提取finished_points文件
        finished_points_files = analyzer.extract_finished_points_files(results)
        
        # 保存完整分析结果
        output_file = "D:\\MacBook\\MacBookDocument\\SourceCode\\GitHub_Public_Repos\\GMAS_Script\\DailyDataCollection\\core\\utils\\matcher\\string_matching\\tests\\test_data\\kmz_filename\\kmz_filename_kmz_analysis_results.json"
        analyzer.save_analysis_results(results, output_file)
        
        # 保存finished_points文件列表
        finished_points_file = "D:\\MacBook\\MacBookDocument\\SourceCode\\GitHub_Public_Repos\\GMAS_Script\\DailyDataCollection\\core\\utils\\matcher\\string_matching\\tests\\test_data\\kmz_filename\\finished_points_files.json"
        try:
            with open(finished_points_file, 'w', encoding='utf-8') as f:
                json.dump(finished_points_files, f, ensure_ascii=False, indent=2)
            print(f"✅ finished_points文件列表已保存到: {finished_points_file}")
        except Exception as e:
            print(f"❌ 保存finished_points文件列表失败: {e}")
        
        # 显示无法匹配的文件
        analyzer.show_unmatched_files(results)
        
        # 显示模糊匹配文件的详情
        analyzer.show_fuzzy_matched_files(results)

if __name__ == "__main__":
    main()
