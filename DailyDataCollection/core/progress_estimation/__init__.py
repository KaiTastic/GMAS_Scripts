"""
进度估算模块

包含项目进度跟踪、完成日期估算和燃尽/燃起图表生成功能：
- DataAnalyzer: 数据分析器，处理历史观测数据，支持真实数据和模拟数据
- FinishDateEstimator: 完成日期估算器
- ProgressCharts: 燃尽/燃起图表生成器
- ProgressTracker: 进度跟踪器，集成所有功能
- ExcelDataConnector: Excel数据连接器，读取真实GMAS数据
"""

try:
    from .data_analyzer import DataAnalyzer
    from .finish_date_estimator import FinishDateEstimator
    from .progress_charts import ProgressCharts
    from .progress_tracker import ProgressTracker
    from .excel_data_connector import ExcelDataConnector
    from .real_excel_data_connector import RealExcelDataConnector
    from .mapsheet_estimation_runner import MapsheetEstimationRunner
    from .method_integrator import MethodIntegrator
    from .completed_project_handler import CompletedProjectHandler

    __all__ = [
        'DataAnalyzer',
        'FinishDateEstimator', 
        'ProgressCharts',
        'ProgressTracker',
        'ExcelDataConnector',
        'RealExcelDataConnector',
        'MapsheetEstimationRunner',
        'MethodIntegrator',
        'CompletedProjectHandler'
    ]
except ImportError as e:
    print(f"导入进度估算模块时出错: {e}")
    __all__ = []