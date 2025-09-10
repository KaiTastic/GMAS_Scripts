"""
进度估算模块 - 现代化估算引擎

专为GMAS项目进度跟踪和完成日期估算设计的高性能模块。
提供统一的API接口、智能任务调度和配置管理功能。

## 快速开始

### 1. 简单估算
```python
from core.progress_estimation import quick_estimate

result = quick_estimate(target_points=5000, current_points=1500)
print(f"预计完成日期: {result['estimated_finish_date']}")
```

### 2. 高级估算
```python
from core.progress_estimation import EstimationFacade

facade = EstimationFacade()
result = facade.advanced_estimate(
    target_points=5000,
    current_points=1500,
    confidence_level=0.8,
    include_charts=True
)
```

### 3. 批量图幅估算
```python
from core.progress_estimation import EstimationScheduler

with EstimationScheduler() as scheduler:
    task_id = scheduler.submit_batch_estimation(
        'batch_001',
        mapsheet_list=['H49E001001', 'H49E001002']
    )
    # 等待完成...
    result = scheduler.get_task_status(task_id)
```

## 核心组件

- **EstimationFacade**: 简化的统一接口
- **CoreEstimator**: 核心估算引擎
- **EstimationScheduler**: 智能任务调度器
- **EstimationConfigManager**: 配置管理器
"""

import logging
from typing import List

logger = logging.getLogger(__name__)

try:
    # 核心接口
    from .estimation_facade import EstimationFacade
    from .core_estimator import CoreEstimator, EstimationConfig, EstimationMode
    from .estimation_scheduler import EstimationScheduler, TaskPriority, EstimationTask
    
    # 配置管理
    from .estimation_config import (
        EstimationConfigManager, 
        DataSourceConfig, 
        EstimationMethodConfig,
        ChartConfig,
        OutputConfig,
        PerformanceConfig
    )
    
    # 便捷函数
    def quick_estimate(target_points: int, current_points: int = None, workspace_path: str = None) -> dict:
        """
        快速估算便捷函数
        
        Args:
            target_points: 目标点数
            current_points: 当前点数
            workspace_path: 工作空间路径
            
        Returns:
            dict: 估算结果摘要
        """
        try:
            facade = EstimationFacade(workspace_path)
            return facade.quick_estimate(target_points, current_points)
        except Exception as e:
            logger.error(f"快速估算失败: {e}")
            return {
                'error': str(e),
                'completion_percentage': 0,
                'estimated_finish_date': None,
                'days_remaining': 0
            }
    
    def advanced_estimate(target_points: int, 
                         current_points: int = None,
                         confidence_level: float = 0.8, 
                         workspace_path: str = None) -> dict:
        """
        高级估算便捷函数
        
        Args:
            target_points: 目标点数
            current_points: 当前点数
            confidence_level: 置信水平
            workspace_path: 工作空间路径
            
        Returns:
            dict: 完整的估算结果
        """
        try:
            facade = EstimationFacade(workspace_path)
            return facade.advanced_estimate(target_points, current_points, confidence_level)
        except Exception as e:
            logger.error(f"高级估算失败: {e}")
            return {
                'error': str(e),
                'estimation_mode': 'advanced',
                'timestamp': None
            }
    
    def batch_mapsheet_estimate(mapsheet_list: List[str] = None, 
                               confidence_level: float = 0.8,
                               workspace_path: str = None) -> dict:
        """
        批量图幅估算便捷函数
        
        Args:
            mapsheet_list: 图幅列表
            confidence_level: 置信水平
            workspace_path: 工作空间路径
            
        Returns:
            dict: 批量估算结果
        """
        try:
            facade = EstimationFacade(workspace_path)
            return facade.mapsheet_estimation_batch(mapsheet_list, confidence_level)
        except Exception as e:
            logger.error(f"批量图幅估算失败: {e}")
            return {
                'error': str(e),
                'total_mapsheets': 0,
                'successful_estimates': 0,
                'failed_estimates': 0
            }
    
    # 版本信息
    __version__ = "1.1.0"
    __author__ = "Kai Cao"
    
    # 公开API
    __all__ = [
        # 核心接口
        'EstimationFacade',
        'CoreEstimator', 
        'EstimationConfig',
        'EstimationMode',
        'EstimationScheduler',
        'TaskPriority',
        'EstimationTask',
        
        # 配置管理
        'EstimationConfigManager',
        'DataSourceConfig',
        'EstimationMethodConfig',
        'ChartConfig',
        'OutputConfig',
        'PerformanceConfig',
        
        # 便捷函数
        'quick_estimate',
        'advanced_estimate',
        'batch_mapsheet_estimate'
    ]
    
    logger.info(f"进度估算模块加载成功 - 版本: {__version__}")
    
except ImportError as e:
    logger.error(f"导入进度估算模块时出错: {e}")
    __all__ = []