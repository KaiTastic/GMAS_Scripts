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
from DailyFileGenerator import list_fullpath_of_files_with_keywords, find_files_with_max_number, KMZFile
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
                            print(f"文件{filename}中验证通过")
                        # 清除kmz对象
                        del kmz
                        if mapsheet_name not in self.collect_file_list:
                            self.collect_file_list.append(mapsheet_name)
                        else:
                            print(f"图幅{mapsheet_name}已经收集")
                        print(f"已收集的文件列表：{self.collect_file_list}, 还缺少的文件列表：{list(set(self.filelist) - set(self.collect_file_list))}")
                        if set(self.filelist) == set(self.collect_file_list):
                            print(f"当天计划路线中的图幅信息已全部收集")
                            # TODO: 调用数据收集函数
                            #! 暂时利用Version 1中的代码
                            # 执行 CMD 命令
                            # self.execute_collection()
                            self.execute_collection_version2()

                            exit()
        if not self.collect_file_list:
            print(f"还未收集到任何文件")
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
    def execute_collection_version2():
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
    # # 打印表格---------------------------
    #     map_name_list = []
    #     daily_collection_list = []
    #     daily_plan_list = []
    #     for key, value in collection.dailyFinishedPoints.items():
    #         map_name_list.append(key)
    #         daily_collection_list.append(collection.dailyFinishedPoints[key])
    #         daily_plan_list.append(collection.DailyPlans[key])

    #     # 计算每列的最大宽度
    #     max_len_index = max(len(str(i + 1)) for i in range(len(map_name_list)))
    #     max_len_map_name = max(len(name) for name in map_name_list)
    #     max_len_collection = max(len(str(collection)) for collection in daily_collection_list)
    #     max_len_plan = max(len(plan) for plan in daily_plan_list)

    #     # 定义表头
    #     headers = ["Seq", "Name", "Finished", "Plan"]
    #     header_lengths = [max_len_index, max_len_map_name, max_len_collection, max_len_plan]
    #     sums = sum(header_lengths) + 7 * 3

    #     # 打印表头
    #     header_row = f"{headers[0]:<{header_lengths[0]}} | {headers[1]:<{header_lengths[1]}} | {headers[2]:<{header_lengths[2]}} | {headers[3]:<{header_lengths[3]}}  |"
    #     print('\n'*2, "-" * len(header_row))
    #     print(header_row)
    #     print("-" * len(header_row))
    #     # 打印表格数据
    #     for i in range(len(map_name_list)):
    #         row = f"{i + 1:<{header_lengths[0]}} | {map_name_list[i]:<{header_lengths[1]}} | {daily_collection_list[i]:<{header_lengths[2]}} | {daily_plan_list[i]:<{header_lengths[3]}} |"
    #         print(row)
    #     print("-" * len(header_row))
    #     print(' '*max_len_index, '|', ' '*max_len_map_name, '|', f"{collection.totalDaiyIncreasePointNum}", '|', f"{collection.totalDailyPlanNum}")
    #     print("-" * len(header_row), '\n'*2)
    #     # 打印表格---------------------------
        pass


class Monitor(object):
    maps_info: dict = {}

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
        从100K图幅名称信息表中获取图幅的罗马名称和拉丁名称
        """
        print("开始获取图幅信息...")
        df = pd.read_excel(os.path.join(WORKSPACE, 'resource', 'private', SHEET_NAMES_LUT_100K), sheet_name="Sheet1", header=0, index_col=0)
        # 获取数据帧：筛选出 'Sequence' 列值在 SEQUENCE_MIN 和 SEQUENCE_MAX 之间的行
        filtered_df = df[(df['Sequence'] >= SEQUENCE_MIN) & (df['Sequence'] <= SEQUENCE_MAX)]
        # 确保 'Sequence' 列为 int 类型
        filtered_df.loc[:, 'Sequence'] = filtered_df['Sequence'].astype(int)
        #TODO: 需要增加判断，如果Sequence列中有重复值，需要报错
        #TODO: 需要增加判断，如果Sequence列中去除的值不等于 SEQUENCE_MAX - SEQUENCE_MIN + 1，需要报错
        # # 按照 'Sequence' 列值从小到大排序
        sorted_df = filtered_df.sort_values(by='Sequence')
        # # 获取图幅名称、罗马名称和拉丁名称，并存储为字典
        # 构建以 'Sequence' 为键的字典
        cls.maps_info = {
            row['Sequence']: {
                # 'Sheet ID': row['Alternative sheet ID'],
                'Group': row['Group'],
                'File Name': row['File Name'],
                'Roman Name': row['Roman Name'],
                'Latin Name': row['Latin Name']
            }
            for _, row in sorted_df.iterrows()
        }
        print("图幅信息获取完成")
        return cls.maps_info

    def __setMapsheetList(self):
        # 设置每天需要收集的图幅列表
        # 检查当天PlanRoutes文件夹是否存在，同时获取当天的计划路线列表
        plan_routes_folder = os.path.join(WORKSPACE, self.currentDate.yyyymm_str, self.currentDate.yyyymmdd_str, "Planned routes")
        # 如果当天的计划路线文件夹存在，则获取当天的计划路线列表
        mapsheet_list = []
        if os.path.exists(plan_routes_folder) and os.path.isdir(plan_routes_folder):
            plan_routes_list = [file for file in os.listdir(plan_routes_folder) if file.endswith(".kmz")]
            print(f"当天计划路线列表：{plan_routes_list}")
            for file_name in plan_routes_list:
                lower_file_name = file_name.lower()
                index = lower_file_name.find('_plan_routes_')
                if index != -1:
                    mapsheet_list.append(file_name[:index])
            print(f"当天计划路线中的图幅名称列表：{mapsheet_list}")
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
            MyHandler.execute_collection_version2
            print("数据收集完成")
            exit()


if __name__ == "__main__":
    datenow = DateType(date_datetime=datetime.now())
    # 测试日期
    # datenow = DateType(date_datetime=datetime(2024, 12, 26))
    wechat_path = os.path.join(WECHAT_FOLDER, datenow.yyyy_mm_str)
    currentdatefilelist = Monitor(datenow)
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