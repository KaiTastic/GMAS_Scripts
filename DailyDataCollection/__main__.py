import argparse
import os
from datetime import datetime
from config import *
from DailyFileGenerator import *
from tabulate import tabulate


def parse_args():
    """
    解析命令行参数
    无参数输入时，默认--date为当天，有参数时，为指定参数
    """
    parser = argparse.ArgumentParser(description="处理日期字符串")
    parser.add_argument("--date", nargs='?', default=datetime.now().strftime("%Y%m%d"), type=str, help="8位长度日期字符串，格式为\'YYYYMMDD\'")
    date_str = parser.parse_args().date
    if len(date_str) == 8:
        try:
            datetime.strptime(date_str, "%Y%m%d")
        except ValueError:
            raise ValueError("日期不合法或格式不正确，请确保格式为'YYYYMMDD'")
    else:
        raise ValueError("日期长度不正确，请确保长度为8位")
    return date_str

def main():

    date_str = parse_args()
    print("\n", f"日期: {date_str}")

    colletionDate = DateType(yyyymmdd_str=date_str)
    collection = CurrentDateFiles(colletionDate)

    # 生成表格并输出---------------------------
    collection.onScreenDisplay()
    print("\n")
    
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
        if colletionDate.date_datetime.weekday() == weekday:
            print('\n'*2, f"今天是{colletionDate.date_datetime.strftime('%A')}，需要生成周报", '\n'*2)
            certainReport = DataSubmition(colletionDate, collection.allPoints)
            certainReport.weeklyPointToShp()


if __name__ == "__main__":

    main()
