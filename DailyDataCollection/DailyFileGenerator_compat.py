"""
DailyFileGenerator 兼容层

为现有代码提供完整的向后兼容性支持
从原始文件导入完整功能以确保方法可用性
"""

import warnings
import os
import sys

# 兼容性警告
warnings.warn(
    "DailyFileGenerator 已被重构。建议迁移到新的模块化结构。",
    DeprecationWarning,
    stacklevel=2
)

# 首先尝试从原始文件导入完整功能
try:
    # 添加 deprecated 目录到 Python 路径
    deprecated_path = os.path.join(os.path.dirname(__file__), 'deprecated')
    if deprecated_path not in sys.path:
        sys.path.insert(0, deprecated_path)
    
    # 为了避免执行原始文件的主函数，我们需要安全地导入
    # 读取原始文件内容，但跳过主函数执行部分
    with open(os.path.join(deprecated_path, 'DailyFileGenerator.py'), 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    # 创建一个修改版本，禁用主函数执行
    safe_content = original_content.replace(
        'if __name__ == "__main__":',
        'if False:  # 兼容层：禁用主函数执行'
    )
    
    # 执行修改后的代码
    exec_globals = {}
    exec(safe_content, exec_globals)
    
    # 提取需要的类和函数
    ObservationData = exec_globals['ObservationData']
    FileAttributes = exec_globals['FileAttributes']
    DateIterator = exec_globals['DateIterator']
    DateType = exec_globals['DateType']
    FileIO = exec_globals['FileIO']
    GeneralIO = exec_globals['GeneralIO']
    KMZFile = exec_globals['KMZFile']
    MapsheetDailyFile = exec_globals['MapsheetDailyFile']
    CurrentDateFiles = exec_globals['CurrentDateFiles']
    DataSubmition = exec_globals['DataSubmition']
    list_fullpath_of_files_with_keywords = exec_globals['list_fullpath_of_files_with_keywords']
    find_files_with_max_number = exec_globals['find_files_with_max_number']
    
    print("兼容层：使用原始完整实现（安全导入）")
    IMPORT_SUCCESS = True
    
except ImportError as e:
    print(f"警告：无法从原始文件导入完整功能 ({e})，尝试新模块...")
    IMPORT_SUCCESS = False
    
    # 尝试从新模块导入
    try:
        from core.data_models import ObservationData, FileAttributes, DateIterator, DateType
        from core.file_handlers import FileIO, GeneralIO, KMZFile  
        from core.mapsheet import MapsheetDailyFile, CurrentDateFiles
        from core.reports import DataSubmition
        from core.utils import list_fullpath_of_files_with_keywords, find_files_with_max_number
        
        print("兼容层：使用新的模块化结构")
        IMPORT_SUCCESS = True
        
    except ImportError as e2:
        print(f"错误：新模块也不可用 ({e2})，使用基本占位符")
        
        # 从配置文件导入基本的 DateType
        try:
            from config import DateType
        except ImportError:
            from datetime import datetime
            class DateType:
                def __init__(self, date_datetime=None):
                    self.date_datetime = date_datetime or datetime.now()
        
        # 基本占位符实现
        class FunctionalPlaceholder:
            def __init__(self, *args, **kwargs):
                print(f"警告：{self.__class__.__name__} 使用占位符实现，功能可能受限")
                # 为了避免属性错误，添加一些基本属性
                self.totalDaiyIncreasePointNum = 0
                self.allPoints = []
                
            def __getattr__(self, name):
                # 动态处理缺失的方法
                def placeholder_method(*args, **kwargs):
                    print(f"警告：方法 {name} 不可用（占位符实现）")
                    return None
                return placeholder_method
        
        # 占位符类
        ObservationData = FunctionalPlaceholder
        FileAttributes = FunctionalPlaceholder  
        DateIterator = FunctionalPlaceholder
        FileIO = FunctionalPlaceholder
        GeneralIO = FunctionalPlaceholder
        KMZFile = FunctionalPlaceholder
        MapsheetDailyFile = FunctionalPlaceholder
        CurrentDateFiles = FunctionalPlaceholder
        DataSubmition = FunctionalPlaceholder
        
        def list_fullpath_of_files_with_keywords(*args, **kwargs):
            print("警告：list_fullpath_of_files_with_keywords 功能不可用")
            return []
            
        def find_files_with_max_number(*args, **kwargs):
            print("警告：find_files_with_max_number 功能不可用") 
            return None

# 导出列表
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

if __name__ == "__main__":
    print("DailyFileGenerator 兼容层测试")
    print(f"DateType 可用: {DateType}")
    print(f"CurrentDateFiles 可用: {CurrentDateFiles}")
    if hasattr(CurrentDateFiles, 'dailyExcelReportUpdate'):
        print("✓ dailyExcelReportUpdate 方法可用")
    else:
        print("✗ dailyExcelReportUpdate 方法不可用")
    print("兼容层功能测试完成")
