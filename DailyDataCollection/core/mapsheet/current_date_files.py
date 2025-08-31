"""
当前日期文件处理模块

处理指定日期的所有图幅文件的集合，包括报告生成和统计功能
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Border, Side, Alignment
from tabulate import tabulate

from ..data_models.observation_data import ObservationData
from ..data_models.date_types import DateType
from ..file_handlers.kmz_handler import KMZFile
from .mapsheet_daily import MapsheetDailyFile

# 导入配置
try:
    from config.config_manager import ConfigManager
    config_manager = ConfigManager()
    config = config_manager.get_config()
    WORKSPACE = config['system']['workspace']
    SHEET_NAMES_FILE = config_manager.get_resolved_path('sheet_names_file')
    SEQUENCE_MIN = config['mapsheet']['sequence_min']
    SEQUENCE_MAX = config['mapsheet']['sequence_max']
except ImportError:
    WORKSPACE = ""
    SHEET_NAMES_FILE = ""
    SEQUENCE_MIN = 41
    SEQUENCE_MAX = 51

# 创建 logger 实例
logger = logging.getLogger('Current Date Files')
logger.setLevel(logging.ERROR)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class CurrentDateFiles:
    """当前日期文件容器类，用于存储指定日期的所有图幅的集合"""
    
    maps_info: Dict[int, Dict[str, Any]] = {}

    def __new__(cls, currentdate: 'DateType', *args, **kwargs):
        """单例模式，确保图幅信息只初始化一次"""
        if not hasattr(cls, 'instance'):
            # 使用新的图幅管理器
            from .mapsheet_manager import mapsheet_manager
            cls.maps_info = mapsheet_manager.maps_info
        cls.instance = super(CurrentDateFiles, cls).__new__(cls)
        return cls.instance

    def __init__(self, currentdate: 'DateType'):
        """
        初始化当前日期文件集合
        
        Args:
            currentdate: 日期对象
        """
        self.currentDate = currentdate
        self.currentDateFiles: List[MapsheetDailyFile] = []
        
        # 本日新增点数、线路数、点要素和线要素
        self._totalDaiyIncreasePointNum: Optional[int] = None
        self._totalDailyIncreasePoints: Dict = {}
        self._totalDaiyIncreaseRouteNum: Optional[int] = None
        self._totalDailyIncreaseRoutes: List = []
        
        # 总计计划线路数
        self._totalPlanNum: Optional[int] = None
        self._totalPlans: List = []
        
        # 截止本日总计点数和线路数
        self._totalPointNum: Optional[int] = None
        self._totalRouteNum: Optional[int] = None
        self._allPoints: Optional[Dict] = None
        self._allRoutes: Optional[List] = None
        
        # 本日各图幅完成的点数量
        self._dailyIncreasedPoints: Optional[Dict] = None
        # 截止本日，各图幅各自完成的点的总数
        self._dailyFinishedPoints: Optional[Dict] = None
        # 本日各图幅计划的线数量
        self._dailyPlanedRoutes: Optional[Dict] = None

        # 错误信息
        self.__errorMsg: Optional[List] = None
        
        # 获取当天的文件
        self.__datacollect()

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

    @property
    def totalDaiyIncreasePointNum(self) -> int:
        """本日新增点数总计"""
        if self._totalDaiyIncreasePointNum is None:
            total = 0
            for mapsheet in self.currentDateFiles:
                if mapsheet.dailyincreasePointNum:
                    total += mapsheet.dailyincreasePointNum
            self._totalDaiyIncreasePointNum = total
        return self._totalDaiyIncreasePointNum

    @property
    def dailyFinishedPoints(self) -> Dict[str, int]:
        """截止本日各图幅完成的点数"""
        if not self._dailyFinishedPoints:
            sorted_mapsheets = sorted(self.currentDateFiles, key=lambda mapsheet: mapsheet.sequence)
            dailyPoints = {}
            for mapsheet in sorted_mapsheets:
                dailyPoints[mapsheet.romanName] = mapsheet.currentTotalPointNum or 0
            self._dailyFinishedPoints = dailyPoints
        return self._dailyFinishedPoints

    @property
    def dailyIncreasedPoints(self) -> Dict[str, int]:
        """本日各图幅新增的点数"""
        if not self._dailyIncreasedPoints:
            sorted_mapsheets = sorted(self.currentDateFiles, key=lambda mapsheet: mapsheet.sequence)
            dailyPoints = {}
            for mapsheet in sorted_mapsheets:
                dailyPoints[mapsheet.romanName] = mapsheet.dailyincreasePointNum or 0
            self._dailyIncreasedPoints = dailyPoints
        return self._dailyIncreasedPoints

    @property
    def totalDaiyIncreaseRouteNum(self) -> int:
        """本日新增线路数总计"""
        if self._totalDaiyIncreaseRouteNum is None:
            total = 0
            for mapsheet in self.currentDateFiles:
                if mapsheet.dailyincreaseRouteNum:
                    total += mapsheet.dailyincreaseRouteNum
            self._totalDaiyIncreaseRouteNum = total
        return self._totalDaiyIncreaseRouteNum

    @property
    def DailyPlans(self) -> Dict[str, str]:
        """本日各图幅的计划"""
        if not self._dailyPlanedRoutes:
            sorted_mapsheets = sorted(self.currentDateFiles, key=lambda mapsheet: mapsheet.sequence)
            dailyPlaneds = {}
            for mapsheet in sorted_mapsheets:
                if hasattr(mapsheet, 'nextfilename') and mapsheet.nextfilename:
                    dailyPlaneds[mapsheet.romanName] = '#'
                else:
                    dailyPlaneds[mapsheet.romanName] = ''
            self._dailyPlanedRoutes = dailyPlaneds
        return self._dailyPlanedRoutes

    @property
    def totalDailyPlanNum(self) -> int:
        """本日计划总数"""
        if self._totalPlanNum is None:
            total = 0
            for mapsheet in self.currentDateFiles:
                if hasattr(mapsheet, 'nextfilename') and mapsheet.nextfilename:
                    total += 1
            self._totalPlanNum = total
        return self._totalPlanNum

    @property
    def totalPointNum(self) -> int:
        """截止当天所有文件的点要素总数"""
        if self._totalPointNum is None:
            totalNum = 0
            for mapsheet in self.currentDateFiles:
                if mapsheet.currentPlacemarks is not None:
                    totalNum += mapsheet.currentPlacemarks.pointsCount
                elif mapsheet.lastPlacemarks is not None:
                    totalNum += mapsheet.lastPlacemarks.pointsCount
            self._totalPointNum = totalNum
        return self._totalPointNum

    @property
    def allPoints(self) -> Dict:
        """截止当天所有文件的点要素"""
        if self._allPoints is None:
            allPoints = {}
            for mapsheet in self.currentDateFiles:
                if mapsheet.currentPlacemarks is not None:
                    allPoints.update(mapsheet.currentPlacemarks.points)
                elif mapsheet.lastPlacemarks is not None:
                    allPoints.update(mapsheet.lastPlacemarks.points)
            self._allPoints = allPoints
        return self._allPoints

    @property
    def totalRoutesNum(self) -> int:
        """截止当天所有文件的线要素总数"""
        if self._totalRouteNum is None:
            totalNum = 0
            for mapsheet in self.currentDateFiles:
                if mapsheet.currentPlacemarks is not None:
                    totalNum += mapsheet.currentPlacemarks.routesCount
                elif mapsheet.lastPlacemarks is not None:
                    totalNum += mapsheet.lastPlacemarks.routesCount
            self._totalRouteNum = totalNum
        return self._totalRouteNum

    @property
    def allRoutes(self) -> List:
        """截止当天所有文件的线要素"""
        if self._allRoutes is None:
            allRoutes = []
            for mapsheet in self.currentDateFiles:
                if mapsheet.currentPlacemarks is not None:
                    allRoutes.extend(mapsheet.currentPlacemarks.routes)
                elif mapsheet.lastPlacemarks is not None:
                    allRoutes.extend(mapsheet.lastPlacemarks.routes)
            self._allRoutes = allRoutes
        return self._allRoutes

    @property
    def errorMsg(self) -> List:
        """获取错误消息"""
        if self.__errorMsg is None:
            self.__errorMsg = []
            for mapsheet in self.currentDateFiles:
                if mapsheet.errorMsg:
                    self.__errorMsg.append(mapsheet.errorMsg)
        return self.__errorMsg

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
            return dailykmz.write_as(newpath=output_path)
        except Exception as e:
            logger.error(f"生成每日KMZ报告失败: {e}")
            return False

    def dailyExcelReport(self) -> bool:
        """生成每日Excel报告"""
        try:
            dailyExcel = os.path.join(
                WORKSPACE, 
                self.currentDate.yyyymm_str, 
                self.currentDate.yyyymmdd_str, 
                f"{self.currentDate.yyyymmdd_str}_Daily_Statistics.xlsx"
            )
            
            # 删除已存在的文件
            if os.path.exists(dailyExcel):
                os.remove(dailyExcel)
            
            romanNames_list = [
                self.__class__.maps_info[sequence]['Roman Name'] 
                for sequence in range(SEQUENCE_MIN, SEQUENCE_MAX + 1)
            ]
            
            # 计算输出表格的行数和列数
            maxTableRows, maxTableColumns = len(romanNames_list) + 5, 4
            
            # 创建新的Excel文件
            try:
                book = load_workbook(dailyExcel)
            except FileNotFoundError:
                book = Workbook()

            sheet = book.active
            sheet.title = "Daily Statistics"
            
            # 设置表头和数据
            self._setup_excel_headers(sheet, maxTableRows, maxTableColumns, romanNames_list)
            self._setup_excel_styles(sheet, maxTableRows, maxTableColumns)
            self._setup_excel_data(sheet, maxTableRows)
            
            # 保存工作簿
            book.save(dailyExcel)
            print(f"创建每日统计点 {dailyExcel} 空表成功。")
            return True
            
        except Exception as e:
            logger.error(f"生成每日Excel报告失败: {e}")
            return False

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
                finished_points = daily_finished.get(roman_name, 0)
                sheet.cell(row=current_row, column=4, 
                          value=finished_points if finished_points > 0 else None)
                
                current_row += 1
                
                # 防止超出表格范围
                if current_row >= maxTableRows - 1:
                    break
                    
            logger.info(f"成功填充 {current_row-4} 行数据到Excel表格")
            
        except Exception as e:
            logger.error(f"填充Excel数据失败: {e}")
            raise

    def onScreenDisplay(self):
        """在屏幕上显示统计信息"""
        try:
            # 获取填图组号
            team_list = []
            # 获取负责人列表
            person_list = []
            for key in range(SEQUENCE_MIN, SEQUENCE_MAX + 1):
                team_list.append(self.__class__.maps_info[key]['Team Number'])
                person_list.append(self.__class__.maps_info[key]['Leaders'])
            
            # 图幅罗马名称
            map_name_list = []
            # 当天新增点数
            daily_collection_list = []
            # 截止当天, 图幅完成的总点数
            daily_Finished_list = []
            # 图幅第二天的野外计划
            daily_plan_list = []
            
            for key, value in self.dailyIncreasedPoints.items():
                map_name_list.append(key)
                x = ''  # 空值占位符
                # 各个图幅当天的完成点数, 如果完成点数为0, 则显示空字符串, 否则显示完成点数
                daily_collection_list.append(x if self.dailyIncreasedPoints[key] == 0 else self.dailyIncreasedPoints[key])
                # 各个图幅截止当天的完成点数, 如果完成点数为0, 则显示空字符串, 否则显示完成点数
                daily_Finished_list.append(x if self.dailyFinishedPoints[key] == 0 else self.dailyFinishedPoints[key])
                daily_plan_list.append(self.DailyPlans[key])
            
            table_data = []
            # 调整显示的每行顺序
            for i in range(len(map_name_list)):
                table_data.append([team_list[i], map_name_list[i], person_list[i], daily_collection_list[i], daily_plan_list[i], daily_Finished_list[i]])
            
            # 添加总计行
            table_data.append(["TOTAL", "", "", self.totalDaiyIncreasePointNum, self.totalDailyPlanNum, self.totalPointNum])
            headers = ["TEAM", "NAME", "PERSON", "INCREASE", "PLAN", "FINISHED"]
            print(tabulate(table_data, headers, tablefmt="grid"))
            
        except Exception as e:
            logger.error(f"显示统计信息失败: {e}")

    def __str__(self) -> str:
        """字符串表示"""
        return (f"当前日期: {self.currentDate}\n"
                f"总文件数: {len(self.currentDateFiles)}\n"
                f"总点数: {self.totalPointNum}\n"
                f"日增点数: {self.totalDaiyIncreasePointNum}")
