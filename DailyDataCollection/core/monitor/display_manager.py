"""
显示管理器模块 - 负责监控状态的显示和输出
"""

from typing import List, TYPE_CHECKING
from tabulate import tabulate

# 导入编码修复器
try:
    from ..utils.encoding_fixer import safe_print
except ImportError:
    # 如果编码修复器不可用，使用普通print
    safe_print = print

if TYPE_CHECKING:
    from .mapsheet_monitor import MonitorMapSheet


class DisplayManager:
    """显示管理器 - 负责格式化输出监控信息"""
    
    @staticmethod
    def display_mapsheet_update(mapsheet: 'MonitorMapSheet', update_type: str, count: int):
        """显示单个图幅的更新信息"""
        safe_print(f"\n数据第{count}次更新")
        
        headers = ["TEAM", "NAME", "PERSON", "INCREASE", "PLAN", "FINISHED"]
        
        plan_status = '#' if mapsheet.nextfilepath else '-'
        table_data = [[
            mapsheet.teamNumber, 
            mapsheet.romanName, 
            mapsheet.teamleader, 
            f'{mapsheet.dailyincreasePointNum}', 
            plan_status, 
            f'{mapsheet.currentTotalPointNum}'
        ]]
        
        safe_print(tabulate(table_data, headers, tablefmt="grid"))
        
        if mapsheet.errorMsg:
            safe_print(f"图幅文件中存在错误信息: \n{mapsheet.errorMsg}")
    
    @staticmethod
    def display_remaining_files(remaining_count: int, total_planned: int):
        """显示剩余待接收文件数量"""
        safe_print(f"当前待接收的文件数量/当日计划数量: {remaining_count}/{total_planned}")
    
    @staticmethod
    def display_monitoring_status(current_time, remaining_files: List[str]):
        """显示监控状态"""
        safe_print("\n")
        safe_print(15*"-", f"当前时间为 {current_time}, 持续监测中...", 15*"-")
    
    @staticmethod
    def display_urgent_mode(remaining_files: List[str], mapsheets: List['MonitorMapSheet']):
        """显示催促模式信息"""
        safe_print(f"进入催促模式...")
        
        for filename in remaining_files:
            for mapsheet in mapsheets:
                if filename == mapsheet.mapsheetFileName:
                    safe_print(f"请注意: {mapsheet.teamNumber} {mapsheet.mapsheetFileName}文件未接收完成,责任人: {mapsheet.teamleader}")
        safe_print("\n")
    
    @staticmethod
    def display_completion_message():
        """显示完成消息"""
        safe_print(f"所有待接收的文件已经全部接收完成,退出监视...")
    
    @staticmethod
    def display_plan_mode_start(end_time):
        """显示计划路线接收模式开始"""
        safe_print(f"当天没有待接收的完成点，转入计划路线接收模式...\n预计停止接收时间: {end_time.hour:02}:{end_time.minute:02}")
    
    @staticmethod
    def display_timeout_message(end_time):
        """显示超时消息"""
        safe_print(f"已到截止时间: {end_time.hour:02}:{end_time.minute:02}分，停止接收路线计划,退出监视...")
    
    @staticmethod
    def display_file_detected(filename: str):
        """显示检测到文件"""
        safe_print(f'\n监测到KMZ文件: {filename}')
    
    @staticmethod
    def display_validation_error(filename: str, error_type: str):
        """显示验证错误"""
        error_messages = {
            'invalid_name': f"文件名称不符合要求（无法判断是完成点文件/计划线路文件）: {filename}",
            'no_valid_finished': f"文件名中没有包含有效完成点名称: {filename}",
            'no_valid_plan': f"文件名中没有包含有效的计划路线名称: {filename}"
        }
        
        message = error_messages.get(error_type, f"未知验证错误: {filename}")
        safe_print(message)
