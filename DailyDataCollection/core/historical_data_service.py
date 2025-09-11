"""
历史数据服务模块

整合图幅配置和Excel数据，提供统一的历史数据访问接口
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import json
import logging

from .mapsheet.mapsheet_manager import MapsheetManager, MapsheetHistoricalData
from .data_connectors.excel_data_connector import ExcelDataConnector
from .data_models.date_types import DateType

logger = logging.getLogger(__name__)


class HistoricalDataService:
    """历史数据服务类 - 统一管理所有历史数据源"""
    
    def __init__(self):
        self.mapsheet_manager = MapsheetManager()
        self.excel_connector = ExcelDataConnector()
        self._cache_file = Path("cache/historical_data_cache.json")
        self._last_sync_time: Optional[datetime] = None
        self._sync_interval = timedelta(hours=1)  # 同步间隔
        
    def sync_historical_data(self, force: bool = False) -> bool:
        """
        同步历史数据
        
        Args:
            force: 是否强制同步
            
        Returns:
            是否成功同步
        """
        # 检查是否需要同步
        if not force and self._last_sync_time:
            if datetime.now() - self._last_sync_time < self._sync_interval:
                logger.info("数据同步间隔未到，跳过同步")
                return True
        
        try:
            # 1. 确保Excel连接器已加载数据
            if not self.excel_connector.load_excel_data():
                logger.error("无法加载Excel数据")
                return False
            
            # 2. 获取数据时间范围
            timeline = self.excel_connector.get_project_timeline()
            if timeline:
                start_date = DateType(timeline.get('start_date', datetime.now() - timedelta(days=90)))
                end_date = DateType(timeline.get('latest_date', datetime.now()))
            else:
                end_date = DateType(datetime.now())
                start_date = DateType(datetime.now() - timedelta(days=90))
            
            # 3. 提取每个图幅的历史数据
            mapsheet_historical_data = self.excel_connector.extract_mapsheet_historical_data(
                start_date, end_date
            )
            
            if not mapsheet_historical_data:
                logger.warning("未提取到任何历史数据")
                return False
            
            # 4. 更新MapsheetManager中的历史数据
            success_count = 0
            for mapsheet_name, daily_records in mapsheet_historical_data.items():
                if self._update_mapsheet_history(mapsheet_name, daily_records):
                    success_count += 1
            
            logger.info(f"成功同步 {success_count}/{len(mapsheet_historical_data)} 个图幅的历史数据")
            
            # 5. 更新目标点数
            self._sync_target_points()
            
            # 6. 保存到缓存
            self._save_cache()
            
            self._last_sync_time = datetime.now()
            return True
            
        except Exception as e:
            logger.error(f"同步历史数据失败: {e}")
            return False
    
    def _update_mapsheet_history(self, mapsheet_name: str, daily_records: List[Dict]) -> bool:
        """更新单个图幅的历史数据"""
        # 查找对应的图幅序号
        sequence = self._find_sequence_by_name(mapsheet_name)
        if not sequence:
            logger.debug(f"未找到图幅 {mapsheet_name} 的序号")
            return False
        
        # 获取或创建历史数据对象
        hist_data = self.mapsheet_manager._historical_data.get(sequence)
        if not hist_data:
            info = self.mapsheet_manager.get_mapsheet_info(sequence)
            if not info:
                return False
            
            hist_data = MapsheetHistoricalData(
                sequence=sequence,
                roman_name=info['Roman Name'],
                target_total=info.get('Target Total', 750)
            )
            self.mapsheet_manager._historical_data[sequence] = hist_data
        
        # 清空旧数据并更新
        hist_data.daily_completions.clear()
        for record in daily_records:
            date_str = record['date']
            daily_points = record.get('daily_points', 0)
            hist_data.update_completion(date_str, daily_points)
        
        return True
    
    def _find_sequence_by_name(self, name: str) -> Optional[float]:
        """通过名称查找图幅序号"""
        name = str(name).strip()
        
        for seq, info in self.mapsheet_manager.maps_info.items():
            # 尝试多种匹配方式
            if (info['Roman Name'] == name or
                info['File Name'] == name or
                name in info['File Name'] or
                info.get('Arabic Name') == name or
                info.get('Team Number') == name):
                return seq
        
        return None
    
    def _sync_target_points(self):
        """同步目标点数"""
        try:
            metadata = self.excel_connector.extract_mapsheet_metadata()
            
            for mapsheet_id, meta in metadata.items():
                sequence = self._find_sequence_by_name(mapsheet_id)
                if sequence and sequence in self.mapsheet_manager._historical_data:
                    hist_data = self.mapsheet_manager._historical_data[sequence]
                    target = meta.get('target_points', 750)
                    if target > 0:
                        hist_data.target_total = int(target)
                        # 重新计算完成百分比
                        hist_data.completion_percentage = (
                            hist_data.total_completed / target * 100
                        ) if target > 0 else 0
                            
        except Exception as e:
            logger.error(f"同步目标点数失败: {e}")
    
    def get_mapsheet_progress(self, sequence: float) -> Dict[str, Any]:
        """
        获取图幅进度信息
        
        Args:
            sequence: 图幅序号
            
        Returns:
            进度信息字典
        """
        # 确保数据是最新的
        self.sync_historical_data()
        
        hist_data = self.mapsheet_manager._historical_data.get(sequence)
        if not hist_data:
            return None
        
        info = self.mapsheet_manager.get_mapsheet_info(sequence)
        
        return {
            'sequence': sequence,
            'roman_name': hist_data.roman_name,
            'team_number': info.get('Team Number') if info else None,
            'total_completed': hist_data.total_completed,
            'target_total': hist_data.target_total,
            'completion_percentage': hist_data.completion_percentage,
            'last_updated': hist_data.last_updated,
            'daily_trend': self._calculate_daily_trend(hist_data),
            'estimated_completion_date': self._estimate_completion_date(hist_data)
        }
    
    def _calculate_daily_trend(self, hist_data: MapsheetHistoricalData) -> List[Dict]:
        """计算每日趋势"""
        if not hist_data.daily_completions:
            return []
        
        # 获取最近30天的数据
        sorted_dates = sorted(hist_data.daily_completions.keys())[-30:]
        
        trend = []
        cumulative = 0
        for date_str in sorted_dates:
            daily = hist_data.daily_completions[date_str]
            cumulative += daily
            trend.append({
                'date': date_str,
                'daily': daily,
                'cumulative': cumulative
            })
        
        return trend
    
    def _estimate_completion_date(self, hist_data: MapsheetHistoricalData) -> Optional[str]:
        """估算完成日期"""
        if not hist_data.daily_completions or hist_data.total_completed >= hist_data.target_total:
            return None
        
        # 计算最近7天的平均速度
        recent_data = list(hist_data.daily_completions.values())[-7:]
        avg_speed = sum(recent_data) / len(recent_data) if recent_data else 0
        
        if avg_speed <= 0:
            return None
        
        remaining_points = hist_data.target_total - hist_data.total_completed
        estimated_days = remaining_points / avg_speed
        
        last_date = max(hist_data.daily_completions.keys())
        last_datetime = datetime.strptime(last_date, '%Y-%m-%d')
        completion_date = last_datetime + timedelta(days=int(estimated_days))
        
        return completion_date.strftime('%Y-%m-%d')
    
    def _save_cache(self):
        """保存缓存"""
        try:
            # 确保缓存目录存在
            self._cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            cache_data = {
                'last_sync': self._last_sync_time.isoformat() if self._last_sync_time else None,
                'total_mapsheets': len(self.mapsheet_manager._historical_data),
                'sync_summary': 'Historical data synchronized successfully'
            }
            
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")


# 全局实例
_historical_data_service: Optional[HistoricalDataService] = None


def get_historical_data_service() -> HistoricalDataService:
    """获取历史数据服务实例"""
    global _historical_data_service
    if _historical_data_service is None:
        _historical_data_service = HistoricalDataService()
    return _historical_data_service
