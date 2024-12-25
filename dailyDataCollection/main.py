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
    
    date_str = "20241221"
    currentDate = DateType(yyyymmdd_str=date_str)

    # 设置日志记录文件位置
    logfile = os.path.join(WORKSPACE, currentDate.yyyymm_str, currentDate.yyyymmdd_str, f"validateKMZfiles{currentDate.yyyymmdd_str}.log")
    globalLogger = Logger(name='global logger', log_file=logfile, level=logging.INFO)

    collection = CurrentDateFiles(currentDate)
    print(f"{currentDate.yyyymmdd_str}新增点数：", collection.totalDaiyIncreasePointNum)
    print(f"{currentDate.yyyymmdd_str}新增路线数：", collection.totalDaiyIncreaseRouteNum)
    print(f"计划路线：", collection.totalDailyPlans)
    print(f"错误信息：", collection.errorMsg)
    print(f"截止{currentDate.yyyymmdd_str}完成的总点数：", collection.totalPointNum)
    print(f"截止{currentDate.yyyymmdd_str}完成的总线路数：", collection.totalRoutesNum)
    # print(f"截止{currentDate.yyyymmdd_str}完成的所有点要素：", collection.allPoints)
    print(f"截止{currentDate.yyyymmdd_str}完成的所有点要素个数数：", len(collection.allPoints))
    # print(f"截止{currentDate.yyyymmdd_str}所有线要素：", collection.allRoutes)
    print(f"截止{currentDate.yyyymmdd_str}所有线要素个数数：", len(collection.allRoutes))
    print(collection.dailyFinishedPoints)

    # 将当天的点要素和线要素写入到 KMZ 文件
    pointDict = collection.allPoints
    pointDict_len = len(pointDict)
    print(pointDict_len)
    # print(pointDict)
    routeDict = collection.allRoutes
    routeDict_len = len(routeDict)
    print(routeDict_len)
    # print(routeDict)

    KMZFile(placemarks=PlacemarkerData(points=pointDict, pointsCount=pointDict_len, routes=routeDict, routesCount=routeDict_len)).writeas(kmz_path=os.path.join(WORKSPACE, currentDate.yyyymm_str, currentDate.yyyymmdd_str, f"GMAS_Points_and_tracks_until_{currentDate.yyyymmdd_str}.kmz") )

    # 将当天的点写入到Excel文件
    collection.dailyExcelReport()


    # 如果当天是设定的日期，则将 KMZ 文件转换为 SHP 文件，并将 SHP 文件拷贝至制图工程文件夹
    for weekday in COLLECTION_WEEKDAYS:
        if currentDate.date_datetime.weekday() == weekday:
            certainReport = DataSubmition(currentDate, collection.allPoints)
            certainReport.weeklyPointToShp()

    # 关闭日志记录器
    globalLogger.close(message="日志记录器关闭, 程序结束")