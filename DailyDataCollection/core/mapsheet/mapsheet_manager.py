"""
图幅管理器模块

提供统一的图幅信息管理、初始化和配置功能，避免代码重复和配置不一致
"""

import logging
from typing import Dict, List, Any, Optional, Type, TYPE_CHECKING
import pandas as pd
from pathlib import Path
from datetime import datetime, date
from dataclasses import dataclass, field
import json

from config.config_manager import ConfigManager

if TYPE_CHECKING:
    from ..data_models.date_types import DateType
    from .mapsheet_daily import MapsheetDailyFile

# 创建 logger 实例
logger = logging.getLogger('Mapsheet Manager')
logger.setLevel(logging.ERROR)


@dataclass
class MapsheetHistoricalData:
    """图幅历史数据模型"""
    sequence: float
    roman_name: str
    # 日期到完成点数的映射
    daily_completions: Dict[str, int] = field(default_factory=dict)
    # 累计完成点数
    total_completed: int = 0
    # 目标点数
    target_total: int = 750
    # 完成百分比
    completion_percentage: float = 0.0
    # 最后更新日期
    last_updated: Optional[str] = None
    
    def update_completion(self, date_str: str, points: int):
        """更新某日完成点数"""
        self.daily_completions[date_str] = points
        self.total_completed = sum(self.daily_completions.values())
        self.completion_percentage = (self.total_completed / self.target_total * 100) if self.target_total > 0 else 0
        self.last_updated = date_str
    
    def get_daily_completion(self, date_str: str) -> int:
        """获取某日完成点数"""
        return self.daily_completions.get(date_str, 0)
    
    def get_period_completion(self, start_date: str, end_date: str) -> int:
        """获取时间段内的完成点数"""
        total = 0
        for date_str, points in self.daily_completions.items():
            if start_date <= date_str <= end_date:
                total += points
        return total


