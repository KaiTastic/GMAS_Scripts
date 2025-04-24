"""
This module is used to monitor the daily data collection process. It will check the status of the data collection.
该模块用来监视微信文件夹中数据的更新
"""

import os
from config import *
from datetime import datetime
import pandas as pd
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from DailyFileGenerator import MapsheetDailyFile, CurrentDateFiles
import re
from tabulate import tabulate

#! 需要改进的方向
#! 1. 可能存在已经获得当日的完成路线后,程序会跳过更新的情况
#! 2. 将error信息纳入是否接收的判断中


# 单个图幅
class MonitorMapSheet(MapsheetDailyFile):
    """ 该类继承自MapsheetsDailyFile类,主要用于监视图幅文件的变化
            属性: 
            fileToReceiveFlag: bool,表示当天是否有已有计划路线
            matchedFinishedFileCountNum: int,表示当天接收到的完成路线数量
                                                如果self.fileToReceiveFlag为True同时self.matchedFinishedFileCountNum>=1,则说明当天的计划路线文件已经接收完成
                                                与此同时,self.currentfilename会有值,存储当天已完成的路线文件名    
            matchedPlanFileCountNum: int,表示当天接收到的计划路线数量
            方法: 
                __hasPlan: 检查当天的计划路线文件是否存在,用于决定是否要接收当天的完成路线文件
                update: 更新当前图幅的状态
                __onScreenDisplay: 在屏幕上以表格的形式显示改图幅当天的接收完成路线文件的数量
    """
    def __init__(self, mapsheetFileName: str, currentDate: 'DateType'):

        super().__init__(mapsheetFileName, currentDate)

        # 检查是否有当日计划
        self.fileToReceiveFlag: bool = False
        self.__hasPlan()

        # 记录当天接收到的完成路线文件数量
        self.matchedFinishedFileCountNum: int = 0
        # 记录当天接收到的计划路线数量
        self.matchedPlanFileCountNum: int = 0
    
    def updateFinished(self):
        """在完成接收完成路线文件时,更新当前图幅的状态
        """
        # 接收的数量加1
        self.matchedFinishedFileCountNum += 1
        self.getCurrentDateFile(self)
        self.findlastFinished(self)
        self.dailyIncrease()
        self.soFarfinished()
        self.__onScreenDisplay(flag='finished')

    def updatePlan(self):
        """在完成接收计划路线文件时,更新当前图幅的状态
        """
        # 接收的数量加1
        self.matchedPlanFileCountNum += 1
        # NOTE: 使用观察者模式来通知接收完成路线文件,并计算完成的点数
        self.findNextPlan(self)
        self.__onScreenDisplay(flag='plan')

    def __hasPlan(self):
        """通过检查当天的计划路线文件是否存在,来判断是否有当日完成点待接收
        :return: bool
        """
        # NOTE: 后续需要增加从Excel表格中获取判断的逻辑,做到表和文件一致的双重校验
        planFilePath = os.path.join(WORKSPACE, self.currentDate.yyyymm_str, self.currentDate.yyyymmdd_str, "Planned routes", f"{self.mapsheetFileName}_plan_routes_{self.currentDate.yyyymmdd_str}.kmz")
        if os.path.exists(planFilePath):
            self.fileToReceiveFlag = True
        else:
            self.fileToReceiveFlag = False
        return self.fileToReceiveFlag

    def __onScreenDisplay(self, flag):
        """
        在屏幕上以表格的形式显示改图幅当天的接收完成路线文件的数量
        """
        if flag == 'plan':
            print(f"\n数据第{self.matchedPlanFileCountNum}次更新")
        elif flag == 'finished':
            print(f"\n数据第{self.matchedFinishedFileCountNum}次更新")
        else:
            print(f"参数错误，请检查")

        headers = ["TEAM", "NAME", "PERSON", "INCREASE", "PLAN", "FINISHED"]
        if self.nextfilepath:
            table_data = [[self.teamNumber, self.romanName, self.teamleader, f'{self.dailyincreasePointNum}', '#', f'{self.currentTotalPointNum}']]
        else:
            table_data = [[self.teamNumber, self.romanName, self.teamleader, f'{self.dailyincreasePointNum}', '-', f'{self.currentTotalPointNum}']]
        print(tabulate(table_data, headers, tablefmt="grid"))

        if self.errorMsg:
            print(f"图幅文件中存在错误信息: \n{self.errorMsg}")


