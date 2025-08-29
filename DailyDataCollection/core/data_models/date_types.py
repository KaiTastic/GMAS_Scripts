"""
日期类型和迭代器模块

包含日期处理相关的类和工具
"""

from datetime import datetime, timedelta
from typing import Literal, Optional
from dataclasses import dataclass


@dataclass
class DateType:
    """日期类型类，用于处理日期的各种格式"""

    date_datetime: Optional[datetime] = None
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
        """设置各种日期字符串格式"""
        if self.date_datetime:
            self.yymmdd_str = self.date_datetime.strftime("%y%m%d")
            self.yyyymm_str = self.date_datetime.strftime("%Y%m")
            self.yyyy_str = self.date_datetime.strftime("%Y")
            self.yy_str = self.date_datetime.strftime("%y")
            self.mm_str = self.date_datetime.strftime("%m")
            self.dd_str = self.date_datetime.strftime("%d")
            self.yyyy_mm_str = self.date_datetime.strftime("%Y-%m")
            self.yymm_str = self.date_datetime.strftime("%y%m")

    def __str__(self) -> str:
        return self.yyyymmdd_str


class DateIterator:
    """日期迭代器类，用于按指定方向迭代日期"""
    
    def __init__(self, start_date: str, direction: Literal['forward', 'backward'] = 'forward'):
        """
        初始化迭代器
        
        Args:
            start_date: 起始日期, 格式为 'YYYYMMDD'
            direction: 迭代方向
                'forward': 从起始日期开始向后迭代, 即向前（下一天）迭代
                'backward': 从起始日期开始向前迭代, 即向后（上一天）迭代
        """
        # 将字符串日期转换为 datetime 对象
        self.date = datetime.strptime(start_date, "%Y%m%d")
        self.direction = direction

    def __iter__(self):
        """返回迭代器自身"""
        return self

    def __next__(self) -> str:
        """根据迭代方向返回下一个日期"""
        if self.direction == 'forward':
            self.date += timedelta(days=1)
        elif self.direction == 'backward':
            self.date -= timedelta(days=1)
        else:
            raise ValueError("Invalid direction. Use 'forward' or 'backward'.")

        # 返回当前日期并格式化为字符串
        return self.date.strftime("%Y%m%d")

    def switch_direction(self) -> None:
        """切换迭代方向"""
        if self.direction == 'forward':
            self.direction = 'backward'
        else:
            self.direction = 'forward'

    def reset(self, new_start_date: str) -> None:
        """重置为新的起始日期"""
        self.date = datetime.strptime(new_start_date, "%Y%m%d")
