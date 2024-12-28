import argparse
import logging
import os
from datetime import datetime
from config import *
from DailyFileGenerator import *
from tabulate import tabulate


def parse_args():
    # 无参数输入时，默认date_str为当天，有参数时，为指定参数
    parser = argparse.ArgumentParser(description="处理日期字符串")
    parser.add_argument("--date_str", nargs='?', default=datetime.now().strftime("%Y%m%d"), type=str, help="日期字符串，格式为\'YYYYMMDD\'")
    return parser.parse_args()

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default='config.yaml', help='config file path')
    args = parse_args()


globalLogger = Logger(name='global logger', level=logging.INFO)

if __name__ == "__main__":
    
    today = DateType(date_datetime=datetime.now())
    # today = DateType(yyyymmdd_str='20241225')

    # 设置日志记录文件位置
    logfile = os.path.join(WORKSPACE, today.yyyymm_str, today.yyyymmdd_str, f"validateKMZfiles{today.yyyymmdd_str}.log")
    globalLogger = Logger(name='global logger', log_file=logfile, level=logging.INFO)

    collection = CurrentDateFiles(today)
    print('\n'*2)
    print(f"截止{today.yyyymmdd_str}完成的总点数：", collection.totalPointNum)
    print(f"截止{today.yyyymmdd_str}完成的总线路数：", collection.totalRoutesNum)
    print(f"{today.yyyymmdd_str}新增点数：", collection.totalDaiyIncreasePointNum)
    # print(f"{today.yyyymmdd_str}新增路线数：", collection.totalDaiyIncreaseRouteNum)
    print(f"{today.yyyymmdd_str}计划路线数：", collection.totalDailyPlanNum)
    print(f"错误信息：", collection.errorMsg)

    # 生成表格并输出---------------------------
    summary_table = ["", "", collection.totalDaiyIncreasePointNum, collection.totalDailyPlanNum]
    map_name_list = []
    daily_collection_list = []
    daily_plan_list = []
    for key, value in collection.dailyFinishedPoints.items():
        map_name_list.append(key)
        x = ''  # Define x with an appropriate value
        daily_collection_list.append(x if collection.dailyFinishedPoints[key] == 0 else collection.dailyFinishedPoints[key])
        daily_plan_list.append(collection.DailyPlans[key])
    table_data = []
    for i in range(len(map_name_list)):
        table_data.append([i + 1, map_name_list[i], daily_collection_list[i], daily_plan_list[i]])
    table_data.append(["", "", collection.totalDaiyIncreasePointNum, collection.totalDailyPlanNum])
    print('\n'*2)
    headers = ["Seq", "Name", "Finished", "Plan"]
    print(tabulate(table_data, headers, tablefmt="grid"))
    print('\n'*2)
    # 生成表格并输出---------------------------
    
    # 将当天的点要素和线要素写入到 KMZ 文件
    collection.dailyKMZReport()
    # 生成Excel文件
    collection.dailyExcelReport()
    # 将当天的点写入到Excel文件
    collection.dailyExcelReportUpdate()

    # 如果当天是设定的日期，则将 KMZ 文件转换为 SHP 文件，并将 SHP 文件拷贝至制图工程文件夹
    for weekday in COLLECTION_WEEKDAYS:
        if today.date_datetime.weekday() == weekday:
            print('\n'*2, f"今天是{today.date_datetime.strftime('%A')}，需要生成周报", '\n'*2)
            certainReport = DataSubmition(today, collection.allPoints)
            certainReport.weeklyPointToShp()

    # 关闭日志记录器
    globalLogger.close(message="日志记录器关闭, 程序结束")