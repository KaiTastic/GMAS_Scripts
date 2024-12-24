import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
from os import close
import re
import sys


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
ICON_FILE = "Layer0_Symbol_Square.png"

# 设置制图工程文件夹
MAP_PROJECT_FOLDER = "Finished observation points of Group1"

# 设置文件向后回溯查找的日期，格式为"YYYYMMDD"
# 一般设置为该批次图幅开始的日期，例如"20240901"
TRACEBACK_DATE = "20240901"
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
SEQUENCE_MIN = 1
SEQUENCE_MAX = 22












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
        if not cls._instance:
            cls._instance = super(cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, name='global_logger', log_file='app.log', level=logging.INFO, max_bytes=5*1024*1024, backup_count=2, email_config=None):
        if 'logger' not in self.__dict__:
            self.logger = logging.getLogger(name)
            self.logger.setLevel(level)

            # 控制台日志处理器
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(self.loggerFormat())
            self.logger.addHandler(console_handler)

            # 文件日志处理器，带有日志轮转功能
            file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
            file_handler.setFormatter(self.loggerFormat())
            self.logger.addHandler(file_handler)

            # 如果提供了电子邮件配置，添加电子邮件处理器
            if email_config:
                self.mail_handler(email_config)

    def loggerFormat(self, format_='default'):
        # 设置日志格式
        if format_ == 'default':
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        elif format_ == 'simple':
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        return formatter

    def mail_handler(self, email_config=None):
        mail_handler = SMTPHandler(
            mailhost=(email_config['mailhost'], email_config['port']),
            fromaddr=email_config['fromaddr'],
            toaddrs=email_config['toaddrs'],
            subject=email_config['subject'],
            credentials=(email_config['username'], email_config['password']),
            secure=()
        )
        mail_handler.setLevel(logging.ERROR)
        mail_handler.setFormatter(self.loggerFormat())
        self.logger.addHandler(mail_handler)
        
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


# 示例用法, 请根据实际情况修改, 例如邮件配置
if __name__ == "__main__":


    logger = Logger(name='my_logger', log_file='my_app.log', level=logging.DEBUG, email_config=Logger.EMAIL_CONFIG)

    logger.debug('这是一个调试消息')
    logger.info('这是一个信息消息')
    logger.warning('这是一个警告消息')
    logger.error('这是一个错误消息')
    logger.critical('这是一个严重错误消息')

