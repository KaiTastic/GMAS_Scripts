"""
DailyFileGenerator 兼容层

为了保持与现有代码的兼容性，这个模块重新导出重构后的类
"""

import warnings
from datetime import datetime, timedelta

# 导入重构后的模块
try:
    from core.data_models import ObservationData, FileAttributes, DateIterator, DateType
    from core.file_handlers import FileIO, GeneralIO, KMZFile
    from core.utils import list_fullpath_of_files_with_keywords, find_files_with_max_number
    from core.mapsheet import MapsheetDailyFile, CurrentDateFiles
    from core.reports import DataSubmition
    
    # 兼容性警告
    warnings.warn(
        "直接从 DailyFileGenerator 导入已弃用。请使用 core 包中的模块。",
        DeprecationWarning,
        stacklevel=2
    )
    
    # 导出所有类以保持向后兼容
    __all__ = [
        'ObservationData',
        'FileAttributes', 
        'DateType',
        'DateIterator',
        'FileIO',
        'GeneralIO',
        'KMZFile',
        'MapsheetDailyFile',
        'CurrentDateFiles',
        'DataSubmition',
        'list_fullpath_of_files_with_keywords',
        'find_files_with_max_number'
    ]
    
except ImportError as e:
    print(f"警告：导入重构模块失败，回退到原始实现: {e}")
    
    # 如果导入失败，这里可以定义一些基本的兼容性类
    class ObservationData:
        def __init__(self, *args, **kwargs):
            raise ImportError("请安装所需的依赖包或检查模块路径")
    
    __all__ = []


# 保留原有的主函数逻辑以确保兼容性
if __name__ == "__main__":
    try:
        from core.data_models import DateType
        from config import TRACEBACK_DATE
        
        # 回溯日期测试
        date = DateType(date_datetime=datetime.now())
        while date.date_datetime > datetime.strptime(TRACEBACK_DATE, "%Y%m%d"):
            collection = CurrentDateFiles(date)
            print(f"{date}新增点数: ", collection.totalDaiyIncreasePointNum, 3*"\n")
            print(f"{collection}")
            date = DateType(date_datetime=date.date_datetime - timedelta(days=1))
    except Exception as e:
        print(f"运行主函数时出错: {e}")
