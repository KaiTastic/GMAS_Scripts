#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实Excel数据连接器

专门处理GMAS真实Excel文件结构的数据连接器
数据结构：行=团队，列=日期，数据=每日观测点数
"""

import logging
import pandas as pd
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np

# 导入项目模块
from core.data_models.date_types import DateType
from config.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class RealExcelDataConnector:
    """真实Excel数据连接器，处理GMAS实际的Excel文件格式"""
    
    def __init__(self):
        """初始化真实Excel数据连接器"""
        self.config_manager = ConfigManager()
        self.excel_file_path = self._get_excel_file_path()
        self.excel_data = None
        self.date_columns = []  # 存储日期列
        self.team_rows = []     # 存储团队行信息
        
    def _get_excel_file_path(self) -> str:
        """获取Excel文件路径"""
        try:
            # 从配置文件获取路径
            stats_config = self.config_manager.get('reports.statistics')
            if stats_config and 'daily_details_file' in stats_config:
                file_path_template = stats_config['daily_details_file']
                context = {'stats_config': stats_config}
                excel_path = self.config_manager.resolve_path_template(file_path_template, context)
                logger.info(f"Excel文件路径: {excel_path}")
                return excel_path
            else:
                # 使用默认路径
                workspace = self.config_manager.get('system.workspace', 'D:\\RouteDesign')
                filename = "Daily_statistics_details_for_Group_3.2.xlsx"
                excel_path = os.path.join(workspace, filename)
                logger.warning(f"配置中未找到Excel路径，使用默认路径: {excel_path}")
                return excel_path
                
        except Exception as e:
            # 异常情况使用默认路径
            workspace = self.config_manager.get('system.workspace', 'D:\\RouteDesign')
            filename = "Daily_statistics_details_for_Group_3.2.xlsx"
            excel_path = os.path.join(workspace, filename)
            logger.error(f"获取Excel路径时发生错误: {e}，使用默认路径: {excel_path}")
            return excel_path
    
    def load_excel_data(self) -> bool:
        """
        加载真实Excel数据
        
        Returns:
            bool: 加载是否成功
        """
        if not os.path.exists(self.excel_file_path):
            logger.error(f"Excel文件不存在: {self.excel_file_path}")
            return False
        
        try:
            # 使用pandas读取Excel，自动处理日期列名
            self.excel_data = pd.read_excel(self.excel_file_path, sheet_name='总表')
            
            # 清理数据：移除完全为空的行
            self.excel_data = self.excel_data.dropna(how='all')
            
            # 分析数据结构
            self._analyze_data_structure()
            
            logger.info(f"成功加载真实Excel数据: {self.excel_data.shape}")
            logger.info(f"找到日期列: {len(self.date_columns)} 个")
            logger.info(f"找到团队行: {len(self.team_rows)} 个")
            
            return True
                
        except Exception as e:
            logger.error(f"加载Excel数据失败: {e}")
            return False
    
    def _analyze_data_structure(self):
        """分析Excel数据结构"""
        if self.excel_data is None:
            return
        
        # 找到日期列（datetime类型的列）
        self.date_columns = []
        for col in self.excel_data.columns:
            if isinstance(col, datetime):
                self.date_columns.append(col)
        
        # 找到团队行（非空的Team No.）
        self.team_rows = []
        team_col = 'Team No.'
        
        if team_col in self.excel_data.columns:
            for idx, team_value in enumerate(self.excel_data[team_col]):
                if pd.notna(team_value) and 'Team' in str(team_value):
                    # 获取团队信息
                    team_info = {
                        'row_idx': idx,
                        'team_no': team_value,
                        'sheet_no': self.excel_data.iloc[idx]['Sheet No.'] if 'Sheet No.' in self.excel_data.columns else None,
                        'sheet_name': self.excel_data.iloc[idx]['Sheet Name'] if 'Sheet Name' in self.excel_data.columns else None,
                        'person': self.excel_data.iloc[idx]['Person in Charge'] if 'Person in Charge' in self.excel_data.columns else None
                    }
                    self.team_rows.append(team_info)
        
        logger.info(f"分析完成: {len(self.date_columns)} 个日期列, {len(self.team_rows)} 个团队")
    
    def extract_team_historical_data(self, start_date: DateType, end_date: DateType = None) -> Dict[str, List[Dict]]:
        """
        提取每个团队的历史数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期，默认为今天
            
        Returns:
            Dict[str, List[Dict]]: 每个团队的历史数据，格式为 {team_identifier: [daily_records]}
        """
        if self.excel_data is None:
            if not self.load_excel_data():
                return {}
        
        if end_date is None:
            end_date = DateType(datetime.now())
        
        try:
            team_data = {}
            
            # 筛选日期范围内的列
            valid_date_columns = []
            for col in self.date_columns:
                col_date = DateType(col)
                if start_date.date_datetime <= col_date.date_datetime <= end_date.date_datetime:
                    valid_date_columns.append(col)
            
            logger.info(f"在指定日期范围内找到 {len(valid_date_columns)} 个有效日期列")
            
            # 为每个团队提取数据
            for team_info in self.team_rows:
                team_identifier = f"{team_info['team_no']}_{team_info['sheet_no']}"
                team_data[team_identifier] = []
                
                row_idx = team_info['row_idx']
                
                # 提取该团队在每个日期的数据
                for date_col in valid_date_columns:
                    try:
                        points_value = self.excel_data.iloc[row_idx][date_col]
                        
                        points = 0
                        if pd.notna(points_value):
                            try:
                                points = int(float(points_value))
                                if points < 0:
                                    points = 0
                            except (ValueError, TypeError):
                                points = 0
                        
                        # 创建该团队在该日期的记录
                        record = {
                            'date': DateType(date_col).yyyymmdd_str,
                            'date_obj': date_col,
                            'daily_points': points,
                            'workday': date_col.weekday() < 5,
                            'team_info': team_info
                        }
                        
                        team_data[team_identifier].append(record)
                        
                    except Exception as e:
                        logger.debug(f"解析团队 {team_identifier} 在 {date_col} 的数据失败: {e}")
                        continue
            
            # 为每个团队计算累计完成量
            for team_identifier in team_data:
                records = team_data[team_identifier]
                if records:
                    # 按日期排序
                    records.sort(key=lambda x: x['date'])
                    
                    # 计算累计完成量
                    cumulative = 0
                    for record in records:
                        cumulative += record['daily_points']
                        record['cumulative_points'] = cumulative
            
            logger.info(f"成功提取 {len(team_data)} 个团队的历史数据")
            return team_data
            
        except Exception as e:
            logger.error(f"提取团队历史数据失败: {e}")
            return {}
    
    def get_team_current_status(self) -> Dict[str, Dict]:
        """
        获取每个团队的当前状态
        
        Returns:
            Dict[str, Dict]: 每个团队的当前状态信息
        """
        if self.excel_data is None:
            if not self.load_excel_data():
                return {}
        
        try:
            team_status = {}
            
            # 为每个团队计算状态
            for team_info in self.team_rows:
                team_identifier = f"{team_info['team_no']}_{team_info['sheet_no']}"
                row_idx = team_info['row_idx']
                
                try:
                    # 计算最近活动统计和总完成数
                    latest_points = 0
                    latest_date = None
                    active_days = 0
                    daily_total = 0  # 从日期列计算的实际完成总数
                    
                    for date_col in self.date_columns:
                        points_value = self.excel_data.iloc[row_idx][date_col]
                        
                        if pd.notna(points_value):
                            try:
                                points = int(float(points_value))
                                if points < 0:
                                    points = 0
                                
                                daily_total += points
                                
                                if points > 0:
                                    active_days += 1
                                    latest_points = points
                                    latest_date = date_col
                                    
                            except (ValueError, TypeError):
                                continue
                    
                    # 使用日期列的总和作为当前完成数（因为Total列为空）
                    current_points = daily_total
                    
                    # 从Adjusted Num列获取目标数
                    target_points = 0
                    if 'Adjusted \nNum' in self.excel_data.columns:
                        adjusted_value = self.excel_data.iloc[row_idx]['Adjusted \nNum']
                        if pd.notna(adjusted_value):
                            try:
                                target_points = int(float(adjusted_value))
                                if target_points < 0:
                                    target_points = 0
                            except (ValueError, TypeError):
                                target_points = 0
                    
                    # 如果没有目标数，使用当前完成数的估算值
                    if target_points == 0:
                        target_points = max(current_points * 2, 500)  # 最少500点
                    
                    team_status[team_identifier] = {
                        'team_info': team_info,
                        'current_points': current_points,  # 使用日期列总和作为当前完成数
                        'estimated_target': target_points,  # 使用Adjusted Num列作为目标数
                        'completion_rate': (current_points / target_points * 100) if target_points > 0 else 0,
                        'active_days': active_days,
                        'latest_daily_points': latest_points,
                        'latest_date': latest_date.strftime('%Y-%m-%d') if latest_date else None,
                        'avg_daily_points': (current_points / active_days) if active_days > 0 else 0,
                        'note': f'使用日期列总和({current_points})作为当前完成数，Adjusted Num({target_points})作为目标数'
                    }
                    
                except Exception as e:
                    logger.debug(f"处理团队 {team_identifier} 状态失败: {e}")
                    continue
            
            logger.info(f"获取 {len(team_status)} 个团队的当前状态")
            return team_status
            
        except Exception as e:
            logger.error(f"获取团队状态失败: {e}")
            return {}
    
    def extract_mapsheet_historical_data(self, start_date: DateType, end_date: DateType = None) -> Dict[str, List[Dict]]:
        """
        按图幅提取历史数据（团队按图幅分组）
        
        Args:
            start_date: 开始日期
            end_date: 结束日期，默认为今天
            
        Returns:
            Dict[str, List[Dict]]: 每个图幅的历史数据
        """
        # 先获取团队数据
        team_data = self.extract_team_historical_data(start_date, end_date)
        
        # 按图幅分组
        mapsheet_data = {}
        
        for team_identifier, records in team_data.items():
            if not records:
                continue
            
            # 从团队信息中获取图幅编号
            team_info = records[0]['team_info']
            sheet_no = team_info.get('sheet_no', 'Unknown')
            
            if sheet_no not in mapsheet_data:
                mapsheet_data[sheet_no] = []
            
            # 将该团队的记录添加到对应图幅
            for record in records:
                # 创建图幅记录（包含团队信息）
                mapsheet_record = record.copy()
                mapsheet_record['team_identifier'] = team_identifier
                mapsheet_data[sheet_no].append(mapsheet_record)
        
        # 对每个图幅按日期合并数据
        merged_mapsheet_data = {}
        for sheet_no, records in mapsheet_data.items():
            # 按日期分组
            date_groups = {}
            for record in records:
                date_key = record['date']
                if date_key not in date_groups:
                    date_groups[date_key] = []
                date_groups[date_key].append(record)
            
            # 为每个日期合并团队数据
            merged_records = []
            for date_key, day_records in date_groups.items():
                total_daily_points = sum(r['daily_points'] for r in day_records)
                
                merged_record = {
                    'date': date_key,
                    'date_obj': day_records[0]['date_obj'],
                    'daily_points': total_daily_points,
                    'workday': day_records[0]['workday'],
                    'team_count': len(day_records),
                    'team_details': {r['team_identifier']: r['daily_points'] for r in day_records}
                }
                
                merged_records.append(merged_record)
            
            # 按日期排序并计算累计
            merged_records.sort(key=lambda x: x['date'])
            cumulative = 0
            for record in merged_records:
                cumulative += record['daily_points']
                record['cumulative_points'] = cumulative
            
            merged_mapsheet_data[sheet_no] = merged_records
        
        logger.info(f"按图幅分组后得到 {len(merged_mapsheet_data)} 个图幅的数据")
        return merged_mapsheet_data
    
    def get_mapsheet_current_status(self) -> Dict[str, Dict]:
        """
        获取每个图幅的当前状态（团队数据合并）
        
        Returns:
            Dict[str, Dict]: 每个图幅的当前状态信息
        """
        team_status = self.get_team_current_status()
        
        # 按图幅分组
        mapsheet_status = {}
        
        for team_identifier, status in team_status.items():
            team_info = status['team_info']
            sheet_no = team_info.get('sheet_no', 'Unknown')
            
            if sheet_no not in mapsheet_status:
                mapsheet_status[sheet_no] = {
                    'current_points': 0,
                    'estimated_target': 0,
                    'active_days': 0,
                    'team_count': 0,
                    'teams': [],
                    'latest_date': None
                }
            
            # 累加数据
            mapsheet_status[sheet_no]['current_points'] += status['current_points']
            mapsheet_status[sheet_no]['estimated_target'] += status['estimated_target']
            mapsheet_status[sheet_no]['active_days'] = max(mapsheet_status[sheet_no]['active_days'], status['active_days'])
            mapsheet_status[sheet_no]['team_count'] += 1
            mapsheet_status[sheet_no]['teams'].append({
                'team_identifier': team_identifier,
                'team_info': team_info,
                'points': status['current_points']
            })
            
            # 更新最新日期
            if status['latest_date']:
                if not mapsheet_status[sheet_no]['latest_date'] or status['latest_date'] > mapsheet_status[sheet_no]['latest_date']:
                    mapsheet_status[sheet_no]['latest_date'] = status['latest_date']
        
        # 计算完成率和平均值
        for sheet_no in mapsheet_status:
            status = mapsheet_status[sheet_no]
            if status['estimated_target'] > 0:
                status['completion_rate'] = status['current_points'] / status['estimated_target'] * 100
            else:
                status['completion_rate'] = 0
            
            if status['active_days'] > 0:
                status['avg_daily_points'] = status['current_points'] / status['active_days']
            else:
                status['avg_daily_points'] = 0
        
        logger.info(f"按图幅分组后得到 {len(mapsheet_status)} 个图幅的状态")
        return mapsheet_status
