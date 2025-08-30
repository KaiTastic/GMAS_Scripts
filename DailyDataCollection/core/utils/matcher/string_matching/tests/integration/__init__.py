#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试模块初始化
"""

from .test_end_to_end import TestEndToEnd
from .test_integration_scenarios import TestIntegrationScenarios
from .test_real_world_data import TestRealWorldData

__all__ = [
    'TestEndToEnd',
    'TestIntegrationScenarios',
    'TestRealWorldData'
]