# 待收集的图幅集合
class MonitorMapSheetCollection(object):
    """
    需要收集的图幅列表
    为容器类
    """
    # 类变量,存储图幅信息
    maps_info: dict = None

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.mapsInfo()
            cls.instance = super(MonitorMapSheetCollection, cls).__new__(cls)
        return cls.instance

    def __init__(self, currentDate):
        self.currentDate = currentDate
        # 待收集的图幅实例列表
        self.mapSheetTobeCollect: list[MonitorMapSheet] = []
        # 待收集的图幅名称列表
        self.mapSheetTobeCollect_namelist_list = []
        # 所有的图幅名称列表
        self.mapSheet_namelist_list = []
        # 记录当天的计划路线文件数量
        self.plannedRouteFileNum: int = 0
        self.__setMapsheetList()

    @classmethod
    def mapsInfo(cls):
        """
        调用CurrentDateFiles类中的mapsInfo方法,从100K图幅名称信息表中获取图幅的信息
        """
        # print("开始获取图幅信息...")
        cls.maps_info = CurrentDateFiles.mapsInfo()
        # print(cls.maps_info)
        # print("图幅信息获取完成")
        return cls.maps_info

    def __setMapsheetList(self):
        # 设置每天需要收集的图幅列表
        # 所有的图幅信息
        # mapsheet_list = []
        # 当天需要收集的图幅列表
        for sequence in range(SEQUENCE_MIN, SEQUENCE_MAX+1):
            mapsheetFileName = self.__class__.maps_info[sequence]['File Name'] 
            # 实例化 MonitorMapSheet类
            mapsheet = MonitorMapSheet(mapsheetFileName, self.currentDate)
            # 将所有的图幅名称和实例都添加到列表中
            self.mapSheet_namelist_list.append(mapsheetFileName)
            self.mapSheetTobeCollect.append(mapsheet)
            # 检查当天的计划路线文件是否存在,如果存在,则将图幅名称添加到列表中
            if mapsheet.fileToReceiveFlag:
                # 当日的计划数目+1
                self.plannedRouteFileNum += 1
                # 检查当天的完成点文件是否已经识别出来,如果已经识别出来（不为None）,则不会被添加到列表中
                if mapsheet.currentfilename is None:
                    # print(f"当天计划路线中的图幅名称: {mapsheetFileName}")
                    self.mapSheetTobeCollect_namelist_list.append(mapsheetFileName)
        return self

    def __contains__(self, item):
        return item in self.mapSheetTobeCollect


