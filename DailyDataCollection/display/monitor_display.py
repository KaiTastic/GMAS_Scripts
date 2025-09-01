"""
监控显示器 - 专门处理监控相关的显示功能
"""

from typing import List, TYPE_CHECKING
from tabulate import tabulate

if TYPE_CHECKING:
    from core.monitor.mapsheet_monitor import MonitorMapSheet


class MonitorDisplay:
    """监控显示器 - 负责所有监控相关的显示功能"""
    
    @staticmethod
    def show_mapsheet_update(mapsheet: 'MonitorMapSheet', update_type: str, count: int):
        """显示单个图幅的更新信息"""
        print(f"\n数据第{count}次更新")
        
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
        
        print(tabulate(table_data, headers, tablefmt="grid"))
        
        if mapsheet.errorMsg:
            print(f"图幅文件中存在错误信息: \n{mapsheet.errorMsg}")
    
    @staticmethod
    def show_remaining_files(remaining_count: int, total_planned: int):
        """显示剩余待接收文件数量"""
        print(f"当前待接收的文件数量/当日计划数量: {remaining_count}/{total_planned}")
    
    @staticmethod
    def show_monitoring_status(current_time, remaining_files: List[str]):
        """显示监控状态"""
        print("\n")
        print(15*"-", f"当前时间为 {current_time}, 持续监测中...", 15*"-")
    
    @staticmethod
    def show_status(mode_title: str, status_message: str, mapsheets: List['MonitorMapSheet']):
        """显示监控状态信息"""
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M:%S")
        
        print("\n")
        print(f"[{current_time}] {mode_title}")
        if status_message:
            print(status_message)
        
        # 显示监控表格 - 只显示有当日计划的图幅
        if mapsheets:
            headers = ["TEAM", "NAME", "PERSON", "STATUS"]
            table_data = []
            
            for mapsheet in mapsheets:
                # 只显示有当日计划的图幅
                if mapsheet.fileToReceiveFlag:
                    status = "√" if mapsheet.finished else "等待中"
                    
                    table_data.append([
                        mapsheet.teamNumber,
                        mapsheet.romanName,
                        mapsheet.teamleader,
                        status,
                    ])
                else:
                    table_data.append([
                        mapsheet.teamNumber,
                        mapsheet.romanName,
                        mapsheet.teamleader,
                        "-",
                    ])

            if table_data:
                print(tabulate(table_data, headers, tablefmt="grid"))
            else:
                print("当前没有需要监控的图幅（所有图幅都没有当日计划）")
        
        print("-" * 80)
    
    @staticmethod
    def show_urgent_mode(remaining_files: List[str], mapsheets: List['MonitorMapSheet']):
        """显示催促模式信息"""
        print(f"进入催促模式...")
        
        for filename in remaining_files:
            for mapsheet in mapsheets:
                # 只催促有当日计划的图幅
                if filename == mapsheet.mapsheetFileName and mapsheet.fileToReceiveFlag:
                    print(f"请注意: {mapsheet.teamNumber} {mapsheet.mapsheetFileName}文件未接收完成,责任人: {mapsheet.teamleader}")
        print("\n")
    
    @staticmethod
    def show_plan_mode_start(end_time):
        """显示计划路线接收模式开始"""
        print(f"当天没有待接收的完成点，转入计划路线接收模式...\n预计停止接收时间: {end_time.hour:02}:{end_time.minute:02}")
    
    @staticmethod
    def show_timeout(end_time):
        """显示超时消息"""
        print(f"已到截止时间: {end_time.hour:02}:{end_time.minute:02}分，停止接收路线计划,退出监视...")
    
    @staticmethod
    def get_planned_mapsheets_count(mapsheets: List['MonitorMapSheet']) -> tuple:
        """
        统计有当日计划的图幅信息
        
        Returns:
            tuple: (有当日计划的图幅数量, 总图幅数量, 有计划且未完成的图幅数量)
        """
        total_count = len(mapsheets)
        planned_count = sum(1 for ms in mapsheets if ms.fileToReceiveFlag)
        planned_unfinished_count = sum(1 for ms in mapsheets if ms.fileToReceiveFlag and not ms.finished)
        
        return planned_count, total_count, planned_unfinished_count
