import argparse
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


if __name__ == "__main__":
    
    today = DateType(date_datetime=datetime.now())
    # today = DateType(yyyymmdd_str='20250321')

    collection = CurrentDateFiles(today)

    # 生成表格并输出---------------------------
    collection.onScreenDisplay()
    print("\n")
    
    # print(f"截止{today.yyyymmdd_str}完成的总点数：", collection.totalPointNum)
    # print(f"截止{today.yyyymmdd_str}完成的总线路数：", collection.totalRoutesNum)
    # print(f"{today.yyyymmdd_str}新增点数：", collection.totalDaiyIncreasePointNum)
    # print(f"{today.yyyymmdd_str}新增路线数：", collection.totalDaiyIncreaseRouteNum)
    # print(f"{today.yyyymmdd_str}计划路线数：", collection.totalDailyPlanNum)
    print(f"文件中存在的错误信息：")
    for _ in collection.errorMsg:
        if _ != None:
            print(_)

    print('\n'*2)

    # 将当天的点要素和线要素写入到 KMZ 文件
    collection.dailyKMZReport()
    # 生成每日报表的Excel文件
    collection.dailyExcelReport()
    # 将当天的点写入到Excel文件
    collection.dailyExcelReportUpdate()

    # 如果当天是设定的日期，则将 KMZ 文件转换为 SHP 文件，并将 SHP 文件拷贝至制图工程文件夹
    for weekday in COLLECTION_WEEKDAYS:
        if today.date_datetime.weekday() == weekday:
            print('\n'*2, f"今天是{today.date_datetime.strftime('%A')}，需要生成周报", '\n'*2)
            certainReport = DataSubmition(today, collection.allPoints)
            certainReport.weeklyPointToShp()
