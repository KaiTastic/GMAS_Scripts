"""
This module is used to monitor the daily data collection process. It will check the status of the data collection.
用来监视微信文件夹中数据的更新
"""

import os
from config import *
from datetime import datetime
import pandas as pd
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from DailyFileGenerator import KMZFile, MapsheetDailyFile, CurrentDateFiles, list_fullpath_of_files_with_keywords, find_files_with_max_number
import re
import subprocess


def monitor_folder(duration):
    """
    监视文件夹中的文件变化，动态显示剩余时间
    :param duration: 监视的总时间（秒）
    """
    start_time = time.time()
    end_time = start_time + duration

    while time.time() < end_time:
        remaining_time = int(end_time - time.time())
        print(f"监视文件夹中的文件变化，剩余时间：{remaining_time} 秒", end='\r')
        time.sleep(1)

    print("\n微信文件夹持续监视中...'")

class MyHandler(FileSystemEventHandler):
    def __init__(self, date: DateType, filelist: list):
        self.date = date
        self.filelist = filelist
        self.collect_file_list = []

    def on_created(self, event):
        # print(f'File created: {event.src_path}')
        # print(f'有文件创建更新')
        filename = os.path.basename(event.src_path)
        if filename.endswith(".kmz"):
            match = re.search(r'\d{8}', filename)
            if match and match.group() == self.date.yyyymmdd_str:
                lower_filename = filename.lower()
                index = lower_filename.find('_finished_points_and_tracks_')
                if index != -1:
                    mapsheet_name = filename[:index]
                    if mapsheet_name.lower() in [item.lower() for item in self.filelist]:
                        print(f"\n获取到kmz文件，验证kmz文件中...")
                        kmz = KMZFile(event.src_path)
                        if kmz.errorMsg:
                            print(f"文件{filename}中存在错误：{kmz.errorMsg}")
                        else:
                            print(f"文件{filename}验证通过")
                            #TODO: 需要执行当天的点数量检查
                            filenameDaily = MapsheetDailyFile(mapsheet_name, self.date)
                            print(f"{self.date.yyyymmdd_str}日{filename}完成点数：{filenameDaily.dailyincreasePointNum}")
                            del filenameDaily
                        # 清除kmz对象
                        del kmz
                        if mapsheet_name not in self.collect_file_list:
                            self.collect_file_list.append(mapsheet_name)
                        else:
                            print(f"图幅{mapsheet_name}已经收集")
                        print(f"已收集的文件列表：{self.collect_file_list}, 还缺少的文件列表：{list(set(self.filelist) - set(self.collect_file_list))}")
                        if set(self.filelist) == set(self.collect_file_list):
                            print(f"当天计划路线中的图幅信息已全部收集")
                            time.sleep(30)
                            # TODO: 调用数据收集函数
                            #! 暂时利用Version 1中的代码
                            # 执行 CMD 命令
                            # self.execute_collection()
                            self.execute_collection_version_2()
                            exit()
        if not self.collect_file_list:
            print(f"未收集到任何文件")
        print("继续监视目标文件夹...")

    def execute_collection_version1(self):
        print("开始数据收集...")
        cmd_command = f"python310 D:\RouteDesigen\PythonRun\daily_statistics.py {self.date.yyyymmdd_str}"
        print(cmd_command)
        result = subprocess.run(cmd_command, shell=True, capture_output=True, text=True)
        print(result.stdout)
        print("数据收集完成，开始合并KMZ文件...")
        cmd_command = f"python310 D:\RouteDesigen\PythonRun\mergeKMZandRender.py {self.date.yyyymmdd_str}"
        print(cmd_command)
        result = subprocess.run(cmd_command, shell=True, capture_output=True, text=True)
        print(result.stdout)
        print("合并KMZ文件完成")
    
    @staticmethod
    def execute_collection_version_2():
        print("开始数据收集...")
        cmd_command = f"python310 D:\MacBook\MacBookDocument\SourceCode\GMAS\dailyDataCollection\main.py"
        result = subprocess.run(cmd_command, shell=True, capture_output=True, text=True)
        print(result.stdout)
        print("数据收集完成")

    # def on_deleted(self, event):
    #     print(f'File deleted: {event.src_path}')
    
    # def on_moved(self, event):
    #     print(f'File moved: from {event.src_path} to {event.dest_path}')

    def reportTable(self):
         pass


