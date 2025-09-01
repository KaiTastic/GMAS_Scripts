"""
当前日期文件处理模块

处理指定日期的所有图幅文件的集合，包括报告生成和统计功能
"""

import os
import logging
import functools
import threading
import warnings
from typing import Dict, List, Optional, Any, Tuple
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Border, Side, Alignment

from ..data_models.observation_data import ObservationData
from ..data_models.date_types import DateType
from ..file_handlers.kmz_handler import KMZFile
from .mapsheet_daily import MapsheetDailyFile

# 使用系统配置模块
from config.config_manager import ConfigManager

# 获取配置实例
config_manager = ConfigManager()
WORKSPACE = config_manager.get('system.workspace')
SHEET_NAMES_FILE = config_manager.get_resolved_path('sheet_names_file')
SEQUENCE_MIN = config_manager.get('mapsheet.sequence_min')
SEQUENCE_MAX = config_manager.get('mapsheet.sequence_max')

# 创建 logger 实例
logger = logging.getLogger('Current Date Files')
if not logger.handlers:  # 避免重复添加处理器
    logger.setLevel(logging.INFO)  # 改为INFO级别以看到详细日志
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # 添加这一行防止向上传播
    logger.propagate = False

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

    def write_completed_data_to_statistics_excel(self, target_excel_path: str) -> bool:
        """
        将当日新增的数据列写入指定的统计Excel文件
        
        Args:
            target_excel_path: 目标Excel文件路径，例如 "D:\\RouteDesign\\Daily_statistics_details_for_Group_3.2.xlsx"
            
        Returns:
            bool: 写入成功返回True，失败返回False
        """
        try:
            # 检查目标文件是否存在
            if not os.path.exists(target_excel_path):
                logger.error(f"目标Excel文件不存在: {target_excel_path}")
                return False
            
            # 加载现有工作簿
            wb = load_workbook(target_excel_path)
            
            # 使用"总表"工作表
            if "总表" in wb.sheetnames:
                ws = wb["总表"]
            else:
                ws = wb.active
                logger.warning("未找到'总表'工作表，使用默认工作表")
            
            # 获取当前日期的新增数据（而不是累计完成数据）
            daily_increased = self.dailyIncreasedPoints
            
            # 查找日期所在的列
            target_col = self._find_date_row_in_excel(ws)
            if target_col is None:
                logger.error(f"在Excel中未找到日期 {self.currentDate} 对应的列")
                return False
            
            self._fill_increased_data_to_col(ws, target_col)
            
            # 写入新增数据到相应的行
            # self._write_increased_data_to_col(ws, target_col, daily_increased)
            
            # 保存文件
            wb.save(target_excel_path)
            logger.info(f"成功将当日新增数据写入Excel文件: {target_excel_path}")
            return True
            
        except Exception as e:
            logger.error(f"写入当日新增数据到Excel文件失败: {e}")
            return False

    def _fill_increased_data_to_col(self, ws, target_col):
        """
        Purpose: Fill in the increased data for the specified column
        """
        """填充实际数据到Excel表格"""
        try:
            # 获取数据字典
            daily_increased = self.dailyIncreasedPoints
            
            # 按序号排序的图幅列表
            sorted_mapsheets = sorted(self.currentDateFiles, key=lambda mapsheet: mapsheet.sequence)
            
            # 从第3行开始填充数据 (前2行是表头)
            current_row = 3

            for mapsheet in sorted_mapsheets:
                roman_name = mapsheet.romanName
            
                # 当日新增点数 (如果为0显示空值)
                increased_points = daily_increased.get(roman_name, 0)
                ws.cell(row=current_row, column=target_col, 
                          value=increased_points if increased_points > 0 else None)
                
                current_row += 1
                    
            logger.info(f"成功填充 {current_row-3} 行数据到Daily statics Excel表格")
        
        except Exception as e:
            logger.error(f"写入当日新增数据到Daily statics Excel表格失败: {e}")
            return False
    
    def _find_date_row_in_excel(self, worksheet) -> Optional[int]:
        """
        在Excel工作表中查找当前日期对应的行
        
        Args:
            worksheet: openpyxl工作表对象
            
        Returns:
            int or None: 找到的行号，未找到返回None
        """
        try:
            # 在第一行查找日期列
            target_date = self.currentDate.date_datetime  # datetime对象
            
            # 检查第一行的日期列（从第9列开始，基于Excel结构分析）
            for col in range(9, min(worksheet.max_column + 1, 110)):  # 扩展搜索范围
                cell_value = worksheet.cell(row=1, column=col).value
                if cell_value:
                    # 如果是datetime对象，直接比较日期
                    if hasattr(cell_value, 'date'):
                        if cell_value.date() == target_date.date():
                            logger.info(f"在Excel第1行第{col}列找到匹配日期: {cell_value}")
                            return col  # 返回列号而不是行号
                    # 如果是字符串，尝试解析
                    elif isinstance(cell_value, str):
                        cell_str = cell_value.strip()
                        # 可能的日期格式
                        possible_date_formats = [
                            self.currentDate.yyyymmdd_str,  # "20250831"
                            f"{self.currentDate.yyyy_str}-{self.currentDate.mm_str}-{self.currentDate.dd_str}",  # "2025-08-31"
                            f"{self.currentDate.yyyy_str}/{self.currentDate.mm_str}/{self.currentDate.dd_str}",  # "2025/08/31"
                        ]
                        
                        if any(date_format in cell_str for date_format in possible_date_formats):
                            logger.info(f"在Excel第1行第{col}列找到日期字符串: {cell_str}")
                            return col  # 返回列号
            
            logger.warning(f"在Excel第1行中未找到日期 {target_date.date()} 对应的列")
            return None
            
        except Exception as e:
            logger.error(f"查找日期列失败: {e}")
            return None

    def onScreenDisplay(self) -> None:
        """在屏幕上显示统计信息 - 使用统一显示管理器"""
        from display import CollectionDisplay
        
        # 委托给CollectionDisplay处理
        CollectionDisplay.show_statistics(self)

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
