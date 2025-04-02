import argparse
import os
from datetime import datetime
from config import *
from DailyFileGenerator import *
from tabulate import tabulate
from monitor import DataHandler


def parse_args():
    """
    解析命令行参数
    无参数输入时，默认--date为当天，有参数时，为指定参数
    """
    parser = argparse.ArgumentParser(description="处理日期字符串")
    parser.add_argument("--date", nargs='?', default=datetime.now().strftime("%Y%m%d"), type=str, help="8位长度日期字符串，格式为\'YYYYMMDD\'")
    parser.add_argument("--monitor", nargs='?', default=False, type=bool, help="是否持续监控微信文件夹")
    date_str = parser.parse_args().date
    monitor_bool = parser.parse_args().monitor
    if len(date_str) == 8:
        try:
            datetime.strptime(date_str, "%Y%m%d")
        except ValueError:
            raise ValueError("日期不合法或格式不正确，请确保格式为'YYYYMMDD'")
    else:
        raise ValueError("日期长度不正确，请确保长度为8位")
    return date_str, monitor_bool


class DataCollectNow():

    def __init__(self, colletionDate: DateType):
        """
        初始化数据采集类
        :param colletionDate: DateType 对象，包含日期信息
        """
        self.colletionDate = colletionDate

    def __call__(self):
        collection = CurrentDateFiles(self.colletionDate)
        # 在屏幕上显示文件结果和错误信息
        collection.onScreenDisplay()
        print("\n")
        print(f"文件中存在的错误信息：")
        for _ in collection.errorMsg:
            if _ != None:
                print(_)
        print('\n')

        # 将当天的点要素和线要素写入到 KMZ 文件
        collection.dailyKMZReport()
        # 生成每日报表的Excel文件
        collection.dailyExcelReport()
        # 将当天的点写入到Excel文件
        collection.dailyExcelReportUpdate()

        # 如果当天是设定的日期，则将 KMZ 文件转换为 SHP 文件，并将 SHP 文件拷贝至制图工程文件夹
        for weekday in COLLECTION_WEEKDAYS:
            if self.colletionDate.date_datetime.weekday() == weekday:
                print('\n'*2, f"今天是{self.colletionDate.date_datetime.strftime('%A')}，需要生成周报", '\n'*2)
                certainReport = DataSubmition(self.colletionDate, collection.allPoints)
                certainReport.weeklyPointToShp()


def main():

    date_str, monitor_bool = parse_args()
    print(3*'\n', 15*"-", "当前日期：", date_str, 15*"-")

    colletionDate = DateType(yyyymmdd_str=date_str)

    if monitor_bool:
        # 监控模式
        print("以监控模式运行中...")
        # 这里可以添加监控逻辑
        event_handler = DataHandler(currentDate=colletionDate)
        # 手动启动监视方法
        event_handler.obsserverService(event_handler=event_handler, executor=DataCollectNow(colletionDate))
    else:
        # 非监控模式
        print("以非监控模式运行中...")
        executor = DataCollectNow(colletionDate)
        executor()


if __name__ == "__main__":

    main()
