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


globalLogger = Logger(name='global logger', level=logging.INFO)

if __name__ == "__main__":
    
    today = DateType(date_datetime=datetime.now())
    # today = DateType(yyyymmdd_str='20241221')

    # 设置日志记录文件位置
    logfile = os.path.join(WORKSPACE, today.yyyymm_str, today.yyyymmdd_str, f"validateKMZfiles{today.yyyymmdd_str}.log")
    globalLogger = Logger(name='global logger', log_file=logfile, level=logging.INFO)

    collection = CurrentDateFiles(today)
    print(f"截止{today.yyyymmdd_str}完成的总点数：", collection.totalPointNum)
    print(f"截止{today.yyyymmdd_str}完成的总线路数：", collection.totalRoutesNum)
    print(f"{today.yyyymmdd_str}新增点数：", collection.totalDaiyIncreasePointNum)
    # print(f"{today.yyyymmdd_str}新增路线数：", collection.totalDaiyIncreaseRouteNum)
    print(f"{today.yyyymmdd_str}计划路线数：", collection.totalDailyPlanNum)
    print(f"错误信息：", collection.errorMsg)
    print(json.dumps(collection.dailyFinishedPoints, indent=4, ensure_ascii=False))
    print(json.dumps(collection.DailyPlans, indent=4, ensure_ascii=False))

    # 将当天的点要素和线要素写入到 KMZ 文件
    collection.dailyKMZReport()
    # 将当天的点写入到Excel文件
    collection.dailyExcelReport()


    # 如果当天是设定的日期，则将 KMZ 文件转换为 SHP 文件，并将 SHP 文件拷贝至制图工程文件夹
    for weekday in COLLECTION_WEEKDAYS:
        if today.date_datetime.weekday() == weekday:
            print(f"今天是星期{today.date_datetime.strftime('%A')}，需要生成周报")
            certainReport = DataSubmition(today, collection.allPoints)
            certainReport.weeklyPointToShp()

    # 关闭日志记录器
    globalLogger.close(message="日志记录器关闭, 程序结束")