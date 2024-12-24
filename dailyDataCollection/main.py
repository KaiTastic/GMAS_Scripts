import argparse
import logging
import os
from datetime import datetime
from config import *
from DailyFileGenerator import *


def parse_args():
    # 无参数输入时，默认date_str为当天，有参数时，为指定参数
    parser = argparse.ArgumentParser(description="处理日期字符串")
    parser.add_argument("--date_str", nargs='?', default=datetime.now().strftime("%Y%m%d"), type=str, help="日期字符串，格式为\'YYYYMMDD\'")
    return parser.parse_args()

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default='config.yaml', help='config file path')
    args = parse_args()


if __name__ == '__main__':

    date_str = "20210101"

    # 将日期字符串转换为datetime对象
    date_datetime = datetime.strptime(date_str, "%Y%m%d")
    # 格式化日期字符串年月, 2021010
    yearAndmonth_str = date_datetime.strftime("%Y%m")

    # 设置日志记录文件位置
    log_file = os.path.join(WORKSPACE, yearAndmonth_str, date_str, f"validateKMZfiles{date_str}.log")
    golobaLogger = Logger(name='my_logger', log_file=log_file, level=logging.INFO)


    # 如果当天是设定的日期，则将 KMZ 文件转换为 SHP 文件，并将 SHP 文件拷贝至制图工程文件夹
    for weekday in COLLECTION_WEEKDAYS:
        if date_datetime.weekday() == weekday:
            certainReport = DataSubmition(date_str)
            certainReport.toShp(pointCoords)

    # 关闭日志记录器
    golobaLogger.close(message="日志记录器关闭, 程序结束")