class MapsheetManager:
    """
    增强版图幅管理器 - 提供统一的图幅信息管理、初始化和历史数据管理功能
    
    该类负责：
    1. 从配置文件读取图幅信息
    2. 提供统一的图幅数据访问接口
    3. 管理图幅序号范围和映射关系
    4. 为收集模块和监控模块提供一致的初始化逻辑
    5. 管理图幅历史完成数据和统计信息
    """
    
    _instance: Optional['MapsheetManager'] = None
    _maps_info: Dict[float, Dict[str, Any]] = {}
    _historical_data: Dict[float, MapsheetHistoricalData] = {}
    _config_manager: Optional[ConfigManager] = None
    _initialized: bool = False
    _history_cache_file: Path = Path("cache/mapsheet_history.json")
    
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
            self._load_historical_data()
            self._initialized = True
    
    def _load_mapsheet_info(self) -> None:
        """加载图幅信息"""
        try:
            config = self._config_manager.get_all_config()
            sheet_names_file = self._config_manager.get('file_paths.sheet_names_file')
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
                    'Leaders_zh': row['Leaders_zh'],
                    'Leaders_en': row['Leaders_en'],
                    # 图幅坐标范围
                    # 'Min X': row['Min X'],
                    # 'Max X': row['Max X'],
                    # 'Min Y': row['Min Y'],
                    # 'Max Y': row['Max Y'],
                    'Target Total': row['Target Total'],
                }
                for _, row in sorted_df.iterrows()
            }
            
            # 初始化历史数据结构
            for seq, info in self._maps_info.items():
                if seq not in self._historical_data:
                    self._historical_data[seq] = MapsheetHistoricalData(
                        sequence=seq,
                        roman_name=info['Roman Name'],
                        target_total=int(info.get('Target Total', 750))
                    )
            
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
        config = self._config_manager.get_all_config()
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
    
    def get_mapsheet_target(self, roman_name: str) -> int:
        """
        根据罗马名称获取图幅的目标点数
        
        Args:
            roman_name: 图幅的罗马名称
            
        Returns:
            int: 目标点数，如果没有找到或配置错误则返回默认值750
        """
        try:
            for info in self._maps_info.values():
                if info.get('Roman Name') == roman_name:
                    target = info.get('Target Total')
                    if target and isinstance(target, (int, float)) and target > 0:
                        return int(target)
                    break
            
            # 如果没有找到或目标值无效，返回默认值
            logger.warning(f"图幅 {roman_name} 没有有效的目标点数配置，使用默认值3000")
            return 750
            
        except Exception as e:
            logger.error(f"获取图幅 {roman_name} 目标点数失败: {e}")
            return 750
    
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
    
    def _load_historical_data(self) -> None:
        """加载历史完成数据"""
        try:
            # 1. 从缓存文件加载（如果存在）
            if self._history_cache_file.exists():
                self._load_from_cache()
            
            # 2. 从Excel文件加载最新数据
            self._load_from_excel_files()
            
            # 3. 保存到缓存
            self._save_to_cache()
            
            # 4. 生成统计报告
            self._generate_statistics_report()
            
        except Exception as e:
            logger.error(f"加载历史数据失败: {e}")
    
    def _load_from_excel_files(self) -> None:
        """从Excel文件加载历史完成数据"""
        try:
            config = self._config_manager.get_all_config()
            # 使用系统配置中的workspace作为数据目录
            workspace_path = self._config_manager.get('system.workspace')
            data_dir = Path(workspace_path)
            
            if not data_dir.exists():
                logger.warning(f"数据目录不存在: {data_dir}")
                return
            
            # 扫描所有Excel文件
            excel_files = list(data_dir.glob("*.xlsx"))
            logger.info(f"在 {data_dir} 找到 {len(excel_files)} 个Excel文件")
            
            for excel_file in excel_files:
                # 从文件名提取日期（假设格式为 YYYYMMDD_*.xlsx）
                file_name = excel_file.stem
                date_str = file_name.split('_')[0] if '_' in file_name else None
                
                if not date_str or len(date_str) != 8:
                    continue
                
                # 格式化日期字符串
                formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                
                try:
                    # 读取Excel文件
                    df = pd.read_excel(excel_file, sheet_name=None, engine='openpyxl')
                    
                    # 遍历所有工作表（每个工作表代表一个图幅）
                    for sheet_name, sheet_df in df.items():
                        # 通过罗马名称匹配图幅
                        for seq, info in self._maps_info.items():
                            if info['Roman Name'] == sheet_name:
                                # 计算该图幅在该日期的完成点数
                                if 'Status' in sheet_df.columns:
                                    completed_points = len(sheet_df[sheet_df['Status'] == 'Completed'])
                                    
                                    # 更新历史数据
                                    if seq in self._historical_data:
                                        self._historical_data[seq].update_completion(
                                            formatted_date, 
                                            completed_points
                                        )
                                break
                    
                except Exception as e:
                    logger.warning(f"处理文件 {excel_file} 失败: {e}")
                    continue
            
            logger.info(f"成功加载历史数据")
            
        except Exception as e:
            logger.error(f"从Excel加载历史数据失败: {e}")
    
    def _load_from_cache(self) -> None:
        """从缓存文件加载历史数据"""
        try:
            with open(self._history_cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                
            for seq_str, data in cache_data.items():
                seq = float(seq_str)
                if seq in self._maps_info:
                    self._historical_data[seq] = MapsheetHistoricalData(
                        sequence=seq,
                        roman_name=data['roman_name'],
                        daily_completions=data['daily_completions'],
                        total_completed=data['total_completed'],
                        target_total=data['target_total'],
                        completion_percentage=data['completion_percentage'],
                        last_updated=data.get('last_updated')
                    )
            
            logger.info(f"从缓存加载了 {len(self._historical_data)} 个图幅的历史数据")
            
        except Exception as e:
            logger.warning(f"加载缓存失败: {e}")
    
    def _save_to_cache(self) -> None:
        """保存历史数据到缓存文件"""
        try:
            # 确保缓存目录存在
            self._history_cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            cache_data = {}
            for seq, hist_data in self._historical_data.items():
                cache_data[str(seq)] = {
                    'roman_name': hist_data.roman_name,
                    'daily_completions': hist_data.daily_completions,
                    'total_completed': hist_data.total_completed,
                    'target_total': hist_data.target_total,
                    'completion_percentage': hist_data.completion_percentage,
                    'last_updated': hist_data.last_updated
                }
            
            with open(self._history_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"历史数据已保存到缓存")
            
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
    
    def _generate_statistics_report(self) -> None:
        """生成统计报告"""
        total_target = sum(h.target_total for h in self._historical_data.values())
        total_completed = sum(h.total_completed for h in self._historical_data.values())
        overall_percentage = (total_completed / total_target * 100) if total_target > 0 else 0
        
        # 找出进度最快和最慢的图幅
        sorted_by_progress = sorted(
            self._historical_data.values(), 
            key=lambda x: x.completion_percentage, 
            reverse=True
        )
        
        top_3 = sorted_by_progress[:3] if len(sorted_by_progress) >= 3 else sorted_by_progress
        bottom_3 = sorted_by_progress[-3:] if len(sorted_by_progress) >= 3 else []
        
        logger.info(f"""
        ========== 图幅完成情况统计 ==========
        总目标点数: {total_target:,}
        总完成点数: {total_completed:,}
        整体完成率: {overall_percentage:.2f}%
        
        进度最快的图幅:
        {self._format_progress_list(top_3)}
        
        进度最慢的图幅:
        {self._format_progress_list(bottom_3)}
        =====================================
        """)
    
    def _format_progress_list(self, mapsheets: List[MapsheetHistoricalData]) -> str:
        """格式化进度列表"""
        lines = []
        for ms in mapsheets:
            lines.append(
                f"  - {ms.roman_name}: {ms.total_completed}/{ms.target_total} "
                f"({ms.completion_percentage:.1f}%)"
            )
        return '\n'.join(lines)
    
    # 历史数据访问方法
    def get_historical_data(self, sequence: float) -> Optional[MapsheetHistoricalData]:
        """获取指定图幅的历史数据"""
        return self._historical_data.get(sequence)
    
    def get_daily_completion(self, sequence: float, date_str: str) -> int:
        """获取指定图幅在指定日期的完成点数"""
        hist_data = self._historical_data.get(sequence)
        return hist_data.get_daily_completion(date_str) if hist_data else 0
    
    def get_total_completion(self, sequence: float) -> int:
        """获取指定图幅的累计完成点数"""
        hist_data = self._historical_data.get(sequence)
        return hist_data.total_completed if hist_data else 0
    
    def get_completion_percentage(self, sequence: float) -> float:
        """获取指定图幅的完成百分比"""
        hist_data = self._historical_data.get(sequence)
        return hist_data.completion_percentage if hist_data else 0.0
    
    def get_all_historical_data(self) -> Dict[float, MapsheetHistoricalData]:
        """获取所有图幅的历史数据"""
        return self._historical_data.copy()
    
    def update_historical_data(self, sequence: float, date_str: str, points: int) -> bool:
        """更新历史数据"""
        if sequence in self._historical_data:
            self._historical_data[sequence].update_completion(date_str, points)
            self._save_to_cache()  # 自动保存
            return True
        return False
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """获取进度摘要"""
        total_target = sum(h.target_total for h in self._historical_data.values())
        total_completed = sum(h.total_completed for h in self._historical_data.values())
        
        # 按完成率分组
        progress_groups = {
            'completed': [],     # 100%
            'high': [],         # 75-99%
            'medium': [],       # 50-74%
            'low': [],          # 25-49%
            'very_low': []      # 0-24%
        }
        
        for seq, hist_data in self._historical_data.items():
            info = self._maps_info.get(seq, {})
            data = {
                'sequence': seq,
                'roman_name': hist_data.roman_name,
                'team_number': info.get('Team Number'),
                'completed': hist_data.total_completed,
                'target': hist_data.target_total,
                'percentage': hist_data.completion_percentage
            }
            
            if hist_data.completion_percentage >= 100:
                progress_groups['completed'].append(data)
            elif hist_data.completion_percentage >= 75:
                progress_groups['high'].append(data)
            elif hist_data.completion_percentage >= 50:
                progress_groups['medium'].append(data)
            elif hist_data.completion_percentage >= 25:
                progress_groups['low'].append(data)
            else:
                progress_groups['very_low'].append(data)
        
        return {
            'total_target': total_target,
            'total_completed': total_completed,
            'overall_percentage': (total_completed / total_target * 100) if total_target > 0 else 0,
            'progress_groups': progress_groups,
            'last_updated': max(
                (h.last_updated for h in self._historical_data.values() if h.last_updated),
                default=None
            )
        }


# 延迟创建全局实例 - 避免模块导入时的初始化问题
_mapsheet_manager_instance = None

def get_mapsheet_manager() -> 'MapsheetManager':
    """获取图幅管理器的全局实例（延迟创建）"""
    global _mapsheet_manager_instance
    if _mapsheet_manager_instance is None:
        _mapsheet_manager_instance = MapsheetManager()
    return _mapsheet_manager_instance

# 向后兼容的属性访问
class _MapsheetManagerProxy:
    """图幅管理器代理，提供向后兼容的属性访问"""
    def __getattr__(self, name):
        return getattr(get_mapsheet_manager(), name)
    
    def __call__(self, *args, **kwargs):
        return get_mapsheet_manager()(*args, **kwargs)

# 保持向后兼容性
mapsheet_manager = _MapsheetManagerProxy()
