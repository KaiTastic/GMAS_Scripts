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
    无参数输入时, 默认--date为当天, 有参数时, 为指定参数
    """
    parser = argparse.ArgumentParser(description="处理日期字符串; 是否以监控模式持续监控微信文件夹; 是否停止监控的时间")
    parser.add_argument("--date", nargs='?', default=datetime.now().strftime("%Y%m%d"), type=str, help="收集数据的日期, 默认为当天, 8位长度日期字符串, 格式为\'YYYYMMDD\'")
    parser.add_argument("--monitor", nargs='?', default=False, type=bool, help="是否持续监控微信文件夹")
    parser.add_argument("--endtime", nargs='?', default=None, type=str, help="停止监控的时间, 长度为6位, 格式为\'HHMMSS\'")

    date_str = parser.parse_args().date
    monitor_bool = parser.parse_args().monitor
    endtime_str = parser.parse_args().endtime

    # 验证日期字符串的长度和格式
    if len(date_str) == 8:
        try:
            datetime.strptime(date_str, "%Y%m%d")
            date_datetype = DateType(yyyymmdd_str=date_str)
        except ValueError:
            raise ValueError("日期不合法或格式不正确, 请确保格式为'YYYYMMDD'")
    else:
        raise ValueError("日期长度不正确, 请确保长度为8位")
    
    # 验证监控模式参数
    if isinstance(monitor_bool, bool):
        monitor_bool = monitor_bool
    else:
        raise ValueError("监控模式参数不合法, 请确保为布尔值")
    
    # 验证停止监控时间格式
    if endtime_str:
        if len(endtime_str) == 6:
            try:
                endtime = datetime.strptime(endtime_str, "%H%M%S")
            except ValueError:
                raise ValueError("时间不合法或格式不正确, 请确保格式为'HHMMSS'")
        else:
            raise ValueError("时间长度不正确, 请确保长度为6位")
    else:
        endtime = None
    return date_datetype, monitor_bool, endtime


class DataCollectNow():

    def __init__(self, colletionDate: DateType):
        """
        初始化数据采集类
        :param colletionDate: DateType 对象, 包含日期信息
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

        # 如果当天是设定的日期, 则将 KMZ 文件转换为 SHP 文件, 并将 SHP 文件拷贝至制图工程文件夹
        for weekday in COLLECTION_WEEKDAYS:
            if self.colletionDate.date_datetime.weekday() == weekday:
                print('\n'*2, f"今天是{self.colletionDate.date_datetime.strftime('%A')}, 需要生成周报", '\n'*2)
                certainReport = DataSubmition(self.colletionDate, collection.allPoints)
                certainReport.weeklyPointToShp()


def main():

    date_datetype, monitor_bool, endtime = parse_args()
    print(1*'\n',15*"-", "当前日期：", date_datetype.yyyymmdd_str, 15*"-", 1*'\n')


    if monitor_bool:
        # 监控模式
        # 增加一个默认终止时间
        if endtime is None:
            endtime = datetime.now().replace(hour=20, minute=30, second=0, microsecond=0)
        print(f"以监控模式运行中...\n文件夹状态监控刷新间隔为{MONIT_STATUS_INTERVAL_MINUTE}分钟，监控停止时间为：", f"{endtime.hour:02}", ":", f"{endtime.minute:02}")


        # 这里可以添加监控逻辑
        event_handler = DataHandler(currentDate=date_datetype)
        # 手动启动监视方法
        event_handler.obsserverService(event_handler=event_handler, executor=DataCollectNow(date_datetype), endtime=endtime)
    else:
        # 非监控模式
        print("以非监控模式运行中...")
        executor = DataCollectNow(date_datetype)
        executor()


if __name__ == "__main__":

    main()
