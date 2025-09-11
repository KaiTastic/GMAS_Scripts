"""
Progress Estimation Module

提供生产进度评估和预测功能。
"""

from .core_estimator import CoreEstimator
from .estimation_facade import EstimationFacade
from .estimation_scheduler import EstimationScheduler
from .mapsheet_completion_calculator import MapsheetCompletionCalculator
from .real_target_completion_predictor import RealTargetCompletionPredictor

# 统一使用主配置管理器
from config.config_manager import ConfigManager

__all__ = [
    'CoreEstimator',
    'EstimationFacade',
    'EstimationScheduler', 
    'MapsheetCompletionCalculator',
    'RealTargetCompletionPredictor',
    'ConfigManager'
]

__version__ = "2.0.0"