class DataHandler(FileSystemEventHandler, MonitorMapSheetCollection):
    """待接收的文件监视器
        self.currentDate: 当前日期
        self.mapSheetTobeCollect_namelist_list: 待接收的文件列表
                                                在接收到有效文件后,弹出该文件名,直到列表为空
    """
    def __init__(self, currentDate: DateType):

        super().__init__(currentDate)
        # 待接收的文件，动态变化
        self.mapSheetTobeCollect_namelist_list_pop = self.mapSheetTobeCollect_namelist_list.copy()

    def on_created(self, event):
        on_observed_filename = os.path.basename(event.src_path).lower()
        if on_observed_filename.endswith(".kmz"):
            print("\n")
            print(f'有KMZ文件创建更新: {event.src_path}')
            if self.__fileNameValidateDate(on_observed_filename) and self.__fileNameValidateMapSheetName(on_observed_filename):
                index_1 = on_observed_filename.find('_finished_points_and_tracks_')
                index_2 = on_observed_filename.find('_plan_routes_')
                # 如果文件名中包含'_finished_points_and_tracks_',则说明是完成点文件
                if index_1 != -1:
                    self.__finishKMZFileValidate(on_observed_filename)
                # 如果文件名中包含'_plan_routes_',则说明是计划路线文件
                elif index_2 != -1:
                    self.__planKMZFileValidate(on_observed_filename)
                else:
                    print(f"文件名称不符合要求（无法判断是完成点文件/计划线路文件）: {on_observed_filename}")            
        # else:
        #     print(f"文件未识别: {on_observed_filename}")
        # print("文件未识别,继续监视目标文件夹...", end="\n")

    def __fileNameValidateDate(self, on_observed_filename):
        """验证文件名中的日期信息是否符合格式要求: 8位数字,即YYYYMMDD,同时可转换为有效的日期
        """
        if on_observed_filename.endswith(".kmz"):
            # 从文件名称匹配到的日期
            matchedDate_yyyymmdd_str = re.search(r'\d{8}', on_observed_filename)
            try:
                on_observed_file_datetime = datetime.strptime(matchedDate_yyyymmdd_str.group(), "%Y%m%d")
            except ValueError:
                print(f"文件名中的日期不合法: {on_observed_filename}")
            # 如果文件名中的日期大于等于当前日期,则合法
            if on_observed_file_datetime.date() >= self.currentDate.date_datetime.date():
                return True
            else:
                print(f"无法从文件名匹配到有效日期（日期格式错误/日期不为当天/日期不为下一天): {on_observed_filename}")
                return False
        else:
            print(f"文件名日期格式错误(不正确/不足8位): {on_observed_filename}")
            return False

    def __fileNameValidateMapSheetName(self, on_observed_filename):
        """验证文件名中的图幅信息是否符合要求
        :param filename: 文件名
        :return: bool
        """
        for item in self.mapSheet_namelist_list:
            if on_observed_filename.startswith(item.lower()):
                # break
                return True
        else:
            print(f"文件名中没有包含有效的图幅名称: {on_observed_filename}")
            return False

    def __finishKMZFileValidate(self, on_observed_filename):
        """验证KMZ文件的名称是否符合要求
        :param filename: 文件名
        :return: bool
        """
        if on_observed_filename.endswith(".kmz"):
            matchedDate_yyyymmdd_str = re.search(r'\d{8}', on_observed_filename)
            on_observed_file_datetime = datetime.strptime(matchedDate_yyyymmdd_str.group(), "%Y%m%d")
            # 如果文件名中的日期为当前日期,则合法
            if on_observed_file_datetime.date() == self.currentDate.date_datetime.date():
                for item in self.mapSheetTobeCollect:
                    toBeCollectFileName = item.mapsheetFileName + '_finished_points_and_tracks_' + self.currentDate.yyyymmdd_str
                    index = on_observed_filename.find(toBeCollectFileName.lower())
                    if index != -1:
                        # print(f"\n获取到有效计划路线kmz文件")
                        item.updateFinished()
                        if item.mapsheetFileName in self.mapSheetTobeCollect_namelist_list_pop:
                            # 删除（弹出）已完成的文件名
                            self.mapSheetTobeCollect_namelist_list_pop.remove(item.mapsheetFileName)
                        # 显示剩余待接收的文件数量
                        self.remainFileNum()
                        return True
                else:
                    print(f"文件名中没有包含有效完成点名称: {on_observed_filename}")
                    return False
            else:
                print(f"无法从完成点文件名中匹配出有效日期（格式错误/日期不为当天): {on_observed_filename}")
                return False
        else:
            return False
            
    def __planKMZFileValidate(self, on_observed_filename):
        """验证KMZ文件的名称是否符合要求
        :param filename: 文件名
        :return: bool
        """
        if on_observed_filename.endswith(".kmz"):
            matchedDate_yyyymmdd_str = re.search(r'\d{8}', on_observed_filename)
            # print(f"从文件名称匹配到的日期: {matchedDate_yyyymmdd_str.group()}")
            on_observed_file_datetime = datetime.strptime(matchedDate_yyyymmdd_str.group(), "%Y%m%d")
            # 如果文件名中的日期大于当前日期,则合法
            if on_observed_file_datetime.date() > self.currentDate.date_datetime.date():
                on_observed_file_datetime_DateType = DateType(date_datetime=on_observed_file_datetime)
                for item in self.mapSheetTobeCollect:
                    toBeCollectFileName = item.mapsheetFileName  + '_plan_routes_' + on_observed_file_datetime_DateType.yyyymmdd_str
                    index = on_observed_filename.find(toBeCollectFileName.lower())
                    if index != -1:
                        # print(f"\n获取到有效计划路线kmz文件")
                        item.updatePlan()
                        return True
                else:
                    print(f"文件名中没有包含有效的计划路线名称: {on_observed_filename}")
                    return False
            else:
                print(f"无法从计划路线文件名中匹配出有效日期（格式错误/日期不为下一天): {on_observed_filename}")
                return False
        else:
            return False
        
    def obsserverService(self, event_handler, executor=None, endtime=None):
        """开始监视微信文件夹
        """
        wechat_path = os.path.join(WECHAT_FOLDER, self.currentDate.yyyy_mm_str)

        observer = Observer()
        observer.schedule(event_handler, wechat_path, recursive=True)
        observer.start()

        if self.plannedRouteFileNum > 0:

            # 第一次进入监控循环,显示当前待接收的文件列表
            if self.mapSheetTobeCollect_namelist_list_pop != []:
                self.remainFileNum()
                print(f"当前待接收的文件列表: {self.mapSheetTobeCollect_namelist_list_pop}")

            while self.mapSheetTobeCollect_namelist_list_pop != []:

                datetime_now = datetime.now()
                # 在每个MONIT_STATUS_INTERVAL_MINUTE分钟整点显示一次监控状态，第二个判断条件是为了避免在整点时显示多次
                if datetime_now.minute % MONITOR_STATUS_INTERVAL_MINUTE == 0 and (0 <= datetime_now.second < MONITOR_TIME_INTERVAL_SECOND):
                    print("\n")
                    print(15*"-",f"当前时间为 {datetime_now}, 持续监测中...", 15*"-")

                    self.remainFileNum()

                    # 如果当前时间超过晚上7点,则进入催促模式
                    if (datetime_now.hour >= 19 and datetime_now.minute >= 0) or (len(self.mapSheetTobeCollect_namelist_list_pop) <= 5):
                        print(f"进入催促模式...")
                        for item_filename in self.mapSheetTobeCollect_namelist_list_pop:
                            # 提醒发送催促消息
                            for item in self.mapSheetTobeCollect:
                                if item_filename == item.mapsheetFileName:
                                    print(f"请注意: {item.teamNumber}", f"{item.mapsheetFileName}文件未接收完成,责任人: {item.teamleader}")
                        print("\n")
                    # else:
                    #     print(f"当前待接收的文件列表: {self.mapSheetTobeCollect_namelist_list_pop}\n")

                # 每隔设定时间检查一次
                time.sleep(MONITOR_TIME_INTERVAL_SECOND)
                print(".", end="", flush=True)
                
            else:
                print(f"所有待接收的文件已经全部接收完成,退出监视...")
                if executor:
                    # 执行文件处理任务
                    executor()

                # 停止监视
                observer.stop()
                observer.join()
        else:

            print(f"当天没有待接收的完成点，转入计划路线接收模式...\n预计接停止收时间:", f"{endtime.hour:02}", ":", f"{endtime.minute:02}")
            # 时间同上
            while datetime.now() <= endtime:

                datetime_now = datetime.now()
                # 在每个MONITOR_STATUS_INTERVAL_MINUTE分钟整点显示一次监控状态，第二个判断条件是为了避免在整点时显示多次
                if datetime_now.minute % MONITOR_STATUS_INTERVAL_MINUTE == 0 and (0 <= datetime_now.second < MONITOR_TIME_INTERVAL_SECOND):
                    print("\n", 15*"-",f"当前时间为 {datetime_now}, 持续监测中", 15*"-")

                # 每隔设定时间检查一次
                time.sleep(MONITOR_TIME_INTERVAL_SECOND)
                print(".", end="", flush=True)

            else:
                print(f"已到截止时间:", f"{endtime.hour:02}", ":", f"{endtime.minute:02}分，停止接收路线计划,退出监视...")
                if executor:
                    # 执行文件处理任务
                    executor()

                # 停止监视
                observer.stop()
                observer.join()
    
    def remainFileNum(self):
        # 显示当前待接收的文件数量和列表和Plan的数量,表示为(n/m)格式
        print(f"当前待接收的文件数量/当日计划数量: {len(self.mapSheetTobeCollect_namelist_list_pop)}","/", self.plannedRouteFileNum)



        
if __name__ == "__main__":

    datenow = DateType(date_datetime=datetime.now())
    # 测试日期
    # datenow = DateType(date_datetime=datetime(2025, 4, 3))

    event_handler = DataHandler(currentDate=datenow)
    # 手动启动监视方法
    event_handler.obsserverService()