class Monitor(object):
    maps_info: dict = None

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.mapsInfo()
            cls.instance = super(Monitor, cls).__new__(cls)
        return cls.instance

    def __init__(self, currentDate):
        self.currentDate = currentDate
        self._mapsheet_filename_list = []
        self.__setMapsheetList()
        self.mapdicts ={}

    @classmethod
    def mapsInfo(cls):
        """
        调用CurrentDateFiles类中的mapsInfo方法，从100K图幅名称信息表中获取图幅的罗马名称和拉丁名称
        """
        # print("开始获取图幅信息...")
        cls.maps_info = CurrentDateFiles.mapsInfo()
        # print(cls.maps_info)
        # print("图幅信息获取完成")
        return cls.maps_info

    def __setMapsheetList(self):
        # 设置每天需要收集的图幅列表
        # 检查当天PlanRoutes文件夹是否存在，同时获取当天的计划路线列表
        plan_routes_folder = os.path.join(WORKSPACE, self.currentDate.yyyymm_str, self.currentDate.yyyymmdd_str, "Planned routes")
        # 如果当天的计划路线文件夹存在，则获取当天的计划路线列表
        mapsheet_list = []
        if os.path.exists(plan_routes_folder) and os.path.isdir(plan_routes_folder):
            plan_routes_list = [file for file in os.listdir(plan_routes_folder) if file.endswith(".kmz")]
            # print(f"当天计划路线列表：{plan_routes_list}")
            for file_name in plan_routes_list:
                lower_file_name = file_name.lower()
                index = lower_file_name.find('_plan_routes_')
                if index != -1:
                    mapsheet_list.append(file_name[:index])
            print(f"{self.currentDate}当天计划路线中的图幅数量：{len(mapsheet_list)}")
            print(f"{self.currentDate}当天计划路线中的图幅名称列表：{mapsheet_list}")
            mapsheet_filename_list = [info['File Name'] for mapsheet in mapsheet_list for sequence, info in self.maps_info.items() if info['File Name'].lower() == mapsheet.lower()]
            self._mapsheet_filename_list = mapsheet_filename_list
            if len(self._mapsheet_filename_list) == len(plan_routes_list):
                print(f"当天计划路线中的图幅信息获取成功")
                return True
            else:
                print(f"当天计划路线中的图幅信息获取失败")
                return False

    def __contains__(self, item):
        return item in self._mapsheet_filename_list
    
    def starter(self):
        # 获取微信文件夹路径
        for mapsheet_filename in self._mapsheet_filename_list:
            mapsheet_dict = {}
            # 获取每个图幅的文件路径
            fullpath_finished = list_fullpath_of_files_with_keywords(wechat_path, [mapsheet_filename, 'finished_points_and_tracks', '.kmz', self.currentDate.yyyymmdd_str])
            #TODO: 需要增加判断，修改为第二天的计划路线文件夹
            # fullpath_plan = list_fullpath_of_files_with_keywords(wechat_path, [mapsheet_filename, 'plan_routes', '.kmz', self.currentDate.yyyymm_str])

            if fullpath_finished:
                mapsheet_dict["Finished"] = "Acquired"
                mapsheet_dict["Finished File Number"] = len(fullpath_finished)
                # print(fullpath_finished)
            else:
                mapsheet_dict["Finished"] = ""
                mapsheet_dict["Finished File Number"] = 0
            # if fullpath_finished:
            #     mapsheet_dict["Plan"] = "Acquired"
            #     mapsheet_dict["Plan File Number"] = len(fullpath_plan)
            # else:
            #     mapsheet_dict["Plan"] = ""
            #     mapsheet_dict["Plan File Number"] = 0
            self.mapdicts[mapsheet_filename] = mapsheet_dict
        print(self.mapdicts)

        collect_flag_list = []
        for key, value in self.mapdicts.items():
            # 如果所有的值Finished都>0，则直接调用数据收集函数
            if value["Finished File Number"] > 0:
                print(f"图幅{key}的文件已经收集")
                collect_flag_list.append(True)
            else:
                collect_flag_list.append(False)
        if all(collect_flag_list):
            print("当天完成点已经收齐，开始启动数据收集")
            MyHandler.execute_collection_version_2
            print("数据收集完成")
            exit()


if __name__ == "__main__":
    datenow = DateType(date_datetime=datetime.now())
    # 测试日期
    # datenow = DateType(date_datetime=datetime(2024, 12, 26))
    wechat_path = os.path.join(WECHAT_FOLDER, datenow.yyyy_mm_str)
    currentdatefilelist = Monitor(datenow)
    # print(currentdatefilelist._mapsheet_filename_list)
    currentdatefilelist.starter()

    event_handler = MyHandler(date=datenow, filelist=currentdatefilelist._mapsheet_filename_list)

    observer = Observer()
    observer.schedule(event_handler, wechat_path, recursive=True)

    print(5*'\n', 5*"*", "当前日期：", datenow.yyyymmdd_str, 5*"*")
    print(f'开始监视微信文件夹...\n')
    observer.start()

    try:
        while True:
            time.sleep(300)
            print(f"{datetime.now()}")
            print("继续监视中...\n")
    except KeyboardInterrupt:
        observer.stop()
    observer.join()