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
        """从Excel文件加载历史完成数据 - 使用统一的数据连接器"""
        try:
            # 使用新位置的数据连接器
            from ..data_connectors.excel_data_connector import ExcelDataConnector
            from ..data_models.date_types import DateType
            from datetime import datetime, timedelta
            
            # 创建数据连接器实例
            connector = ExcelDataConnector()
            
            # 检查连接状态
            status = connector.get_connection_status()
            if not status['excel_file']['exists']:
                logger.warning(f"统一Excel文件不存在: {status['excel_file']['path']}")
                # 回退到传统扫描方法
                self._load_from_workspace_files()
                return
            
            # 加载Excel数据
            if not connector.load_excel_data():
                logger.error("无法加载统一Excel数据")
                self._load_from_workspace_files()
                return
            
            # 1. 获取项目时间线
            timeline = connector.get_project_timeline()
            if timeline and timeline.get('start_date'):
                start_date = DateType(timeline['start_date'])
                end_date = DateType(timeline.get('latest_date', datetime.now()))
            else:
                # 默认获取最近90天
                end_date = DateType(datetime.now())
                start_date = DateType(datetime.now() - timedelta(days=90))
            
            # 2. 提取图幅历史数据
            mapsheet_historical_data = connector.extract_mapsheet_historical_data(start_date, end_date)
            
            if not mapsheet_historical_data:
                logger.warning("未能从统一Excel文件提取历史数据")
                self._load_from_workspace_files()
                return
            
            # 3. 提取图幅元数据（包含目标点数）
            mapsheet_metadata = connector.extract_mapsheet_metadata()
            
            # 4. 更新本地历史数据结构
            updated_count = 0
            for mapsheet_name, daily_records in mapsheet_historical_data.items():
                # 查找对应的图幅序号
                sequence = self._find_sequence_by_identifier(mapsheet_name)
                
                if sequence is None:
                    logger.debug(f"未找到匹配的图幅: {mapsheet_name}")
                    continue
                
                if sequence not in self._historical_data:
                    # 创建新的历史数据对象
                    self._historical_data[sequence] = MapsheetHistoricalData(
                        sequence=sequence,
                        roman_name=self._maps_info[sequence]['Roman Name'],
                        target_total=self._maps_info[sequence].get('Target Total', 750)
                    )
                
                # 清空旧数据，使用新数据
                hist_data = self._historical_data[sequence]
                hist_data.daily_completions.clear()
                
                # 处理每日记录
                prev_cumulative = 0
                for record in sorted(daily_records, key=lambda x: x['date']):
                    date_str = record['date']
                    
                    # 优先使用 daily_points，如果没有则从 cumulative_points 计算
                    if 'daily_points' in record and record['daily_points'] is not None:
                        daily_points = record['daily_points']
                    elif 'cumulative_points' in record and record['cumulative_points'] is not None:
                        # 从累计值计算当日增量
                        cumulative = record['cumulative_points']
                        daily_points = cumulative - prev_cumulative
                        prev_cumulative = cumulative
                    else:
                        continue
                    
                    # 更新历史数据
                    hist_data.update_completion(date_str, daily_points)
                
                updated_count += 1
            
            # 5. 从元数据更新目标点数
            for mapsheet_id, metadata in mapsheet_metadata.items():
                sequence = self._find_sequence_by_identifier(mapsheet_id)
                
                if sequence and sequence in self._historical_data:
                    target = metadata.get('target_points', 750)
                    if target > 0 and target != self._historical_data[sequence].target_total:
                        self._historical_data[sequence].target_total = int(target)
                        # 重新计算完成百分比
                        hist_data = self._historical_data[sequence]
                        hist_data.completion_percentage = (
                            hist_data.total_completed / hist_data.target_total * 100
                        ) if hist_data.target_total > 0 else 0
            
            logger.info(f"成功从统一Excel文件加载历史数据，更新了 {updated_count}/{len(self._maps_info)} 个图幅")
            
            # 6. 显示数据质量信息
            data_quality = self._assess_data_quality()
            logger.info(f"数据质量评估: 覆盖率={data_quality['coverage']:.1f}%, "
                    f"完整性={data_quality['completeness']:.1f}%")
            
        except ImportError as e:
            logger.error(f"无法导入ExcelDataConnector: {e}")
            # 回退到传统方法
            self._load_from_workspace_files()
        except Exception as e:
            logger.error(f"使用数据连接器加载失败: {e}")
            # 回退到传统方法
            self._load_from_workspace_files()

    def _find_sequence_by_identifier(self, identifier: str) -> Optional[float]:
        """通过各种标识符查找图幅序号"""
        if not identifier:
            return None
        
        identifier = str(identifier).strip()
        
        for seq, info in self._maps_info.items():
            # 1. 尝试直接序号匹配
            try:
                if float(identifier) == seq:
                    return seq
            except ValueError:
                pass
            
            # 2. 罗马名称匹配
            if info['Roman Name'] == identifier:
                return seq
            
            # 3. 文件名匹配（精确或部分）
            if info['File Name'] == identifier or identifier in info['File Name']:
                return seq
            
            # 4. Sheet ID 匹配
            if info.get('Sheet ID') == identifier:
                return seq
            
            # 5. 阿拉伯名称匹配
            if info.get('Arabic Name') == identifier:
                return seq
            
            # 6. 团队编号匹配
            if info.get('Team Number') == identifier:
                return seq
        
        return None

    def _load_from_workspace_files(self) -> None:
        """从工作空间的每日Excel文件加载（传统方法，作为备用）"""
        logger.info("使用传统方法从工作空间扫描Excel文件")
        
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
            logger.info(f"传统方法：在 {data_dir} 找到 {len(excel_files)} 个Excel文件")
            
            if not excel_files:
                logger.warning("未找到任何Excel文件")
                return
            
            # 处理每个Excel文件
            loaded_files = 0
            for excel_file in excel_files[:10]:  # 限制处理文件数量避免过载
                try:
                    # 从文件名推断日期
                    date_str = self._extract_date_from_filename(excel_file.name)
                    if not date_str:
                        continue
                    
                    # 读取Excel文件
                    df = pd.read_excel(excel_file, sheet_name=0)
                    
                    if df.empty or len(df.columns) < 2:
                        continue
                    
                    # 处理文件数据
                    self._process_excel_file_data(df, date_str)
                    loaded_files += 1
                    
                except Exception as e:
                    logger.debug(f"处理文件 {excel_file} 失败: {e}")
                    continue
            
            logger.info(f"传统方法成功处理了 {loaded_files} 个Excel文件")
            
        except Exception as e:
            logger.error(f"传统方法加载历史数据失败: {e}")
    
    def _extract_date_from_filename(self, filename: str) -> Optional[str]:
        """从文件名提取日期"""
        import re
        
        # 尝试匹配各种日期格式
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{4}\d{2}\d{2})',    # YYYYMMDD
            r'(\d{2}-\d{2}-\d{4})',  # DD-MM-YYYY
            r'(\d{2}\d{2}\d{4})'     # DDMMYYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, filename)
            if match:
                date_part = match.group(1)
                try:
                    # 标准化为 YYYY-MM-DD 格式
                    if len(date_part) == 8:  # YYYYMMDD
                        return f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
                    elif '-' in date_part:
                        parts = date_part.split('-')
                        if len(parts[0]) == 4:  # YYYY-MM-DD
                            return date_part
                        else:  # DD-MM-YYYY
                            return f"{parts[2]}-{parts[1]}-{parts[0]}"
                except:
                    continue
        
        return None
    
    def _process_excel_file_data(self, df: pd.DataFrame, date_str: str) -> None:
        """处理单个Excel文件的数据"""
        try:
            # 假设第一列是图幅名称，第二列是完成点数
            for _, row in df.iterrows():
                mapsheet_name = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                points_value = row.iloc[1] if len(row) > 1 else 0
                
                if not mapsheet_name:
                    continue
                
                # 转换点数
                try:
                    points = int(float(points_value)) if pd.notna(points_value) else 0
                    if points < 0:
                        points = 0
                except (ValueError, TypeError):
                    points = 0
                
                if points == 0:
                    continue
                
                # 查找对应的图幅序号
                sequence = self._find_sequence_by_identifier(mapsheet_name)
                if not sequence:
                    continue
                
                # 创建或更新历史数据
                if sequence not in self._historical_data:
                    self._historical_data[sequence] = MapsheetHistoricalData(
                        sequence=sequence,
                        roman_name=self._maps_info[sequence]['Roman Name'],
                        target_total=self._maps_info[sequence].get('Target Total', 750)
                    )
                
                # 更新该日期的完成数据
                self._historical_data[sequence].update_completion(date_str, points)
                
        except Exception as e:
            logger.debug(f"处理Excel文件数据失败: {e}")

    def _assess_data_quality(self) -> Dict[str, float]:
        """评估数据质量"""
        total_mapsheets = len(self._maps_info)
        mapsheets_with_data = sum(1 for h in self._historical_data.values() if h.daily_completions)
        
        total_days = 0
        total_expected_days = 0
        
        for hist_data in self._historical_data.values():
            if hist_data.daily_completions and hist_data.last_updated:
                # 计算应有的天数
                dates = sorted(hist_data.daily_completions.keys())
                if len(dates) >= 2:
                    first_date = datetime.strptime(dates[0], '%Y-%m-%d')
                    last_date = datetime.strptime(dates[-1], '%Y-%m-%d')
                    expected_days = (last_date - first_date).days + 1
                    actual_days = len(dates)
                    
                    total_expected_days += expected_days
                    total_days += actual_days
        
        coverage = (mapsheets_with_data / total_mapsheets * 100) if total_mapsheets > 0 else 0
        completeness = (total_days / total_expected_days * 100) if total_expected_days > 0 else 0
        
        return {
            'coverage': coverage,      # 有数据的图幅百分比
            'completeness': completeness  # 数据完整性百分比
        }

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
