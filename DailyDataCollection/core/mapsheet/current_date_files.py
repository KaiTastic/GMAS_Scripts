"""
当前日期文件处理模块

处理指定日期的所有图幅文件的集合，包括报告生成和统计功能
"""

import os
import json
import logging
import functools
import threading
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Border, Side, Alignment
from tabulate import tabulate

from ..data_models.observation_data import ObservationData
from ..data_models.date_types import DateType
from ..file_handlers.kmz_handler import KMZFile
from .mapsheet_daily import MapsheetDailyFile


class ConfigurationManager:
    """配置管理器 - 单例模式"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        try:
            from config.config_manager import ConfigManager
            config_manager = ConfigManager()
            config = config_manager.get_config()
            self.WORKSPACE = config['system']['workspace']
            self.SHEET_NAMES_FILE = config_manager.get_resolved_path('sheet_names_file')
            self.SEQUENCE_MIN = config['mapsheet']['sequence_min']
            self.SEQUENCE_MAX = config['mapsheet']['sequence_max']
        except ImportError:
            self.WORKSPACE = ""
            self.SHEET_NAMES_FILE = ""
            self.SEQUENCE_MIN = 41
            self.SEQUENCE_MAX = 51
        
        self._initialized = True


# 全局配置实例
_config = ConfigurationManager()
WORKSPACE = _config.WORKSPACE
SHEET_NAMES_FILE = _config.SHEET_NAMES_FILE
SEQUENCE_MIN = _config.SEQUENCE_MIN
SEQUENCE_MAX = _config.SEQUENCE_MAX

# 创建 logger 实例
logger = logging.getLogger('Current Date Files')
if not logger.handlers:  # 避免重复添加处理器
    logger.setLevel(logging.ERROR)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class CurrentDateFiles:
    """当前日期文件容器类，用于存储指定日期的所有图幅的集合"""
    
    _instances = {}  # 基于日期的实例缓存
    _lock = threading.Lock()
    maps_info: Dict[int, Dict[str, Any]] = {}

    def __new__(cls, currentdate: 'DateType', *args, **kwargs):
        """改进的单例模式，基于日期创建不同实例"""
        date_key = str(currentdate)
        
        if date_key not in cls._instances:
            with cls._lock:
                if date_key not in cls._instances:
                    # 使用新的图幅管理器
                    from .mapsheet_manager import mapsheet_manager
                    cls.maps_info = mapsheet_manager.maps_info
                    cls._instances[date_key] = super(CurrentDateFiles, cls).__new__(cls)
                    cls._instances[date_key]._initialized = False
        
        return cls._instances[date_key]

    def __init__(self, currentdate: 'DateType'):
        """
        初始化当前日期文件集合
        
        Args:
            currentdate: 日期对象
        """
        if self._initialized:
            return
            
        self.currentDate = currentdate
        self.currentDateFiles: List[MapsheetDailyFile] = []
        
        # 清理所有缓存属性
        self._clear_cache()
        
        # 获取当天的文件
        self.__datacollect()
        self._initialized = True

    def _clear_cache(self):
        """清理所有缓存属性"""
        self._cached_sorted_mapsheets = None
        self._error_msg_cache = None

    @functools.cached_property
    def sorted_mapsheets(self) -> List[MapsheetDailyFile]:
        """缓存的排序图幅列表"""
        return sorted(self.currentDateFiles, key=lambda mapsheet: mapsheet.sequence)

    @classmethod
    def mapsInfo(cls) -> Dict[int, Dict[str, Any]]:
        """
        从100K图幅名称信息表中获取图幅的罗马名称和拉丁名称
        
        注意：此方法已弃用，请使用 mapsheet_manager.maps_info 替代
        """
        import warnings
        warnings.warn(
            "CurrentDateFiles.mapsInfo() 已弃用，请使用 mapsheet_manager.maps_info",
            DeprecationWarning,
            stacklevel=2
        )
        
        from .mapsheet_manager import mapsheet_manager
        return mapsheet_manager.maps_info

    def __datacollect(self) -> 'CurrentDateFiles':
        """收集当天的所有文件 - 使用统一的图幅管理器"""
        from .mapsheet_manager import mapsheet_manager
        # 使用图幅管理器创建图幅对象集合
        self.currentDateFiles = mapsheet_manager.create_mapsheet_collection(MapsheetDailyFile, self.currentDate)
        return self

    @functools.cached_property
    def totalDaiyIncreasePointNum(self) -> int:
        """本日新增点数总计"""
        return sum(
            mapsheet.dailyincreasePointNum or 0 
            for mapsheet in self.currentDateFiles
        )

    @functools.cached_property
    def dailyFinishedPoints(self) -> Dict[str, int]:
        """截止本日各图幅完成的点数"""
        finished_points = {}
        for mapsheet in self.sorted_mapsheets:
            roman_name = mapsheet.romanName
            
            # 策略1: 如果有当前文件且点数大于0，使用当前总点数
            if (mapsheet.currentTotalPointNum is not None and 
                mapsheet.currentTotalPointNum > 0):
                finished_points[roman_name] = mapsheet.currentTotalPointNum
                continue
            
            # 策略2: 如果有当前placemarks且点数大于0
            if (mapsheet.currentPlacemarks is not None and 
                mapsheet.currentPlacemarks.pointsCount > 0):
                finished_points[roman_name] = mapsheet.currentPlacemarks.pointsCount
                continue
            
            # 策略3: 关键修复 - 如果当前没有数据但有历史数据，使用历史数据
            # 这种情况表示当天没有新增，但之前有累计数据
            if (mapsheet.lastPlacemarks is not None and 
                mapsheet.lastPlacemarks.pointsCount > 0):
                finished_points[roman_name] = mapsheet.lastPlacemarks.pointsCount
                logger.info(f"图幅 {roman_name} 当天无新增，使用历史累计数据: {mapsheet.lastPlacemarks.pointsCount} 点")
                continue
            
            # 策略4: 如果当前文件存在但是空的，并且历史文件有数据
            # 这处理了当天文件存在但为空的情况
            if (mapsheet.currentPlacemarks is not None and 
                mapsheet.currentPlacemarks.pointsCount == 0 and
                mapsheet.lastPlacemarks is not None and 
                mapsheet.lastPlacemarks.pointsCount > 0):
                finished_points[roman_name] = mapsheet.lastPlacemarks.pointsCount
                logger.info(f"图幅 {roman_name} 当天文件为空，使用历史累计数据: {mapsheet.lastPlacemarks.pointsCount} 点")
                continue
            
            # 最后才设为0，并详细记录原因
            finished_points[roman_name] = 0
            has_current = mapsheet.currentPlacemarks is not None
            has_last = mapsheet.lastPlacemarks is not None
            current_count = mapsheet.currentPlacemarks.pointsCount if has_current else "N/A"
            last_count = mapsheet.lastPlacemarks.pointsCount if has_last else "N/A"
            
            logger.warning(f"图幅 {roman_name} 无法获取完成点数，设为0。详情: "
                         f"当前文件={has_current}(点数={current_count}), "
                         f"历史文件={has_last}(点数={last_count})")
        
        return finished_points

    @functools.cached_property
    def dailyIncreasedPoints(self) -> Dict[str, int]:
        """本日各图幅新增的点数"""
        return {
            mapsheet.romanName: mapsheet.dailyincreasePointNum or 0
            for mapsheet in self.sorted_mapsheets
        }

    @functools.cached_property
    def totalDaiyIncreaseRouteNum(self) -> int:
        """本日新增线路数总计"""
        return sum(
            mapsheet.dailyincreaseRouteNum or 0 
            for mapsheet in self.currentDateFiles
        )

    @functools.cached_property
    def DailyPlans(self) -> Dict[str, str]:
        """本日各图幅的计划"""
        return {
            mapsheet.romanName: '#' if (hasattr(mapsheet, 'nextfilename') and mapsheet.nextfilename) else ''
            for mapsheet in self.sorted_mapsheets
        }

    @functools.cached_property
    def totalDailyPlanNum(self) -> int:
        """本日计划总数"""
        return sum(
            1 for mapsheet in self.currentDateFiles
            if hasattr(mapsheet, 'nextfilename') and mapsheet.nextfilename
        )

    @functools.cached_property
    def totalPointNum(self) -> int:
        """截止当天所有文件的点要素总数"""
        total = 0
        for mapsheet in self.currentDateFiles:
            if mapsheet.currentPlacemarks is not None:
                total += mapsheet.currentPlacemarks.pointsCount
            elif mapsheet.lastPlacemarks is not None:
                total += mapsheet.lastPlacemarks.pointsCount
        return total

    @functools.cached_property
    def allPoints(self) -> Dict:
        """截止当天所有文件的点要素"""
        all_points = {}
        for mapsheet in self.currentDateFiles:
            if mapsheet.currentPlacemarks is not None:
                all_points.update(mapsheet.currentPlacemarks.points)
            elif mapsheet.lastPlacemarks is not None:
                all_points.update(mapsheet.lastPlacemarks.points)
        return all_points

    @functools.cached_property
    def totalRoutesNum(self) -> int:
        """截止当天所有文件的线要素总数"""
        total = 0
        for mapsheet in self.currentDateFiles:
            if mapsheet.currentPlacemarks is not None:
                total += mapsheet.currentPlacemarks.routesCount
            elif mapsheet.lastPlacemarks is not None:
                total += mapsheet.lastPlacemarks.routesCount
        return total

    @functools.cached_property
    def allRoutes(self) -> List:
        """截止当天所有文件的线要素"""
        all_routes = []
        for mapsheet in self.currentDateFiles:
            if mapsheet.currentPlacemarks is not None:
                all_routes.extend(mapsheet.currentPlacemarks.routes)
            elif mapsheet.lastPlacemarks is not None:
                all_routes.extend(mapsheet.lastPlacemarks.routes)
        return all_routes

    @property
    def errorMsg(self) -> List:
        """获取错误消息"""
        if self._error_msg_cache is None:
            self._error_msg_cache = [
                mapsheet.errorMsg for mapsheet in self.currentDateFiles 
                if mapsheet.errorMsg
            ]
        return self._error_msg_cache

    def __contains__(self, key) -> bool:
        """重写__contains__方法, 用于判断图幅文件是否存在"""
        return key in self.currentDateFiles

    def dailyKMZReport(self) -> bool:
        """生成每日KMZ报告"""
        try:
            dailykmz = KMZFile(
                placemarks=ObservationData(
                    points=self.allPoints, 
                    pointsCount=len(self.allPoints), 
                    routes=self.allRoutes, 
                    routesCount=len(self.allRoutes)
                )
            )
            output_path = os.path.join(
                WORKSPACE, 
                self.currentDate.yyyymm_str, 
                self.currentDate.yyyymmdd_str, 
                f"GMAS_Points_and_tracks_until_{self.currentDate.yyyymmdd_str}.kmz"
            )
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            success = dailykmz.write_as(newpath=output_path)
            if success:
                logger.info(f"成功生成每日KMZ报告: {output_path}")
            return success
            
        except Exception as e:
            logger.error(f"生成每日KMZ报告失败: {e}")
            return False

    def dailyExcelReport(self) -> bool:
        """生成每日Excel报告"""
        try:
            output_path = self._get_excel_output_path()
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 删除已存在的文件
            if os.path.exists(output_path):
                os.remove(output_path)
                logger.info(f"删除已存在的Excel文件: {output_path}")
            
            # 创建Excel报告
            self._create_excel_workbook(output_path)
            
            logger.info(f"成功创建每日统计报告: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"生成每日Excel报告失败: {e}")
            return False

    def _get_excel_output_path(self) -> str:
        """获取Excel输出路径"""
        return os.path.join(
            WORKSPACE, 
            self.currentDate.yyyymm_str, 
            self.currentDate.yyyymmdd_str, 
            f"{self.currentDate.yyyymmdd_str}_Daily_Statistics.xlsx"
        )

    def _get_roman_names_list(self) -> List[str]:
        """获取罗马名称列表"""
        return [
            self.__class__.maps_info[sequence]['Roman Name'] 
            for sequence in range(SEQUENCE_MIN, SEQUENCE_MAX + 1)
        ]

    def _create_excel_workbook(self, output_path: str) -> None:
        """创建Excel工作簿"""
        roman_names_list = self._get_roman_names_list()
        max_table_rows = len(roman_names_list) + 5
        max_table_columns = 4
        
        # 创建新的Excel文件
        book = Workbook()
        sheet = book.active
        sheet.title = "Daily Statistics"
        
        # 设置表头、样式和数据
        self._setup_excel_headers(sheet, max_table_rows, max_table_columns, roman_names_list)
        self._setup_excel_styles(sheet, max_table_rows, max_table_columns)
        self._setup_excel_data(sheet, max_table_rows)
        
        # 保存工作簿
        book.save(output_path)

    def _setup_excel_headers(self, sheet, maxTableRows: int, maxTableColumns: int, romanNames_list: List[str]):
        """设置Excel表头"""
        # 每日统计点文件的表头（前三行）
        daily_stat_header1 = ['Date', self.currentDate.yyyy_str + "/" + self.currentDate.mm_str + "/" + self.currentDate.dd_str]
        daily_stat_header2 = [
            'Map sheet name',
            'Regular observation points finished',
            'Field points on revised route'
        ]
        daily_stat_header3 = [
            '', '', 'Added observation points',
            'Added Structure points, photo points, mineralization points'
        ]
        
        # 写入表头
        for col_num, value in enumerate(daily_stat_header1, start=1):
            sheet.cell(row=1, column=col_num, value=value)
        for col_num, value in enumerate(daily_stat_header2, start=1):
            sheet.cell(row=2, column=col_num, value=value)
        for col_num, value in enumerate(daily_stat_header3, start=1):
            sheet.cell(row=3, column=col_num, value=value)
        
        # 写入图幅名称
        for i, value in enumerate(romanNames_list, start=4):
            sheet.cell(row=i, column=1, value=value)
        
        # 写入表尾
        daily_stat_footer = ['Today', '', '', '']
        total_Point_Num_footer = ['TOTAL (Group 3)', '', '', '']
        
        for col_num, value in enumerate(daily_stat_footer, start=1):
            sheet.cell(row=maxTableRows-1, column=col_num, value=value)
        for col_num, value in enumerate(total_Point_Num_footer, start=1):
            sheet.cell(row=maxTableRows, column=col_num, value=value)

    def _setup_excel_styles(self, sheet, maxTableRows: int, maxTableColumns: int):
        """设置Excel样式"""
        # 设置字体
        font_header = Font(name='Calibri', size=12, bold=True)
        font = Font(name='Calibri', size=11)
        
        # 设置边框
        border = Border(
            left=Side(border_style='thin'),
            right=Side(border_style='thin'),
            top=Side(border_style='thin'),
            bottom=Side(border_style='thin')
        )
        
        # 应用样式
        for row in range(1, maxTableRows + 1):
            for col in range(1, maxTableColumns + 1):
                cell = sheet.cell(row=row, column=col)
                cell.border = border
                
                # 设置字体
                if row in [1, 2, 3, maxTableRows-1, maxTableRows]:
                    cell.font = font_header
                else:
                    cell.font = font
        
        # 设置对齐
        center_aligned = Alignment(horizontal='center', vertical='center')
        for row in range(1, maxTableRows + 1):
            for col in range(1, maxTableColumns + 1):
                sheet.cell(row=row, column=col).alignment = center_aligned
        
        # 调整列宽
        for column in sheet.columns:
            max_length = 0
            column = [cell for cell in column]
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except Exception:
                    pass
            adjusted_width = (max_length + 2)
            sheet.column_dimensions[column[0].column_letter].width = adjusted_width

    def _setup_excel_data(self, sheet, maxTableRows: int):
        """设置Excel数据和公式"""
        # 填充实际数据到Excel表格
        self._fill_excel_data(sheet, maxTableRows)
        
        # 设置合计行的公式
        sheet.cell(row=maxTableRows-1, column=2).value = f"=SUM(B4:B{maxTableRows-2})"
        sheet.cell(row=maxTableRows-1, column=3).value = f"=SUM(C4:C{maxTableRows-2})"
        sheet.cell(row=maxTableRows-1, column=4).value = f"=SUM(D4:D{maxTableRows-2})"

        # 在倒数第二行（合计行）写入当日新增数量
        sheet.cell(row=maxTableRows-1, column=2, value=self.totalDaiyIncreasePointNum) 

        # 在最后一行（TOTAL行）写入总数
        sheet.cell(row=maxTableRows, column=2, value=self.totalPointNum)             # 累计总数

        # 合并单元格
        sheet.merge_cells('B1:D1')
        sheet.merge_cells('C2:D2')
        sheet.merge_cells('A2:A3')
        sheet.merge_cells('B2:B3')

    def _fill_excel_data(self, sheet, maxTableRows: int):
        """填充实际数据到Excel表格"""
        try:
            # 获取数据字典
            daily_increased = self.dailyIncreasedPoints
            daily_finished = self.dailyFinishedPoints
            daily_plans = self.DailyPlans
            
            # 按序号排序的图幅列表
            sorted_mapsheets = sorted(self.currentDateFiles, key=lambda mapsheet: mapsheet.sequence)
            
            # 从第4行开始填充数据 (前3行是表头)
            current_row = 4
            
            for mapsheet in sorted_mapsheets:
                roman_name = mapsheet.romanName
                
                # 第1列：图幅名称
                sheet.cell(row=current_row, column=1, value=roman_name)
                
                # 第2列：当日新增点数 (如果为0显示空值)
                increased_points = daily_increased.get(roman_name, 0)
                sheet.cell(row=current_row, column=2, 
                          value=increased_points if increased_points > 0 else None)
                
                # 第3列：当日新增线路/结构点等 (暂时留空，可以后续扩展)
                sheet.cell(row=current_row, column=3, value=None)
                
                # 第4列：累计完成点数 (如果为0显示空值)
                # finished_points = daily_finished.get(roman_name, 0)
                # sheet.cell(row=current_row, column=4, 
                #           value=finished_points if finished_points > 0 else None)
                
                current_row += 1
                
                # 防止超出表格范围
                if current_row >= maxTableRows - 1:
                    break
                    
            logger.info(f"成功填充 {current_row-4} 行数据到Excel表格")
            
        except Exception as e:
            logger.error(f"填充Excel数据失败: {e}")
            raise

    def debug_mapsheet_points(self, mapsheet_name: str = None) -> None:
        """调试图幅点数信息"""
        print(f"\n{'='*60}")
        print(f"调试图幅点数信息 - {self.currentDate}")
        print(f"{'='*60}")
        
        for mapsheet in self.sorted_mapsheets:
            if mapsheet_name and mapsheet.romanName != mapsheet_name:
                continue
                
            print(f"\n图幅: {mapsheet.romanName} (序号: {mapsheet.sequence})")
            print(f"  currentTotalPointNum: {mapsheet.currentTotalPointNum}")
            print(f"  dailyincreasePointNum: {mapsheet.dailyincreasePointNum}")
            
            # 当前文件信息
            if hasattr(mapsheet, 'currentPlacemarks') and mapsheet.currentPlacemarks:
                print(f"  currentPlacemarks.pointsCount: {mapsheet.currentPlacemarks.pointsCount}")
                print(f"  当前文件路径: {getattr(mapsheet, 'currentfilepath', 'N/A')}")
            else:
                print(f"  currentPlacemarks: None")
                print(f"  当前文件路径: {getattr(mapsheet, 'currentfilepath', 'N/A')}")
                
            # 历史文件信息
            if hasattr(mapsheet, 'lastPlacemarks') and mapsheet.lastPlacemarks:
                print(f"  lastPlacemarks.pointsCount: {mapsheet.lastPlacemarks.pointsCount}")
                print(f"  历史文件路径: {getattr(mapsheet, 'lastfilepath', 'N/A')}")
            else:
                print(f"  lastPlacemarks: None")
                print(f"  历史文件路径: {getattr(mapsheet, 'lastfilepath', 'N/A')}")
                
            # 文件存在性检查
            current_file_exists = False
            last_file_exists = False
            if hasattr(mapsheet, 'currentfilepath') and mapsheet.currentfilepath:
                current_file_exists = os.path.exists(mapsheet.currentfilepath)
                print(f"  当前文件存在: {current_file_exists}")
            if hasattr(mapsheet, 'lastfilepath') and mapsheet.lastfilepath:
                last_file_exists = os.path.exists(mapsheet.lastfilepath)
                print(f"  历史文件存在: {last_file_exists}")
                
            # 错误信息
            if hasattr(mapsheet, 'errorMsg') and mapsheet.errorMsg:
                print(f"  错误信息: {mapsheet.errorMsg}")
                
            # 在dailyFinishedPoints中的最终值
            final_value = self.dailyFinishedPoints.get(mapsheet.romanName, '未找到')
            print(f"  ➡️  最终FINISHED值: {final_value}")
            
            if mapsheet_name:  # 如果指定了特定图幅，只显示这一个
                break

    def onScreenDisplay(self) -> None:
        """在屏幕上显示统计信息"""
        try:
            # 获取基础数据
            team_data, person_data = self._get_team_and_person_data()
            map_data = self._get_map_display_data()
            
            # 构建表格数据
            table_data = self._build_table_data(team_data, person_data, map_data)
            
            # 添加总计行
            table_data.append([
                "TOTAL", "", "", 
                self.totalDaiyIncreasePointNum, 
                self.totalDailyPlanNum, 
                self.totalPointNum
            ])
            
            # 检查并报告异常情况
            self._check_and_report_anomalies()
            
            # 显示表格
            headers = ["TEAM", "NAME", "PERSON", "INCREASE", "PLAN", "FINISHED"]
            print(tabulate(table_data, headers, tablefmt="grid"))
            
        except Exception as e:
            logger.error(f"显示统计信息失败: {e}")

    def _check_and_report_anomalies(self) -> None:
        """检查并报告异常情况"""
        zero_finished_maps = []
        for mapsheet in self.sorted_mapsheets:
            finished_count = self.dailyFinishedPoints.get(mapsheet.romanName, 0)
            if finished_count == 0:
                # 检查这个图幅是否真的应该有数据
                has_current = mapsheet.currentPlacemarks is not None
                has_last = mapsheet.lastPlacemarks is not None
                has_error = hasattr(mapsheet, 'errorMsg') and mapsheet.errorMsg
                
                zero_finished_maps.append({
                    'name': mapsheet.romanName,
                    'has_current': has_current,
                    'has_last': has_last,
                    'has_error': has_error,
                    'current_total': getattr(mapsheet, 'currentTotalPointNum', None)
                })
        
        if zero_finished_maps:
            print(f"\n检测到 {len(zero_finished_maps)} 个图幅的FINISHED值为0:")
            for item in zero_finished_maps:
                status_info = []
                if item['has_current']:
                    status_info.append("有当前数据")
                if item['has_last']:
                    status_info.append("有历史数据")
                if item['has_error']:
                    status_info.append("有错误")
                
                status_str = ", ".join(status_info) if status_info else "截至目前无数据"
                print(f"   - {item['name']}: 图幅总完成数据={item['current_total']}, 状态=({status_str})")
            print()  # 空行分隔

    def _get_team_and_person_data(self) -> Tuple[List[str], List[str]]:
        """获取团队和负责人数据"""
        team_list = []
        person_list = []
        
        # 遍历排序后的图幅列表，确保与地图显示数据的顺序一致
        for mapsheet in self.sorted_mapsheets:
            map_info = self.__class__.maps_info.get(mapsheet.sequence, {})
            team_list.append(map_info.get('Team Number', ''))
            person_list.append(map_info.get('Leaders', ''))
        
        return team_list, person_list

    def _get_map_display_data(self) -> Tuple[List[str], List[Any], List[Any], List[str]]:
        """获取地图显示数据"""
        map_name_list = []
        daily_collection_list = []
        daily_finished_list = []
        daily_plan_list = []
        
        empty_placeholder = ''  # 空值占位符
        
        # 遍历所有排序后的图幅，确保所有图幅都显示
        for mapsheet in self.sorted_mapsheets:
            map_name = mapsheet.romanName
            map_name_list.append(map_name)
            
            # 当天完成点数，如果为0则显示空字符串
            increased_count = self.dailyIncreasedPoints.get(map_name, 0)
            daily_collection_list.append(
                increased_count if increased_count > 0 else empty_placeholder
            )
            
            # 截止当天完成的总点数 - 现在总是显示，即使为0也显示数字
            finished_count = self.dailyFinishedPoints.get(map_name, 0)
            daily_finished_list.append(finished_count)  # 移除条件判断，总是显示
            
            # 计划状态
            daily_plan_list.append(self.DailyPlans.get(map_name, ''))
        
        return map_name_list, daily_collection_list, daily_finished_list, daily_plan_list

    def _build_table_data(self, team_data: List[str], person_data: List[str], 
                         map_data: Tuple[List[str], List[Any], List[Any], List[str]]) -> List[List[Any]]:
        """构建表格数据"""
        map_name_list, daily_collection_list, daily_finished_list, daily_plan_list = map_data
        
        table_data = []
        for i in range(len(map_name_list)):
            table_data.append([
                team_data[i],
                map_name_list[i], 
                person_data[i], 
                daily_collection_list[i], 
                daily_plan_list[i], 
                daily_finished_list[i]
            ])
        
        return table_data

    def __str__(self) -> str:
        """字符串表示"""
        try:
            return (
                f"当前日期文件集合\n"
                f"{'='*40}\n"
                f"日期: {self.currentDate}\n"
                f"总文件数: {len(self.currentDateFiles)}\n"
                f"总点数: {self.totalPointNum:,}\n"
                f"日增点数: {self.totalDaiyIncreasePointNum:,}\n"
                f"总路线数: {self.totalRoutesNum:,}\n"
                f"日增路线数: {self.totalDaiyIncreaseRouteNum:,}\n"
                f"计划数: {self.totalDailyPlanNum}\n"
                f"错误数: {len(self.errorMsg)}"
            )
        except Exception as e:
            return f"CurrentDateFiles(日期={self.currentDate}, 错误={e})"

    def __repr__(self) -> str:
        """开发者友好的字符串表示"""
        return (
            f"CurrentDateFiles(currentDate={self.currentDate!r}, "
            f"files_count={len(self.currentDateFiles)}, "
            f"points={self.totalPointNum}, "
            f"daily_increase={self.totalDaiyIncreasePointNum})"
        )
