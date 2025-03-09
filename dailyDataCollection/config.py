import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
from pickle import EMPTY_DICT
import sys
from dataclasses import dataclass
from datetime import datetime
import os
import time
from functools import wraps


"""
初始设置（常量）
"""

# 工作文件夹
WORKSPACE = r"D:\RouteDesigen"
# 当前的微信聊天记录的文件夹， 请根据实际情况修改
# 一般为"文档\WeChat Files\WeChat Files\微信号\FileStorage\File"
WECHAT_FOLDER = r"D:\Users\lenovo\Documents\WeChat Files\WeChat Files\bringsmile\FileStorage\File"

# 100K图幅名称信息等查询表格（lookup table） 
SHEET_NAMES_LUT_100K = "100K_sheet_names_271_name_V3_after_GEOSA_edit.xlsx"

# 图标文件
ICON_FILE_1 = "Layer0_Symbol_Square.png"

# 设置制图工程文件夹
MAP_PROJECT_FOLDER = "Finished observation points of Group3"

# 设置文件向后回溯查找的日期，格式为"YYYYMMDD"
# 一般设置为该批次图幅开始的日期，例如"20240901"
TRACEBACK_DATE = "20250301"
# 设置文件向后回溯查找的天数
TRACEBACK_DAYS = 60
# 设置文件向前查找的天数
TRACEFORWARD_DAYS = 5

# 设置每周的星期几进行数据收集，0-6分别表示星期一至星期日
# 周一是0，周二是1，周三是2，周四是3，周五是4，周六是5，周日是6
# 例如，[1, 3, 5]表示每周的星期二、星期四、星期六进行数据收集
COLLECTION_WEEKDAYS = [5]

# 设置需要统计的图幅的最小和最大序号，包括最小和最大序号
# 例如，SEQUENCE_MIN = 1, SEQUENCE_MAX = 22，表示统计1-22图幅，序号来源于100K图幅名称信息等查询表格lookup table
SEQUENCE_MIN = 26
SEQUENCE_MAX = 40

# 建立资源文件目录，并验证文件是否存在，为当前文件夹子目录中的文件
# 100K图幅名称信息等
# SHEET_NAMES_FILE = os.path.join(WORKSPACE, 'resource', 'private', SHEET_NAMES_LUT_100K)
SHEET_NAMES_FILE = os.path.join('.', 'resource', 'private', SHEET_NAMES_LUT_100K)

# 图标文件
# ICON_1 = os.path.join(WORKSPACE, 'resource', 'private', ICON_FILE_1)
ICON_1 = os.path.join('.', 'resource', 'private', ICON_FILE_1)

# KML文件的XSD模式，分别为2.2和2.3版本，为当前文件夹子目录中的文件
# KML_SCHEMA_22 = os.path.join(WORKSPACE, 'resource', 'kml_xsd', '220', 'ogckml22.xsd')
# KML_SCHEMA_23 = os.path.join(WORKSPACE, 'resource', 'kml_xsd', '230', 'ogckml23.xsd')
KML_SCHEMA_22 = os.path.join('.', 'resource', 'kml_xsd', '220', 'ogckml22.xsd')
KML_SCHEMA_23 = os.path.join('.', 'resource', 'kml_xsd', '230', 'ogckml23.xsd')

# 验证文件是否存在
if not os.path.exists(SHEET_NAMES_FILE):
    raise FileNotFoundError(f"文件'{SHEET_NAMES_FILE}'不存在，请在config.py中设置正确的文件路径")
if not os.path.exists(ICON_1):
    raise FileNotFoundError(f"文件'{ICON_1}'不存在，请在config.py中设置正确的文件路径")
if not os.path.exists(KML_SCHEMA_22):
    raise FileNotFoundError(f"文件'{KML_SCHEMA_22}'不存在，请在config.py中设置正确的文件路径")
if not os.path.exists(KML_SCHEMA_23):
    raise FileNotFoundError(f"文件'{KML_SCHEMA_23}'不存在，请在config.py中设置正确的文件路径")


EMPTY_DICT = {}


def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Function '{func.__name__}' executed in {elapsed_time:.4f} seconds")
        return result
    return wrapper


class Logger:

    _instance = None

    EMAIL_CONFIG = {
        'mailhost': 'smtp.example.com',
        'port': 587,
        'fromaddr': 'your_email@example.com',
        'toaddrs': ['recipient@example.com'],
        'subject': 'Application Error',
        'username': 'your_email@example.com',
        'password': 'your_password'
    }

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self, name='global_logger', log_file='app.log', level=logging.INFO, max_bytes=5*1024*1024, backup_count=2, email_config=None):
        if 'logger' not in self.__dict__:
            self.logger = logging.getLogger(name)
            self.logger.setLevel(level)
            self._add_handler(logging.StreamHandler(sys.stdout), self._logger_format())
            self._add_handler(RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count), self._logger_format())
            if email_config:
                self._add_mail_handler(email_config)

    def _add_handler(self, handler, formatter):
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _add_mail_handler(self, email_config):
        mail_handler = SMTPHandler(
            mailhost=(email_config['mailhost'], email_config['port']),
            fromaddr=email_config['fromaddr'],
            toaddrs=email_config['toaddrs'],
            subject=email_config['subject'],
            credentials=(email_config['username'], email_config['password']),
            secure=()
        )
        mail_handler.setLevel(logging.ERROR)
        self._add_handler(mail_handler, self._logger_format())

    def _logger_format(self, format_='default'):
        if format_ == 'default':
            return logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        elif format_ == 'simple':
            return logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)

    def close(self, message=None):
        for handler in self.logger.handlers:
            if message:
                self.logger.info(message)
            handler.close()
            self.logger.removeHandler(handler)


@dataclass
class DateType:

    date_datetime: datetime = None
    yyyymmdd_str: str = ''
    yymmdd_str: str = ''
    yyyy_str: str = ''
    yyyy_mm_str: str = ''
    yy_str: str = ''
    mm_str: str = ''
    dd_str: str = ''
    yymm_str: str = ''

    def __post_init__(self):
        if self.yyyymmdd_str:
            self.date_datetime = datetime.strptime(self.yyyymmdd_str, "%Y%m%d")
        elif self.date_datetime:
            self.yyyymmdd_str = self.date_datetime.strftime("%Y%m%d")
        self._set_date_strings()

    def _set_date_strings(self):
        self.yymmdd_str = self.date_datetime.strftime("%y%m%d")
        self.yyyymm_str = self.date_datetime.strftime("%Y%m")
        self.yyyy_str = self.date_datetime.strftime("%Y")
        self.yy_str = self.date_datetime.strftime("%y")
        self.mm_str = self.date_datetime.strftime("%m")
        self.dd_str = self.date_datetime.strftime("%d")
        self.yyyy_mm_str = self.date_datetime.strftime("%Y-%m")
        self.yymm_str = self.date_datetime.strftime("%y%m")

    def __str__(self):
        return self.yyyymmdd_str


if __name__ == "__main__":
    logger = Logger(name='my_logger', log_file='my_app.log', level=logging.DEBUG, email_config=Logger.EMAIL_CONFIG)
    logger.debug('这是一个调试消息')
    logger.info('这是一个信息消息')
    logger.warning('这是一个警告消息')
    logger.error('这是一个错误消息')
    logger.critical('这是一个严重错误消息')
    logger.close(message="日志记录器关闭, 程序结束")
