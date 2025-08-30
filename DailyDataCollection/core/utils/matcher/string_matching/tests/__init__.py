#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多目标字符串匹配器测试框架初始化文件
"""

import sys
import os

# 添加父目录到路径，确保可以导入主模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 测试框架版本
__version__ = "1.0.0"
__author__ = "GitHub Copilot"
__description__ = "多目标字符串匹配器测试框架"

# 导入测试基类
from .base_test import BaseTestCase
from .test_runner import TestRunner
from .test_evaluator import TestEvaluator

__all__ = [
    'BaseTestCase',
    'TestRunner', 
    'TestEvaluator'
]
