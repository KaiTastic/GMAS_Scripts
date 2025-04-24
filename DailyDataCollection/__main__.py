import argparse
import os
import sys
from datetime import datetime
from config import *
from DailyFileGenerator import *
from tabulate import tabulate
from monitor import DataHandler

# 增强输出编码支持，确保中文字符正确显示
sys.stdout.reconfigure(encoding='utf-8')


# from contextlib import contextmanager

# @contextmanager
# def redirect_stdout_to_file(file_path):
#     """
#     重定向标准输出到文件
#     :param file_path: 输出文件路径
#     """
#     if file_path.lower() == 'default':
#         file_path = os.path.join(os.getcwd(), "exectue_log.txt")

#     if not os.path.exists(os.path.dirname(file_path)):
#         os.makedirs(os.path.dirname(file_path))

#     original_stdout = sys.stdout
#     original_stderr = sys.stderr
#     try:
#         with open(file_path, 'w') as f:
#             sys.stdout = f  # 重定向标准输出到文件
#             sys.stderr = f  # 重定向标准错误输出到文件
#             yield
#     finally:
#         sys.stdout = original_stdout
#         sys.stderr = original_stderr



def validate_date(date_str) -> DateType:
    """
    验证日期字符串的长度和格式
    :param date_str: 输入的日期字符串
    :param date_format: 日期格式，默认为 'YYYYMMDD'
    :return: 转换后的日期对象
    :raises ValueError: 如果日期格式不正确或长度不符合
    """
    if len(date_str) != 8:
        raise ValueError(f"日期长度不正确, 请确保长度为8位, 输入值: {date_str}")
    try:
        date_datetime = datetime.strptime(date_str, "%Y%m%d")
        return DateType(date_datetime=date_datetime)
    except ValueError:
        raise ValueError(f"日期不合法或格式不正确, 请确保格式为'YYYYMMDD', 输入值: {date_str}")


def validate_bool(value):
    """
    将字符串转换为布尔值
    :param value: 输入的字符串
    :return: 布尔值
    :raises ArgumentTypeError: 如果输入值不是合法的布尔值
    """
    if isinstance(value, bool):
        return value
    if value.lower() in {'true', '1', 'yes', 'y'}:
        return True
    elif value.lower() in {'false', '0', 'no', 'n'}:
        return False
    else:
        raise argparse.ArgumentTypeError(f"无效的布尔值: {value}")


def validate_time(time_str, time_format="%H%M%S"):
    """
    验证时间字符串的格式
    :param time_str: 输入的时间字符串
    :param time_format: 时间格式，默认为 'HHMMSS'
    :return: 转换后的时间对象
    :raises ValueError: 如果时间格式不正确
    """
    if len(time_str) != len(time_format.replace("%", "")):
        raise ValueError(f"时间长度不正确, 请确保长度为{len(time_format.replace('%', ''))}位, 输入值: {time_str}")
    try:
        return datetime.strptime(time_str, time_format).time()
    except ValueError:
        raise ValueError(f"时间不合法或格式不正确, 请确保格式为'{time_format}', 输入值: {time_str}")


def parse_args():
    """
    解析命令行参数
    无参数输入时, 默认--date为当天, 有参数时, 为指定参数
    """
    parser = argparse.ArgumentParser(description="处理日期字符串; 是否以监控模式持续监控微信文件夹; 是否停止监控的时间")
    parser.add_argument(
        "--date",
        nargs='?',
        default=datetime.now().strftime("%Y%m%d"),
        type=str,
        help="收集数据的日期, 默认为当天, 8位长度日期字符串, 格式为\'YYYYMMDD\'"
    )
    parser.add_argument(
        "--monitor",
        nargs='?',
        default=False,
        type=validate_bool,
        help="是否持续监控微信文件夹: 默认为False, 输入\'True(True/1/yes/y)'或\'False(False/0/no/n)'"
    )
    parser.add_argument(
        "--endtime",
        nargs='?',
        default=None,
        type=str,
        help="停止监控的时间, 长度为6位, 格式为\'HHMMSS\'"
    )
    # parser.add_argument(
    #     "--log",
    #     nargs='?',
    #     default=None,
    #     type=str,
    #     help="日志文件路径, 默认为当前目录下的log.txt"
    # )

    args = parser.parse_args()
    date_str = args.date
    monitor_bool = args.monitor
    endtime_str = args.endtime
    # log_file_path = args.log

    # 验证日期字符串的长度和格式
    try:
        date_datetype = validate_date(date_str)
    except ValueError as e:
        raise ValueError(f"日期验证失败: {e}")
    
    # 验证停止监控时间格式
    if endtime_str:
        try:
            endtime = validate_time(endtime_str)
        except ValueError as e:
            raise ValueError(f"停止监控时间验证失败: {e}")
    else:
        endtime = None

    # if log_file_path is not None:
    #         redirect_stdout_to_file(log_file_path)

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
    print("\n")
    print(15*"-", "设定日期：", date_datetype.yyyymmdd_str, f"当前系统时间：{datetime.now().strftime('%H:%M:%S')}", 15*"-", 1*'\n')


    if monitor_bool:
        # 监控模式
        # 增加一个默认终止时间
        if endtime is None:
            endtime = MONITOR_ENDTIME
        print(f"以监控模式运行中...\n监控状态刷新间隔为： {MONITOR_STATUS_INTERVAL_MINUTE}分钟\n监控停止时间为： {endtime.strftime('%H:%M:%S')}\n")


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
