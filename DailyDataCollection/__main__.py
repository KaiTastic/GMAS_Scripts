import argparse
import os
import sys
import logging
from datetime import datetime
from config import *
from DailyFileGenerator_compat import *
from tabulate import tabulate

# 导入编码修复器
from core.utils.encoding_fixer import setup_encoding, safe_print

# 设置UTF-8编码环境
setup_encoding()

# 增强输出编码支持，确保中文字符正确显示
import io
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 设置环境变量确保一致的UTF-8编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 配置日志 - 确保所有处理器都使用UTF-8编码
file_handler = logging.FileHandler('gmas_collection.log', encoding='utf-8')
console_handler = logging.StreamHandler()
console_handler.setStream(sys.stdout)  # 使用已重新配置的stdout

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger(__name__)

# 尝试导入重构后的监控模块，如果失败则使用传统版本
try:
    from core.monitor import MonitorManager
    MONITOR_VERSION = "NEW"
    logger.info("成功导入重构后的监控模块")
except ImportError as e:
    logger.warning(f"无法导入重构后的监控模块: {e}")
    try:
        from deprecated.monitor_legacy import DataHandler
        MONITOR_VERSION = "LEGACY_DEPRECATED"
        logger.info("使用deprecated目录中的传统监控模块")
    except ImportError:
        try:
            from monitor import DataHandler
            MONITOR_VERSION = "LEGACY_CURRENT"
            logger.info("使用当前目录中的传统监控模块")
        except ImportError as e2:
            logger.error(f"无法导入任何监控模块: {e2}")
            MONITOR_VERSION = "NONE"


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
    expected_length = 6  # HHMMSS 格式应该是6位
    if len(time_str) != expected_length:
        raise ValueError(f"时间长度不正确, 请确保长度为{expected_length}位, 输入值: {time_str}")
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
        print(f"文件中存在的错误信息: ")
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


def start_monitoring_with_compatibility(date_datetype, endtime):
    """
    启动监控服务，支持新旧版本的自动兼容
    
    Args:
        date_datetype: DateType对象，包含日期信息
        endtime: 停止监控的时间
    
    Returns:
        bool: 是否成功启动监控
    """
    executor = DataCollectNow(date_datetype)
    
    if MONITOR_VERSION == "NEW":
        return start_new_monitoring(date_datetype, endtime, executor)
    elif MONITOR_VERSION in ["LEGACY_DEPRECATED", "LEGACY_CURRENT"]:
        return start_legacy_monitoring(date_datetype, endtime, executor)
    else:
        logger.error("没有可用的监控模块")
        print("错误: 无法启动监控服务，没有可用的监控模块")
        return False


def start_new_monitoring(date_datetype, endtime, executor):
    """
    使用新的模块化监控系统
    """
    try:
        logger.info("使用重构后的监控模块启动监控...")
        safe_print("使用新版模块化监控系统")
        
        # 从配置文件导入模糊匹配设置
        from config import ENABLE_FUZZY_MATCHING, FUZZY_MATCHING_THRESHOLD, FUZZY_MATCHING_DEBUG
        
        # 创建监控管理器（使用配置文件中的模糊匹配设置）
        monitor_manager = MonitorManager(
            current_date=date_datetype,
            enable_fuzzy_matching=ENABLE_FUZZY_MATCHING,
            fuzzy_threshold=FUZZY_MATCHING_THRESHOLD
        )
        
        # 显示模糊匹配配置
        if ENABLE_FUZZY_MATCHING:
            safe_print(f"模糊匹配已启用 (阈值: {FUZZY_MATCHING_THRESHOLD})")
            if FUZZY_MATCHING_DEBUG:
                safe_print("模糊匹配调试模式已启用")
        else:
            safe_print("使用精确匹配模式")
        
        # 定义完成后的处理函数
        def post_processing():
            logger.info("文件监控完成，开始执行数据收集...")
            try:
                executor()
                logger.info("数据收集任务完成")
            except Exception as e:
                logger.error(f"数据收集任务执行出错: {e}")
        
        # 构建结束时间
        if endtime:
            end_datetime = datetime.combine(date_datetype.date_datetime.date(), endtime)
        else:
            end_datetime = MONITOR_ENDTIME
        
        # 启动监控
        monitor_manager.start_monitoring(
            executor=post_processing,
            end_time=end_datetime
        )
        
        logger.info("新版监控服务已结束")
        return True
        
    except Exception as e:
        logger.error(f"新版监控启动失败: {e}")
        logger.info("尝试回退到传统监控模块...")
        return start_legacy_monitoring(date_datetype, endtime, executor)


def start_legacy_monitoring(date_datetype, endtime, executor):
    """
    使用传统的监控系统
    """
    try:
        logger.info("使用传统监控模块启动监控...")
        print("使用传统监控系统")
        
        # 构建结束时间
        if endtime:
            end_datetime = datetime.combine(date_datetype.date_datetime.date(), endtime)
        else:
            end_datetime = MONITOR_ENDTIME
        
        # 创建传统事件处理器
        event_handler = DataHandler(currentDate=date_datetype)
        
        # 启动传统监控
        event_handler.obsserverService(
            event_handler=event_handler, 
            executor=executor, 
            endtime=end_datetime
        )
        
        logger.info("传统监控服务已结束")
        return True
        
    except Exception as e:
        logger.error(f"传统监控启动失败: {e}")
        print(f"错误: 监控服务启动失败 - {e}")
        return False


def main():

    date_datetype, monitor_bool, endtime = parse_args()
    print("\n")
    print(15*"-", "设定日期: ", date_datetype.yyyymmdd_str, f"当前系统时间: {datetime.now().strftime('%H:%M:%S')}", 15*"-", 1*'\n')

    # 显示监控模块版本信息
    version_info = {
        "NEW": "重构版模块化监控系统",
        "LEGACY_DEPRECATED": "传统监控系统 (deprecated目录)",
        "LEGACY_CURRENT": "传统监控系统 (当前目录)",
        "NONE": "无可用监控模块"
    }
    print(f"监控模块状态: {version_info.get(MONITOR_VERSION, '未知')}")

    if monitor_bool:
        # 监控模式
        # 增加一个默认终止时间
        if endtime is None:
            endtime = MONITOR_ENDTIME.time()
            
        print(f"以监控模式运行中...\n监控状态刷新间隔为:  {MONITOR_STATUS_INTERVAL_MINUTE}分钟\n监控停止时间为:  {endtime.strftime('%H:%M:%S') if hasattr(endtime, 'strftime') else endtime}\n")

        # 启动兼容性监控
        success = start_monitoring_with_compatibility(date_datetype, endtime)
        if not success:
            print("监控启动失败，转为非监控模式运行...")
            logger.warning("监控启动失败，执行单次数据收集")
            executor = DataCollectNow(date_datetype)
            executor()
    else:
        # 非监控模式
        print("以非监控模式运行中...")
        executor = DataCollectNow(date_datetype)
        executor()


if __name__ == "__main__":

    main()
