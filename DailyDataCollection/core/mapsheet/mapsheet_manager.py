"""
图幅管理器模块

提供统一的图幅信息管理、初始化和配置功能，避免代码重复和配置不一致
"""

import logging
from typing import Dict, List, Any, Optional, Type, TYPE_CHECKING
import pandas as pd
from pathlib import Path

from config.config_manager import ConfigManager

if TYPE_CHECKING:
    from ..data_models.date_types import DateType
    from .mapsheet_daily import MapsheetDailyFile

# 创建 logger 实例
logger = logging.getLogger('Mapsheet Manager')
logger.setLevel(logging.ERROR)


class MapsheetManager:
    """
    图幅管理器 - 提供统一的图幅信息管理和初始化功能
    
    该类负责：
    1. 从配置文件读取图幅信息
    2. 提供统一的图幅数据访问接口
    3. 管理图幅序号范围和映射关系
    4. 为收集模块和监控模块提供一致的初始化逻辑
    """
    
    _instance: Optional['MapsheetManager'] = None
    _maps_info: Dict[float, Dict[str, Any]] = {}
    _config_manager: Optional[ConfigManager] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'MapsheetManager':
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(MapsheetManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化图幅管理器"""
        if not self._initialized:
            self._config_manager = ConfigManager()
            self._load_mapsheet_info()
            self._initialized = True
    
    def _load_mapsheet_info(self) -> None:
        """加载图幅信息"""
        try:
            config = self._config_manager.get_config()
            sheet_names_file = self._config_manager.get_resolved_path('sheet_names_file')
            sequence_min = config['mapsheet']['sequence_min']
            sequence_max = config['mapsheet']['sequence_max']
            
            # 使用UTF-8编码读取Excel文件
            df = pd.read_excel(sheet_names_file, sheet_name="Sheet1", header=0, engine='openpyxl')
            
            # 确保DataFrame中的字符串列使用UTF-8编码
            for col in df.select_dtypes(include=['object']).columns:
                try:
                    df[col] = df[col].astype(str).apply(
                        lambda x: x.encode('utf-8').decode('utf-8') if isinstance(x, str) else x
                    )
                except (UnicodeDecodeError, UnicodeEncodeError):
                    pass
            
            # 筛选序号范围内的图幅
            filtered_df = df[(df['Sequence'] >= sequence_min) & (df['Sequence'] <= sequence_max)]
            
            # 验证数据完整性
            expected_count = sequence_max - sequence_min + 1
            if len(filtered_df) != expected_count:
                raise ValueError(f"图幅数量不匹配: 期望{expected_count}个，实际{len(filtered_df)}个")
            
            if filtered_df['Sequence'].duplicated().any():
                raise ValueError("图幅信息表中存在重复的图幅序号")
            
            # 按序号排序并构建字典
            sorted_df = filtered_df.sort_values(by='Sequence')
            self._maps_info = {
                float(row['Sequence']): {
                    'Sheet ID': row['Alternative sheet ID'],  # Excel列名映射
                    'Group': row['Group'],
                    'File Name': row['File Name'],
                    'Arabic Name': row['Arabic'],
                    'Roman Name': row['Roman Name'],
                    'Latin Name': row['Latin Name'],
                    'Team Number': row['Team Number'],
                    'Leaders': row['Leaders'],
                }
                for _, row in sorted_df.iterrows()
            }
            
            logger.info(f"成功加载{len(self._maps_info)}个图幅信息")
            
        except Exception as e:
            logger.error(f"加载图幅信息失败: {e}")
            self._maps_info = {}
            raise
    
    @property
    def maps_info(self) -> Dict[float, Dict[str, Any]]:
        """获取图幅信息字典"""
        return self._maps_info.copy()
    
    @property
    def sequence_range(self) -> tuple[int, int]:
        """获取图幅序号范围"""
        config = self._config_manager.get_config()
        return (config['mapsheet']['sequence_min'], config['mapsheet']['sequence_max'])
    
    @property
    def team_number_range(self) -> tuple[int, int]:
        """获取团队编号范围 - 从实际数据中计算"""
        team_numbers = []
        for info in self._maps_info.values():
            team_num = info.get('Team Number')
            if team_num and str(team_num).startswith('Team'):
                try:
                    num = int(str(team_num).split()[1])
                    team_numbers.append(num)
                except (IndexError, ValueError):
                    continue
        
        if team_numbers:
            return (min(team_numbers), max(team_numbers))
        else:
            # 如果没有找到团队编号，返回默认范围
            logger.warning("未找到有效的团队编号，使用默认范围")
            return (316, 326)
    
    def get_mapsheet_info(self, sequence: float) -> Optional[Dict[str, Any]]:
        """
        根据序号获取图幅信息
        
        Args:
            sequence: 图幅序号
            
        Returns:
            图幅信息字典，如果不存在则返回None
        """
        return self._maps_info.get(sequence)
    
    def get_mapsheet_filenames(self) -> List[str]:
        """获取所有图幅文件名列表"""
        return [info['File Name'] for info in self._maps_info.values()]
    
    def get_mapsheet_by_team_number(self, team_number: str) -> Optional[Dict[str, Any]]:
        """
        根据团队编号获取图幅信息
        
        Args:
            team_number: 团队编号 (如 "Team 316")
            
        Returns:
            图幅信息字典，如果不存在则返回None
        """
        for info in self._maps_info.values():
            if info.get('Team Number') == team_number:
                return info
        return None
    
    def create_mapsheet_collection(
        self, 
        mapsheet_class: Type['MapsheetDailyFile'],
        current_date: 'DateType'
    ) -> List['MapsheetDailyFile']:
        """
        创建图幅对象集合
        
        Args:
            mapsheet_class: 图幅类（MapsheetDailyFile或其子类）
            current_date: 当前日期
            
        Returns:
            图幅对象列表
        """
        mapsheets = []
        sequence_min, sequence_max = self.sequence_range
        
        for map_index in range(sequence_min, sequence_max + 1):
            map_key = float(map_index)
            if map_key in self._maps_info:
                mapsheet_filename = self._maps_info[map_key]['File Name']
                mapsheet = mapsheet_class(mapsheet_filename, current_date)
                mapsheets.append(mapsheet)
        
        return mapsheets
    
    def validate_configuration(self) -> bool:
        """
        验证配置一致性
        
        Returns:
            True如果配置一致，否则False
        """
        try:
            sequence_min, sequence_max = self.sequence_range
            team_min, team_max = self.team_number_range
            
            # 验证序号范围和图幅数量一致性
            expected_count = sequence_max - sequence_min + 1
            actual_count = len(self._maps_info)
            
            if expected_count != actual_count:
                logger.error(f"图幅数量不一致: 配置期望{expected_count}个，实际{actual_count}个")
                return False
            
            # 验证团队编号范围和图幅数量一致性
            team_count = team_max - team_min + 1
            if expected_count != team_count:
                logger.error(f"团队数量不一致: 图幅{expected_count}个，团队{team_count}个")
                return False
            
            # 验证序号映射关系
            for i, (seq, info) in enumerate(sorted(self._maps_info.items())):
                expected_seq = sequence_min + i
                expected_team = f"Team {team_min + i}"
                
                if seq != expected_seq:
                    logger.error(f"序号不连续: 期望{expected_seq}，实际{seq}")
                    return False
                
                if info.get('Team Number') != expected_team:
                    logger.error(f"团队编号不匹配: 序号{seq}期望{expected_team}，实际{info.get('Team Number')}")
                    return False
            
            logger.info("配置验证通过")
            return True
            
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取图幅管理器摘要信息
        
        Returns:
            包含统计信息的字典
        """
        sequence_min, sequence_max = self.sequence_range
        team_min, team_max = self.team_number_range
        
        return {
            'total_mapsheets': len(self._maps_info),
            'sequence_range': f"{sequence_min}-{sequence_max}",
            'team_range': f"{team_min}-{team_max}",
            'mapsheet_files': self.get_mapsheet_filenames(),
            'configuration_valid': self.validate_configuration()
        }


# 全局实例
mapsheet_manager = MapsheetManager()
